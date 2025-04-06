import logging

from htpclient.config import Config
from htpclient.session import Session


class JsonRequest:

    def __init__(self, data):
        self.data = data
        self.config = Config()
        self.session = Session().s

    def execute(self, ignore_certificate: bool = True):
        try:
            logging.debug(self.data)
            r = self.session.post(
                self.config.get_value('url'),
                json=self.data,
                timeout=30,
                verify=not ignore_certificate,
                allow_redirects=True)
            if r.status_code != 200:
                logging.error("Status code from server: " + str(r.status_code))
                return None
            logging.debug(r.content)
            return r.json()
        except Exception as e:
            logging.error("Error occurred: " + str(e))
            return None
