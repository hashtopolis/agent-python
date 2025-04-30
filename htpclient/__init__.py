import datetime
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import time
from typing import Any

import psutil
import requests
import urllib3
from unidecode import unidecode
from urllib3.exceptions import InsecureRequestWarning

from htpclient.config import Config
from htpclient.cracker import Cracker
from htpclient.hashcat_cracker import HashcatCracker
from htpclient.operating_system import OperatingSystem
from htpclient.utils import download_file, file_get_content, file_set_content, replace_double_space

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

VERSION_NUMBER = "0.8.0"
VERSION_NAME = "s3-python-" + VERSION_NUMBER


class Agent:
    """The agent class"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config = Config(base_dir)
        self.last_update_check = datetime.datetime.now()
        self.last_clean_up = datetime.datetime.now()
        self.send_errors: dict[str, int] = {}
        self.send_warnings: dict[str, int] = {}
        self.default_error_task = self.config.get_value("default-error-task")
        self.agent_id = self.config.get_value("agent-id")
        self.api_key = self.config.get_value("api-key")
        self.__session = self.__start_session()
        self.__url = self.__get_url()

        self.__check_access()
        self.__register()
        self.__update_device_information()
        self.__login()
        self.__download_utils()
        self.clean_up(start=True)

        self.update_client()

        if self.config.get_value("multicast"):
            self.start_uftpd()

    @staticmethod
    def get_version():
        """Get the version of the agent"""
        return VERSION_NAME

    @staticmethod
    def get_version_number():
        """Get the version number of the agent"""
        return VERSION_NUMBER

    @property
    def operating_system(self):
        """Get the operating system of the agent"""
        return self.__get_os()

    @operating_system.setter
    def operating_system(self, value: Any):
        raise AttributeError("Property 'operating_system' is read-only")

    def __start_session(self):
        """Start a session with the server."""
        session = requests.Session()
        session.headers.update({"User-Agent": Agent.get_version()})
        verify = self.config.get_value("verify-request")
        session.verify = verify if isinstance(verify, bool) else True

        cert = self.config.get_value("cert")

        if cert and isinstance(cert, str):
            session.cert = cert
            logging.debug("Using certificate: %s", cert)

        proxies = self.config.get_value("proxies")

        if proxies and isinstance(proxies, dict):
            session.proxies = proxies
            logging.debug("Using proxies: %s", proxies)

        auth_user = self.config.get_value("auth-user")
        auth_password = self.config.get_value("auth-password")

        if auth_user and auth_password and isinstance(auth_user, str) and isinstance(auth_password, str):
            session.auth = (auth_user, auth_password)
            logging.debug("Using authentication: %s", auth_user)

        return session

    def __get_url(self):
        url = self.config.get_value("url")

        if not url or not isinstance(url, str):
            logging.error("URL is not set in the configuration file.")
            raise ValueError("URL is not set in the configuration file.")

        logging.debug("Using URL: %s", url)

        return url

    def __get_os(self):
        operating_system = platform.system()

        try:
            return OperatingSystem.get_by_platform_name(operating_system)
        except ValueError as e:
            raise ValueError("It seems your operating system is not supported.") from e

    def __check_access(self):
        query = {"action": "testConnection"}
        response = self.post(query)

        if response is None:
            raise ConnectionError("Could not connect to the server.")

        logging.info("Connection to server successful.")

    def __register(self):
        token = self.config.get_value("token")

        if token and isinstance(token, str):
            return

        query: dict[str, Any] = {
            "action": "register",
            "voucher": self.config.get_value("voucher"),
            "name": self.config.get_value("name"),
        }

        if self.config.get_value("cpu-only"):
            query["cpu-only"] = True

        response = self.post(query, False)

        if response is None:
            raise ConnectionError("Could not register to the server.")

        if not response["token"]:
            logging.error("Could not register to the server.")
            raise ConnectionError("Could not register to the server.")

        token = response["token"]
        self.config.set_value("voucher", "")
        self.config.set_value("token", token)
        logging.info("Successfully registered to the server.")

    def __update_device_information(self):
        query: dict[str, Any] = {
            "action": "updateInformation",
            "uid": self.config.get_value("uuid"),
            "os": self.operating_system.value,
            "devices": self.__get_devices(),
        }

        response = self.post(query)

        if response is None:
            return

        logging.info("Successfully updated device information.")

    def __login(self):
        query = {
            "action": "login",
            "clientSignature": Agent.get_version(),
        }

        response = self.post(query)

        if response is None:
            raise ConnectionError("Could not login to the server.")

        logging.info("Successfully logged in to the server.")

        if response.get("server-version", None):
            logging.info("Server version: %s", response["server-version"])

        if response.get("multicastEnabled", False):
            logging.info("Multicast enabled on server.")

            if self.operating_system != OperatingSystem.LINUX:
                self.send_warning("Multicast is only supported on Linux.")
                return

            self.config.set_value("multicast", True)

    def __download_utils(self):
        seven_zip_path = os.path.join(self.base_dir, "7zr" + OperatingSystem.get_extension(self.operating_system))
        uftpd_path = os.path.join(self.base_dir, "uftpd" + OperatingSystem.get_extension(self.operating_system))

        if not os.path.isfile(seven_zip_path):
            query = {"action": "downloadBinary", "type": "7zr"}
            response = self.post(query)

            if response is None:
                return

            if not response["executable"]:
                self.send_error(f"Getting 7zr failed: {response}")
                return

            if not self.download(response["executable"], seven_zip_path):
                return

            os.chmod(seven_zip_path, os.stat(seven_zip_path).st_mode | stat.S_IEXEC)

        if not os.path.isfile(uftpd_path) and self.config.get_value("multicast"):
            query = {"action": "downloadBinary", "type": "uftpd"}
            response = self.post(query)

            if response is None:
                return

            if not response["executable"]:
                self.send_error(f"Getting uftpd failed: {response}")
                return

            if not self.download(response["executable"], uftpd_path):
                return

            os.chmod(uftpd_path, os.stat(uftpd_path).st_mode | stat.S_IEXEC)

    def __get_devices(self):
        devices: list[str] = []
        cpu_only = self.config.get_value("cpu-only")

        if not isinstance(cpu_only, bool):
            cpu_only = False

        if self.operating_system == OperatingSystem.WINDOWS:
            devices.extend(self.__get_windows_devices(cpu_only))
        elif self.operating_system == OperatingSystem.LINUX:
            devices.extend(self.__get_linux_devices(cpu_only))
        elif self.operating_system == OperatingSystem.MAC:
            devices.extend(self.__get_mac_devices(cpu_only))
        else:
            self.send_error("Operating system not supported.")
            raise ValueError("Operating system not supported.")

        return devices

    def __get_windows_devices(self, cpu_only: bool):
        devices: list[str] = []

        platform_release = platform.uname().release
        if platform_release == "" or int(platform_release) >= 10:
            try:
                output = (
                    subprocess.check_output(
                        "powershell -Command Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name",
                        shell=True,
                    )
                    .decode(errors="replace")
                    .splitlines()
                )
                lines = [line.strip() for line in output if line.strip() and line.strip() != "Name"]
                devices.extend(lines)
            except Exception:
                self.send_warning("Could not get CPU information.")
        else:
            try:
                output = subprocess.check_output("wmic cpu get name", shell=True).decode(errors="replace").splitlines()
                lines = [line.strip() for line in output if line.strip() and line.strip() != "Name"]
                devices.extend(lines)
            except Exception:
                self.send_warning("Could not get CPU information.")

        if not cpu_only:
            if platform_release == "" or int(platform_release) >= 10:
                try:
                    output = (
                        subprocess.check_output(
                            "powershell -Command Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty"
                            " Name",
                            shell=True,
                        )
                        .decode(errors="replace")
                        .splitlines()
                    )
                    lines = [line.strip() for line in output if line.strip() and line.strip() != "Name"]
                    devices.extend(lines)
                except Exception:
                    self.send_warning("Could not get GPU information.")
            else:
                try:
                    output = (
                        subprocess.check_output("wmic path win32_VideoController get name", shell=True)
                        .decode(errors="replace")
                        .splitlines()
                    )
                    lines = [line.strip() for line in output if line.strip() and line.strip() != "Name"]
                    devices.extend(lines)
                except Exception:
                    self.send_warning("Could not get GPU information.")

        return devices

    def __get_linux_devices(self, cpu_only: bool):
        devices: list[str] = []

        try:
            output = subprocess.check_output("cat /proc/cpuinfo", shell=True).decode(errors="replace").splitlines()
            lines = [
                replace_double_space(line.split(":", 1)[1].strip())
                for line in output
                if line.strip() and (line.startswith("model name") or line.startswith("physical id"))
            ]

            paired_lines = [f"{lines[i + 1]}:{lines[i]}" for i in range(0, len(lines), 2)]
            names = [line.split(":", 1)[1].replace("\t", " ") for line in sorted(set(paired_lines))]
            devices.extend(names)
        except Exception:
            self.send_warning("Could not get CPU information.")

        if not cpu_only:
            try:
                subprocess.check_output("lspci", shell=True)
            except Exception:
                try:
                    subprocess.check_output("sudo apt-get install pciutils", shell=True)
                except Exception:
                    self.send_warning("Could not install pciutils.")
                    return devices

            try:
                output = (
                    subprocess.check_output("lspci | grep -E 'VGA compatible controller|3D controller'", shell=True)
                    .decode(errors="replace")
                    .splitlines()
                )
                lines = [line.split(" ", 1)[1].split(":")[1].strip() for line in output if line.strip()]
                devices.extend(lines)
            except Exception:
                self.send_warning("Could not get GPU information.")

        return devices

    def __get_mac_devices(self, cpu_only: bool):
        devices: list[str] = []

        try:
            output = (
                subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True)
                .decode(errors="replace")
                .splitlines()
            )
            lines = [line.strip() for line in output if line.strip()]
            devices.extend(lines)
        except Exception:
            self.send_warning("Could not get CPU information.")

        if not cpu_only:
            try:
                output = (
                    subprocess.check_output("system_profiler SPDisplaysDataType -detaillevel mini", shell=True)
                    .decode(errors="replace")
                    .splitlines()
                )
                lines = [
                    line.split(":")[1].strip() for line in output if line.strip() and "Chipset Model" in line.strip()
                ]
                devices.extend(lines)
            except Exception:
                self.send_warning("Could not get GPU information")

        return devices

    def __request(
        self,
        method: str,
        json: dict[str, Any],
        token_required: bool = True,
        forced_timeout: int | None = None,
        user: bool = False,
    ):
        try:
            logging.debug("Doing request with method %s and data %s", method, json)
            timeout = self.config.get_value("request-timeout")

            if not isinstance(timeout, int):
                timeout = 30

            if forced_timeout:
                timeout = forced_timeout

            if token_required:
                json["token"] = self.config.get_value("token")

            if user:
                url = self.__url.replace("api/server.php", "api/user.php")
            else:
                url = self.__url

            allow_redirects = self.config.get_value("allow-redirects-request")
            allow_redirects = allow_redirects if isinstance(allow_redirects, bool) else True

            response = self.__session.request(method, url, json=json, timeout=timeout, allow_redirects=allow_redirects)

            return self.__handle_response(response, json)
        except Exception as e:
            self.send_error(str(e))
            return None

    def __handle_response(self, response: requests.Response, json: dict[str, Any]):
        uri = response.url
        if response.status_code != 200:
            status_code = response.status_code
            self.send_error(f"Status code from server: {status_code} for URI: {uri} with input: {json}")
            return None

        logging.debug(response.content)
        try:
            json_response = response.json()

            if not json_response["response"] in {"OK", "SUCCESS"}:
                if json["action"] == "clientError":
                    return json_response
                self.send_error(f"Error from server for URI: {uri}: input: {json} response: {json_response}")
                return None

            return json_response

        except Exception as e:
            self.send_error(f"Error occurred for URI: {uri}: {e}")
            return None

    def post(
        self, json: dict[str, Any], token_required: bool = True, forced_timeout: int | None = None, user: bool = False
    ):
        """Send a POST request to the server."""
        return self.__request("POST", json, token_required, forced_timeout, user)

    def get(self, json: dict[str, Any], token_required: bool = True, forced_timeout: int | None = None):
        """Send a GET request to the server."""
        return self.__request("GET", json, token_required, forced_timeout)

    def put(self, json: dict[str, Any], token_required: bool = True, forced_timeout: int | None = None):
        """Send a PUT request to the server."""
        return self.__request("PUT", json, token_required, forced_timeout)

    def download(self, url: str, output: str):
        """Download a file from the server."""
        try:
            logging.debug("Downloading %s to %s", url, output)
            base_url = self.config.get_value("url").replace("api/server.php", "")  # type: ignore

            if not url.startswith(base_url):  # type: ignore
                url = base_url + url  # type: ignore

            response = self.__session.get(url, stream=True)  # type: ignore

            if not response.status_code in [200, 301, 302]:
                self.send_error(f"File download header reported wrong status code: {response.status_code}")
                return False

            download_file(response, output)
            return True
        except Exception as e:
            self.send_error("Download error while downloading %s: %s" % (url, e))
            return False

    def rsync(self, local_path: str):
        """Download a file from the server via rsync."""
        logging.info('Getting file "%s" via rsync', local_path.split("/")[-1])
        remote_path = os.path.join(self.config.get_value("rsync-path"), os.path.basename(local_path))  # type: ignore
        try:
            subprocess.check_output(f"rsync -avzP --partial {remote_path} {local_path}", shell=True)
        except Exception as e:
            self.send_error(f"Rsync error while downloading {local_path}: {e}")
            return False

        return True

    def clean_up(self, all_files: bool = False, start: bool = False):
        """Clean up the agent directory."""
        if all_files:
            for key in self.config.DIRECTORY_KEYS:
                path = self.config.get_value(key)

                if not isinstance(path, str):
                    continue

                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                except Exception as e:
                    logging.error("Could not remove directory %s: %s", path, e)

            for key in self.config.FILES_KEYS:
                path = self.config.get_value(key)

                if not isinstance(path, str):
                    continue

                try:
                    if os.path.isfile(path):
                        os.remove(path)
                except Exception as e:
                    logging.error("Could not remove file %s: %s", path, e)

            files = os.listdir(self.base_dir)

            for file in files:
                file_path = os.path.join(self.base_dir, file)

                if os.path.isfile(file_path) and file != "hashtopolis.zip":
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logging.error("Could not remove file %s: %s", file_path, e)

        days_not_accessed = self.config.get_value("file-remove-after-not-accessed-days")

        if not isinstance(days_not_accessed, int):
            days_not_accessed = 14

        not_accessed_time = datetime.timedelta(days=days_not_accessed).total_seconds()

        if self.config.get_value("auto-clean"):
            files_dir = self.config.get_value("files-path")

            if isinstance(files_dir, str) and os.path.isdir(files_dir):
                for file in os.listdir(files_dir):
                    file_path = os.path.join(files_dir, file)

                    if not os.path.isfile(file_path):
                        continue

                    file_stats = os.stat(file_path)

                    if file_stats.st_size == 0:
                        try:
                            logging.info("Removing empty file %s", file_path)
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

                    if (time.time() - file_stats.st_atime) > not_accessed_time:
                        try:
                            logging.info(
                                "Removing file %s as it was not accessed for %s seconds",
                                file_path,
                                time.time() - file_stats.st_atime,
                            )
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

            hashlist_files = self.config.get_value("hashlists-path")

            if isinstance(hashlist_files, str) and os.path.isdir(hashlist_files):
                for file in os.listdir(hashlist_files):
                    file_path = os.path.join(hashlist_files, file)

                    if not os.path.isfile(file_path):
                        continue

                    file_stats = os.stat(file_path)

                    if file_stats.st_size == 0:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

                    if (time.time() - file_stats.st_atime) > not_accessed_time:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

            crackers_files = self.config.get_value("crackers-path")

            if isinstance(crackers_files, str) and os.path.isdir(crackers_files):
                for file in os.listdir(crackers_files):
                    file_path = os.path.join(crackers_files, file)

                    if os.path.isdir(file_path):
                        continue

                    file_stats = os.stat(file_path)

                    if file_stats.st_size == 0:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

                    if (time.time() - file_stats.st_atime) > not_accessed_time:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

            preprocessor_files = self.config.get_value("preprocessors-path")

            if isinstance(preprocessor_files, str) and os.path.isdir(preprocessor_files):
                for file in os.listdir(preprocessor_files):
                    file_path = os.path.join(preprocessor_files, file)

                    if not os.path.isfile(file_path):
                        continue

                    file_stats = os.stat(file_path)

                    if file_stats.st_size == 0:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

                    # Delete when file is not accessed for 30 days
                    if (time.time() - file_stats.st_atime) > not_accessed_time:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.error("Could not remove file %s: %s", file_path, e)

            zaps_files = self.config.get_value("zaps-path")

            if isinstance(zaps_files, str) and (os.path.isdir(zaps_files) or zaps_files == ""):
                for file in os.listdir(zaps_files):
                    file_path = os.path.join(zaps_files, file)

                    if not os.path.isdir(file_path):
                        continue

                    if not "hashlist_" in file:
                        continue

                    if len(os.listdir(file_path)) == 0:
                        try:
                            shutil.rmtree(file_path)
                        except Exception as e:
                            logging.error("Could not remove directory %s: %s", file_path, e)

        if start:
            # Delete hashtopolis.pid files for all crackers as the agent is started again
            crackers_path = self.config.get_value("crackers-path")

            if isinstance(crackers_path, str) and os.path.isdir(crackers_path):
                for file_or_dir in os.listdir(crackers_path):
                    file_or_dir_path = os.path.join(crackers_path, file_or_dir)

                    if not os.path.isdir(file_or_dir_path) or not file_or_dir.isdigit():
                        continue

                    hashtopolis_file = os.path.join(file_or_dir_path, "hashtopolis.pid")

                    if not os.path.isfile(hashtopolis_file):
                        continue

                    try:
                        os.remove(hashtopolis_file)
                    except Exception as e:
                        logging.error("Could not remove file %s: %s", hashtopolis_file, e)

        # Delete old.zip file if it exists
        old_zip_file = os.path.join(self.base_dir, "old.zip")
        if os.path.isfile(old_zip_file):
            try:
                os.remove(old_zip_file)
            except Exception as e:
                logging.error("Could not remove file %s: %s", old_zip_file, e)

    def de_register(self):
        """De-register the agent from the server."""
        self.send_warning("De-registering agent.")
        logging.debug("De-registering agent.")
        query = {"action": "deregister"}
        response = self.post(query)

        if response is None:
            return

        logging.info("Successfully de-registered from the server.")

        self.clean_up(True)

    def is_running(self):
        """Check if the agent is already running."""
        lock_file = os.path.join(self.base_dir, "lock.pid")

        if os.path.isfile(lock_file):
            pid = file_get_content(lock_file)
            logging.info("Found lock file with PID %s", pid)

            if pid.isdigit() and psutil.pid_exists(int(pid)):
                logging.info("Process with PID %s is running.", pid)
                command = psutil.Process(int(pid)).cmdline()[0].replace("\\", "/").split("/")
                logging.info("Command: %s", command)

                if command[-1].startswith("python"):
                    return True

            logging.info("Process with PID %s is not running.", pid)
            os.remove(lock_file)

        logging.info("No lock file found.")
        file_set_content(lock_file, str(os.getpid()))

        return False

    def update_client(self):
        """Check for client updates and download them."""
        logging.info("Checking for client updates.")
        query = {"action": "checkClientVersion", "version": Agent.get_version_number(), "type": "python"}
        response = self.post(query)

        if response is None:
            return

        if response["version"] == "OK":
            logging.info("Client is up to date.")
            return

        url = response["url"]

        if not url:
            self.send_warning("Got empty URL for client update.")
            return

        logging.info("New client version available.")
        logging.info("Downloading new client version.")
        download_file = os.path.join(self.base_dir, "update.zip")

        if os.path.isfile(download_file):
            os.remove(download_file)

        if not self.download(url, download_file):
            return

        if not os.path.isfile(download_file) or not os.path.getsize(download_file):
            self.send_error("Downloaded file is empty.")
            return

        old_file = os.path.join(self.base_dir, "old.zip")

        os.rename(os.path.join(self.base_dir, "hashtopolis.zip"), old_file)
        os.rename(download_file, os.path.join(self.base_dir, "hashtopolis.zip"))

        logging.info("Update received, restarting client.")
        lock_file = os.path.join(self.base_dir, "lock.pid")

        if os.path.isfile(lock_file):
            os.remove(lock_file)

        self.send_warning("Restarting client due to update.")
        os.execl(sys.executable, sys.executable, "hashtopolis.zip")
        sys.exit(0)

    def start_uftpd(self):
        """Start the multicast daemon."""
        uftpd_path = os.path.join(self.base_dir, "uftpd" + OperatingSystem.get_extension(self.operating_system))

        if not os.path.isfile(uftpd_path):
            self.send_error("uftpd not found.")
            return

        logging.info("Starting uftpd.")

        try:
            subprocess.check_output("killall -s 9 uftpd", shell=True)
        except subprocess.CalledProcessError:
            pass

        multicast_device = self.config.get_value("multicast-device")
        files_path = self.config.get_value("files-path")
        log_path = self.config.get_value("log-path")

        if not isinstance(log_path, str) or not isinstance(files_path, str) or not isinstance(multicast_device, str):
            self.send_error("Log path, files path or multicast device not set.")
            return

        command_parts: list[str] = [
            uftpd_path,
            "-I",
            multicast_device,
            "-D",
            files_path,
            "-L",
            os.path.join(log_path, "multicast_" + str(time.time()) + ".log"),
        ]

        command = " ".join(command_parts)

        subprocess.check_output(command, shell=True)
        logging.info("Started multicast daemon.")

    def update_config(self):
        """Update the agent configuration."""
        self.config.update()

    def send_error(self, error: str, task_id: int | None = None, chunk_id: int | None = None):
        """Send an error to the server."""
        error = unidecode(error)
        error_key = error + str(task_id) + str(chunk_id)
        default_task = False
        errors_to_ignore = self.config.get_value("error-ignored")

        if isinstance(errors_to_ignore, list):
            if any(part in error for part in errors_to_ignore):
                logging.warning("Error ignored: %s", error)
                return

        if task_id is None and self.default_error_task is not None:
            task_id = self.default_error_task  # type: ignore
            default_task = True

        if error_key in self.send_errors:
            if int(time.time() - self.send_errors[error_key]) < self.config.get_value("same-error-timeout"):  # type: ignore
                logging.warning("Error already sent to server: %s", error)
                return

        self.send_errors[error_key] = int(time.time())

        if default_task:
            message = f"Error: {error}"
        else:
            message = f"Error: {error} - Task: {task_id}"

        query: dict[str, str | int | None] = {
            "action": "clientError",
            "message": message,
            "chunkId": chunk_id,
            "taskId": task_id,
        }

        if default_task and not self.agent_id is None and not task_id is None and not self.api_key is None:
            query_assign: dict[str, Any] = {
                "section": "task",
                "request": "taskAssignAgent",
                "agentId": self.agent_id,
                "taskId": task_id,
                "accessKey": self.api_key,
            }

            query_unassign: dict[str, Any] = {
                "section": "task",
                "request": "taskUnassignAgent",
                "agentId": self.agent_id,
                "accessKey": self.api_key,
            }

            query_assign_2: dict[str, Any] = {
                "section": "task",
                "request": "taskAssignAgent",
                "agentId": self.agent_id,
                "taskId": task_id,
                "accessKey": self.api_key,
            }

            self.post(query_assign, False, user=True)
            self.post(query)
            self.post(query_unassign, False, user=True)
            self.post(query_assign_2, False, user=True)

        elif not default_task:
            logging.error("Sent error to server: %s", error)
            response = self.post(query)

            query_assign: dict[str, Any] = {
                "section": "task",
                "request": "taskAssignAgent",
                "agentId": self.agent_id,
                "taskId": self.default_error_task,
                "accessKey": self.api_key,
            }

            query_unassign: dict[str, Any] = {
                "section": "task",
                "request": "taskUnassignAgent",
                "agentId": self.agent_id,
                "accessKey": self.api_key,
            }

            query_assign_2: dict[str, Any] = {
                "section": "task",
                "request": "taskAssignAgent",
                "agentId": self.agent_id,
                "taskId": task_id,
                "accessKey": self.api_key,
            }

            if response and response["response"] == "ERROR":
                query_2: dict[str, Any] = {
                    "action": "clientError",
                    "message": "Warning: Task which caused the error is not assigned to agent.",
                    "chunkId": None,
                    "taskId": self.default_error_task,
                }

                query["taskId"] = self.default_error_task  # type: ignore

                self.post(query_assign, False, user=True)
                self.post(query)
                self.post(query_2)
                self.post(query_unassign, False, user=True)
                self.post(query_assign_2, False, user=True)
        else:
            logging.warning("Error not sent to server as no task could be assigned to the error.")

    def send_warning(self, warning: str, task_id: int | None = None, chunk_id: int | None = None):
        """Send a warning to the server."""
        warning = unidecode(warning)
        warning_key = warning + str(task_id) + str(chunk_id)
        default_task = False
        errors_to_ignore = self.config.get_value("error-ignored")

        if isinstance(errors_to_ignore, list):
            if any(part in warning for part in errors_to_ignore):
                logging.warning("Warning ignored: %s", warning)
                return

        if task_id is None and self.default_error_task is not None:
            task_id = self.default_error_task  # type: ignore
            default_task = True

        if warning_key in self.send_warnings:
            if int(time.time() - self.send_warnings[warning_key]) < self.config.get_value("same-warning-timeout"):  # type: ignore
                logging.warning("Warning already sent to server: %s", warning)
                return

        self.send_warnings[warning_key] = int(time.time())

        if default_task:
            message = f"Warning: {warning}"
        else:
            message = f"Warning: {warning} - Task: {task_id}"

        query: dict[str, str | int | None] = {
            "action": "clientError",
            "message": message,
            "chunkId": chunk_id,
            "taskId": task_id,
        }

        if default_task and not self.agent_id is None and not task_id is None and not self.api_key is None:
            query_assign: dict[str, Any] = {
                "section": "task",
                "request": "taskAssignAgent",
                "agentId": self.agent_id,
                "taskId": task_id,
                "accessKey": self.api_key,
            }

            query_unassign: dict[str, Any] = {
                "section": "task",
                "request": "taskUnassignAgent",
                "agentId": self.agent_id,
                "accessKey": self.api_key,
            }

            self.post(query_assign, False, user=True)
            self.post(query)
            self.post(query_unassign, False, user=True)

        elif not default_task:
            logging.warning("Sent warning to server: %s", warning)
            response = self.post(query)

            query_assign: dict[str, Any] = {
                "section": "task",
                "request": "taskAssignAgent",
                "agentId": self.agent_id,
                "taskId": self.default_error_task,
                "accessKey": self.api_key,
            }

            query_unassign: dict[str, Any] = {
                "section": "task",
                "request": "taskUnassignAgent",
                "agentId": self.agent_id,
                "accessKey": self.api_key,
            }

            if response and response["response"] == "ERROR":
                query_2: dict[str, Any] = {
                    "action": "clientError",
                    "message": "Warning: Task which caused the warning is not assigned to agent.",
                    "chunkId": None,
                    "taskId": self.default_error_task,
                }

                query["taskId"] = self.default_error_task  # type: ignore

                self.post(query_assign, False, user=True)
                self.post(query)
                self.post(query_2)
                self.post(query_unassign, False, user=True)
        else:
            logging.warning("Warning not sent to server as no task could be assigned to the warning.")

    def run_health_check(self, task: Any):
        """Run a health check."""
        logging.info("Running health check.")
        query = {"action": "getHealthCheck"}
        response = self.post(query)

        if response is None:
            return

        try:
            cracker = Cracker(self, response["crackerBinaryId"])
        except Exception:
            self.send_error("Getting cracker failed on health check.")
            return

        check_id = response["checkId"]
        logging.info("Starting health check with ID %s.", check_id)

        hashlists_path = self.config.get_value("hashlists-path")

        if not isinstance(hashlists_path, str):
            self.send_error("Hashlists path not set.")
            return

        health_hashlists_path = os.path.join(hashlists_path, "health_check.txt")
        output_file = os.path.join(hashlists_path, "health_check.out")

        file_set_content(health_hashlists_path, "\n".join(response["hashes"]))

        if os.path.exists(output_file):  # type: ignore
            os.remove(output_file)  # type: ignore

        if cracker.name == "hashcat":
            cracker = HashcatCracker(self, task)
        else:
            self.send_error("Unknown cracker for health check.")
            return

        start = int(time.time())
        [status, errors] = cracker.run_health_check(
            response["attack"], response["hashlistAlias"], health_hashlists_path, output_file
        )
        end = int(time.time())

        if len(status) > 0:
            num_gpus = len(status[0].get_temps())
        else:
            errors.append("Failed to retrieve one successful cracker state, most likely due to failing.")
            num_gpus = 0

        query: dict[str, Any] = {
            "action": "sendHealthCheck",
            "checkId": check_id,
            "start": start,
            "end": end,
            "numGpus": num_gpus,
            "numCracked": len(file_get_content(output_file).splitlines()),  # type: ignore
            "errors": errors,
        }

        self.post(query)
