import platform
import uuid
from time import sleep

from htpclient.dicts import *
from htpclient.helpers import *
from htpclient.jsonRequest import *


class Initialize:
    def __init__(self):
        self.config = Config()

    @staticmethod
    def get_version():
        return "s3-python-0.1.4"

    def run(self):
        self.__check_url()
        self.__check_token()
        self.__update_information()
        self.__login()
        self.__build_directories()

    @staticmethod
    def get_os():
        os = platform.system()
        try:
            return dict_os[os]
        except:
            logging.debug("OS: %s" % os)
            log_error_and_exit("It seems your operating system is not supported.")

    @staticmethod
    def get_os_extension():
        os = Initialize.get_os()
        return dict_ext[os]

    def __login(self):
        query = copyAndSetToken(dict_login, self.config.get_value('token'))
        query['clientSignature'] = self.get_version()
        req = JsonRequest(query)
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
        logging.info("Collecting agent data...")
        devices = []
        if Initialize.get_os() == 0:  # linux
            output = subprocess.check_output("lscpu | grep 'Model name'", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                if len(line) == 0:
                    continue
                devices.append(line.replace("Model name:", "").strip("\r\n "))
            try:
                output = subprocess.check_output("lspci | grep -E 'VGA compatible controller|3D controller'", shell=True)
            except subprocess.CalledProcessError:
                # we silently ignore this case on machines where lspci is not present or architecture has no pci bus
                output = b""
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                if len(line) == 0:
                    continue
                line = line.split(":")
                devices.append(line[2].strip())

        elif Initialize.get_os() == 1:  # windows
            output = subprocess.check_output("wmic cpu get name", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                line = line.rstrip("\r\n ")
                if line == "Name" or len(line) == 0:
                    continue
                devices.append(line)
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
                devices.append(line[1].strip())

        query = copyAndSetToken(dict_updateInformation, self.config.get_value('token'))
        query['uid'] = self.config.get_value('uuid')
        query['os'] = self.get_os()
        query['devices'] = devices
        req = JsonRequest(query)
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
            if len(self.config.get_value('voucher')) > 0:
                # voucher is set in config and can be used to autoregister
                voucher = self.config.get_value('voucher')
            else:
                voucher = input("No token found! Please enter a voucher to register your agent:\n").strip()
            name = platform.node()
            query = dict_register.copy()
            query['voucher'] = voucher
            query['name'] = name
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Request failed!")
                self.__check_token()
            elif ans['response'] != 'SUCCESS' or len(ans['token']) == 0:
                logging.error("Registering failed: " + str(ans))
                self.__check_token()
            else:
                token = ans['token']
                self.config.set_value('voucher', '')
                self.config.set_value('token', token)
                logging.info("Successfully registered!")

    def __check_url(self):
        if len(self.config.get_value('url')) == 0:
            # ask for url
            url = input("Please enter the url to the API of your Hashtopolis installation:\n").strip()
            logging.debug("Setting url to: " + url)
            self.config.set_value('url', url)
        else:
            return
        query = dict_testConnection.copy()
        req = JsonRequest(query)
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
            logging.debug("Connection test successful!")

    @staticmethod
    def __build_directories():
        if not os.path.isdir("crackers"):
            os.mkdir("crackers")
        if not os.path.isdir("files"):
            os.mkdir("files")
        if not os.path.isdir("hashlists"):
            os.mkdir("hashlists")
