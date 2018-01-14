import platform
from time import sleep

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
            sleep(5)
            self.__login()
        else:
            logging.info("Login successful!")

    def __update_information(self):
        # TODO: gather system information
        req = JsonRequest(
            {'action': 'updateInformation', 'token': self.config.get_value('token'), 'uid': 'enter UID here',
             'os': self.get_os(), 'devices': ['mockGPU1', 'mockGPU2']})
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
            name = "generic-python"
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

