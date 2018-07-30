import signal
import sys
import platform
import logging
from types import MappingProxyType

import os
import subprocess

from htpclient.dicts import copyAndSetToken, dict_clientError
from htpclient.jsonRequest import JsonRequest


def log_error_and_exit(message):
    logging.error(message)
    sys.exit(1)


def print_speed(speed):
    prefixes = MappingProxyType(
        {0: "",
         1: "k",
         2: "M",
         3: "G",
         4: "T"})
    exponent = 0
    while speed > 1000:
        exponent += 1
        speed = float(speed) / 1000
    return str("{:6.2f}".format(speed)) + prefixes[exponent] + "H/s"


def get_bit():
    if platform.machine().endswith('64'):
        return "64"
    return "32"


def kill_hashcat(pid, get_os):
    if get_os != 1:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    else:
        subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=pid))


def send_error(error, token, task_id):
    query = copyAndSetToken(dict_clientError, token)
    query['message'] = error
    query['taskId'] = task_id
    req = JsonRequest(query)
    req.execute()


def update_files(command):
    split = command.split(" ")
    ret = []
    for part in split:
        # test if file exists
        if len(part) == 0:
            continue
        path = "files/" + part
        if os.path.exists(path):
            ret.append("../../" + path)
        else:
            ret.append(part)
    return " ".join(ret)
