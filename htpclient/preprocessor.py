import os
import subprocess
from typing import Any

from htpclient.operating_system import OperatingSystem
from htpclient.utils import get_system_bit


class Preprocessor:
    def __init__(self, agent: Any, preprocessor_id: int):  # pylint: disable=E0601:used-before-assignment
        self.agent = agent
        self.preprocessor_id = preprocessor_id

        if not self.__load():
            self.agent.send_error("Loading preprocessor failed")
            raise RuntimeError("Loading preprocessor failed")

    def __load(self):
        preprocessors_dir = self.agent.config.get_value("preprocessors-path")

        if not isinstance(preprocessors_dir, str):
            return False

        preprocessor_path = os.path.join(preprocessors_dir, str(self.preprocessor_id))
        self.preprocessor_path = preprocessor_path

        query: dict[str, Any] = {
            "action": "downloadBinary",
            "type": "preprocessor",
            "preprocessorId": self.preprocessor_id,
        }

        response = self.agent.post(query)

        if response is None or "url" not in response or not response["url"]:
            self.agent.send_error(f"Getting preprocessor failed. Response: {response}")
            return False

        if not self.agent.download(response["url"], preprocessor_path + ".7z"):
            return False

        temp_path = os.path.join(preprocessors_dir, "temp")
        os.makedirs(temp_path, exist_ok=True)

        try:
            if self.agent.operating_system == OperatingSystem.WINDOWS:
                subprocess.check_output(
                    f"7zr{self.agent.operating_system.get_extension()} x -o{temp_path} {preprocessor_path}.7z",
                    shell=True,
                )
            else:
                subprocess.check_output(
                    f"./7zr{self.agent.operating_system.get_extension()} x -o{temp_path} {preprocessor_path}.7z",
                    shell=True,
                )
        except subprocess.CalledProcessError as e:
            self.agent.send_error(f"Extracting preprocessor failed {e}")
            return False

        os.remove(preprocessor_path + ".7z")

        for file in os.listdir(temp_path):
            if os.path.isdir(os.path.join(temp_path, file)):
                os.rename(os.path.join(temp_path, file), preprocessor_path)
                break

            os.rename(temp_path, preprocessor_path)
            break

        if os.path.isdir(temp_path):
            os.rmdir(temp_path)

        executable = response["executable"]

        if os.path.exists(os.path.join(preprocessor_path, executable)):
            self.executable = os.path.join(preprocessor_path, executable)
        else:
            file_path, file_ext = os.path.splitext(executable)
            system_bit = get_system_bit()
            self.executable = os.path.join(preprocessor_path, f"{file_path}{system_bit}{file_ext}")

        if not os.path.exists(self.executable):
            self.agent.send_error(f"Preprocessor executable not found {self.executable}")
            return False

        self.keyspace_command = str(response["keyspaceCommand"]) if response["keyspaceCommand"] else None
        self.skip_command = str(response["skipCommand"]) if response["skipCommand"] else None
        self.limit_command = str(response["limitCommand"]) if response["limitCommand"] else None

        return True
