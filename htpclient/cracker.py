import os
import subprocess
from typing import Any

from htpclient.operating_system import OperatingSystem
from htpclient.utils import get_system_bit


class Cracker:
    """Class representing a cracker"""

    def __init__(self, agent: Any, cracker_id: int):  # pylint: disable=E0601:used-before-assignment
        self.agent = agent
        self.cracker_id = cracker_id

        if not self.__load():
            self.agent.send_error("Loading cracker failed")
            raise RuntimeError("Loading cracker failed")

    def __load(self):
        """Load cracker data"""
        crackers_dir = self.agent.config.get_value("crackers-path")

        if not isinstance(crackers_dir, str):
            return False

        cracker_path = os.path.join(crackers_dir, str(self.cracker_id))
        self.cracker_path = cracker_path

        query: dict[str, Any] = {
            "action": "downloadBinary",
            "type": "cracker",
            "binaryVersionId": self.cracker_id,
        }

        response = self.agent.post(query)

        if response is None or "url" not in response or not response["url"]:
            self.agent.send_error(f"Getting cracker failed. Response: {response}")
            return False

        if not os.path.exists(cracker_path):

            if not self.agent.download(response["url"], cracker_path + ".7z"):
                return False

            temp_path = os.path.join(crackers_dir, "temp")
            os.makedirs(temp_path, exist_ok=True)

            try:
                if self.agent.operating_system == OperatingSystem.WINDOWS:
                    subprocess.check_output(
                        f"7zr{self.agent.operating_system.get_extension()} x -o{temp_path} {cracker_path}.7z",
                        shell=True,
                    )
                else:
                    subprocess.check_output(
                        f"./7zr{self.agent.operating_system.get_extension()} x -o{temp_path} {cracker_path}.7z",
                        shell=True,
                    )
            except subprocess.CalledProcessError as e:
                self.agent.send_error(f"Extracting cracker failed {e}")
                return False

            os.remove(cracker_path + ".7z")

            for file in os.listdir(temp_path):
                if os.path.isdir(os.path.join(temp_path, file)):
                    os.rename(os.path.join(temp_path, file), cracker_path)
                    break

                os.rename(temp_path, cracker_path)
                break

            if os.path.isdir(temp_path):
                os.rmdir(temp_path)

        executable = response["executable"]

        if os.path.exists(os.path.join(cracker_path, executable)):
            self.executable = os.path.join(cracker_path, executable)
        else:
            file_path, file_ext = os.path.splitext(executable)
            system_bit = get_system_bit()
            self.executable = os.path.join(cracker_path, f"{file_path}{system_bit}{file_ext}")

        if not os.path.exists(self.executable):
            self.agent.send_error(f"Cracker executable not found {self.executable}")
            return False

        self.name = str(response["name"]).lower()

        return True
