import logging
import subprocess
from queue import Queue, Empty
from threading import Thread

from htpclient.config import Config
from htpclient.hashcat_status import HashcatStatus
from htpclient.initialize import Initialize
from htpclient.jsonRequest import JsonRequest


class HashcatCracker:
    def __init__(self, cracker_id, binary_download):
        self.config = Config()
        self.io_q = Queue()
        self.callPath = "../crackers/" + str(cracker_id) + "/" + binary_download.get_version()['executable']
        self.executable_name = binary_download.get_version()['executable']

    def run_chunk(self, task, chunk):
        args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopussy"
        args += " --status-timer " + str(task['statustimer'])
        args += " --outfile-check-timer=" + str(task['statustimer'])
        args += " --outfile-check-dir=hashlist_" + str(task['hashlistId'])
        args += " --remove-timer=" + str(task['statustimer'])
        args += " --separator=" + ":"  # TODO what kind of separator we need?
        args += " -s " + str(chunk['skip'])
        args += " -l " + str(chunk['length'])
        args += " " + task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.info("CALL: " + full_cmd)
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')

        logging.info("started cracking")
        out_thread = Thread(target=self.stream_watcher, name='stdout-watcher', args=('OUT', proc.stdout))
        err_thread = Thread(target=self.stream_watcher, name='stderr-watcher', args=('ERR', proc.stderr))
        out_thread.start()
        err_thread.start()

        main_thread = Thread(target=self.run_loop, name='run_loop', args=(proc, chunk, task))
        main_thread.start()

        # wait for all threads to finish
        proc.wait()
        out_thread.join()
        err_thread.join()
        logging.info("finished chunk")

    def run_loop(self, proc, chunk, task):
        cracks = []
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
                        chunk_start = int(status.get_progress_total()) / (chunk['skip'] + chunk['length']) * chunk[
                            'skip']
                        relative_progress = int((status.get_progress() - chunk_start) / float(
                            status.get_progress_total() - chunk_start) * 10000)
                        speed = status.get_speed()
                        while len(cracks) > 0:
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
                            req = JsonRequest({'action': 'sendProgress', 'token': self.config.get_value('token'),
                                               'chunkId': chunk['chunkId'], 'keyspaceProgress': status.get_curku(),
                                               'relativeProgress': relative_progress, 'speed': speed,
                                               'state': status.get_state(), 'cracks': cracks})

                            logging.info("Sending " + str(len(cracks)) + " cracks...")
                            ans = req.execute()
                            if ans is None:
                                logging.error("Failed to send solve!")
                            elif ans['response'] != 'SUCCESS':
                                logging.error("Error from server on solve: " + str(ans))
                            else:
                                cracks = cracks_backup
                                zaps = ans['zaps']
                                if len(zaps) > 0:
                                    logging.info("Writing zaps")
                                    zap_output = '\n'.join(zaps)
                                    f = open("hashlist_" + str(task['hashlistId']), 'a')
                                    f.write(zap_output)
                                    f.close()
                                logging.info("Update accepted. Cracks: " + str(ans['cracked']) + " Skips: " + str(
                                    ans['skipped']) + " Zaps: " + str(len(zaps)))
                    else:
                        line = line.decode()
                        if ":" in line and "Line-length exception" not in line:
                            cracks.append(line.strip())
                        else:
                            logging.warning("HCOUT: " + line)
                else:
                    print("HCERR: " + str(line))
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
        args = " --machine-readable --quiet --runtime=" + str(
            task['bench']) + " --restore-disable --potfile-disable --session=hashtopussy "
        args += task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        full_cmd = self.callPath + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.info("CALL: " + full_cmd)
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')
        output, error = proc.communicate()
        logging.info("started benchmark")
        proc.wait()  # wait until done
        if len(error) > 0:
            # TODO: strip here the ANSI color stuff from the errors
            error = error.replace(b"\r\n", b"\n").decode('utf-8')
            # parse errors and send it to server
            error = error.split('\n')
            for line in error:
                if len(line) == 0:
                    continue
                req = JsonRequest(
                    {'action': 'clientError', 'taskId': task['taskId'], 'token': self.config.get_value('token'),
                     'message': line})
                req.execute()
            return 0
        if len(output) > 0:
            output = output.replace(b"\r\n", b"\n").decode('utf-8')
            output = output.split('\n')
            last_valid_status = None
            for line in output:
                if len(line) == 0:
                    continue
                logging.info("HCSTAT: " + line)
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
