import logging
import os.path
from time import sleep

from htpclient.config import Config
from htpclient.download import Download
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest


class Binary_Download:
    def __init__(self):
        self.config = Config()

    def run(self):
        self.__check_version()
        self.__check_utils()

    def __check_utils(self):
        path = '7zr' + Initialize.get_os_extension()
        if not os.path.isfile(path):
            req = JsonRequest({'action': 'downloadBinary', 'type': '7zr', 'token': self.config.get_value('token')})
            ans = req.execute()
            if ans is None:
                logging.error("Failed to get 7zr!")
                sleep(5)
                self.__check_utils()
            elif ans['response'] != 'SUCCESS' or len(ans['executable']) == 0:
                logging.error("Getting 7zr failed: " + str(ans))
                sleep(5)
                self.__check_utils()
            else:
                Download.download(ans['executable'], path)

    def __check_version(self):
        # TODO: implement
        logging.error("Not implemented yet!")
