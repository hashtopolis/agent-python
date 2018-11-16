import logging
from time import sleep

from htpclient.config import Config
from htpclient.download import Download
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class Hashlist:
    def __init__(self):
        self.config = Config()
        self.chunk = None

    def load_hashlist(self, hashlist_id):
        query = copy_and_set_token(dict_getHashlist, self.config.get_value('token'))
        query['hashlistId'] = hashlist_id
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to get hashlist!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS':
            logging.error("Getting of hashlist failed: " + str(ans))
            sleep(5)
            return False
        else:
            Download.download(self.config.get_value('url').replace("api/server.php", "") + ans['url'], "hashlists/" + str(hashlist_id), True)
            return True

    def load_found(self, hashlist_id, cracker_id):
        query = copy_and_set_token(dict_getFound, self.config.get_value('token'))
        query['hashlistId'] = hashlist_id
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to get found of hashlist!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS':
            logging.error("Getting of hashlist founds failed: " + str(ans))
            sleep(5)
            return False
        else:
            logging.info("Saving found hashes to hashcat potfile...")
            Download.download(self.config.get_value('url').replace("api/server.php", "") + ans['url'], "crackers/" + str(cracker_id) + "/hashcat.potfile", True)
            return True
