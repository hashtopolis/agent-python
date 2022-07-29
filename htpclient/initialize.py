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
        return "s3-python-" + Initialize.get_version_number()

    @staticmethod
    def get_version_number():
        return "0.6.1"

    def run(self, args):
        self.__check_cert(args)
        self.__check_url(args)
        self.__check_token(args)
        self.__update_information()
        self.__login()
        self.__build_directories()

    @staticmethod
    def get_os():
        operating_system = platform.system()
        try:
            return dict_os[operating_system]
        except KeyError:
            logging.debug("OS: %s" % operating_system)
            log_error_and_exit("It seems your operating system is not supported.")

    @staticmethod
    def get_os_extension():
        operating_system = Initialize.get_os()
        return dict_ext[operating_system]

    def __login(self):
        while True:
            query = copy_and_set_token(dict_login, self.config.get_value('token'))
            query['clientSignature'] = self.get_version()
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Login failed!")
                sleep(5)
            elif ans['response'] != 'SUCCESS':
                logging.error("Error from server: " + str(ans))
                self.config.set_value('token', '')
                sleep(5)
            else:
                logging.info("Login successful!")
                if 'server-version' in ans:
                    logging.info("Hashtopolis Server version: " + ans['server-version'])
                if 'multicastEnabled' in ans and ans['multicastEnabled'] and self.get_os() == 0:  # currently only allow linux
                    logging.info("Multicast enabled!")
                    self.config.set_value('multicast', True)
                    if not os.path.isdir("multicast"):
                        os.mkdir("multicast")
                return

    def __update_information(self):
        if not self.config.get_value('uuid'):
            self.config.set_value('uuid', str(uuid.uuid4()))

        # collect devices
        logging.info("Collecting agent data...")
        devices = []
        if Initialize.get_os() == 0:  # linux
            output = subprocess.check_output("cat /proc/cpuinfo", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            tmp = []
            for line in output:
                line = line.strip()
                if not line.startswith('model name') and not line.startswith('physical id'):
                    continue
                value = line.split(':', 1)[1].strip()
                while '  ' in value:
                    value = value.replace('  ', ' ')
                tmp.append(value)

            pairs = []
            for i in range(0, len(tmp), 2):
                pairs.append("%s:%s" % (tmp[i + 1], tmp[i]))

            for line in sorted(set(pairs)):
                devices.append(line.split(':', 1)[1].replace('\t', ' '))
            try:
                output = subprocess.check_output("lspci | grep -E 'VGA compatible controller|3D controller'", shell=True)
            except subprocess.CalledProcessError:
                # we silently ignore this case on machines where lspci is not present or architecture has no pci bus
                output = b""
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                if not line:
                    continue
                line = ' '.join(line.split(' ')[1:]).split(':')
                devices.append(line[1].strip())

        elif Initialize.get_os() == 1:  # windows
            output = subprocess.check_output("wmic cpu get name", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                line = line.rstrip("\r\n ")
                if line == "Name" or not line:
                    continue
                devices.append(line)
            output = subprocess.check_output("wmic path win32_VideoController get name", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                line = line.rstrip("\r\n ")
                if line == "Name" or not line:
                    continue
                devices.append(line)

        else:  # OS X
            output = subprocess.check_output("system_profiler SPDisplaysDataType -detaillevel mini", shell=True)
            output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
            for line in output:
                line = line.rstrip("\r\n ")
                if "Chipset Model" not in line:
                    continue
                line = line.split(":")
                devices.append(line[1].strip())

        while True:
            query = copy_and_set_token(dict_updateInformation, self.config.get_value('token'))
            query['uid'] = self.config.get_value('uuid')
            query['os'] = self.get_os()
            query['devices'] = devices
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Information update failed!")
                sleep(5)
            elif ans['response'] != 'SUCCESS':
                logging.error("Error from server: " + str(ans))
                sleep(5)
            else:
                return

    def __check_token(self, args):
        if not self.config.get_value('token'):
            while True:
                if self.config.get_value('voucher'):
                    # voucher is set in config and can be used to autoregister
                    voucher = self.config.get_value('voucher')
                elif args.voucher:
                    voucher = args.voucher
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
                    sleep(1)
                elif ans['response'] != 'SUCCESS' or not ans['token']:
                    if self.config.get_value('voucher'):
                        self.config.set_value('voucher', ''):
                    logging.error("Registering failed: " + str(ans))
                    sleep(1)
                else:
                    token = ans['token']
                    self.config.set_value('voucher', '')
                    self.config.set_value('token', token)
                    logging.info("Successfully registered!")
                    return

    def __check_cert(self, args):
        cert = self.config.get_value('cert')
        if cert is None:
            if args.cert is not None:
                cert = os.path.abspath(args.cert)
                logging.debug("Setting cert to: " + cert)
                self.config.set_value('cert', cert)
                
        if cert is not None:
            Session().s.cert = cert
            logging.debug("Configuration session cert to: " + cert)

    def __check_url(self, args):
        while True:
            if not self.config.get_value('url'):
                # ask for url
                if args.url is None:
                    url = input("Please enter the url to the API of your Hashtopolis installation:\n").strip()
                else:
                    url = args.url
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
                sleep(1)
            elif ans['response'] != 'SUCCESS':
                logging.error("Connection test failed: " + str(ans))
                self.config.set_value('url', '')
                sleep(1)
            else:
                logging.debug("Connection test successful!")
                return

    @staticmethod
    def __build_directories():
        if not os.path.isdir("crackers"):
            os.mkdir("crackers")
        if not os.path.isdir("files"):
            os.mkdir("files")
        if not os.path.isdir("hashlists"):
            os.mkdir("hashlists")
        if not os.path.isdir("preprocessor"):
            os.mkdir("preprocessor")
