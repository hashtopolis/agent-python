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
from htpclient.helpers import send_error, update_files, kill_hashcat, get_bit, print_speed, get_rules_and_hl, get_wordlist, escape_ansi
from htpclient.dicts import *


class HashcatCracker:
    def __init__(self, cracker_id, binary_download):
        self.config = Config()
        self.io_q = Queue()
        self.executable_name = binary_download.get_version()['executable']
        k = self.executable_name.rfind(".")
        self.executable_name = self.executable_name[:k] + get_bit() + "." + self.executable_name[k + 1:]
        self.cracker_path = "crackers/" + str(cracker_id) + "/"
        self.callPath = self.executable_name
        if Initialize.get_os() != 1:
            self.callPath = "./" + self.callPath
        self.lock = Lock()
        self.cracks = []
        self.first_status = False
        self.usePipe = False
        self.progressVal = 0
        self.statusCount = 0
        self.last_update = 0
        self.wasStopped = False

    def build_command(self, task, chunk):
        args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopolis"
        args += " --status-timer " + str(task['statustimer'])
        args += " --outfile-check-timer=" + str(task['statustimer'])
        args += " --outfile-check-dir=../../hashlist_" + str(task['hashlistId'])
        args += " -o ../../hashlists/" + str(task['hashlistId']) + ".out"
        args += " --remove-timer=" + str(task['statustimer'])
        args += " -s " + str(chunk['skip'])
        args += " -l " + str(chunk['length'])
        args += " " + update_files(task['attackcmd']).replace(task['hashlistAlias'], "../../hashlists/" + str(task['hashlistId'])) + " " + task['cmdpars']
        return self.callPath + args

    def build_pipe_command(self, task, chunk):
        # call the command with piping
        pre_args = " --stdout -s " + str(chunk['skip']) + " -l " + str(chunk['length'])
        pre_args += update_files(task['attackcmd']).replace(task['hashlistAlias'], '')
        post_args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopolis"
        post_args += " --status-timer " + str(task['statustimer'])
        post_args += " --outfile-check-timer=" + str(task['statustimer'])
        post_args += " --outfile-check-dir=../../hashlist_" + str(task['hashlistId'])
        post_args += " -o ../../hashlists/" + str(task['hashlistId']) + ".out"
        post_args += " --remove-timer=" + str(task['statustimer'])
        post_args += " ../../hashlists/" + str(task['hashlistId'])
        return self.callPath + pre_args + " | " + self.callPath + post_args + task['cmdpars']

    def build_prince_command(self, task, chunk):
        binary = "..\..\prince\pp64."
        if Initialize.get_os() != 1:
            binary = "./" + binary + "bin"
        else:
            binary += "exe"
        pre_args = " -s " + str(chunk['skip']) + " -l " + str(chunk['length']) + ' '
        pre_args += get_wordlist(update_files(task['attackcmd'])).replace(task['hashlistAlias'], '')
        post_args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopolis"
        post_args += " --status-timer " + str(task['statustimer'])
        post_args += " --outfile-check-timer=" + str(task['statustimer'])
        post_args += " --outfile-check-dir=../../hashlist_" + str(task['hashlistId'])
        post_args += " -o ../../hashlists/" + str(task['hashlistId']) + ".out"
        post_args += " --remove-timer=" + str(task['statustimer'])
        post_args += " ../../hashlists/" + str(task['hashlistId'])
        post_args += get_rules_and_hl(update_files(task['attackcmd']), task['hashlistAlias']).replace(task['hashlistAlias'], '')
        return binary + pre_args + " | " + self.callPath + post_args + task['cmdpars']

    def run_chunk(self, task, chunk):
        if task['usePrince']:
            full_cmd = self.build_prince_command(task, chunk)
        elif self.usePipe:
            full_cmd = self.build_pipe_command(task, chunk)
        else:
            full_cmd = self.build_command(task, chunk)
        self.statusCount = 0
        self.wasStopped = False
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        # clear old found file
        if os.path.exists("hashlists/" + str(task['hashlistId']) + ".out"):
            os.remove("hashlists/" + str(task['hashlistId']) + ".out")
        # create zap folder
        if not os.path.exists("hashlist_" + str(task['hashlistId'])):
            os.mkdir("hashlist_" + str(task['hashlistId']))
        logging.debug("CALL: " + full_cmd)
        if Initialize.get_os() != 1:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cracker_path, preexec_fn=os.setsid)
        else:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cracker_path)

        logging.debug("started cracking")
        out_thread = Thread(target=self.stream_watcher, name='stdout-watcher', args=('OUT', process.stdout))
        err_thread = Thread(target=self.stream_watcher, name='stderr-watcher', args=('ERR', process.stderr))
        crk_thread = Thread(target=self.output_watcher, name='crack-watcher', args=("hashlists/" + str(task['hashlistId']) + ".out", process))
        out_thread.start()
        err_thread.start()
        crk_thread.start()
        self.first_status = False
        self.last_update = time.time()

        main_thread = Thread(target=self.run_loop, name='run_loop', args=(process, chunk, task))
        main_thread.start()

        # wait for all threads to finish
        process.wait()
        crk_thread.join()
        out_thread.join()
        err_thread.join()
        main_thread.join()
        logging.info("finished chunk")

    def run_loop(self, proc, chunk, task):
        self.cracks = []
        piping_threshold = 95
        enable_piping = True
        if self.config.get_value('piping-threshold'):
            piping_threshold = self.config.get_value('piping-threshold')
        if self.config.get_value('allow-piping'):
            enable_piping = self.config.get_value('allow-piping')
        while True:
            try:
                # Block for 1 second.
                if not self.first_status and self.last_update < time.time() - 5:
                    # send update
                    query = copy_and_set_token(dict_sendProgress, self.config.get_value('token'))
                    query['chunkId'] = chunk['chunkId']
                    query['keyspaceProgress'] = chunk['skip']
                    query['relativeProgress'] = 0
                    query['speed'] = 0
                    query['state'] = 2
                    query['cracks'] = []
                    req = JsonRequest(query)
                    logging.info("Sending keepalive progress to avoid timeout...")
                    req.execute()
                    self.last_update = time.time()
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
                        self.statusCount += 1

                        # test if we have a low utility
                        if not self.usePipe and enable_piping and task['files'] and not task['usePrince'] and 1 < self.statusCount < 10 and status.get_util() != -1 and status.get_util() < piping_threshold:
                            # we need to try piping -> kill the process and then wait for issuing the chunk again
                            self.usePipe = True
                            chunk_start = int(status.get_progress_total() / (chunk['skip'] + chunk['length']) * chunk['skip'])
                            self.progressVal = status.get_progress_total() - chunk_start
                            logging.info("Detected low UTIL value, restart chunk with piping...")
                            try:
                                kill_hashcat(proc.pid, Initialize.get_os())
                            except ProcessLookupError:
                                pass
                            return

                        self.first_status = True
                        # send update to server
                        logging.debug(line.decode().replace('\n', '').replace('\r', ''))
                        total = status.get_progress_total()
                        if self.usePipe:
                            total = self.progressVal
                        chunk_start = int(status.get_progress_total() / (chunk['skip'] + chunk['length']) * chunk['skip'])
                        if total > 0:
                            relative_progress = int((status.get_progress() - chunk_start) / float(total - chunk_start) * 10000)
                        else:
                            relative_progress = 0
                        speed = status.get_speed()
                        initial = True
                        if status.get_state() == 5:
                            time.sleep(1)  # we wait for a second so all output is loaded from file
                            # reset piping stuff when a chunk is successfully finished
                            self.progressVal = 0
                            self.usePipe = False
                        while self.cracks or initial:
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
                            query = copy_and_set_token(dict_sendProgress, self.config.get_value('token'))
                            query['chunkId'] = chunk['chunkId']
                            query['keyspaceProgress'] = status.get_curku()
                            if (self.usePipe or task['usePrince']) and status.get_curku() == 0:
                                query['keyspaceProgress'] = chunk['skip']
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
                                try:
                                    kill_hashcat(proc.pid, Initialize.get_os())
                                except ProcessLookupError:
                                    pass
                                return
                            elif 'agent' in ans.keys() and ans['agent'] == 'stop':
                                # server set agent to stop
                                self.wasStopped = True
                                logging.info("Received stop order from server!")
                                try:
                                    kill_hashcat(proc.pid, Initialize.get_os())
                                except ProcessLookupError:
                                    pass
                                return
                            else:
                                cracks_count = len(self.cracks)
                                self.cracks = cracks_backup
                                zaps = ans['zaps']
                                if zaps:
                                    logging.debug("Writing zaps")
                                    zap_output = ":FF\n".join(zaps) + ':FF\n'
                                    f = open("hashlist_" + str(task['hashlistId']) + "/" + str(time.time()), 'a')
                                    f.write(zap_output)
                                    f.close()
                                logging.info("Progress:" + str(
                                    "{:6.2f}".format(relative_progress / 100)) + "% Speed: " + print_speed(
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
                    msg = escape_ansi(line.replace(b"\r\n", b"\n").decode('utf-8')).strip()
                    if msg:
                        logging.error("HC error: " + msg)
                        send_error(msg, self.config.get_value('token'), task['taskId'])

    def measure_keyspace(self, task, chunk):
        if task['usePrince']:
            self.prince_keyspace(task, chunk)
            return
        full_cmd = self.callPath + " --keyspace --quiet " + update_files(task['attackcmd']).replace(task['hashlistAlias'] + " ", "") + ' ' + task['cmdpars']
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        try:
            output = subprocess.check_output(full_cmd, shell=True, cwd=self.cracker_path)
        except subprocess.CalledProcessError:
            logging.error("Error during keyspace measure")
            send_error("Keyspace measure failed!", self.config.get_value('token'), task['taskId'])
            return
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        keyspace = "0"
        for line in output:
            if not line:
                continue
            keyspace = line
        chunk.send_keyspace(int(keyspace), task['taskId'])

    def prince_keyspace(self, task, chunk):
        binary = "pp64."
        if Initialize.get_os() != 1:
            binary = "./" + binary + "bin"
        else:
            binary += "exe"
        full_cmd = binary + " --keyspace " + get_wordlist(update_files(task['attackcmd'], True)).replace(task['hashlistAlias'], "")
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        try:
            logging.debug("CALL: " + full_cmd)
            output = subprocess.check_output(full_cmd, shell=True, cwd="prince")
        except subprocess.CalledProcessError:
            logging.error("Error during PRINCE keyspace measure")
            send_error("PRINCE keyspace measure failed!", self.config.get_value('token'), task['taskId'])
            return
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        keyspace = "0"
        for line in output:
            if not line:
                continue
            keyspace = line
        if int(keyspace) > 9000000000000000000:  # max size of a long long int
            chunk.send_keyspace(-1, task['taskId'])
        else:
            chunk.send_keyspace(int(keyspace), task['taskId'])

    def run_benchmark(self, task):
        if task['benchType'] == 'speed':
            # do a speed benchmark
            return self.run_speed_benchmark(task)

        args = " --machine-readable --quiet --runtime=" + str(task['bench'])
        args += " --restore-disable --potfile-disable --session=hashtopolis "
        args += update_files(task['attackcmd']).replace(task['hashlistAlias'], "../../hashlists/" + str(task['hashlistId'])) + ' ' + task['cmdpars']
        args += " -o ../../hashlists/" + str(task['hashlistId']) + ".out"
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.debug("CALL: " + full_cmd)
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cracker_path)
        output, error = proc.communicate()
        logging.debug("started benchmark")
        proc.wait()  # wait until done
        if error:
            error = escape_ansi(error.replace(b"\r\n", b"\n").decode('utf-8'))
            # parse errors and send it to server
            error = error.split('\n')
            for line in error:
                if not line:
                    continue
                query = copy_and_set_token(dict_clientError, self.config.get_value('token'))
                query['taskId'] = task['taskId']
                query['message'] = line
                req = JsonRequest(query)
                req.execute()
            # return 0  it might not be ideal to return here.  In case of errors still try to read the benchmark.
        if output:
            output = output.replace(b"\r\n", b"\n").decode('utf-8')
            output = output.split('\n')
            last_valid_status = None
            for line in output:
                if not line:
                    continue
                logging.debug("HCSTAT: " + line.strip())
                status = HashcatStatus(line)
                if status.is_valid():
                    last_valid_status = status
            if last_valid_status is None:
                return 0
            return (last_valid_status.get_progress() - last_valid_status.get_rejected()) / float(last_valid_status.get_progress_total())
        return 0

    def stream_watcher(self, identifier, stream):
        for line in stream:
            self.io_q.put((identifier, line))

        if not stream.closed:
            stream.close()

    def run_speed_benchmark(self, task):
        args = " --machine-readable --quiet --progress-only"
        args += " --restore-disable --potfile-disable --session=hashtopolis "
        if task['usePrince']:
            args += get_rules_and_hl(update_files(task['attackcmd']), task['hashlistAlias']).replace(task['hashlistAlias'], "../../hashlists/" + str(task['hashlistId'])) + ' '
            args += " example.dict" + ' ' + task['cmdpars']
        else:
            args += update_files(task['attackcmd']).replace(task['hashlistAlias'], "../../hashlists/" + str(task['hashlistId'])) + ' ' + task['cmdpars']
        args += " -o ../../hashlists/" + str(task['hashlistId']) + ".out"
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        try:
            logging.debug("CALL: " + full_cmd)
            output = subprocess.check_output(full_cmd, shell=True, cwd=self.cracker_path)
        except subprocess.CalledProcessError as e:
            logging.error("Error during keyspace measure, return code: " + str(e.returncode))
            send_error("Keyspace measure failed!", self.config.get_value('token'), task['taskId'])
            return 0
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        benchmark_sum = [0, 0]
        for line in output:
            if not line:
                continue
            line = line.split(":")
            if len(line) != 3:
                continue
            benchmark_sum[0] += int(line[1])
            benchmark_sum[1] += float(line[2])
        return str(benchmark_sum[0]) + ":" + str(benchmark_sum[1])

    def output_watcher(self, file_path, process):
        while not os.path.exists(file_path):
            time.sleep(1)
            if process.poll() is not None:
                return
        file_handle = open(file_path)
        end_count = 0
        while 1:
            where = file_handle.tell()
            line = file_handle.readline()
            if not line:
                if process.poll() is None:
                    time.sleep(0.05)
                    file_handle.seek(where)
                else:
                    time.sleep(0.05)
                    end_count += 1
                    if end_count > 20:
                        break
            else:
                self.lock.acquire()
                self.cracks.append(line.strip())
                self.lock.release()
        file_handle.close()

    def agent_stopped(self):
        return self.wasStopped
