import copy
import json
import os
import platform
import uuid


class Config:
    """Class to handle the configuration of the agent"""

    DEFAULT_ERRORS_TO_IGNORE = [
        "clGetPlatformIDs(): CL_PLATFORM_NOT_FOUND_KHR",
        "cuInit(): forward compatibility was attempted on non supported HW",
        "cuLinkAddData(): the provided PTX was compiled with an unsupported toolchain.",
        "Kernel ./OpenCL/shared.cl build failed",
        "nvmlDeviceGetTemperatureThreshold(): Not Supported",
        "nvmlDeviceGetTemperature(): Not Supported",
        "nvmlDeviceGetCurrPcieLinkWidth(): Not Supported",
    ]

    DEFAULT_CONFIG: dict[str, str | int | float | bool | None | list[str]] = {
        "files-path": "files",
        "log-path": "logs",
        "log-level": "INFO",
        "crackers-path": "crackers",
        "hashlists-path": "hashlists",
        "zaps-path": "zaps",
        "preprocessors-path": "preprocessors",
        "multicast-path": "multicast",
        "proxies": None,
        "auth-user": None,
        "auth-password": None,
        "multicast": False,
        "multicast-device": "eth0",
        "rsync": False,
        "rsync-path": "rsync",
        "cert": None,
        "url": None,
        "voucher": None,
        "token": None,
        "cpu-only": False,
        "auto-clean": False,
        "name": platform.node(),
        "uuid": str(uuid.uuid4()),
        "request-timeout": 30,
        "same-error-timeout": 300,
        "same-warning-timeout": 300,
        "file-remove-after-not-accessed-days": 14,
        "file-deletion-disabled": False,
        "outfile-history": False,
        "piping-threshold": 95,
        "allow-piping": True,
        "verify-request": True,
        "allow-redirects-request": True,
        "default-error-task": None,
        "agent-id": None,
        "api-key": None,
        "error-ignored": DEFAULT_ERRORS_TO_IGNORE,
    }

    DIRECTORY_KEYS = {
        "files-path",
        "log-path",
        "crackers-path",
        "hashlists-path",
        "preprocessors-path",
        "multicast-path",
        "zaps-path",
        "rsync-path",
    }

    FILES_KEYS = {
        "cert",
    }

    REQUIRED_KEYS = {
        "url",
    }

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, "config.json")
        self.__config: dict[str, str | int | float | bool | None | list[str]] = copy.deepcopy(self.DEFAULT_CONFIG)

        if not os.path.isfile(self.config_path):
            self.__save()

        self.__config.update(self.__load())
        self.__save()

        self.__build_directories()
        self.__check_files_exist()
        self.__check_token()

        self.__check_required_keys()

    def __load(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def __save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.__config, f, indent=2, ensure_ascii=False)

    def __build_directories(self):
        for key in self.DIRECTORY_KEYS:
            dir_path = self.__config[key]

            if not isinstance(dir_path, str):
                continue

            if not os.path.isabs(dir_path):
                dir_path = os.path.join(self.base_dir, dir_path)
                self.__config[key] = dir_path
                self.__save()

            os.makedirs(dir_path, exist_ok=True)

    def __check_files_exist(self):
        for key in self.FILES_KEYS:
            file_path = self.__config[key]

            if not isinstance(file_path, str):
                continue

            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File '{file_path}' for '{key}' does not exist")

    def __check_token(self):
        if self.__config["token"] is None and self.__config["voucher"] is None:
            raise ValueError("Please provide a voucher so the agent can register")

    def __check_required_keys(self):
        for key in self.REQUIRED_KEYS:
            if self.__config[key] is None:
                raise KeyError(f"Key '{key}' is required")

    def get_value(self, key: str):
        """Get the value of a key from the configuration"""
        return self.__config.get(key, None)

    def set_value(self, key: str, value: str | int | float | None):
        """Set the value of a key in the configuration"""
        self.__config[key] = value
        self.__save()

    def get_all(self):
        """Get all the configuration"""
        return self.__config

    def update(self):
        """Update the configuration"""
        self.__config = self.__load()

    def __str__(self):
        return str(self.__config)
