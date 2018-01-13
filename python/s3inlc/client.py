from time import sleep

from htpclient.binarydownload import BinaryDownload
from htpclient.initialize import Initialize
from htpclient.jsonRequest import *
import logging

from htpclient.task import Task

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
    BinaryDownload().run()


def loop():
    # TODO: this loop is running on the agent
    logging.info("Entering loop...")
    task = Task()
    while True:
        task.get_task()
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
