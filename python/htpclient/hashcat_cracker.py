import string
import logging
import subprocess
from queue import Queue, Empty
from threading import Thread, Lock

import time

from htpclient.config import Config
from htpclient.hashcat_status import HashcatStatus
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest, os
from htpclient.helpers import printSpeed
from htpclient.dicts import *


class HashcatCracker:
    def __init__(self, cracker_id, binary_download):
        self.config = Config()
        self.io_q = Queue()
        self.callPath = "../crackers/" + str(cracker_id) + "/" + binary_download.get_version()['executable']
        self.executable_name = binary_download.get_version()['executable']
        self.lock = Lock()
        self.cracks = []

    def run_chunk(self, task, chunk):
        args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopussy"
        args += " --status-timer " + str(task['statustimer'])
        args += " --outfile-check-timer=" + str(task['statustimer'])
        args += " --outfile-check-dir=../hashlist_" + str(task['hashlistId'])
        args += " -o ../hashlists/" + str(task['hashlistId']) + ".out"
        args += " --remove-timer=" + str(task['statustimer'])
        args += " --separator=" + ":"  # TODO what kind of separator we need?
        args += " -s " + str(chunk['skip'])
        args += " -l " + str(chunk['length'])
        args += " " + task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        # clear old found file
        if os.path.exists("hashlists/" + str(task['hashlistId']) + ".out"):
            os.remove("hashlists/" + str(task['hashlistId']) + ".out")
        logging.debug("CALL: " + full_cmd)
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')

        logging.debug("started cracking")
        out_thread = Thread(target=self.stream_watcher, name='stdout-watcher', args=('OUT', proc.stdout))
        err_thread = Thread(target=self.stream_watcher, name='stderr-watcher', args=('ERR', proc.stderr))
        crk_thread = Thread(target=self.output_watcher, name='crack-watcher',
                            args=("hashlists/" + str(task['hashlistId']) + ".out", proc))
        out_thread.start()
        err_thread.start()
        crk_thread.start()

        main_thread = Thread(target=self.run_loop, name='run_loop', args=(proc, chunk, task))
        main_thread.start()

        # wait for all threads to finish
        proc.wait()
        out_thread.join()
        err_thread.join()
        crk_thread.join()
        logging.info("finished chunk")

    def run_loop(self, proc, chunk, task):
        self.cracks = []
        while True:
            try:
                # Block for 1 second.
                item = self.io_q.get(True, 1)
            except Empty:
                # No output in either streams for a second. Are we done?
                if proc.poll() is not None:
                    # is the case when the process is finished
                    break
            else:
                identifier, line = item
                if identifier == 'OUT':
                    status = HashcatStatus(line.decode())
                    if status.is_valid():
                        # send update to server
                        chunk_start = int(
                            status.get_progress_total() / (chunk['skip'] + chunk['length']) * chunk['skip'])
                        relative_progress = int((status.get_progress() - chunk_start) / float(
                            status.get_progress_total() - chunk_start) * 10000)
                        speed = status.get_speed()
                        initial = True
                        while len(self.cracks) > 0 or initial:
                            self.lock.acquire()
                            initial = False
                            cracks_backup = []
                            if len(self.cracks) > 1000:
                                # we split
                                cnt = 0
                                new_cracks = []
                                for crack in self.cracks:
                                    cnt += 1
                                    if cnt > 1000:
                                        cracks_backup.append(crack)
                                    else:
                                        new_cracks.append(crack)
                                self.cracks = new_cracks
                            query = copyAndSetToken(dict_sendProgress, self.config.get_value('token'))
                            query['chunkId'] = chunk['chunkId']
                            query['keyspaceProgress'] = status.get_curku()
                            query['relativeProgress'] = relative_progress
                            query['speed'] = speed
                            query['state'] = status.get_state()
                            query['cracks'] = self.cracks
                            req = JsonRequest(query)

                            logging.debug("Sending " + str(len(self.cracks)) + " cracks...")
                            ans = req.execute()
                            if ans is None:
                                logging.error("Failed to send solve!")
                            elif ans['response'] != 'SUCCESS':
                                logging.error("Error from server on solve: " + str(ans))
                                proc.kill()  # TODO kill process
                            else:
                                cracks_count = len(self.cracks)
                                self.cracks = cracks_backup
                                zaps = ans['zaps']
                                if len(zaps) > 0:
                                    logging.debug("Writing zaps")
                                    zap_output = '\n'.join(zaps) + '\n'
                                    if not os.path.isdir("hashlist_" + str(task['hashlistId'])):
                                        os.mkdir("hashlist_" + str(task['hashlistId']))
                                    f = open("hashlist_" + str(task['hashlistId']) + "/" + str(time.time()), 'a')
                                    f.write(zap_output)
                                    f.close()
                                logging.info("Progress:" + str(
                                    "{:6.2f}".format(relative_progress / 100)) + "% Speed: " + printSpeed(
                                    speed) + " Cracks: " + str(cracks_count) + " Accepted: " + str(
                                    ans['cracked']) + " Skips: " + str(ans['skipped']) + " Zaps: " + str(len(zaps)))
                            self.lock.release()
                    else:
                        # hacky solution to exclude warnings from hashcat
                        if str(line[0]) not in string.printable:
                            continue
                        else:
                            pass
                            # logging.warning("HCOUT: " + line.strip())
                else:
                    logging.error("HCERR: " + str(line).strip())
                    # TODO: send error and abort cracking

    def measure_keyspace(self, task, chunk):
        full_cmd = self.callPath + " --keyspace --quiet " + task['attackcmd'].replace(task['hashlistAlias'] + " ", "")
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        output = subprocess.check_output(full_cmd, shell=True, cwd='files')
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        keyspace = "0"
        for line in output:
            if len(line) == 0:
                continue
            keyspace = line
        chunk.send_keyspace(int(keyspace), task['taskId'])

    def run_benchmark(self, task):
        args = " --machine-readable --quiet --runtime=" + str(task['bench'])
        args += " --restore-disable --potfile-disable --session=hashtopussy "
        args += task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        args += " -o ../hashlists/" + str(task['hashlistId']) + ".out"
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.debug("CALL: " + full_cmd)
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')
        output, error = proc.communicate()
        logging.debug("started benchmark")
        proc.wait()  # wait until done
        if len(error) > 0:
            # TODO: strip here the ANSI color stuff from the errors
            error = error.replace(b"\r\n", b"\n").decode('utf-8')
            # parse errors and send it to server
            error = error.split('\n')
            for line in error:
                if len(line) == 0:
                    continue
                query = copyAndSetToken(dict_clientError, self.config.get_value('token'))
                query['taskId'] = task['taskId']
                query['message'] = line
                req = JsonRequest(query)
                req.execute()
            return 0
        if len(output) > 0:
            output = output.replace(b"\r\n", b"\n").decode('utf-8')
            output = output.split('\n')
            last_valid_status = None
            for line in output:
                if len(line) == 0:
                    continue
                logging.debug("HCSTAT: " + line.strip())
                status = HashcatStatus(line)
                if status.is_valid():
                    last_valid_status = status
            if last_valid_status is None:
                return 0
            return (last_valid_status.get_progress() - last_valid_status.get_rejected()) / float(
                last_valid_status.get_progress_total())
        return 0

    def stream_watcher(self, identifier, stream):
        for line in stream:
            self.io_q.put((identifier, line))

        if not stream.closed:
            stream.close()

    def output_watcher(self, file_path, proc):
        while not os.path.exists(file_path):
            time.sleep(1)
            if proc.poll() is not None:
                return
        file = open(file_path)
        while 1:
            where = file.tell()
            line = file.readline()
            if not line:
                if proc.poll() is None:
                    time.sleep(1)
                    file.seek(where)
                else:
                    break
            else:
                self.lock.acquire()
                self.cracks.append(line.strip())
                self.lock.release()
        file.close()
