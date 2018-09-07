from time import sleep

from htpclient.binarydownload import BinaryDownload
from htpclient.chunk import Chunk
from htpclient.files import Files
from htpclient.generic_cracker import GenericCracker
from htpclient.hashcat_cracker import HashcatCracker
from htpclient.hashlist import Hashlist
from htpclient.helpers import start_uftpd
from htpclient.initialize import Initialize
from htpclient.jsonRequest import *
from htpclient.dicts import *
import logging

from htpclient.task import Task

CONFIG = None
binaryDownload = None


def init():
    global CONFIG, binaryDownload
    logformat = '[%(asctime)s] [%(levelname)-5s] %(message)s'
    dateformat = '%Y-%m-%d %H:%M:%S'
    logfile = 'client.log'
    loglevel = logging.INFO

    logging.getLogger("requests").setLevel(logging.WARNING)

    CONFIG = Config()
    if CONFIG.get_value('debug'):
        loglevel = logging.DEBUG
        logging.getLogger("requests").setLevel(logging.DEBUG)
    logging.basicConfig(filename=logfile, level=loglevel, format=logformat, datefmt=dateformat)
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Starting client '" + Initialize.get_version() + "'...")

    session = Session(requests.Session()).s
    session.headers.update({'User-Agent': Initialize.get_version()})

    if CONFIG.get_value('proxies'):
        session.proxies = CONFIG.get_value('proxies')

    # connection initialization
    Initialize().run()
    # download and updates
    binaryDownload = BinaryDownload()
    binaryDownload.run()
    if CONFIG.get_value('multicast') and Initialize().get_os() == 0:
        start_uftpd(Initialize().get_os_extension(), CONFIG)


def loop():
    global binaryDownload, CONFIG

    logging.debug("Entering loop...")
    task = Task()
    chunk = Chunk()
    files = Files()
    hashlist = Hashlist()
    task_change = True
    last_task_id = 0
    cracker = None
    while True:
        CONFIG.update()
        files.deletion_check()
        if task.get_task() is not None:
            last_task_id = task.get_task()['taskId']
        task.load_task()
        if task.get_task() is None:
            task_change = True
            continue
        else:
            if task.get_task()['taskId'] is not last_task_id:
                task_change = True
        if not binaryDownload.check_version(task.get_task()['crackerId']):
            task_change = True
            task.reset_task()
            continue
        if task.get_task()['usePrince']:
            binaryDownload.check_prince()
        if not files.check_files(task.get_task()['files'], task.get_task()['taskId']):
            task.reset_task()
            continue
        if task_change and not hashlist.load_hashlist(task.get_task()['hashlistId']):
            task.reset_task()
            continue
        if task_change:
            binaryDownload.check_client_version()
            logging.info("Got cracker binary type " + binaryDownload.get_version()['name'])
            if binaryDownload.get_version()['name'].lower() == 'hashcat':
                cracker = HashcatCracker(task.get_task()['crackerId'], binaryDownload)
            else:
                cracker = GenericCracker(task.get_task()['crackerId'], binaryDownload)
        task_change = False
        chunk_resp = chunk.get_chunk(task.get_task()['taskId'])
        if chunk_resp == 0:
            task.reset_task()
            continue
        elif chunk_resp == -1:
            # measure keyspace
            cracker.measure_keyspace(task.get_task(), chunk)
            continue
        elif chunk_resp == -2:
            # measure benchmark
            logging.info("Benchmark task...")
            result = cracker.run_benchmark(task.get_task())
            if result == 0:
                sleep(10)
                task.reset_task()
                # some error must have occurred on benchmarking
                continue
            # send result of benchmark
            query = copy_and_set_token(dict_sendBenchmark, CONFIG.get_value('token'))
            query['taskId'] = task.get_task()['taskId']
            query['result'] = result
            query['type'] = task.get_task()['benchType']
            req = JsonRequest(query)
            ans = req.execute()
            if ans is None:
                logging.error("Failed to send benchmark!")
                sleep(5)
                task.reset_task()
                continue
            elif ans['response'] != 'SUCCESS':
                logging.error("Error on sending benchmark: " + str(ans))
                sleep(5)
                task.reset_task()
                continue
            else:
                logging.info("Server accepted benchmark!")
                continue

        # check if we have an invalid chunk
        if chunk.chunk_data()['length'] == 0:
            logging.error("Invalid chunk size (0) retrieved! Retrying...")
            task.reset_task()
            continue

        # run chunk
        logging.info("Start chunk...")
        cracker.run_chunk(task.get_task(), chunk.chunk_data())
        if cracker.agent_stopped():
            # if the chunk was aborted by a stop from the server, we need to ask for a task again first
            task.reset_task()
        binaryDownload.check_client_version()


if __name__ == "__main__":
    try:
        init()
        loop()
    except KeyboardInterrupt:
        logging.info("Exiting...")
        exit()
