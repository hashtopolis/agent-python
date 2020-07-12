import logging
import time
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
        self.last_check = None
        self.check_interval = 600
        if self.config.get_value('file-deletion-interval'):
            self.check_interval = int(self.config.get_value('file-deletion-interval'))

    def deletion_check(self):
        if self.config.get_value('file-deletion-disable'):
            return
        elif self.last_check is not None and time.time() - self.last_check < self.check_interval:
            return
        query = copy_and_set_token(dict_getFileStatus, self.config.get_value('token'))
        req = JsonRequest(query)
        ans = req.execute()
        self.last_check = time.time()
        if ans is None:
            logging.error("Failed to get file status!")
        elif ans['response'] != 'SUCCESS':
            logging.error("Getting of file status failed: " + str(ans))
        else:
            files = ans['filenames']
            for filename in files:
                if filename.find("/") != -1 or filename.find("\\") != -1:
                    continue  # ignore invalid file names
                elif os.path.dirname("files/" + filename) != "files":
                    continue  # ignore any case in which we would leave the files folder
                elif os.path.exists("files/" + filename):
                    logging.info("Delete file '" + filename + "' as requested by server...")
                    if os.path.splitext("files/" + filename)[1] == '.7z':
                        if os.path.exists("files/" + filename.replace(".7z", ".txt")):
                            logging.info("Also delete assumed wordlist from archive of same file...")
                            os.unlink("files/" + filename.replace(".7z", ".txt"))
                    os.unlink("files/" + filename)

    def check_files(self, files, task_id):
        for file in files:
            file_localpath = "files/" + file
            query = copy_and_set_token(dict_getFile, self.config.get_value('token'))
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
                file_size = int(ans['filesize'])
                if os.path.isfile(file_localpath) and os.stat(file_localpath).st_size == file_size:
                    logging.debug("File is present on agent and has matching file size.")
                    continue
                elif self.config.get_value('multicast'):
                    logging.debug("Multicast is enabled, need to wait until it was delivered!")
                    sleep(5)  # in case the file is not there yet (or not completely), we just wait some time and then try again
                    return False
                # TODO: we might need a better check for this
                if os.path.isfile(file_localpath.replace(".7z", ".txt")):
                    continue
                if self.config.get_value('rsync') and Initialize.get_os() != 1:
                    Download.rsync(self.config.get_value('rsync-path') + '/' + file, file_localpath)
                else:
                    logging.debug("Starting download of file from server...")
                    Download.download(self.config.get_value('url').replace("api/server.php", "") + ans['url'], file_localpath)
                if os.path.isfile(file_localpath) and os.stat(file_localpath).st_size != file_size:
                    logging.error("file size mismatch on file: %s" % file)
                    sleep(5)
                    return False
                if os.path.splitext("files/" + file)[1] == '.7z' and not os.path.isfile("files/" + file.replace(".7z", ".txt")):
                    # extract if needed
                    if Initialize.get_os() != 1:
                        os.system("./7zr" + Initialize.get_os_extension() + " x -aoa -ofiles/ -y files/" + file)
                    else:
                        os.system("7zr" + Initialize.get_os_extension() + " x -aoa -ofiles/ -y files/" + file)
        return True
