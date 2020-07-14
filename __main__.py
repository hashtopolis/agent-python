import glob
import shutil
import signal
import sys
import time
from time import sleep

import psutil as psutil
import argparse

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
    if len(states) > 0:
        num_gpus = len(states[0].get_temps())
    else:
        errors.append("Faild to retrieve one successful cracker state, most likely due to failing.")
        num_gpus = 0
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


# Sets up the logging to stdout and to file with different styles and with the level as set in the config if available
def init_logging(args):
    global CONFIG

    log_format = '[%(asctime)s] [%(levelname)-5s] %(message)s'
    print_format = '%(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    log_level = logging.INFO
    logfile = open('client.log', "a", encoding="utf-8")

    logging.getLogger("requests").setLevel(logging.WARNING)

    CONFIG = Config()
    if args.debug:
        CONFIG.set_value('debug', True)
    if CONFIG.get_value('debug'):
        log_level = logging.DEBUG
        logging.getLogger("requests").setLevel(logging.DEBUG)
    logging.basicConfig(level=log_level, format=print_format, datefmt=date_format)
    file_handler = logging.StreamHandler(logfile)
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)


def init(args):
    global CONFIG, binaryDownload

    logging.info("Starting client '" + Initialize.get_version() + "'...")

    # check if there are running hashcat.pid files around (as we assume that nothing is running anymore if the client gets newly started)
    if os.path.exists("crackers"):
        for root, dirs, files in os.walk("crackers"):
            for folder in dirs:
                if folder.isdigit() and os.path.exists("crackers/" + folder + "/hashtopolis.pid"):
                    logging.info("Cleaning hashcat PID file from crackers/" + folder)
                    os.unlink("crackers/" + folder + "/hashtopolis.pid")

    session = Session(requests.Session()).s
    session.headers.update({'User-Agent': Initialize.get_version()})

    if CONFIG.get_value('proxies'):
        session.proxies = CONFIG.get_value('proxies')

    if CONFIG.get_value('auth-user') and CONFIG.get_value('auth-password'):
        session.auth = (CONFIG.get_value('auth-user'), CONFIG.get_value('auth-password'))

    # connection initialization
    Initialize().run(args)
    # download and updates
    binaryDownload = BinaryDownload(args)
    binaryDownload.run()

    # if multicast is set to run, we need to start the daemon
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
        files.deletion_check()  # check if there are deletion orders from the server
        if task.get_task() is not None:
            last_task_id = task.get_task()['taskId']
        task.load_task()
        if task.get_task_id() == -1:  # get task returned to run a health check
            run_health_check()
            task.reset_task()
            continue
        elif task.get_task() is None:
            task_change = True
            continue
        else:
            if task.get_task()['taskId'] is not last_task_id:
                task_change = True
        # try to download the needed cracker (if not already present)
        if not binaryDownload.check_version(task.get_task()['crackerId']):
            task_change = True
            task.reset_task()
            continue
        # if prince is used, make sure it's downloaded (deprecated, as preprocessors are integrated generally now)
        if 'usePrince' in task.get_task() and task.get_task()['usePrince']:
            if not binaryDownload.check_prince():
                continue
        # if preprocessor is used, make sure it's downloaded
        if 'usePreprocessor' in task.get_task() and task.get_task()['usePreprocessor']:
            if not binaryDownload.check_preprocessor(task):
                continue
        # check if all required files are present
        if not files.check_files(task.get_task()['files'], task.get_task()['taskId']):
            task.reset_task()
            continue
        # download the hashlist for the task
        if task_change and not hashlist.load_hashlist(task.get_task()['hashlistId']):
            task.reset_task()
            continue
        if task_change:  # check if the client version is up-to-date and load the appropriate cracker
            binaryDownload.check_client_version()
            logging.info("Got cracker binary type " + binaryDownload.get_version()['name'])
            if binaryDownload.get_version()['name'].lower() == 'hashcat':
                cracker = HashcatCracker(task.get_task()['crackerId'], binaryDownload)
            else:
                cracker = GenericCracker(task.get_task()['crackerId'], binaryDownload)
        # if it's a task using hashcat brain, we need to load the found hashes
        if task_change and 'useBrain' in task.get_task() and task.get_task()['useBrain'] and not hashlist.load_found(task.get_task()['hashlistId'], task.get_task()['crackerId']):
            task.reset_task()
            continue
        task_change = False
        chunk_resp = chunk.get_chunk(task.get_task()['taskId'])
        if chunk_resp == 0:
            task.reset_task()
            continue
        elif chunk_resp == -1:
            # measure keyspace
            if not cracker.measure_keyspace(task, chunk):  # failure case
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
        cracker.run_chunk(task.get_task(), chunk.chunk_data(), task.get_preprocessor())
        if cracker.agent_stopped():
            # if the chunk was aborted by a stop from the server, we need to ask for a task again first
            task.reset_task()
            task_change = True
        binaryDownload.check_client_version()


def de_register():
    global CONFIG

    logging.info("De-registering client..")
    query = copy_and_set_token(dict_deregister, CONFIG.get_value('token'))
    req = JsonRequest(query)
    ans = req.execute()
    if ans is None:
        logging.error("De-registration failed!")
    elif ans['response'] != 'SUCCESS':
        logging.error("Error on de-registration: " + str(ans))
    else:
        logging.info("Successfully de-registered!")
        # cleanup
        dirs = ['crackers', 'prince', 'hashlists', 'files']
        files = ['config.json', '7zr.exe', '7zr']
        for file in files:
            if os.path.exists(file):
                os.unlink(file)
        for directory in dirs:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        r = glob.glob('hashlist_*')
        for i in r:
            shutil.rmtree(i)
        logging.info("Cleanup finished!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hashtopolis Client v' + Initialize.get_version_number(), prog='python3 hashtopolis.zip')
    parser.add_argument('--de-register', action='store_true', help='client should automatically de-register from server now')
    parser.add_argument('--version', action='store_true', help='show version information')
    parser.add_argument('--number-only', action='store_true', help='when using --version show only the number')
    parser.add_argument('--disable-update', action='store_true', help='disable retrieving auto-updates of the client from the server')
    parser.add_argument('--debug', '-d', action='store_true', help='enforce debugging output')
    parser.add_argument('--voucher', type=str, required=False, help='voucher to use to automatically register')
    parser.add_argument('--url', type=str, required=False, help='URL to Hashtopolis client API')
    parser.add_argument('--cert', type=str, required=False, help='Client TLS cert bundle for Hashtopolis client API')
    args = parser.parse_args()

    if args.version:
        if args.number_only:
            print(Initialize.get_version_number())
        else:
            print(Initialize.get_version())
        sys.exit(0)

    if args.de_register:
        init_logging(args)
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})
        de_register()
        sys.exit(0)

    try:
        init_logging(args)

        # check if there is a lock file and check if this pid is still running hashtopolis
        if os.path.exists("lock.pid") and os.path.isfile("lock.pid"):
            pid = file_get_contents("lock.pid")
            logging.info("Found existing lock.pid, checking if python process is running...")
            if psutil.pid_exists(int(pid)):
                try:
                    command = psutil.Process(int(pid)).cmdline()[0].replace('\\', '/').split('/')
                    print(command)
                    if str.startswith(command[-1], "python"):
                        logging.fatal("There is already a hashtopolis agent running in this directory!")
                        sys.exit(-1)
                except Exception:
                    # if we fail to determine the cmd line we assume that it's either not running anymore or another process (non-hashtopolis)
                    pass
            logging.info("Ignoring lock.pid file because PID is not existent anymore or not running python!")

        # create lock file
        with open("lock.pid", 'w') as f:
            f.write(str(os.getpid()))
            f.close()

        init(args)
        loop()
    except KeyboardInterrupt:
        logging.info("Exiting...")
        # if lock file exists, remove
        if os.path.exists("lock.pid"):
            os.unlink("lock.pid")
        sys.exit()
