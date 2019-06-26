import logging
from time import sleep

from htpclient.config import Config
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class Task:
    def __init__(self):
        self.taskId = 0
        self.task = None
        self.config = Config()
        self.preprocessor = None

    def reset_task(self):
        self.task = None
        self.taskId = 0

    def load_task(self):
        if self.taskId != 0:
            return
        self.task = None
        query = copy_and_set_token(dict_getTask, self.config.get_value('token'))
        req = JsonRequest(query)
        ans = req.execute()
        if ans is None:
            logging.error("Failed to get task!")
            sleep(5)
        elif ans['response'] != 'SUCCESS':
            logging.error("Error from server: " + str(ans))
            sleep(5)
        else:
            if ans['taskId'] is None:
                logging.info("No task available!")
                sleep(5)
                return
            elif ans['taskId'] == -1:
                self.taskId = -1
                return
            self.task = ans
            self.taskId = ans['taskId']
            logging.info("Got task with id: " + str(ans['taskId']))

    def get_task(self):
        return self.task

    def get_task_id(self):
        return self.taskId

    def set_preprocessor(self, settings):
        self.preprocessor = settings
        
    def get_preprocessor(self):
        return self.preprocessor
