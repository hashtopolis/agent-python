import sys
import time
from time import sleep

from htpclient.binarydownload import BinaryDownload
from htpclient.chunk import Chunk
from htpclient.files import Files
from htpclient.generic_cracker import GenericCracker
from htpclient.hashcat_cracker import HashcatCracker
from htpclient.hashlist import Hashlist
from htpclient.helpers import start_uftpd, file_get_contents
from htpclient.initialize import Initialize
from htpclient.jsonRequest import *
from htpclient.dicts import *
import logging

from htpclient.task import Task

CONFIG = None
binaryDownload = None


def run_health_check():
    global CONFIG, binaryDownload
    logging.info("Health check requested by server!")
    logging.info("Retrieving health check settings...")
    query = copy_and_set_token(dict_getHealthCheck, CONFIG.get_value('token'))
    req = JsonRequest(query)
    ans = req.execute()
    if ans is None:
        logging.error("Failed to get health check!")
        sleep(5)
        return
    elif ans['response'] != 'SUCCESS':
        logging.error("Error on getting health check: " + str(ans))
        sleep(5)
        return
    binaryDownload.check_version(ans['crackerBinaryId'])
    check_id = ans['checkId']
    logging.info("Starting check ID " + str(check_id))

    # write hashes to file
    hash_file = open("hashlists/health_check.txt", "w")
    hash_file.write("\n".join(ans['hashes']))
    hash_file.close()

    # delete old file if necessary
    if os.path.exists("hashlists/health_check.out"):
        os.unlink("hashlists/health_check.out")

    # run task
    cracker = HashcatCracker(ans['crackerBinaryId'], binaryDownload)
    start = int(time.time())
    [states, errors] = cracker.run_health_check(ans['attack'], ans['hashlistAlias'])
    end = int(time.time())

    # read results
    if os.path.exists("hashlists/health_check.out"):
        founds = file_get_contents("hashlists/health_check.out").replace("\r\n", "\n").split("\n")
    else:
        founds = []
    num_gpus = len(states[0].get_temps())
    query = copy_and_set_token(dict_sendHealthCheck, CONFIG.get_value('token'))
    query['checkId'] = check_id
    query['start'] = start
    query['end'] = end
    query['numGpus'] = num_gpus
    query['numCracked'] = len(founds) - 1
    query['errors'] = errors
    req = JsonRequest(query)
    ans = req.execute()
    if ans is None:
        logging.error("Failed to send health check results!")
        sleep(5)
        return
    elif ans['response'] != 'OK':
        logging.error("Error on sending health check results: " + str(ans))
        sleep(5)
        return
    logging.info("Health check completed successfully!")


def init():
    global CONFIG, binaryDownload
    log_format = '[%(asctime)s] [%(levelname)-5s] %(message)s'
    print_format = '%(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    log_level = logging.INFO
    logfile = open('client.log', "a", encoding="utf-8")

    logging.getLogger("requests").setLevel(logging.WARNING)

    CONFIG = Config()
    if CONFIG.get_value('debug'):
        log_level = logging.DEBUG
        logging.getLogger("requests").setLevel(logging.DEBUG)
    logging.basicConfig(level=log_level, format=print_format, datefmt=date_format)
    file_handler = logging.StreamHandler(logfile)
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)

    logging.info("Starting client '" + Initialize.get_version() + "'...")

    session = Session(requests.Session()).s
    session.headers.update({'User-Agent': Initialize.get_version()})

    if CONFIG.get_value('proxies'):
        session.proxies = CONFIG.get_value('proxies')

    if CONFIG.get_value('auth-user') and CONFIG.get_value('auth-password'):
        session.auth = (CONFIG.get_value('auth-user'), CONFIG.get_value('auth-password'))

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
        if task.get_task_id() == -1:
            run_health_check()
            task.reset_task()
            continue
        elif task.get_task() is None:
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
            if not cracker.measure_keyspace(task.get_task(), chunk):  # failure case
                task.reset_task()
            continue
        elif chunk_resp == -3:
            run_health_check()
            task.reset_task()
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
        if chunk.chunk_data() is not None and chunk.chunk_data()['length'] == 0:
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
        if len(sys.argv) > 1 and sys.argv[1] == '--version':
            print(Initialize.get_version())
            exit()
        init()
        loop()
    except KeyboardInterrupt:
        logging.info("Exiting...")
        exit()
