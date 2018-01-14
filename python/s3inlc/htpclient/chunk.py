import logging
from time import sleep

from htpclient.config import Config
from htpclient.jsonRequest import JsonRequest


class Chunk:
    def __init__(self):
        self.config = Config()
        self.chunk = None

    def get_chunk(self, taskId):
        req = JsonRequest({'action':'getChunk', 'token': self.config.get_value('token'), 'taskId': taskId})
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
            elif ans['status'] == 'benchmark_required':
                return -2
            else:
                return 1

    def send_keyspace(self, keyspace, task_id):
        req = JsonRequest({'action':'sendKeyspace', 'token': self.config.get_value('token'), 'taskId': task_id, 'keyspace': int(keyspace)})
        ans = req.execute()
        if ans is None:
            logging.error("Failed to send keyspace!")
            sleep(5)
            return 0
        elif ans['response'] != 'SUCCESS':
            logging.error("Sending of keyspace failed: " + str(ans))
            sleep(5)
            return 0
        else:
            logging.info("Keyspace got accepted!")
