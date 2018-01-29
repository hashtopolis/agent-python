import logging
import os.path
import stat
from time import sleep

from htpclient.config import Config
from htpclient.download import Download
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class BinaryDownload:
    def __init__(self):
        self.config = Config()
        self.last_version = None

    def run(self):
        self.__check_utils()

    def get_version(self):
        return self.last_version

    def __check_utils(self):
        path = '7zr' + Initialize.get_os_extension()
        if not os.path.isfile(path):
            query = copyAndSetToken(dict_downloadBinary, self.config.get_value('token'))
            query['type'] = '7zr'
            req = JsonRequest(query)
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
                os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    def check_version(self, crackerId):
        path = "crackers/" + str(crackerId) + "/"
        query = copyAndSetToken(dict_downloadBinary, self.config.get_value('token'))
        query['type'] = 'cracker'
        query['binaryVersionId'] = crackerId
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to load cracker`!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS' or len(ans['url']) == 0:
            logging.error("Getting cracker failed: " + str(ans))
            sleep(5)
            return False
        else:
            self.last_version = ans
            if not os.path.isdir(path):
                # we need to download the 7zip
                Download.download(ans['url'], "crackers/" + str(crackerId) + ".7z")
                os.system("7zr" + Initialize.get_os_extension() + " x -ocrackers/temp crackers/" + str(crackerId) + ".7z")
                os.unlink("crackers/" + str(crackerId) + ".7z")
                for name in os.listdir("crackers/temp"):
                    if os.path.isdir("crackers/temp/" + name):
                        os.rename("crackers/temp/" + name, "crackers/" + str(crackerId))
                    else:
                        os.rename("crackers/temp", "crackers/" + str(crackerId))
                        break
        return True
