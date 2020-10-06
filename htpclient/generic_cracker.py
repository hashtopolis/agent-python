import logging
import subprocess
from time import sleep
from queue import Queue, Empty
from threading import Thread

from htpclient.config import Config
from htpclient.generic_status import GenericStatus
from htpclient.helpers import send_error
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest
from htpclient.dicts import *


class GenericCracker:
    def __init__(self, cracker_id, binary_download):
        self.config = Config()
        self.io_q = Queue()
        self.callPath = "../crackers/" + str(cracker_id) + "/" + binary_download.get_version()['executable']
        self.executable_name = binary_download.get_version()['executable']
        self.keyspace = 0

    def run_chunk(self, task, chunk, preprocessor):
        args = " crack -s " + str(chunk['skip'])
        args += " -l " + str(chunk['length'])
        args += " " + task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.debug("CALL: " + full_cmd)
        process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')

        logging.debug("started cracking")
        out_thread = Thread(target=self.stream_watcher, name='stdout-watcher', args=('OUT', process.stdout))
        err_thread = Thread(target=self.stream_watcher, name='stderr-watcher', args=('ERR', process.stderr))
        out_thread.start()
        err_thread.start()

        main_thread = Thread(target=self.run_loop, name='run_loop', args=(process, chunk, task))
        main_thread.start()

        # wait for all threads to finish
        process.wait()
        out_thread.join()
        err_thread.join()
        logging.info("finished chunk")

    def run_loop(self, process, chunk, task):
        cracks = []
        while True:
            try:
                # Block for 1 second.
                item = self.io_q.get(True, 1)
            except Empty:
                # No output in either streams for a second. Are we done?
                if process.poll() is not None:
                    # is the case when the process is finished
                    break
            else:
                identifier, line = item
                if identifier == 'OUT':
                    status = GenericStatus(line.decode())
                    if status.is_valid():
                        # send update to server
                        progress = status.get_progress()
                        speed = status.get_speed()
                        initial = True
                        while cracks or initial:
                            initial = False
                            cracks_backup = []
                            if len(cracks) > 1000:
                                # we split
                                cnt = 0
                                new_cracks = []
                                for crack in cracks:
                                    cnt += 1
                                    if cnt > 1000:
                                        cracks_backup.append(crack)
                                    else:
                                        new_cracks.append(crack)
                                cracks = new_cracks

                            query = copy_and_set_token(dict_sendProgress, self.config.get_value('token'))
                            query['chunkId'] = chunk['chunkId']
                            query['keyspaceProgress'] = chunk['skip']
                            query['relativeProgress'] = progress
                            query['speed'] = speed
                            query['state'] = (4 if progress == 10000 else 2)
                            query['cracks'] = cracks
                            req = JsonRequest(query)

                            logging.debug("Sending " + str(len(cracks)) + " cracks...")
                            ans = req.execute()
                            if ans is None:
                                logging.error("Failed to send solve!")
                            elif ans['response'] != 'SUCCESS':
                                logging.error("Error from server on solve: " + str(ans))
                            else:
                                if ans['zaps']:
                                    with open("files/zap", "wb") as zapfile:  # need to check if we are in the main dir here
                                        zapfile.write('\n'.join(ans['zaps']).encode())
                                        zapfile.close()
                                cracks = cracks_backup
                                logging.info(
                                    "Progress: " + str(progress / 100) + "% Cracks: " + str(len(cracks)) +
                                    " Accepted: " + str(ans['cracked']) + " Skips: " + str(ans['skipped']) + " Zaps: " + str(len(ans['zaps'])))
                    else:
                        line = line.decode()
                        if ":" in line:
                            cracks.append(line.strip())
                        else:
                            logging.warning("OUT: " + line.strip())
                else:
                    print("ERROR: " + str(line).strip())
                    # TODO: send error and abort cracking

    def measure_keyspace(self, task, chunk):
        task = task.get_task()
        full_cmd = self.callPath + " keyspace " + task['attackcmd'].replace("-a " + task['hashlistAlias'] + " ", "")
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        try:
            logging.debug("CALL: " + full_cmd)
            output = subprocess.check_output(full_cmd, shell=True, cwd='files')
        except subprocess.CalledProcessError as e:
            logging.error("Error during keyspace measurement: " + str(e))
            send_error("Keyspace measure failed!", self.config.get_value('token'), task['taskId'], None)
            sleep(5)
            return False
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        keyspace = "0"
        for line in output:
            if not line:
                continue
            keyspace = line
        self.keyspace = int(keyspace)
        return chunk.send_keyspace(int(keyspace), task['taskId'])

    def run_benchmark(self, task):
        ksp = self.keyspace
        if ksp == 0:
            ksp = task['keyspace']
        args = task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        full_cmd = self.callPath + " crack " + args + " -s 0 -l " + str(ksp) + " --timeout=" + str(task['bench'])
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.debug("CALL: " + full_cmd)
        output = subprocess.check_output(full_cmd, shell=True, cwd='files')
        if output:
            output = output.replace(b"\r\n", b"\n").decode('utf-8')
            output = output.split('\n')
            last_valid_status = None
            for line in output:
                if not line:
                    continue
                status = GenericStatus(line)
                if status.is_valid():
                    last_valid_status = status
            if last_valid_status is None:
                query = copy_and_set_token(dict_clientError, self.config.get_value('token'))
                query['taskId'] = task['taskId']
                query['message'] = "Generic benchmark failed!"
                req = JsonRequest(query)
                req.execute()
                return 0
            return float(last_valid_status.get_progress()) / 10000
        else:
            query = copy_and_set_token(dict_clientError, self.config.get_value('token'))
            query['taskId'] = task['taskId']
            query['message'] = "Generic benchmark gave no output!"
            req = JsonRequest(query)
            req.execute()
        return 0

    def stream_watcher(self, identifier, stream):
        for line in stream:
            self.io_q.put((identifier, line))

        if not stream.closed:
            stream.close()

    def agent_stopped(self):
        return False
