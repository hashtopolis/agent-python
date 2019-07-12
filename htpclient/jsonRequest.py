import logging

from htpclient.config import *
from htpclient.session import *


class JsonRequest:
    def __init__(self, data):
        self.data = data
        self.config = Config()
        self.session = Session().s

    def execute(self):
        try:
            logging.debug(self.data)
            r = self.session.post(self.config.get_value('url'), json=self.data, timeout=30)
            if r.status_code != 200:
                logging.error("Status code from server: " + str(r.status_code))
                return None
            logging.debug(r.content)
            return r.json()
        except Exception as e:
            logging.error("Error occurred: " + str(e))
            return None
