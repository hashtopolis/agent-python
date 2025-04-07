from enum import Enum


class OperatingSystem(Enum):
    """Enum representing the operating system"""

    LINUX = 0
    WINDOWS = 1
    MAC = 2

    @staticmethod
    def get_by_platform_name(name: str):
        """Get the operating system by the platform name"""
        if name == "Linux":
            return OperatingSystem.LINUX
        if name == "Windows":
            return OperatingSystem.WINDOWS
        if name == "Darwin":
            return OperatingSystem.MAC
        raise ValueError("Unknown platform name")

    def get_extension(self):
        """Get the extension for the operating system"""
        if self == OperatingSystem.WINDOWS:
            return ".exe"
        return ""
