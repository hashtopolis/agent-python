import logging
from time import sleep

import os

from htpclient.config import Config
from htpclient.download import Download
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest


class Files:
    def __init__(self):
        self.config = Config()
        self.chunk = None

    def check_files(self, files, task_id):
        for file in files:
            if os.path.isfile("files/" + file):
                continue;
            req = JsonRequest({'action':'getFile', 'token': self.config.get_value('token'), 'taskId': task_id, 'file':file})
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
                if os.path.splitext("files/" + file)[1] == '.7z':
                    # extract if needed
                    os.system("7zr" + Initialize.get_os_extension() + " x -ofiles/ files/" + file)
        return True

