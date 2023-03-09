import logging
import time
from time import sleep
from pathlib import Path

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
                file_path = Path(self.config.get_value('files-path'), filename)
                if filename.find("/") != -1 or filename.find("\\") != -1:
                    continue  # ignore invalid file names
                elif os.path.dirname(file_path) != "files":
                    continue  # ignore any case in which we would leave the files folder
                elif os.path.exists(file_path):
                    logging.info("Delete file '" + filename + "' as requested by server...")
                    # When we get the delete requests, this function will check if the <filename>.7z maybe as
                    # an extracted text file. That file will also be deleted.
                    if os.path.splitext(file_path)[1] == '.7z':
                        txt_file = Path(f"{os.path.splitext(file_path)[0]}.txt")
                        if os.path.exists(txt_file):
                            logging.info("Also delete assumed wordlist from archive of same file...")
                            os.unlink(txt_file)
                    os.unlink(file_path)

    def check_files(self, files, task_id):
        for file in files:
            file_localpath = Path(self.config.get_value('files-path'), file)
            txt_file = Path(f"{os.path.splitext(file_localpath)[0]}.txt")
            query = copy_and_set_token(dict_getFile, self.config.get_value('token'))
            query['taskId'] = task_id
            query['file'] = file
            req = JsonRequest(query)
            ans = req.execute()

            # Process request
            if ans is None:
                logging.error("Failed to get file!")
                sleep(5)
                return False
            elif ans['response'] != 'SUCCESS':
                logging.error("Getting of file failed: " + str(ans))
                sleep(5)
                return False
            else:
                # Filesize is OK
                file_size = int(ans['filesize'])
                if os.path.isfile(file_localpath) and os.stat(file_localpath).st_size == file_size:
                    logging.debug("File is present on agent and has matching file size.")
                    continue
                
                # Multicasting configured
                elif self.config.get_value('multicast'):
                    logging.debug("Multicast is enabled, need to wait until it was delivered!")
                    sleep(5)  # in case the file is not there yet (or not completely), we just wait some time and then try again
                    return False
                
                # TODO: we might need a better check for this
                if os.path.isfile(txt_file):
                    continue
                
                # Rsync
                if self.config.get_value('rsync') and Initialize.get_os() != 1:
                    Download.rsync(Path(self.config.get_value('rsync-path'), file), file_localpath) 
                else:
                    logging.debug("Starting download of file from server...")
                    Download.download(self.config.get_value('url').replace("api/server.php", "") + ans['url'], file_localpath)

                # Mismatch filesize
                if os.path.isfile(file_localpath) and os.stat(file_localpath).st_size != file_size:
                    logging.error("file size mismatch on file: %s" % file)
                    sleep(5)
                    return False
                
                # 7z extraction, check if the <filename>.txt does exist.
                if os.path.splitext(file_localpath)[1] == '.7z' and not os.path.isfile(txt_file):
                    # extract if needed
                    files_path = Path(self.config.get_value('files-path'))
                    if Initialize.get_os() == 1:
                        # Windows
                        cmd = f'7zr{Initialize.get_os_extension()} x -aoa -o"{files_path}" -y "{file_localpath}"'
                    else:
                        # Linux
                        cmd = f"./7zr{Initialize.get_os_extension()} x -aoa -o'{files_path}' -y '{file_localpath}'"
                    os.system(cmd)
        return True
