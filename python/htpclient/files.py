import logging
from time import sleep

import os

from htpclient.config import Config
from htpclient.download import Download
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class Files:
    def __init__(self):
        self.config = Config()
        self.chunk = None

    def check_files(self, files, task_id):
        for file in files:
            if os.path.isfile("files/" + file) or os.path.isfile("files/" + file.replace(".7z", ".txt")):
                continue
            query = copyAndSetToken(ditc_getFile, self.config.get_value('token'))
            query['taskId'] = task_id
            query['file'] = file
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Failed to get file!")
                sleep(5)
                return False
            elif ans['response'] != 'SUCCESS':
                logging.error("Getting of file failed: " + str(ans))
                sleep(5)
                return False
            else:
                Download.download(self.config.get_value('url').replace("api/server.php", "") + ans['url'], "files/" + file)
                if os.path.splitext("files/" + file)[1] == '.7z' and not os.path.isfile("files/" + file.replace(".7z", ".txt")):
                    # extract if needed
                    if Initialize.get_os() != 1:
                        os.system("./7zr" + Initialize.get_os_extension() + " x -aoa -ofiles/ -y files/" + file)
                    else:
                        os.system("7zr" + Initialize.get_os_extension() + " x -aoa -ofiles/ -y files/" + file)
        return True
