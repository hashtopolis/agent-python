import logging
import os.path
from pathlib import Path
import stat
import sys
from time import sleep

from htpclient.config import Config
from htpclient.download import Download
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class BinaryDownload:
    def __init__(self, args):
        self.config = Config()
        self.last_version = None
        self.args = args

    def run(self):
        self.check_client_version()
        self.__check_utils()

    def get_version(self):
        return self.last_version

    def check_client_version(self):
        if self.args.disable_update:
            return
        Path("old.zip").unlink(missing_ok=True)  # cleanup old version
        query = copy_and_set_token(dict_checkVersion, self.config.get_value('token'))
        query['version'] = Initialize.get_version_number()
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Agent version check failed!")
        elif ans['response'] != 'SUCCESS':
            logging.error("Error from server: " + str(ans['message']))
        else:
            if ans['version'] == 'OK':
                logging.info("Client is up-to-date!")
            else:
                url = ans['url']
                if not url:
                    logging.warning("Got empty URL for client update!")
                else:
                    logging.info("New client version available!")
                    Path("update.zip").unlink(missing_ok=True)
                    Download.download(url, "update.zip")
                    if os.path.isfile("update.zip") and os.path.getsize("update.zip"):
                        Path("old.zip").unlink(missing_ok=True)
                        Path("hashtopolis.zip").unlink(missing_ok=True)
                        Path("update.zip").rename("hashtopolis.zip")
                        logging.info("Update received, restarting client...")
                        Path("lock.pid").unlink(missing_ok=True)
                        os.execl(sys.executable, sys.executable, "hashtopolis.zip")
                        exit(0)

    def __check_utils(self):
        path = '7zr' + Initialize.get_os_extension()
        if not os.path.isfile(path):
            query = copy_and_set_token(dict_downloadBinary, self.config.get_value('token'))
            query['type'] = '7zr'
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Failed to get 7zr!")
                sleep(5)
                self.__check_utils()
            elif ans['response'] != 'SUCCESS' or not ans['executable']:
                logging.error("Getting 7zr failed: " + str(ans))
                sleep(5)
                self.__check_utils()
            else:
                Download.download(ans['executable'], path)
                os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        path = 'uftpd' + Initialize.get_os_extension()
        if not os.path.isfile(path) and self.config.get_value('multicast'):
            query = copy_and_set_token(dict_downloadBinary, self.config.get_value('token'))
            query['type'] = 'uftpd'
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Failed to get uftpd!")
                sleep(5)
                self.__check_utils()
            elif ans['response'] != 'SUCCESS' or not ans['executable']:
                logging.error("Getting uftpd failed: " + str(ans))
                sleep(5)
                self.__check_utils()
            else:
                Download.download(ans['executable'], path)
                os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    def check_prince(self):
        logging.debug("Checking if PRINCE is present...")
        path = "prince/"
        if os.path.isdir(path):  # if it already exists, we don't need to download it
            logging.debug("PRINCE is already downloaded")
            return True
        logging.debug("PRINCE not found, download...")
        query = copy_and_set_token(dict_downloadBinary, self.config.get_value('token'))
        query['type'] = 'prince'
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to load prince!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS' or not ans['url']:
            logging.error("Getting prince failed: " + str(ans))
            sleep(5)
            return False
        else:
            if not Download.download(ans['url'], "prince.7z"):
                logging.error("Download of prince failed!")
                sleep(5)
                return False
            if Initialize.get_os() == 1:
                os.system("7zr" + Initialize.get_os_extension() + " x -otemp prince.7z")
            else:
                os.system("./7zr" + Initialize.get_os_extension() + " x -otemp prince.7z")
            for name in os.listdir("temp"):  # this part needs to be done because it is compressed with the main subfolder of prince
                if os.path.isdir("temp/" + name):
                    os.rename("temp/" + name, "prince")
                    break
            os.unlink("prince.7z")
            os.rmdir("temp")
            logging.debug("PRINCE downloaded and extracted")
        return True

    def check_preprocessor(self, task):
        logging.debug("Checking if requested preprocessor is present...")
        path = Path(self.config.get_value('preprocessors-path'), str(task.get_task()['preprocessor']))
        query = copy_and_set_token(dict_downloadBinary, self.config.get_value('token'))
        query['type'] = 'preprocessor'
        query['preprocessorId'] = task.get_task()['preprocessor']
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to load preprocessor settings!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS' or not ans['url']:
            logging.error("Getting preprocessor settings failed: " + str(ans))
            sleep(5)
            return False
        else:
            task.set_preprocessor(ans)
            if os.path.isdir(path):  # if it already exists, we don't need to download it
                logging.debug("Preprocessor is already downloaded")
                return True
            logging.debug("Preprocessor not found, download...")
            if not Download.download(ans['url'], "temp.7z"):
                logging.error("Download of preprocessor failed!")
                sleep(5)
                return False
            if Initialize.get_os() == 1:
                os.system(f"7zr{Initialize.get_os_extension()} x -otemp temp.7z")
            else:
                os.system(f"./7zr{Initialize.get_os_extension()} x -otemp temp.7z")
            for name in os.listdir("temp"):  # this part needs to be done because it is compressed with the main subfolder of prince
                if os.path.isdir(Path('temp', name)):
                    os.rename(Path('temp', name), path)
                    break
            os.unlink("temp.7z")
            os.rmdir("temp")
            logging.debug("Preprocessor downloaded and extracted")
        return True

    def check_version(self, cracker_id):
        path = Path(self.config.get_value('crackers-path'), str(cracker_id))
        query = copy_and_set_token(dict_downloadBinary, self.config.get_value('token'))
        query['type'] = 'cracker'
        query['binaryVersionId'] = cracker_id
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to load cracker!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS' or not ans['url']:
            logging.error("Getting cracker failed: " + str(ans))
            sleep(5)
            return False
        else:
            self.last_version = ans
            if not os.path.isdir(path):
                # we need to download the 7zip
                if not Download.download(ans['url'], self.config.get_value('crackers-path') + "/" + str(cracker_id) + ".7z"):
                    logging.error("Download of cracker binary failed!")
                    sleep(5)
                    return False

                # we need to extract the 7zip
                temp_folder = Path(self.config.get_value('crackers-path'), 'temp')
                zip_file = Path(self.config.get_value('crackers-path'), f'{cracker_id}.7z')

                if Initialize.get_os() == 1:
                    # Windows
                    cmd = f'7zr{Initialize.get_os_extension()} x -o"{temp_folder}" "{zip_file}"'
                else:
                    # Linux
                    cmd = f"./7zr{Initialize.get_os_extension()} x -o'{temp_folder}' '{zip_file}'"
                os.system(cmd)

                # Clean up 7zip
                os.unlink(zip_file)

                # Workaround for a 7zip containing a folder name or already the contents of a cracker
                for name in os.listdir(temp_folder):
                    to_check_path = Path(temp_folder, name)
                    if os.path.isdir(to_check_path):
                        os.rename(to_check_path, path)
                    else:
                        os.rename(temp_folder, path)
                        break
        return True
