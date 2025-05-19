import logging
import os
import subprocess
import time
from queue import Empty, Queue
from threading import Lock, Thread
from typing import IO, Any

import unidecode

from htpclient.chunk import Chunk
from htpclient.generic_status import GenericStatus
from htpclient.operating_system import OperatingSystem
from htpclient.task import Task
from htpclient.utils import (
    format_speed,
    kill_hashcat,
    run_command_and_get_output,
    run_command_and_get_output_and_errors,
)


class GenericCracker:
    """Class representing a Hashcat cracker"""

    crack_split_length = 1000

    def __init__(self, agent: Any, task: Task):  # pylint: disable=E0601:used-before-assignment
        self.agent = agent
        self.task = task
        self.queue: Queue[tuple[str, bytes]] = Queue()
        self.call_path = f"{self.task.cracker.executable}"

        self.lock = Lock()
        self.cracks: list[str] = []
        self.first_status = False
        self.use_pipe = self.task.use_pipe
        self.progress = 0
        self.status_count = 0
        self.last_update = 0
        self.uses_slow_hash_flag = False
        self.was_stopped = False

    def measure_keyspace(self, chunk: Chunk):  # pylint: disable=R0912:too-many-branches
        """Measure the keyspace of a chunk"""
        attack_command = (
            self.task.attack_command.replace(self.task.hashlist_alias, "")
            if self.task.hashlist_alias
            else self.task.attack_command
        )

        command = f"{self.call_path} keyspace {attack_command}"

        try:
            lines = run_command_and_get_output(command)
        except subprocess.CalledProcessError as e:
            self.agent.send_error(f"Error while measuring keyspace: {e}", self.task.task_id)
            return False

        keyspace = 0

        for line in lines:
            if not line:
                continue

            try:
                keyspace = int(line)
            except ValueError:
                pass

        if keyspace == 0:
            self.agent.send_error("Failed to measure keyspace as keyspace is 0", self.task.task_id)
            return False

        return chunk.send_keyspace(keyspace)

    def run_benchmark(self, chunk: Chunk):
        """Run a benchmark"""
        hashlists_path = self.agent.config.get_value("hashlists-path")

        if not isinstance(hashlists_path, str):
            self.agent.send_error("Hashlists path not set", self.task.task_id)
            return None

        hashlist_path = os.path.join(hashlists_path, str(self.task.hashlist_id))

        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, f'"{hashlist_path}"')

        command = f"{self.call_path} crack {attack_command} -s 0 -l {chunk.length} --timeout={self.task.benchmark_time}"

        try:
            output_lines, error_lines = run_command_and_get_output_and_errors(command, ["CL_DEVICE_NOT_AVAILABLE"])
        except Exception as e:
            self.agent.send_error(f"Error while running benchmark: {e}", self.task.task_id)
            return 0

        for line in error_lines:
            if not line:
                continue

            self.agent.send_warning(f"Error while running benchmark: {line}", self.task.task_id)

        last_valid_status = None
        for line in output_lines:
            if not line:
                continue

            status = GenericStatus(line)
            if status.is_valid():
                last_valid_status = status

        if last_valid_status is None:
            self.agent.send_error("Failed to run benchmark", self.task.task_id)
            return 0

        return float(last_valid_status.get_progress()) / 10000

    def run_chunk(self, chunk: Chunk):
        """Run a chunk"""
        self.status_count = 0
        self.was_stopped = False

        hashlists_path = self.agent.config.get_value("hashlists-path")
        zaps_path = self.agent.config.get_value("zaps-path")

        if not isinstance(hashlists_path, str):
            self.agent.send_error("Hashlists path not set", self.task.task_id)
            return

        if not isinstance(zaps_path, str):
            self.agent.send_error("Zaps path not set", self.task.task_id)
            return

        hashlist_path = os.path.join(hashlists_path, str(self.task.hashlist_id))
        hashlist_output_path = os.path.join(hashlists_path, str(self.task.hashlist_id) + ".out")
        hashlist_output_backup_path = os.path.join(
            hashlists_path, str(self.task.hashlist_id) + str(time.time()) + ".out.bak"
        )
        zap_path = os.path.join(zaps_path, f"hashlist_{self.task.hashlist_id}")

        if os.path.exists(hashlist_output_path):
            if self.agent.config.get_value("outfile-history"):
                os.rename(hashlist_output_path, hashlist_output_backup_path)
            else:
                os.remove(hashlist_output_path)

        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, f'"{hashlist_path}"')

        command = f"{self.call_path} crack -s {chunk.skip} -l {chunk.length} {attack_command}"

        if self.agent.operating_system != OperatingSystem.WINDOWS:
            process = subprocess.Popen(  # pylint: disable=W1509:subprocess-popen-preexec-fn
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )
        else:
            process = subprocess.Popen(  # pylint: disable=R1732:consider-using-with
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        stdout_watcher = Thread(target=self.__watch_stream, args=("OUT", process.stdout))
        stderr_watcher = Thread(target=self.__watch_stream, args=("ERR", process.stderr))

        stdout_watcher.start()
        stderr_watcher.start()

        self.first_status = False
        self.last_update = time.time()

        main_thread = Thread(target=self.__run, name="GenericCrackerRun", args=(process, chunk, zap_path))
        main_thread.start()

        process.wait()
        stdout_watcher.join()
        stderr_watcher.join()
        main_thread.join()

    def __run(self, process: subprocess.Popen[Any], chunk: Chunk, zap_path: str):  # pylint: disable=R0912,R0914,R0915
        """Run the Hashcat process"""
        self.cracks = []

        while True:
            try:
                if not self.first_status and time.time() - self.last_update > 10:
                    query: dict[str, Any] = {
                        "action": "sendProgress",
                        "chunkId": chunk.chunk_id,
                        "keyspaceProgress": chunk.skip,
                        "relativeProgress": 0,
                        "speed": 0,
                        "state": 2,
                        "cracks": [],
                    }

                    self.agent.post(query)
                    self.last_update = time.time()

                # Send error message when last update is more then 30 minutes ago
                if time.time() - self.last_update > 1800:
                    self.agent.send_error("No status update for at least 1800 seconds", self.task.task_id)

                name, line = self.queue.get(timeout=1)
            except Empty:
                if process.poll() is not None:
                    break
                continue

            if name == "OUT":
                status = GenericStatus(line.decode())

                if status.is_valid():
                    self.status_count += 1
                    relative_progress = status.get_progress()
                    speed = status.get_speed()

                    self.first_status = True
                    initial = True

                    state = 4 if relative_progress == 10000 else 2

                    while self.cracks or initial:
                        with self.lock:
                            initial = False
                            crack_backup: list[str] = []

                            if len(self.cracks) > self.crack_split_length:
                                crack_count = 0
                                new_cracks: list[str] = []

                                for crack in self.cracks:
                                    crack_count += 1
                                    if crack_count > self.crack_split_length:
                                        crack_backup.append(crack)
                                    else:
                                        new_cracks.append(crack)

                                self.cracks = new_cracks

                            query: dict[str, Any] = {
                                "action": "sendProgress",
                                "chunkId": chunk.chunk_id,
                                "keyspaceProgress": chunk.skip,
                                "relativeProgress": relative_progress,
                                "speed": speed,
                                "state": state,
                                "cracks": self.cracks,
                            }

                            query["cracks"] = self.cracks

                            if len(self.cracks) > 0:
                                logging.info("Found %d cracks. Sending to server...", len(self.cracks))
                                logging.info(self.cracks)

                            response = self.agent.post(query)
                            self.last_update = time.time()

                            if response is None:
                                self.was_stopped = True
                                try:
                                    kill_hashcat(process.pid, self.agent.operating_system)
                                except ProcessLookupError:
                                    pass
                                return

                            if response.get("agent") == "stop":
                                self.was_stopped = True
                                try:
                                    kill_hashcat(process.pid, self.agent.operating_system)
                                except ProcessLookupError:
                                    pass
                                return

                            if len(self.cracks) > 0:
                                logging.info(
                                    "Send %d cracked hashes to server for chunk %d should be %d - %d skipped",
                                    len(self.cracks),
                                    chunk.chunk_id,
                                    len(self.cracks),
                                    response["skipped"],
                                )

                            zaps = response.get("zaps")

                            if zaps:
                                zap_output = "\tFF\n".join(zaps) + "\tFF\n"
                                with open(os.path.join(zap_path, f"{time.time()}"), "a+", encoding="utf-8") as f:
                                    f.write(zap_output)

                            print(
                                f"Progress: {relative_progress / 100:.2f}% Speed: {format_speed(speed)} Cracks:"
                                f" {len(self.cracks)} Accepted: {response['cracked']} Skips:"
                                f" {response['skipped']} Zaps: {len(zaps)}",
                                end="\r",
                            )

                            self.cracks = crack_backup
                else:
                    try:
                        if b":" not in line:
                            self.agent.send_warning(
                                f"GenericCracker: Unknown line {unidecode.unidecode(line.decode().strip())}",
                                self.task.task_id,
                            )
                            continue
                    except UnicodeDecodeError:
                        self.agent.send_warning(f"GenericCracker: Unknown line {line.strip()}", self.task.task_id)
                        continue

                    try:
                        line = line.decode()
                    except UnicodeDecodeError:
                        line = "$HEX[" + line.hex() + "]"

                    self.cracks.append(line.strip())

            elif name == "ERR":
                msg = unidecode.unidecode(line.decode().strip())
                if msg and msg != "^C":
                    self.agent.send_error(f"Generic cracker error: {msg}", self.task.task_id)

    def __watch_stream(self, name: str, stream: IO[bytes]):
        for line in stream:
            self.queue.put((name, line))

        if not stream.closed:
            stream.close()

    def agent_stopped(self):
        """Check if the agent was stopped"""
        return self.was_stopped
