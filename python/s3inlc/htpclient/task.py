import logging
from time import sleep

from htpclient.config import Config
from htpclient.jsonRequest import JsonRequest


class Task:
    def __init__(self):
        self.taskId = 0
        self.task = None
        self.config = Config()

    def get_task(self):
        if self.taskId != 0:
            return
        req = JsonRequest({'action': 'getTask', 'token': self.config.get_value('token')})
        ans = req.execute()
        if ans is None:
            logging.error("Failed to get task!")
            sleep(5)
        elif ans['response'] != 'SUCCESS':
            logging.error("Error from server: " + str(ans))
            sleep(5)
        else:
            self.task = ans
            self.taskId = ans['taskId']
            logging.info("Got task with id: " + str(ans['taskId']))
