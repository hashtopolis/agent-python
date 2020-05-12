import re
import signal
import sys
import platform
import logging
import time
from types import MappingProxyType

import os
import subprocess

from htpclient.dicts import copy_and_set_token, dict_clientError
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


def send_error(error, token, task_id, chunk_id):
    query = copy_and_set_token(dict_clientError, token)
    query['message'] = error
    query['chunkId'] = chunk_id
    query['taskId'] = task_id
    req = JsonRequest(query)
    req.execute()


def file_get_contents(filename):
    with open(filename) as f:
        return f.read()


def start_uftpd(os_extension, config):
    try:
        subprocess.check_output("killall -s 9 uftpd", shell=True)  # stop running service to make sure we can start it again
    except subprocess.CalledProcessError:
        pass  # ignore in case uftpd was not running
    path = './uftpd' + os_extension
    cmd = path + ' '
    if config.get_value('multicast-device'):
        cmd += "-I " + config.get_value('multicast-device') + ' '
    else:
        cmd += "-I eth0 "  # wild guess as default
    cmd += "-D " + os.path.abspath("files/") + ' '
    cmd += "-L " + os.path.abspath("multicast/" + str(time.time()) + ".log")
    logging.debug("CALL: " + cmd)
    subprocess.check_output(cmd, shell=True)
    logging.info("Started multicast daemon")


def get_wordlist(command):
    split = clean_list(command.split(" "))
    for index, part in enumerate(split):
        if part[0] == '-':
            continue
        elif index == 0 or split[index - 1][0] != '-':
            return part
    return ''


def get_rules_and_hl(command, alias):
    split = clean_list(command.split(" "))
    rules = []
    for index, part in enumerate(split):
        if index > 0 and (split[index - 1] == '-r' or split[index - 1] == '--rules-file'):
            rules.append(split[index - 1])
            rules.append(split[index - 0])
        if part == alias:
            rules.append(part)
    return " ".join(rules)


def clean_list(element_list):
    index = 0
    for part in element_list:
        if not part:
            del element_list[index]
            index -= 1
        index += 1
    return element_list


# the prince flag is deprecated
def update_files(command, prince=False):
    split = command.split(" ")
    ret = []
    for part in split:
        # test if file exists
        if not part:
            continue
        path = "files/" + part
        if os.path.exists(path):
            if prince:
                ret.append("../" + path)
            else:
                ret.append("../../" + path)
        else:
            ret.append(part)
    return " %s " % " ".join(ret)


def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)
