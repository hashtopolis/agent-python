import logging
from time import sleep

from htpclient.config import Config
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class Chunk:
    def __init__(self):
        self.config = Config()
        self.chunk = None

    def chunk_data(self):
        return self.chunk

    def get_chunk(self, task_id):
        query = copy_and_set_token(dict_getChunk, self.config.get_value('token'))
        query['taskId'] = task_id
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to get chunk!")
            sleep(5)
            return 0
        elif ans['response'] != 'SUCCESS':
            logging.error("Getting of chunk failed: " + str(ans))
            sleep(5)
            return 0
        else:
            # test what kind the answer is
            if ans['status'] == 'keyspace_required':
                return -1
            elif ans['status'] == 'benchmark':
                return -2
            elif ans['status'] == 'fully_dispatched':
                return 0
            elif ans['status'] == 'health_check':
                return -3
            else:
                self.chunk = ans
                return 1

    def send_keyspace(self, keyspace, task_id):
        query = copy_and_set_token(dict_sendKeyspace, self.config.get_value('token'))
        query['taskId'] = task_id
        query['keyspace'] = int(keyspace)
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to send keyspace!")
            sleep(5)
            return False
        elif ans['response'] != 'SUCCESS':
            logging.error("Sending of keyspace failed: " + str(ans))
            sleep(5)
            return False
        else:
            logging.info("Keyspace got accepted!")
            return True
