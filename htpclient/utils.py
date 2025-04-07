import ctypes
import logging
import os
import platform
import signal
import subprocess

import requests
from tqdm import tqdm

from htpclient.operating_system import OperatingSystem


def replace_double_space(text: str):
    """Replace double spaces with single spaces"""
    while "  " in text:
        text = text.replace("  ", " ")

    return text


def file_get_content(file_path: str):
    """Get the content of a file"""
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read()

    return data


def file_set_content(file_path: str, data: str):
    """Set the content of a file"""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(data)


def get_system_bit() -> str:
    """Get the system bit"""
    return "64" if platform.machine().endswith("64") else "32"


def format_speed(speed: float) -> str:
    """Format the speed to a human-readable format"""
    prefixes = {0: "", 1: "k", 2: "M", 3: "G", 4: "T", 5: "P"}
    exponent = 0

    while speed > 1000:
        if exponent == 5:
            break

        exponent += 1
        speed = float(speed) / 1000

    return f"{speed:6.2f}{prefixes[exponent]}H/s"


def kill_hashcat(pid: int, operating_system: OperatingSystem):
    """Kill the hashcat process"""
    if operating_system != OperatingSystem.WINDOWS:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    else:
        subprocess.run(f"TASKKILL /F /PID {pid} /T", check=True)
        logging.info("Killed hashcat process with PID %d", pid)


def get_storage_remaining(storage_path: str, operating_system: OperatingSystem) -> int:
    """Get the remaining storage space in bytes"""
    if operating_system == OperatingSystem.WINDOWS:
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore
            ctypes.c_wchar_p(storage_path), None, None, ctypes.pointer(free_bytes)
        )
        return free_bytes.value

    stats = os.statvfs(storage_path)
    return stats.f_bavail * stats.f_frsize


def get_storage_total(storage_path: str, operating_system: OperatingSystem) -> int:
    """Get the total storage space in bytes"""
    if operating_system == OperatingSystem.WINDOWS:
        total_bytes = ctypes.c_ulonglong(0)
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore
            ctypes.c_wchar_p(storage_path), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes)
        )
        return total_bytes.value

    stats = os.statvfs(storage_path)
    return stats.f_blocks * stats.f_frsize


def download_file(response: requests.Response, output: str):
    """Download a file from a response"""
    chunk_size = 4096  # Define the chunk size for downloading

    os.makedirs(os.path.dirname(output), exist_ok=True)  # Create the output directory

    # Get the total file length from the response headers
    total_length = int(response.headers.get("Content-Length", 0))

    # Open the file for writing in binary mode
    with open(output, "wb") as file, tqdm(
        total=total_length, unit="B", unit_scale=True, desc="Downloading"
    ) as progress_bar:

        try:
            # Iterate over the response content in chunks
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive new chunks
                    file.write(chunk)
                    progress_bar.update(len(chunk))

        except Exception as e:
            logging.error("Error occurred while downloading the file: %s", e)
            return False

    return True


def run_command_and_get_output(command: str, output_considered_error: list[str] | None = None):
    """Run a command and get the output"""
    output_lines: list[str] = []

    logging.debug("Running command: %s", command)

    # Start the process
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Read the output line by line as it is produced
    for line in iter(process.stdout.readline, ""):  # type: ignore
        if not output_considered_error is None and any(error_part in line for error_part in output_considered_error):
            process.kill()
            raise RuntimeError("Error occurred while running the command")

        print(line, end="")  # Print to terminal (real-time progress)
        output_lines.append(line.strip())  # Collect the output lines

    process.stdout.close()  # type: ignore
    process.wait()  # Wait for the process to finish

    return output_lines


def run_command_and_get_output_and_errors(command: str, output_considered_error: list[str] | None = None):
    """Run a command and get the output and errors"""
    output_lines: list[str] = []
    error_lines: list[str] = []

    # Start the process with separate pipes for stdout and stderr
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Read the output (stdout and stderr) in real-time
    while True:
        output = process.stdout.readline()  # type: ignore
        error = process.stderr.readline()  # type: ignore

        if not output_considered_error is None and any(
            error_part in output or error_part in error for error_part in output_considered_error
        ):
            process.kill()
            raise RuntimeError("Error occurred while running the command")

        if output == "" and error == "" and process.poll() is not None:
            break

        if output:
            print(output, end="")  # Print stdout to terminal in real-time
            output_lines.append(output.strip())  # Append to output list

        if error:
            print(error, end="")  # Print stderr to terminal in real-time
            error_lines.append(error.strip())  # Append to error list

    process.stdout.close()  # type: ignore
    process.stderr.close()  # type: ignore

    process.wait()  # Wait for the process to finish

    return output_lines, error_lines
