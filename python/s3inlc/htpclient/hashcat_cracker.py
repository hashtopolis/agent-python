import logging
import subprocess

from htpclient.config import Config
from htpclient.hashcat_status import HashcatStatus
from htpclient.jsonRequest import JsonRequest


class HashcatCracker:
    def __init__(self, crackerId, binaryDownload):
        self.config = Config()
        self.callPath = "../crackers/" + str(crackerId) + "/" + binaryDownload.get_version()['executable']

    def run_chunk(self, task, chunk):
        args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopussy"
        args += " --status-timer " + str(task['statustimer'])
        args += " --outfile-check-timer=" + str(task['statustimer'])
        args += " --remove-timer=" + str(task['statustimer'])
        args += " --separator=" + ":" # TODO what kind of separator we need?
        args += " -s " + str(chunk['skip'])
        args += " -l " + str(chunk['length'])
        args += " " + task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        logging.info("CALL: " + self.callPath + args)
        proc = subprocess.Popen(self.callPath + args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')
        output, error = proc.communicate()
        logging.info("started cracking")

    def run_benchmark(self, task):
        args = " --machine-readable --quiet --runtime=" + str(task['bench']) + " --restore-disable --potfile-disable --session=hashtopussy "
        args += task['attackcmd'].replace(task['hashlistAlias'], "../hashlists/" + str(task['hashlistId']))
        logging.info("CALL: " + self.callPath + args)
        proc = subprocess.Popen(self.callPath + args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='files')
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
                req = JsonRequest({'action': 'clientError', 'taskId': task['taskId'], 'token': self.config.get_value('token'), 'message': line})
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
            return last_valid_status.get_progress()/float(last_valid_status.get_progress_total())
        return 0
