import requests

from htpclient.config import *


class JsonRequest:
    def __init__(self, data):
        self.data = data
        self.config = Config()

    def execute(self):
        try:
            logging.debug(self.data)
            r = requests.post(self.config.get_value('url'), json=self.data)
            if r.status_code != 200:
                logging.error("Status code from server: " + str(r.status_code))
                return None
            logging.debug(r.content)
            return r.json()
        except Exception as e:
            logging.error("Error occurred: " + str(e))
            return None
