import logging
import os
import re
import string
import subprocess
import time
from queue import Empty, Queue
from threading import Lock, Thread
from typing import IO, Any

import psutil
import unidecode

from htpclient.chunk import Chunk
from htpclient.hashcat_status import HashcatStatus
from htpclient.operating_system import OperatingSystem
from htpclient.task import Task
from htpclient.utils import (
    format_speed,
    kill_hashcat,
    run_command_and_get_output,
    run_command_and_get_output_and_errors,
)


class HashcatCracker:
    """Class representing a Hashcat cracker"""

    crack_split_length = 1000

    def __init__(self, agent: Any, task: Task):  # pylint: disable=E0601:used-before-assignment
        self.agent = agent
        self.task = task
        self.queue: Queue[tuple[str, bytes]] = Queue()
        self.call_path = f"{self.task.cracker.executable}"

        try:
            output = run_command_and_get_output(f"{self.call_path} --version")
        except subprocess.CalledProcessError as e:
            self.agent.send_error(f"Error while checking cracker version: {e}")
            return

        self.version = output[0].strip().replace("v", "")
        self.lock = Lock()
        self.cracks: list[str] = []
        self.first_status = False
        self.use_pipe = self.task.use_pipe
        self.progress = 0
        self.status_count = 0
        self.last_update = 0
        self.uses_slow_hash_flag = False
        self.was_stopped = False

        self.new_output_format = self.__determine_output_format()

        self.output_format = "1,2,3,4" if self.new_output_format else "15"

    def __determine_output_format(self):  # pylint: disable=R0911:too-many-return-statements
        """Determine if the output format is new"""
        if not "-" in self.version:
            release = self.version.split(".")

            try:
                if int(release[0]) >= 6:
                    return True
            except ValueError:
                return True

            return False

        if len(self.version.split("-")) == 1:
            self.agent.send_warning(f"Could not determine hashcat output format version: {self.version}")
            return False

        release = self.version.split("-")[0].split(".")
        commit = self.version.split("-")[1]

        try:
            if int(release[0]) < 5:
                return False

            if int(release[0]) == 5 and int(release[1]) < 1:
                return False

            if int(release[0]) == 5 and int(release[1]) == 1 and int(release[2]) == 0 and int(commit) < 1618:
                return False

        except ValueError:
            return True

        return True

    def measure_keyspace(self, chunk: Chunk):  # pylint: disable=R0912:too-many-branches
        """Measure the keyspace of a chunk"""
        if self.task.use_preprocessor:
            return self.__measure_keyspace_with_preprocessor(chunk)

        attack_command = (
            self.task.attack_command.replace(self.task.hashlist_alias, "")
            if self.task.hashlist_alias
            else self.task.attack_command
        )

        command = f"{self.call_path} --keyspace --quiet {attack_command} {self.task.command_parameters}"

        if self.task.use_brain:
            command += " -S"

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

            if "--encoding-to iso-8859-1" in attack_command:
                command = (
                    f"{self.call_path} --keyspace --quiet {attack_command} --encoding-from iso-8859-1"
                    f" {self.task.command_parameters}"
                )

                try:
                    lines = run_command_and_get_output(command)
                except subprocess.CalledProcessError as e:
                    self.agent.send_error(f"Error while measuring keyspace: {e}", self.task.task_id)
                    return False

                new_keyspace = 0

                for line in lines:
                    if not line:
                        continue

                    try:
                        new_keyspace = int(line)
                    except ValueError:
                        pass

                if new_keyspace != 0:
                    self.agent.send_error(
                        "Keyspace is 0, but it is not 0 with iso-8859-1 encoding change the attack command to use from"
                        " this encoding",
                        self.task.task_id,
                    )
            return False

        return chunk.send_keyspace(keyspace)

    def __measure_keyspace_with_preprocessor(self, chunk: Chunk):

        if self.task.preprocessor.keyspace_command is None:
            return chunk.send_keyspace(-1)

        if self.agent.operating_system == OperatingSystem.WINDOWS:
            call_path = f'"{self.task.preprocessor.executable}"'
        else:
            call_path = f'"./{self.task.preprocessor.executable}"'

        command = f"{call_path} {self.task.preprocessor.keyspace_command} {self.task.preprocessor_command}"

        try:
            lines = run_command_and_get_output(command)
        except subprocess.CalledProcessError as e:
            self.agent.send_error(f"Error while measuring keyspace for preprocessor: {e}", self.task.task_id)
            return False

        keyspace = 0

        for line in lines:
            if not line:
                continue

            try:
                keyspace = int(line)
            except ValueError:
                continue

            if keyspace > 9000000000000000000:
                keyspace = -1
                break

        return chunk.send_keyspace(keyspace)

    def run_benchmark(self, chunk: Chunk):  # pylint: disable=W0613:unused-argument
        """Run a benchmark"""
        if self.task.benchmark_type == "speed":
            return self.__run_speed_benchmark()

        hashlists_path = self.agent.config.get_value("hashlists-path")

        if not isinstance(hashlists_path, str):
            self.agent.send_error("Hashlists path not set", self.task.task_id)
            return None

        hashlist_path = os.path.join(hashlists_path, str(self.task.hashlist_id))
        hashlist_output_path = os.path.join(hashlists_path, str(self.task.hashlist_id) + ".out")

        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, f'"{hashlist_path}"')

        command_parts: list[str] = [
            "--machine-readable",
            "--quiet",
            f"--runtime={self.task.benchmark_time}",
            "--restore-disable",
            "--potfile-disable",
            "--session=hashtopolis",
            "-p",
            '"\t"',
            attack_command,
            self.task.command_parameters,
            "-o",
            f'"{hashlist_output_path}"',
        ]

        command = f"{self.call_path} {' '.join(command_parts)}"

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

            status = HashcatStatus(line)
            if status.is_valid():
                last_valid_status = status

        if last_valid_status is None:
            self.agent.send_error("Failed to run benchmark", self.task.task_id)
            return 0

        return (
            last_valid_status.get_progress() - last_valid_status.get_rejected()
        ) / last_valid_status.get_progress_total()

    def __run_speed_benchmark(self):
        hashlists_path = self.agent.config.get_value("hashlists-path")

        if not isinstance(hashlists_path, str):
            self.agent.send_error("Hashlists path not set", self.task.task_id)
            return None

        hashlist_path = os.path.join(hashlists_path, str(self.task.hashlist_id))
        hashlist_output_path = os.path.join(hashlists_path, str(self.task.hashlist_id) + ".out")

        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, f'"{hashlist_path}"')

        if "--increment" in self.task.command_parameters:
            self.agent.send_error("Incremental mode not supported for speed benchmark", self.task.task_id)
            return 0

        command_parts: list[str] = [
            "--machine-readable",
            "--quiet",
            "--progress-only",
            "--restore-disable",
            "--potfile-disable",
            "--session=hashtopolis",
            "-p",
            '"\t"',
            attack_command,
            self.task.command_parameters,
        ]

        if self.task.use_preprocessor:
            command_parts.append("example.dict")

        if self.task.use_brain:
            command_parts.append("-S")

        command_parts.extend(["-o", f'"{hashlist_output_path}"'])

        command = f"{self.call_path} {' '.join(command_parts)}"

        try:
            output = run_command_and_get_output(command, ["CL_DEVICE_NOT_AVAILABLE"])
        except Exception as e:
            self.agent.send_error(f"Error while running benchmark: {e}", self.task.task_id)
            return 0

        benchmark_sum: dict[int, float | int] = {0: 0, 1: 0.0}

        for line in output:
            if not line or not ":" in line:
                continue

            line = line.split(":")

            if len(line) != 3:
                continue

            try:
                benchmark_sum[0] += int(line[1])
                benchmark_sum[1] += float(line[2]) * int(line[1])
            except ValueError:
                continue

        if benchmark_sum[0] == 0:
            self.agent.send_error("Failed to run benchmark", self.task.task_id)
            return 0

        return f"{benchmark_sum[0]}:{benchmark_sum[1] / benchmark_sum[0]}"

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

        os.makedirs(zap_path, exist_ok=True)

        if self.task.use_preprocessor:
            command = self.__get_preprocessor_command(chunk, zaps_path, hashlist_output_path, hashlist_path)
        elif self.task.use_pipe:
            command = self.__get_pipe_command(chunk, zaps_path, hashlist_output_path, hashlist_path)
        else:
            command = self.__get_command(chunk, zaps_path, hashlist_output_path, hashlist_path)

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
        crack_watcher = Thread(target=self.__watch_cracks, args=(hashlist_output_path, process))

        stdout_watcher.start()
        stderr_watcher.start()
        crack_watcher.start()

        self.first_status = False
        self.last_update = time.time()

        main_thread = Thread(target=self.__run, name="HashcatCrackerRun", args=(process, chunk, zap_path))
        main_thread.start()

        process.wait()
        stdout_watcher.join()
        stderr_watcher.join()
        crack_watcher.join()
        main_thread.join()

    def __get_command(self, chunk: Chunk, zaps_path: str, hashlist_output_path: str, hashlist_path: str):
        command_parts: list[str] = [
            "--machine-readable",
            "--quiet",
            "--status",
            "--restore-disable",
            "--session=hashtopolis",
            f"--status-timer {self.task.status_timer}",
            f"--outfile-check-timer={self.task.status_timer}",
            f'--outfile-check-dir="{zaps_path}"',
            f'-o "{hashlist_output_path}"',
            f"--outfile-format={self.output_format}",
            '-p "\t"',
            f"-s {chunk.skip}",
            f"-l {chunk.length}",
        ]

        if self.task.use_brain:
            command_parts.extend([
                "--brain-client",
                f"--brain-host {self.task.brain_host}",
                f"--brain-port {self.task.brain_port}",
                f"--brain-password {self.task.brain_password}",
            ])
            if self.task.brain_features:
                command_parts.append(f"--brain-client-features {self.task.brain_features}")
        else:
            command_parts.extend([
                "--potfile-disable",
                "--remove",
                f"--remove-timer={self.task.status_timer}",
            ])

        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, f'"{hashlist_path}"')

        command_parts.extend([attack_command, self.task.command_parameters])

        full_command = f"{self.call_path} {' '.join(command_parts)}"

        regex = r"\s-S(?:\s|$)"

        if re.search(regex, full_command):
            self.uses_slow_hash_flag = True

        return full_command

    def __get_pipe_command(self, chunk: Chunk, zaps_path: str, hashlist_output_path: str, hashlist_path: str):
        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, "")
        pre_args = [
            "--stdout",
            "-s",
            str(chunk.skip),
            "-l",
            str(chunk.length),
            attack_command,
        ]

        post_args = [
            "--machine-readable",
            "--quiet",
            "--status",
            "--remove",
            "--restore-disable",
            "--potfile-disable",
            "--session=hashtopolis",
            f"--status-timer {self.task.status_timer}",
            f"--outfile-check-timer={self.task.status_timer}",
            f"--outfile-check-dir={zaps_path}",
            f'-o "{hashlist_output_path}"',
            f"--outfile-format={self.output_format}",
            f'-p "{str(chr(9))}"',
            f"--remove-timer={self.task.status_timer}",
            f'"{hashlist_path}"',
        ]

        return (
            f"{self.call_path} {' '.join(pre_args)} |"
            f" {self.call_path} {' '.join(post_args)} {self.task.command_parameters}"
        )

    def __get_preprocessor_command(self, chunk: Chunk, zaps_path: str, hashlist_output_path: str, hashlist_path: str):
        pre_args: list[str] = []
        if not self.task.preprocessor.skip_command is None and not self.task.preprocessor.limit_command is None:
            pre_args.extend([
                self.task.preprocessor.skip_command,
                str(chunk.skip),
                self.task.preprocessor.limit_command,
                str(chunk.length),
            ])

        pre_args.append(self.task.preprocessor_command)

        if self.task.preprocessor.skip_command is None or self.task.preprocessor.limit_command is None:
            skip_length = chunk.skip + chunk.length
            pre_args.extend([
                f"| head -n {skip_length}",
                f"| tail -n {chunk.length}",
            ])

        attack_command = self.task.attack_command.replace(self.task.hashlist_alias, "")

        post_args = [
            "--machine-readable",
            "--quiet",
            "--status",
            "--restore-disable",
            "--potfile-disable",
            "--session=hashtopolis",
            f"--status-timer {self.task.status_timer}",
            f"--outfile-check-timer={self.task.status_timer}",
            f"--outfile-check-dir={zaps_path}",
            f'-o "{hashlist_output_path}"',
            f"--outfile-format={self.output_format}",
            '-p "\t"',
            f"--remove-timer={self.task.status_timer}",
            f'"{hashlist_path}"',
            attack_command,
            self.task.command_parameters,
        ]

        return f"{self.task.preprocessor.executable} {' '.join(pre_args)} | {self.call_path} {' '.join(post_args)}"

    def __run(self, process: subprocess.Popen[Any], chunk: Chunk, zap_path: str):  # pylint: disable=R0912,R0914,R0915
        """Run the Hashcat process"""
        self.cracks = []
        piping_threshold = self.agent.config.get_value("piping-threshold")
        enable_piping = self.agent.config.get_value("allow-piping")

        if not isinstance(piping_threshold, int):
            piping_threshold = 95

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
                status = HashcatStatus(line.decode())

                if status.is_valid():
                    self.status_count += 1
                    total_progress = status.get_progress_total()
                    util_status = status.get_util()
                    speed = status.get_speed()
                    state = status.get_state()

                    if (
                        enable_piping
                        and not self.uses_slow_hash_flag
                        and self.task.use_brain
                        and self.task.slow_hash
                        and not self.use_pipe
                    ):
                        if (
                            self.task.file_names
                            and not self.task.use_preprocessor
                            and 1 < self.status_count < 10
                            and util_status != -1
                            and util_status < piping_threshold
                        ):
                            self.use_pipe = True
                            chunk_start = int(total_progress / (chunk.skip + chunk.length) * chunk.skip)
                            self.progress = total_progress - chunk_start

                            try:
                                kill_hashcat(process.pid, self.agent.operating_system)
                            except ProcessLookupError:
                                pass
                            return

                    self.first_status = True
                    if self.use_pipe:
                        total_progress = self.progress

                    chunk_start = int(total_progress / (chunk.skip + chunk.length) * chunk.skip)

                    if total_progress > 0:
                        relative_progress = int(
                            (status.get_progress() - chunk_start) / float(total_progress - chunk_start) * 10000
                        )
                    else:
                        relative_progress = 0

                    initial = True

                    if state in {4, 5}:
                        self.use_pipe = False
                        self.progress = 0
                        time.sleep(5)

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
                                "keyspaceProgress": status.get_curku(),
                                "relativeProgress": relative_progress,
                                "speed": speed,
                                "state": state,
                                "cracks": self.cracks,
                            }

                            if (self.use_pipe or self.task.use_preprocessor) and status.get_curku() == 0:
                                query["keyspaceProgress"] = chunk.skip

                            prepared: list[tuple[str, ...]] = []

                            # crack format: hash[:salt:double]:plain:hex_plain:crack_pos -> : is replaced by \t
                            for crack in self.cracks:
                                hash_, other = crack.split("\t", 1)
                                count_tab = other.count("\t")

                                if count_tab == 2:
                                    plain, hex_plain, crack_pos = other.split("\t")
                                    prepared.append((hash_, plain, hex_plain, crack_pos))
                                else:
                                    salt, plain, hex_plain, crack_pos = other.rsplit("\t", 3)
                                    salt = salt.replace("\t", ":")
                                    prepared.append((hash_, salt, plain, hex_plain, crack_pos))

                            query["cracks"] = prepared

                            if status.get_temps():
                                query["gpuTemp"] = status.get_temps()

                            if status.get_all_util():
                                query["gpuUtil"] = status.get_all_util()

                            query["cpuUtil"] = [round(psutil.cpu_percent(), 1)]

                            if len(prepared) > 0:
                                logging.info("Found %d cracks. Sending to server...", len(prepared))
                                logging.info(prepared)

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
                                    len(prepared),
                                    chunk.chunk_id,
                                    len(self.cracks),
                                    response["skipped"],
                                )

                            self.cracks = crack_backup
                            zaps = response.get("zaps")

                            if zaps:
                                zap_output = "\tFF\n".join(zaps) + "\tFF\n"
                                with open(os.path.join(zap_path, f"{time.time()}"), "a+", encoding="utf-8") as f:
                                    f.write(zap_output)

                            print(
                                f"Progress: {relative_progress / 100:.2f}% Speed: {format_speed(speed)} Cracks:"
                                f" {len(prepared)} Accepted: {response['cracked']} Skips: {response['skipped']} Zaps:"
                                f" {len(zaps)}",
                                end="\r",
                            )
                else:
                    if str(line[0]) not in string.printable:
                        continue
            elif name == "ERR":
                msg = unidecode.unidecode(line.decode().strip())
                if msg and msg != "^C":
                    self.agent.send_error(f"Hashcat error: {msg}", self.task.task_id)

    def __watch_stream(self, name: str, stream: IO[bytes]):
        for line in stream:
            self.queue.put((name, line))

        if not stream.closed:
            stream.close()

    def __watch_cracks(self, hashlist_output_path: str, process: subprocess.Popen[Any]):
        # Wait until the file exists or the process ends
        while not os.path.exists(hashlist_output_path):
            if process.poll() is not None:
                return
            time.sleep(1)

        # Open the file and watch for new lines
        with open(hashlist_output_path, "r", encoding="utf-8") as f:
            end_count = 0

            while True:
                where = f.tell()
                line = f.readline()

                if not line:  # No new line
                    if process.poll() is None:  # Process is still running
                        time.sleep(0.05)
                        f.seek(where)
                    else:  # Process has ended, but check for more output
                        time.sleep(0.05)
                        end_count += 1
                        if end_count > 20 * 5:  # Stop after 5 second (20 * 0.05s) * 5 of no new output
                            break
                else:
                    # Safely add the new crack line to the list
                    with self.lock:
                        self.cracks.append(line.strip())

    def agent_stopped(self):
        """Check if the agent was stopped"""
        return self.was_stopped

    def run_health_check(self, attack: str, hashlist_alias: str, hashlist_path: str, output_path: str):
        """Run a health check"""
        attack = attack.replace(hashlist_alias, f'"{hashlist_path}"')
        command_parts = [
            "--machine-readable",
            "--quiet",
            "--restore-disable",
            "--potfile-disable",
            "--session=health",
            attack,
            f'-o "{output_path}"',
        ]

        full_command = f"{self.call_path} {' '.join(command_parts)}"

        if self.agent.operating_system == OperatingSystem.WINDOWS:
            full_command = full_command.replace("/", "\\")

        output, error = run_command_and_get_output_and_errors(full_command)

        errors = [unidecode.unidecode(line) for line in error]
        states: list[HashcatStatus] = []

        if output:
            for line in output:
                if not line:
                    continue

                status = HashcatStatus(line)
                if status.is_valid():
                    states.append(status)

        return states, errors
