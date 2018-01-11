from time import sleep

from htpclient.binary_download import Binary_Download
from htpclient.initialize import Initialize
from htpclient.jsonRequest import *
import logging

CONFIG = None


def init():
    global CONFIG

    # TODO: fix logging style
    logging.basicConfig(filename='client.log', level=logging.DEBUG)
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.ERROR)
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    CONFIG = Config()
    # connection initialization
    Initialize().run()
    # download and updates
    Binary_Download().run()


def loop():
    # TODO: this loop is running on the agent
    logging.info("Entering loop...")
    while True:
        sleep(10)
        # Request Task
        # - Load cracker if needed
        # - Load Files
        # - Load Hashlist
        # - Request Chunk
        #   - Do Keyspace
        #   - Do Benchmark
        # - As long as there is no error, request more chunks


if __name__ == "__main__":
    init()
    loop()
