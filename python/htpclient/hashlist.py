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
        query = copyAndSetToken(dict_getHashlist, self.config.get_value('token'))
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
            Download.download(self.config.get_value('url').replace("api/server.php", "") + ans['url'], "hashlists/" + str(hashlist_id))
            return True
