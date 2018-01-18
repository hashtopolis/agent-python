import platform
import uuid
from time import sleep

import subprocess

from htpclient.jsonRequest import *


class Initialize:
    def __init__(self):
        self.config = Config()

    def run(self):
        self.__check_url()
        self.__check_token()
        self.__update_information()
        self.__login()
        self.__build_directories()

    @staticmethod
    def get_os():
        if os.name == 'nt':
            system = 1  # Windows
        elif os.name == 'posix':
            # Linux or OS X
            if platform.system() == 'Darwin':
                system = 2  # OS X
            else:
                system = 0  # Linux
        else:
            system = 0  # Linux
        return system

    @staticmethod
    def get_os_extension():
        if os.name == 'nt':
            ext = '.exe'  # Windows
        elif os.name == 'posix':
            ext = ''  # Linux or OS X
        else:
            ext = ''
        return ext

    def __login(self):
        req = JsonRequest(
            {'action': 'login', 'token': self.config.get_value('token'), 'clientSignature': 'generic-python_alpha'})
        ans = req.execute()
        if ans is None:
            logging.error("Login failed!")
            sleep(5)
            self.__login()
        elif ans['response'] != 'SUCCESS':
            logging.error("Error from server: " + str(ans))
            self.config.set_value('token', '')
            self.__login()
        else:
            logging.info("Login successful!")

    def __update_information(self):
        if len(self.config.get_value('uuid')) == 0:
            self.config.set_value('uuid', str(uuid.uuid4()))

        # collect devices
        devices = []
        if Initialize.get_os() == 0:  # linux
            pass
        elif Initialize.get_os() == 1:  # windows
            output = subprocess.check_output("wmic path win32_VideoController get name", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                line = line.rstrip("\r\n ")
                if line == "Name" or len(line) == 0:
                    continue
                devices.append(line)
        else:  # OS X
            output = subprocess.check_output("system_profiler -detaillevel mini", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                line = line.rstrip("\r\n ")
                if "Chipset Model" not in line:
                    continue
                line = line.split(":")
                devices.append(line[1])

        req = JsonRequest(
            {'action': 'updateInformation', 'token': self.config.get_value('token'),
             'uid': self.config.get_value('uuid'),
             'os': self.get_os(), 'devices': devices})

        # MAC
        # system name: scutil --get ComputerName
        # devices: system_profiler -detaillevel mini
        # Filter for Chipset Model
        # Filter for Graphics/Displays

        # LINUX
        # lscpu
        # filter Model Name
        # lspci
        # filter VGA compatible controller

        ans = req.execute()
        if ans is None:
            logging.error("Information update failed!")
            sleep(5)
            self.__update_information()
        elif ans['response'] != 'SUCCESS':
            logging.error("Error from server: " + str(ans))
            sleep(5)
            self.__update_information()

    def __check_token(self):
        if len(self.config.get_value('token')) == 0:
            voucher = input("No token found! Please enter a voucher to register your agent:\n")
            # TODO: read the name of the computer to register
            name = platform.node()
            req = JsonRequest({'action': 'register', 'voucher': voucher, 'name': name})
            ans = req.execute()
            if ans is None:
                logging.error("Request failed!")
                self.__check_token()
            elif ans['response'] != 'SUCCESS' or len(ans['token']) == 0:
                logging.error("Registering failed: " + str(ans))
                self.__check_token()
            else:
                token = ans['token']
                self.config.set_value('token', token)
                logging.info("Successfully registered!")

    def __check_url(self):
        if len(self.config.get_value('url')) == 0:
            # ask for url
            url = input("Please enter the url to the API of your Hashtopussy installation:\n")
            logging.debug("Setting url to: " + url)
            self.config.set_value('url', url)
        else:
            return
        req = JsonRequest({'action': 'testConnection'})
        ans = req.execute()
        if ans is None:
            logging.error("Connection test failed!")
            self.config.set_value('url', '')
            self.__check_url()
        elif ans['response'] != 'SUCCESS':
            logging.error("Connection test failed: " + str(ans))
            self.config.set_value('url', '')
            self.__check_url()
        else:
            logging.info("Connection test successful!")

    @staticmethod
    def __build_directories():
        if not os.path.isdir("crackers"):
            os.mkdir("crackers")
        if not os.path.isdir("files"):
            os.mkdir("files")
        if not os.path.isdir("hashlists"):
            os.mkdir("hashlists")
