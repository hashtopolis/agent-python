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

    def check_version(self, cracker_id):
        path = "crackers/" + str(cracker_id) + "/"
        query = copyAndSetToken(dict_downloadBinary, self.config.get_value('token'))
        query['type'] = 'cracker'
        query['binaryVersionId'] = cracker_id
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
                if not Download.download(ans['url'], "crackers/" + str(cracker_id) + ".7z"):
                    logging.error("Download of cracker binary failed!")
                    sleep(5)
                    return False
                if Initialize.get_os() == 1:
                    os.system("7zr" + Initialize.get_os_extension() + " x -ocrackers/temp crackers/" + str(cracker_id) + ".7z")
                else:
                    os.system("./7zr" + Initialize.get_os_extension() + " x -ocrackers/temp crackers/" + str(cracker_id) + ".7z")
                os.unlink("crackers/" + str(cracker_id) + ".7z")
                for name in os.listdir("crackers/temp"):
                    if os.path.isdir("crackers/temp/" + name):
                        os.rename("crackers/temp/" + name, "crackers/" + str(cracker_id))
                    else:
                        os.rename("crackers/temp", "crackers/" + str(cracker_id))
                        break
        return True
