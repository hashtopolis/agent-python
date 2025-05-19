import datetime
import os
import subprocess
from time import sleep
from typing import Any

from htpclient.operating_system import OperatingSystem
from htpclient.utils import get_storage_remaining, get_storage_total


class Files:
    """Class representing files"""

    COMPRESSION_FILE_EXTENSIONS = {".7z"}
    POSSIBLE_TEXT_EXTENSIONS = {".txt", ".wordlist", ".wordlists", ".dict", ".dictionary", ".dic", ".gz"}

    def __init__(self, agent: Any):  # pylint: disable=E0601:used-before-assignment
        self.agent = agent
        self.last_check = datetime.datetime.now()
        self.downloaded: dict[str, bool] = {}
        self.deleted_old_files: list[str] = []

    def check_file_exists(self, file_name: str, task_id: int):
        """Check if a file exists and download it if not"""
        file_path = os.path.join(self.agent.config.get_value("files-path"), file_name)  # type: ignore

        query: dict[str, Any] = {
            "action": "getFile",
            "taskId": task_id,
            "file": file_name,
        }

        response = self.agent.post(query)  # type: ignore

        if response is None:
            return None

        if any(file_name.endswith(ext) for ext in self.COMPRESSION_FILE_EXTENSIONS):
            self.downloaded[os.path.splitext(file_path)[0]] = False  # type: ignore
            return self.check_compressed_file(file_path, response, task_id)  # type: ignore

        self.downloaded[file_path] = False
        return self.check_single_file(file_path, response, task_id)  # type: ignore

    def check_single_file(self, file_path: str, response: dict[str, Any], task_id: int):
        """Check a single file"""
        if os.path.isfile(file_path) and os.stat(file_path).st_size == int(response["filesize"]):
            return file_path

        if os.path.isfile(file_path) and os.stat(file_path).st_size != int(response["filesize"]):
            self.agent.send_warning(f"File size mismatch on file: {file_path} - removing file and retrying...", task_id)
            os.remove(file_path)
            sleep(5)
            return None

        if not os.path.isfile(file_path) and self.agent.config.get_value("multicast"):  # type: ignore
            self.agent.send_warning("Multicast is enabled, need to wait until file was delivered!", task_id)
            sleep(5)  # in case the file is not there yet (or not completely), we just wait some time and then try again
            return None

        if get_storage_total(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
            response["filesize"]
        ):
            self.agent.send_error("Not enough storage space available", task_id)
            return None

        if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
            response["filesize"]
        ):
            self.agent.send_warning("Not enough storage space available, cleaning up files...", task_id)
            self.clean_up()
            self.agent.clean_up()

            if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
                response["filesize"]
            ):
                self.agent.send_warning(
                    "Cleanup did not create enough space, deleting oldest file and then retrying...", task_id
                )
                self.remove_oldest_file()

                if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
                    response["filesize"]
                ):
                    self.agent.send_error("Not enough storage space available, even after deleting some files", task_id)
                    return None

        if self.agent.config.get_value("rsync") and self.agent.operating_system != OperatingSystem.WINDOWS:
            if not self.agent.rsync(file_path):
                return None
        else:
            if not self.agent.download(response["url"], file_path):  # type: ignore
                return None

        self.downloaded[file_path] = True

        if os.path.isfile(file_path) and os.stat(file_path).st_size != int(response["filesize"]):
            self.agent.send_warning(f"File size mismatch on file: {file_path} - removing file and retrying...", task_id)
            os.remove(file_path)
            sleep(5)
            return None

        return file_path

    def check_compressed_file(self, file_path: str, response: dict[str, Any], task_id: int):
        """Check a compressed file"""
        new_file_path = os.path.splitext(file_path)[0]

        if os.path.isfile(new_file_path):
            return new_file_path

        if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
            response["filesize"]
        ):
            self.agent.send_error("Not enough storage space available", task_id)
            return None

        if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
            response["filesize"]
        ):
            self.agent.send_warning("Not enough storage space available, cleaning up files...", task_id)
            self.clean_up()
            self.agent.clean_up()

            if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
                response["filesize"]
            ):
                self.agent.send_warning(
                    "Cleanup did not create enough space, deleting oldest file and then retrying...", task_id
                )
                self.remove_oldest_file()

                if get_storage_remaining(self.agent.config.get_value("files-path"), self.agent.operating_system) < int(  # type: ignore
                    response["filesize"]
                ):
                    self.agent.send_error("Not enough storage space available, even after deleting some files", task_id)
                    return None

        if not os.path.isfile(file_path):
            if self.agent.config.get_value("rsync") and self.agent.operating_system != OperatingSystem.WINDOWS:
                if not self.agent.rsync(file_path):
                    return None
            else:
                if not self.agent.download(response["url"], file_path):  # type: ignore
                    return None

            if os.path.isfile(file_path) and os.stat(file_path).st_size != int(response["filesize"]):
                self.agent.send_warning(
                    f"File size mismatch on file: {file_path} - removing file and retrying...", task_id
                )
                os.remove(file_path)
                sleep(5)
                return None

        if os.path.isfile(file_path):
            if self.agent.operating_system == OperatingSystem.WINDOWS:
                subprocess.check_output(
                    f"7zr{self.agent.operating_system.get_extension()} x -aoa"
                    f" -o\"{self.agent.config.get_value('files-path')}\" -y \"{file_path}\"",
                    shell=True,
                )
            else:
                subprocess.check_output(
                    f"./7zr{self.agent.operating_system.get_extension()} x -aoa"
                    f" -o\"{self.agent.config.get_value('files-path')}\" -y \"{file_path}\"",
                    shell=True,
                )

            os.remove(file_path)
            new_file_path = os.path.splitext(file_path)[0]

        return new_file_path

    def clean_up(self):
        """Clean up files"""
        self.last_check = datetime.datetime.now()
        if self.agent.config.get_value("file-deletion-disable"):
            return

        query = {"action": "getFileStatus"}
        response = self.agent.post(query)

        if response is None:
            return

        file_names = response["filenames"]

        for file_name in file_names:
            file_path = os.path.join(self.agent.config.get_value("files-path"), file_name)  # type: ignore

            if file_name.find("/") != -1 or file_name.find("\\") != -1:
                continue  # ignore invalid file names

            if os.path.dirname(file_path) != os.path.dirname(self.agent.config.get_value("files-path")):  # type: ignore
                continue  # ignore any case in which we would leave the files folder

            if os.path.exists(file_path):  # type: ignore
                if any(file_name.endswith(ext) for ext in self.COMPRESSION_FILE_EXTENSIONS):
                    new_file_path = os.path.splitext(file_path)[0]  # type: ignore

                    possible_text_files = [new_file_path] + [  # type: ignore
                        f"{new_file_path}{ext}" for ext in self.POSSIBLE_TEXT_EXTENSIONS
                    ]

                    for text_file in possible_text_files:  # type: ignore
                        if os.path.exists(text_file):  # type: ignore
                            os.remove(text_file)  # type: ignore

                os.remove(file_path)  # type: ignore

    def remove_oldest_file(self):
        """Remove the oldest file"""
        files_dir = self.agent.config.get_value("files-path")  # type: ignore
        files = os.listdir(files_dir)  # type: ignore

        if not files:
            return

        oldest_file = min(files, key=lambda f: os.path.getatime(os.path.join(files_dir, f)))  # type: ignore
        self.deleted_old_files.append(oldest_file)  # type: ignore
        os.remove(os.path.join(files_dir, oldest_file))  # type: ignore
        self.agent.send_warning(f"Removed oldest file: {oldest_file}")
