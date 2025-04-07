import argparse
import datetime
import logging
import os
import sys
import time
from dataclasses import dataclass
from logging.handlers import TimedRotatingFileHandler
from time import sleep
from typing import Any

import psutil

from htpclient import Agent
from htpclient.chunk import ChunkStatus
from htpclient.files import Files
from htpclient.generic_cracker import GenericCracker
from htpclient.hashcat_cracker import HashcatCracker
from htpclient.task import Task

cur_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


@dataclass
class Arguments:
    """Data class for arguments"""

    de_register: bool
    version: bool
    number_only: bool
    debug: bool
    idle: bool


# Sets up the logging to stdout and to file with different styles and with the level as set in the config if available
def init_logging(debug: bool, log_dir: str = "logs"):
    """Initialize logging"""
    # Log formats
    file_log_format = "%(asctime)s - [%(levelname)-5s] - %(message)s"
    console_log_format = "[%(levelname)-5s] %(message)s"  # Simpler format for console output
    log_date_format = "%Y-%m-%d %H:%M:%S"
    log_level = logging.DEBUG if debug else logging.INFO

    # Ensure the logs directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Set up a TimedRotatingFileHandler to rotate logs every 5 days
    log_path = os.path.join(log_dir, "client.log")
    file_handler = TimedRotatingFileHandler(log_path, when="D", interval=5, backupCount=5, encoding="utf-8", utc=True)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(file_log_format, datefmt=log_date_format))

    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)  # Set log level for root logger
    root_logger.addHandler(file_handler)  # Add the file handler to the root logger

    # Console handler with a different format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(console_log_format))  # Simpler format for console
    root_logger.addHandler(console_handler)

    # Optionally, adjust the log level for specific libraries (e.g., 'requests')
    logging.getLogger("requests").setLevel(logging.WARNING if not debug else logging.DEBUG)


def loop(agent: Agent, idle: bool):
    """Main loop"""
    logging.debug("Entering loop...")
    task = None
    old_task = None
    files = Files(agent)
    cracker = None
    idle_check = 0
    idle_state = not idle

    while True:
        if idle and time.time() - idle_check >= 3600:
            idle_check = time.time()
            if psutil.cpu_percent() > 10:
                idle_state = False
            else:
                idle_state = True

        if not idle_state:
            logging.debug("System is not idle, waiting...")
            sleep(60)
            continue

        if task is not None:
            old_task = task

        sleep(5)  # wait for 5 seconds before trying again to get a task to avoid spamming the server
        try:
            task = Task.get_task(agent)
        except Exception as e:
            logging.error("Failed to get task: %s", e)
            continue

        if agent.last_update_check + datetime.timedelta(weeks=1) < datetime.datetime.now():
            agent.last_update_check = datetime.datetime.now()
            logging.info("Checking for updates...")
            agent.update_client()

        if agent.last_clean_up + datetime.timedelta(days=1) < datetime.datetime.now():
            logging.info("Cleaning up...")
            agent.clean_up()

        if files.last_check + datetime.timedelta(minutes=5) < datetime.datetime.now():
            logging.info("Checking for files to clean up...")
            files.clean_up()

        logging.info("Updating config...")
        agent.update_config()

        if not task:
            logging.warning("No task available")
            continue

        if task.downloaded_files:
            logging.debug("Retrying to get task to check if still current task...")
            continue

        if task.task_id == -1:
            logging.info("Running health check...")
            agent.run_health_check(task)
            continue

        if (old_task and task.task_id != old_task.task_id) or cracker is None or cracker.task.task_id != task.task_id:
            if task.cracker.name == "hashcat":
                cracker = HashcatCracker(agent, task)
            else:
                cracker = GenericCracker(agent, task)

        logging.info("Getting chunk...")
        chunk = task.get_chunk()

        if not chunk:
            logging.warning("No chunk available")
            continue

        if chunk.status == ChunkStatus.KEYSPACE_REQUIRED:
            logging.info("Measuring keyspace...")
            cracker.measure_keyspace(chunk)
            continue

        if chunk.status == ChunkStatus.BENCHMARK:
            logging.info("Running benchmark...")
            result = cracker.run_benchmark(chunk)

            if result == 0:
                sleep(10)
                continue

            query: dict[str, Any] = {
                "action": "sendBenchmark",
                "taskId": task.task_id,
                "result": result,
                "type": task.benchmark_type,
            }

            response = agent.post(query)

            if response is None:
                logging.error("Failed to send benchmark!")
                sleep(5)
                continue

        if chunk.status == ChunkStatus.NORMAL:
            logging.info("Running chunk...")
            if chunk.length == 0:
                agent.send_warning("Invalid chunk size (0) retrieved! Retrying...", task.task_id)
                continue

            cracker.run_chunk(chunk)

            if cracker.agent_stopped():
                continue


def argument_parser() -> Arguments:
    """Parse arguments"""
    parser = argparse.ArgumentParser(
        description="Hashtopolis Client v" + Agent.get_version_number(), prog="python3 hashtopolis.zip"
    )
    parser.add_argument(
        "--de-register", action="store_true", help="client should automatically de-register from server now"
    )
    parser.add_argument("--version", action="store_true", help="show version information")
    parser.add_argument("--number-only", action="store_true", help="when using --version show only the number")
    parser.add_argument("--debug", "-d", action="store_true", help="enforce debugging output")
    parser.add_argument("--idle", action="store_true", help="run in idle mode (only when machine is idle)")

    args = parser.parse_args()
    return Arguments(
        de_register=args.de_register,
        version=args.version,
        number_only=args.number_only,
        debug=args.debug,
        idle=args.idle,
    )


if __name__ == "__main__":
    args = argument_parser()
    init_logging(args.debug)
    logging.debug("Starting client with arguments: %s", args)

    if args.version:
        if args.number_only:
            logging.info(Agent.get_version_number())
        else:
            logging.info(Agent.get_version())
        sys.exit(0)

    agent = Agent(cur_dir)

    if args.de_register:
        agent.de_register()
        sys.exit(0)

    if agent.is_running():
        logging.error("There is already a hashtopolis agent running in this directory!")
        sys.exit(-1)

    try:
        loop(agent, args.idle)
    except KeyboardInterrupt:
        agent.send_warning("Client was stopped by user")
        logging.info("Exiting...")
        # if lock file exists, remove
        if os.path.exists("lock.pid"):
            os.remove("lock.pid")
        sys.exit()
    except Exception as e:
        print(f"Client crashed: {e}")
        agent.send_error(f"Client crashed: {e}")
