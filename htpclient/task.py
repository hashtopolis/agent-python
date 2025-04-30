import logging
import os
from enum import Enum
from time import sleep
from typing import TYPE_CHECKING, Any

from htpclient.chunk import Chunk, ChunkStatus
from htpclient.cracker import Cracker
from htpclient.files import Files
from htpclient.hashlist import Hashlist
from htpclient.preprocessor import Preprocessor

if TYPE_CHECKING:
    from htpclient import Agent


class TaskSpecialID(Enum):
    """Enum representing special task IDs"""

    HEALTH_CHECK = -1


class Task:
    """Class representing a task"""

    task_id: int

    def __init__(
        self,
        agent: Agent,  # pylint: disable=E0601:used-before-assignment
        task_id: int,
        data: dict[str, Any] | None = None,
    ):
        self.agent = agent
        self.task_id = task_id
        self.downloaded_files = False
        self.forced_encoding = None

        if task_id == TaskSpecialID.HEALTH_CHECK.value:
            if data is None:
                raise ValueError("Data must be provided for health check")
            self.cracker_id = data["crackerBinaryId"]
            try:
                self.cracker = Cracker(self.agent, self.cracker_id)
            except Exception as e:
                self.agent.send_error("Loading task failed", task_id)
                raise RuntimeError("Loading task failed") from e

        if not self.__load(data):
            self.agent.send_error("Loading task failed", task_id)
            raise RuntimeError("Loading task failed")

    @staticmethod
    def get_task(agent: Agent):  # pylint: disable=E0601:used-before-assignment
        """Get a task from the server"""
        query = {"action": "getTask"}
        response = agent.post(query)
        task_id = None

        if response is None:
            return None

        if response["taskId"] is None:
            agent.send_warning("No task available")
            sleep(10)
            return None

        if response["taskId"] == TaskSpecialID.HEALTH_CHECK.value:
            return Task(agent, TaskSpecialID.HEALTH_CHECK.value, None)

        task_id = int(response["taskId"])
        logging.info("Got task with id: %s", str(response["taskId"]))
        return Task(agent, task_id, response)

    def __load(self, response: dict[str, Any] | None):
        if response is None:
            return False

        self.cracker_id = int(response["crackerId"])
        self.use_preprocessor = bool(response["usePreprocessor"])
        self.preprocessor_id = int(response["preprocessor"])
        self.preprocessor_command = str(response["preprocessorCommand"])
        self.file_names: list[str] = response["files"]
        self.hashlist_id = int(response["hashlistId"])
        self.use_brain = bool(response["useBrain"])
        self.benchmark_type = str(response["benchType"])
        self.benchmark_time = int(response["bench"])
        self.attack_command = str(response["attackcmd"])
        self.command_parameters = str(response["cmdpars"])
        self.hashlist_alias = str(response["hashlistAlias"])
        self.use_pipe = bool(response["enforcePipe"])
        self.slow_hash = bool(response["slowHash"])
        self.status_timer = int(response["statustimer"])
        self.brain_host = str(response.get("brainHost", ""))
        self.brain_port = int(response.get("brainPort", 0))
        self.brain_password = str(response.get("brainPass", ""))
        self.brain_features = str(response.get("brainFeatures", ""))

        try:
            self.cracker = Cracker(self.agent, self.cracker_id)
        except Exception as e:
            logging.error("Failed to load cracker: %s", e)
            return False

        if self.use_preprocessor:
            try:
                self.preprocessor = Preprocessor(self.agent, self.preprocessor_id)
            except Exception as e:
                logging.error("Failed to load preprocessor: %s", e)
                return False

        try:
            self.hashlist = Hashlist(self.agent, self.hashlist_id)
        except Exception as e:
            logging.error("Failed to load hashlist: %s", e)
            return False

        if self.use_brain and not self.hashlist.load_found_hashes(self.hashlist_id, self.cracker_id):
            self.agent.send_error(f"Failed to get found hashes for hashlist {self.hashlist_id}", self.task_id)
            return False

        # Load the files
        files = Files(self.agent)

        file_paths: dict[str, str] = {}

        for file_name in self.file_names:
            file_path = files.check_file_exists(file_name, self.task_id)

            if file_path is None:
                self.agent.send_error(f"Failed to get file {file_name} for task " + str(self.task_id), self.task_id)
                return False

            if not self.downloaded_files and files.downloaded.get(file_path, False):
                self.downloaded_files = True

            file_paths[file_name] = file_path

        if len(files.deleted_old_files) > 0:
            if any(file_path in file_paths.values() for file_path in files.deleted_old_files):
                self.agent.send_error(
                    "The machine cannot download the file, because the file is too big. The agent cannot clean up any"
                    " more files.",
                    self.task_id,
                )
                return False

        self.file_paths = file_paths

        for file_name, file_path in file_paths.items():
            logging.info("File %s is at %s", file_name, file_path)

            base_name = os.path.splitext(file_name)[0]

            # When an attack is created with an 7z file, the file extension is not known in the attack command by default
            self.attack_command = self.attack_command.replace(f"{base_name}.???", file_name)
            self.preprocessor_command = self.preprocessor_command.replace(f"{base_name}.???", file_name)

            if not file_name in self.attack_command:
                if os.path.splitext(file_name)[0] in self.attack_command:
                    self.agent.send_warning(
                        f"File {file_name} not found in attack command, but base name"
                        f" {os.path.splitext(file_name)[0]} found",
                        self.task_id,
                    )
                    self.attack_command = self.attack_command.replace(os.path.splitext(file_name)[0], f'"{file_path}"')
                    self.preprocessor_command = self.preprocessor_command.replace(
                        os.path.splitext(file_name)[0], f'"{file_path}"'
                    )
                else:
                    self.agent.send_error(f"File {file_name} not found in attack command", self.task_id)
            else:
                self.attack_command = self.attack_command.replace(file_name, f'"{file_path}"')  # type: ignore
                self.preprocessor_command = self.preprocessor_command.replace(file_name, f'"{file_path}"')  # type: ignore

        return True

    def get_chunk(self):
        """Get a chunk for the task"""
        try:
            chunk = Chunk(self.agent, self.task_id)
        except Exception as e:
            logging.error("Failed to load chunk: %s", e)
            return None

        if chunk.status == ChunkStatus.FULLY_DISPATCHED:
            logging.info("Chunk is fully dispatched")
            return None

        if chunk.status == ChunkStatus.HEALTH_CHECK:
            logging.info("Running health check...")
            self.agent.run_health_check(self)
            return None

        return chunk
