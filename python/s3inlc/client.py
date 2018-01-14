import subprocess
from time import sleep

from htpclient.binarydownload import BinaryDownload
from htpclient.chunk import Chunk
from htpclient.files import Files
from htpclient.hashlist import Hashlist
from htpclient.initialize import Initialize
from htpclient.jsonRequest import *
import logging

from htpclient.task import Task

CONFIG = None
binaryDownload = None


def init():
    global CONFIG, binaryDownload

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
    binaryDownload = BinaryDownload()
    binaryDownload.run()


def loop():
    global binaryDownload

    # TODO: this loop is running on the agent
    logging.info("Entering loop...")
    task = Task()
    chunk = Chunk()
    files = Files()
    hashlist = Hashlist()
    while True:
        task.load_task()
        if task.get_task() is None:
            continue
        if not binaryDownload.check_version(task.get_task()['crackerId']):
            continue
        if not files.check_files(task.get_task()['files'], task.get_task()['taskId']):
            continue
        if not hashlist.load_hashlist(task.get_task()['hashlistId']):
            continue
        logging.info("Got cracker binary type " + binaryDownload.get_version()['name'])
        chunkResp = chunk.get_chunk(task.get_task()['taskId'])
        if chunkResp == 0:
            continue
        elif chunkResp == -1:
            # measure keyspace
            output = subprocess.check_output(["crackers/" + str(task.get_task()['crackerId']) + "/" + binaryDownload.get_version()['executable'], '--keyspace' ] + task.get_task()['attackcmd'].replace("#HL# ", "").split(" "))
            output = output.rstrip()
            chunk.send_keyspace(output, task.get_task()['taskId'])
            sleep(10)
            continue
        elif chunkResp == -2:
            # measure benchmark
            sleep(10)
            continue
        # run
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
