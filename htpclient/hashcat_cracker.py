import string
import logging
import subprocess
import psutil
from pathlib import Path
from time import sleep
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
        self.version_string = ""

        # Build cracker executable name by taking basename plus extension
        self.executable_name = binary_download.get_version()['executable']
        k = self.executable_name.rfind(".")
        self.executable_name = self.executable_name[:k] + "." + self.executable_name[k + 1:]
        self.cracker_path = Path(self.config.get_value('crackers-path'), str(cracker_id))

        self.executable_path = Path(self.cracker_path, self.executable_name)
        if not os.path.isfile(self.executable_path):  # in case it's not the new hashcat filename, try the old one (hashcat<bit>.<ext>)
            self.executable_name = binary_download.get_version()['executable']
            k = self.executable_name.rfind(".")
            self.executable_name = self.executable_name[:k] + get_bit() + "." + self.executable_name[k + 1:]

        if Initialize.get_os() == 1:
            # Windows
            self.callPath = f'"{self.executable_name}"'
        else:
            # Linux / Mac
            self.callPath = f"'./{self.executable_name}'"

        cmd = [str(self.executable_path), "--version"]
        
        try:
            logging.debug(f"CALL: {' '.join(cmd)}")
            output = subprocess.check_output(cmd, cwd=self.cracker_path)
        except subprocess.CalledProcessError as e:
            logging.error("Error during version detection: " + str(e))
            sleep(5)
        self.version_string = output.decode().replace('v', '')

        self.lock = Lock()
        self.cracks = []
        self.first_status = False
        self.usePipe = False
        self.progressVal = 0
        self.statusCount = 0
        self.last_update = 0
        self.uses_slow_hash_flag = False
        self.wasStopped = False

    def get_outfile_format(self):
        if self.version_string.find('-') == -1:
            release = self.version_string.split('.')
            try:
                if int(str(release[0])) >= 6:
                    return "1,2,3,4"
            except ValueError:
                return "1,2,3,4"  # if there is a custom version, we assume it's using the new format
            return "15" # if we cannot determine the version or if the release is older than 6.0.0, we will use the old format
        split = self.version_string.split('-')
        if len(split) < 2:
            return "15" # something is wrong with the version string, go for old format
        release = str(split[0]).split('.')
        commit = str(split[1])
        if int(str(release[0])) < 5:
            return "15"
        elif int(str(release[0])) == 5 and int(str(release[1])) < 1:
            return "15"
        elif int(str(release[0])) == 5 and int(str(release[1])) == 1 and int(str(release[2])) == 0 and int(commit) < 1618:
            return "15"
        return "1,2,3,4" # new outfile format

    def build_command(self, task, chunk):
        args = []

        zaps_file = Path(self.config.get_value('zaps-path'), f"hashlist_{task['hashlistId']}")
        output_file = Path(self.config.get_value('hashlists-path'), f"{task['hashlistId']}.out")
        hashlist_file = Path(self.config.get_value('hashlists-path'), str(task['hashlistId']))
        args.append('--machine-readable')
        args.append('--quiet')
        args.append('--status')
        args.append('--restore-disable')
        args.append('--session=hashtopolis')
        args.append(f"--status-timer {task['statustimer']}")
        args.append(f"--outfile-check-timer={task['statustimer']}")
        args.append(f'--outfile-check-dir="{zaps_file}"')
        args.append(f'-o "{output_file}"')
        args.append(f'--outfile-format={self.get_outfile_format()}')
        args.append('-p "\t"')
        args.append(f"-s {chunk['skip']}")
        args.append(f"-l {chunk['length']}")
        
        if 'useBrain' in task and task['useBrain']:  # when using brain we set the according parameters
            args.append('--brain-client')
            args.append(f"--brain-host {task['brainHost']}")
            args.append(f"--brain-port {task['brainPort']}")
            args.append(f"--brain-password {task['brainPass']}")
            
            if 'brainFeatures' in task:
                args.append(f"--brain-client-features {task['brainFeatures']}")
        else:  # remove should only be used if we run without brain
            args.append('--potfile-disable')
            args.append('--remove')
            args.append(f"--remove-timer={task['statustimer']}")
        
        files = update_files(task['attackcmd'])
        files = files.replace(task['hashlistAlias'], f'"{hashlist_file}"')
        args.append(files)
        args.append(task['cmdpars'])

        
        
        full_cmd = ' '.join(args)
        full_cmd = f'{self.callPath} {full_cmd}'

        if ' -S ' in full_cmd:
            self.uses_slow_hash_flag = True

        return full_cmd

    def build_pipe_command(self, task, chunk):
        # call the command with piping
        pre_args = " --stdout -s " + str(chunk['skip']) + " -l " + str(chunk['length']) + ' '
        pre_args += update_files(task['attackcmd']).replace(task['hashlistAlias'], '')
        post_args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopolis"
        post_args += " --status-timer " + str(task['statustimer'])
        post_args += " --outfile-check-timer=" + str(task['statustimer'])
        post_args += " --outfile-check-dir='" + self.config.get_value('zaps-path') + "/hashlist_" + str(task['hashlistId']) + "'"
        post_args += " -o '" + self.config.get_value('hashlists-path') + "/" + str(task['hashlistId']) + ".out' --outfile-format=" + self.get_outfile_format() + " -p \"" + str(chr(9)) + "\""
        post_args += " --remove-timer=" + str(task['statustimer'])
        post_args += " '" + self.config.get_value('hashlists-path') + "/" + str(task['hashlistId']) + "'"
        return f"'{self.callPath}'" + pre_args + " | " + f"'{self.callPath}'" + post_args + task['cmdpars']

    # DEPRECATED
    def build_prince_command(self, task, chunk):
        binary = "../../prince/pp64."
        if Initialize.get_os() != 1:
            binary = "./" + binary + "bin"
        else:
            binary += "exe"
        pre_args = " -s " + str(chunk['skip']) + " -l " + str(chunk['length']) + ' '
        pre_args += get_wordlist(update_files(task['attackcmd']).replace(task['hashlistAlias'], ''))
        post_args = " --machine-readable --quiet --status --remove --restore-disable --potfile-disable --session=hashtopolis"
        post_args += " --status-timer " + str(task['statustimer'])
        post_args += " --outfile-check-timer=" + str(task['statustimer'])
        post_args += " --outfile-check-dir=../../hashlist_" + str(task['hashlistId'])
        post_args += " -o ../../hashlists/" + str(task['hashlistId']) + ".out --outfile-format=" + self.get_outfile_format() + " -p \"" + str(chr(9)) + "\""
        post_args += " --remove-timer=" + str(task['statustimer'])
        post_args += " ../../hashlists/" + str(task['hashlistId'])
        post_args += get_rules_and_hl(update_files(task['attackcmd']), task['hashlistAlias']).replace(task['hashlistAlias'], '')
        return binary + pre_args + " | " + self.callPath + post_args + task['cmdpars']

    def build_preprocessor_command(self, task, chunk, preprocessor):
        binary_path = Path(self.config.get_value('preprocessors-path'), str(task['preprocessor']))
        binary = preprocessor['executable']

        if not os.path.isfile(binary_path / binary):
            split = binary.split(".")
            binary = '.'.join(split[:-1]) + get_bit() + "." + split[-1]
        binary = binary_path / binary

        pre_args = []

        # in case the skip or limit command are not available, we try to achieve the same with head/tail (the more chunks are run, the more inefficient it might be)
        if preprocessor['skipCommand'] is not None and preprocessor['limitCommand'] is not None:
            pre_args.extend([preprocessor['skipCommand'], str(chunk['skip'])])
            pre_args.extend([preprocessor['limitCommand'], str(chunk['length'])])

        pre_args.append(update_files(task['preprocessorCommand']))

        # TODO: add support for windows as well (pre-built tools)
        if preprocessor['skipCommand'] is None or preprocessor['limitCommand'] is None:
            skip_length = chunk['skip'] + chunk['length']
            pre_args.append(f"| head -n {skip_length}")
            pre_args.append(f"| tail -n {chunk['length']}")
        
        zaps_file = Path(self.config.get_value('zaps-path'), f"hashlist_{task['hashlistId']}")
        output_file = Path(self.config.get_value('hashlists-path'), f"{task['hashlistId']}.out")
        hashlist_file = Path(self.config.get_value('hashlists-path'), str(task['hashlistId']))

        post_args = []
        post_args.append('--machine-readable')
        post_args.append('--quiet')
        post_args.append('--status')
        post_args.append('--remove')
        post_args.append('--restore-disable')
        post_args.append('--potfile-disable')
        post_args.append('--session=hashtopolis')
        post_args.append(f"--status-timer {task['statustimer']}")

        post_args.append(f"--outfile-check-timer={task['statustimer']}")
        post_args.append(f'--outfile-check-dir="{zaps_file}"')
        post_args.append(f'-o "{output_file}"')
        post_args.append(f'--outfile-format={self.get_outfile_format()}')
        post_args.append('-p "\t"')
        post_args.append(f"--remove-timer={task['statustimer']}")
        post_args.append(f'"{hashlist_file}"')

        files = update_files(task['attackcmd'])
        files = files.replace(task['hashlistAlias'] + " ", "")
        post_args.append(files)
        post_args.append(task['cmdpars'])

        pre_args = ' '.join(pre_args)
        post_args = ' '.join(post_args)

        full_cmd = f'"{binary}" {pre_args} | {self.callPath} {post_args}'

        return full_cmd

    def run_chunk(self, task, chunk, preprocessor):
        if 'enforcePipe' in task and task['enforcePipe']:
            logging.info("Enforcing pipe command because of task setting...")
            self.usePipe = True
        if 'usePrince' in task and task['usePrince']:  # DEPRECATED
            full_cmd = self.build_prince_command(task, chunk)
        elif 'usePreprocessor' in task and task['usePreprocessor']:
            full_cmd = self.build_preprocessor_command(task, chunk, preprocessor)
        elif self.usePipe:
            full_cmd = self.build_pipe_command(task, chunk)
        else:
            full_cmd = self.build_command(task, chunk)
        self.statusCount = 0
        self.wasStopped = False
        
        # Set paths
        outfile_path = Path(self.config.get_value('hashlists-path'), f"{task['hashlistId']}.out")
        outfile_backup_path = Path(self.config.get_value('hashlists-path'), f"{task['hashlistId']}_{time.time()}.out")
        zapfile_path = Path(self.config.get_value('zaps-path'), f"hashlist_{task['hashlistId']}")
        
        # clear old found file - earlier we deleted them, but just in case, we just move it to a unique filename if configured so
        if os.path.exists(outfile_path):
            if self.config.get_value('outfile-history'):
                os.rename(outfile_path, outfile_backup_path)
            else:
                os.unlink(outfile_path)
    
        # create zap folder
        if not os.path.exists(zapfile_path):
            os.mkdir(zapfile_path)
        
        # Call command
        logging.debug("CALL: " + full_cmd)
        if Initialize.get_os() != 1:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cracker_path, preexec_fn=os.setsid)
        else:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cracker_path)

        logging.debug("started cracking")
        out_thread = Thread(target=self.stream_watcher, name='stdout-watcher', args=('OUT', process.stdout))
        err_thread = Thread(target=self.stream_watcher, name='stderr-watcher', args=('ERR', process.stderr))
        crk_thread = Thread(target=self.output_watcher, name='crack-watcher', args=(outfile_path, process))
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
        zap_path = Path(self.config.get_value('zaps-path'), f"hashlist_{task['hashlistId']}")

        self.cracks = []
        piping_threshold = 95
        enable_piping = False
        if self.config.get_value('piping-threshold'):
            piping_threshold = self.config.get_value('piping-threshold')
        if self.config.get_value('allow-piping') != '':
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
                        # not allowed if brain is used
                        if enable_piping and not self.uses_slow_hash_flag and ('useBrain' not in task or not task['useBrain']) and 'slowHash' in task and task['slowHash'] and not self.usePipe:
                            if task['files'] and not ('usePrince' in task and task['usePrince']) and not ('usePreprocessor' in task and task['usePreprocessor']) and 1 < self.statusCount < 10 and status.get_util() != -1 and status.get_util() < piping_threshold:
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
                        if self.usePipe:  # if we are piping, we might have saved the total progress before switching to piping, so we can use this
                            total = self.progressVal
                        # we need to calculate the chunk start, because progress does not start at 0 for a chunk
                        chunk_start = int(status.get_progress_total() / (chunk['skip'] + chunk['length']) * chunk['skip'])
                        if total > 0:
                            relative_progress = int((status.get_progress() - chunk_start) / float(total - chunk_start) * 10000)
                        else:  # this is the case when we cannot say anything about the progress
                            relative_progress = 0
                        speed = status.get_speed()
                        initial = True
                        if status.get_state() == 4 or status.get_state() == 5:
                            time.sleep(5)  # we wait five seconds so all output is loaded from file
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
                            if (self.usePipe or 'usePrince' in task and task['usePrince'] or 'usePreprocessor' in task and task['usePreprocessor']) and status.get_curku() == 0:
                                query['keyspaceProgress'] = chunk['skip']
                            query['relativeProgress'] = relative_progress
                            query['speed'] = speed
                            query['state'] = status.get_state()
                            # crack format: hash[:salt]:plain:hex_plain:crack_pos (separator will be tab instead of :)
                            prepared = []
                            for crack in self.cracks:
                                prepared.append(crack.split("\t"))
                            query['cracks'] = prepared
                            if status.get_temps():
                                query['gpuTemp'] = status.get_temps()
                            if status.get_all_util():
                                query['gpuUtil'] = status.get_all_util()
                            query['cpuUtil'] = [round(psutil.cpu_percent(), 1)]
                            req = JsonRequest(query)

                            logging.debug("Sending " + str(len(self.cracks)) + " cracks...")
                            ans = req.execute()
                            if ans is None:
                                logging.error("Failed to send solve!")
                                sleep(1)
                            elif ans['response'] != 'SUCCESS':
                                self.wasStopped = True
                                logging.error("Error from server on solve: " + str(ans))
                                try:
                                    kill_hashcat(proc.pid, Initialize.get_os())
                                except ProcessLookupError:
                                    pass
                                sleep(5)
                                return
                            elif 'agent' in ans.keys() and ans['agent'] == 'stop':
                                # server set agent to stop
                                self.wasStopped = True
                                logging.info("Received stop order from server!")
                                try:
                                    kill_hashcat(proc.pid, Initialize.get_os())
                                except ProcessLookupError:
                                    pass
                                sleep(5)
                                return
                            else:
                                cracks_count = len(self.cracks)
                                self.cracks = cracks_backup
                                zaps = ans['zaps']
                                if zaps:
                                    logging.debug("Writing zaps")
                                    zap_output = "\tFF\n".join(zaps) + '\tFF\n'
                                    f = open(Path(zap_path) / str(time.time()), 'a')
                                    f.write(zap_output)
                                    f.close()
                                logging.info("Progress:" + str("{:6.2f}".format(relative_progress / 100)) + "% Speed: " + print_speed(speed) + " Cracks: " + str(cracks_count) + " Accepted: " + str(ans['cracked']) + " Skips: " + str(ans['skipped']) + " Zaps: " + str(len(zaps)))
                            self.lock.release()
                    else:
                        # hacky solution to exclude warnings from hashcat
                        if str(line[0]) not in string.printable:
                            continue
                        else:
                            pass  # logging.warning("HCOUT: " + line.strip())
                elif identifier == 'ERR':
                    msg = escape_ansi(line.replace(b"\r\n", b"\n").decode('utf-8')).strip()
                    if msg and str(msg) != '^C':  # this is maybe not the fanciest way, but as ctrl+c is sent to the underlying process it reports it to stderr
                        logging.error("HC error: " + msg)
                        send_error(msg, self.config.get_value('token'), task['taskId'], chunk['chunkId'])
                        sleep(0.1)  # we set a minimal sleep to avoid overreaction of the client sending a huge number of errors, but it should not be slowed down too much, in case the errors are not critical and the agent can continue

    def measure_keyspace(self, task, chunk):
        if 'usePrince' in task.get_task() and task.get_task()['usePrince']:
            return self.prince_keyspace(task.get_task(), chunk)
        elif 'usePreprocessor' in task.get_task() and task.get_task()['usePreprocessor']:
            return self.preprocessor_keyspace(task, chunk)
        task = task.get_task()  # TODO: refactor this to be better code
        files = update_files(task['attackcmd'])
        files = files.replace(task['hashlistAlias'] + " ", "")
               
        full_cmd = f"{self.callPath} --keyspace --quiet {files} {task['cmdpars']}"
        
        if 'useBrain' in task and task['useBrain']:
            full_cmd = f"{full_cmd} -S"

        output = b''
        try:
            logging.debug(f"CALL: {full_cmd}")
            output = subprocess.check_output(full_cmd, shell=True, cwd=self.cracker_path, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error("Error during keyspace measure: " + str(e) + " Output: " + output.decode(encoding='utf-8'))
            send_error("Keyspace measure failed!", self.config.get_value('token'), task['taskId'], None)
            sleep(5)
            return False
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        ks = 0
        # try to parse each line as a keyspace result integer (normally only one line should be in output, but some warnings might show up)
        for line in output:
            if not line:
                continue
            try:
                ks = int(line)
            except ValueError:
                pass
        return chunk.send_keyspace(ks, task['taskId'])

    # DEPRECATED
    def prince_keyspace(self, task, chunk):
        binary = "pp64."
        if Initialize.get_os() != 1:
            binary = "./" + binary + "bin"
        else:
            binary += "exe"
        full_cmd = binary + " --keyspace " + get_wordlist(update_files(task['attackcmd'], True).replace(task['hashlistAlias'], ""))
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        try:
            logging.debug("CALL: " + full_cmd)
            output = subprocess.check_output(full_cmd, shell=True, cwd="prince")
        except subprocess.CalledProcessError:
            logging.error("Error during PRINCE keyspace measure")
            send_error("PRINCE keyspace measure failed!", self.config.get_value('token'), task['taskId'], None)
            sleep(5)
            return False
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        keyspace = "0"
        for line in output:
            if not line:
                continue
            keyspace = line
        # as the keyspace of prince can get very very large, we only save it in case it's small enough to fit in a long,
        # otherwise we assume that the user will abort the task earlier anyway
        if int(keyspace) > 9000000000000000000:  # close to max size of a long long int
            return chunk.send_keyspace(-1, task['taskId'])
        return chunk.send_keyspace(int(keyspace), task['taskId'])

    def preprocessor_keyspace(self, task, chunk):
        preprocessor = task.get_preprocessor()
        preprocessors_path = self.config.get_value('preprocessors-path')
        if preprocessor['keyspaceCommand'] is None:  # in case there is no keyspace flag, we just assume the task will be that large to run forever
          return chunk.send_keyspace(-1, task.get_task()['taskId'])

        binary = preprocessor['executable']
        if not os.path.isfile(binary):
            split = binary.split(".")
            binary = '.'.join(split[:-1]) + get_bit() + "." + split[-1]
        
        if Initialize.get_os() == 1:
            # Windows
            binary = f'"{binary}"'
        else:
            # Mac / Linux
            binary = f'"./{binary}"'
        
        args = []
        args.append(preprocessor['keyspaceCommand'])
        args.append(update_files(task.get_task()['preprocessorCommand']))

        full_cmd = ' '.join(args)
        full_cmd = f"{binary} {full_cmd}"

        try:
            logging.debug("CALL: " + full_cmd)
            output = subprocess.check_output(full_cmd, shell=True, cwd=Path(preprocessors_path, str(task.get_task()['preprocessor'])))
        except subprocess.CalledProcessError:
            logging.error("Error during preprocessor keyspace measure")
            send_error("Preprocessor keyspace measure failed!", self.config.get_value('token'), task.get_task()['taskId'], None)
            sleep(5)
            return False
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        keyspace = "0"
        for line in output:
            if not line:
                continue
            keyspace = line
        # as the keyspace of preprocessors can get very very large, we only save it in case it's small enough to fit in a long,
        # otherwise we assume that the user will abort the task earlier anyway
        if int(keyspace) > 9000000000000000000:  # close to max size of a long long int
            return chunk.send_keyspace(-1, task.get_task()['taskId'])
        return chunk.send_keyspace(int(keyspace), task.get_task()['taskId'])

    def run_benchmark(self, task):
        if task['benchType'] == 'speed':
            # do a speed benchmark
            return self.run_speed_benchmark(task)
        args = []
        args.append('--machine-readable')
        args.append('--quiet')
        args.append(f"--runtime={task['bench']}")
        
        args.append('--restore-disable')
        args.append('--potfile-disable')
        args.append('--session=hashtopolis')
        args.append('-p')
        args.append('"\t"')
        
        
      
        hashlist_path = Path(self.config.get_value('hashlists-path'), str(task['hashlistId']))
        hashlist_out_path = Path(self.config.get_value('hashlists-path'), f"{str(task['hashlistId'])}.out")

        files = update_files(task['attackcmd'])
        files = files.replace(task['hashlistAlias'], f'"{hashlist_path}"')

        args.append(files)
        args.append(task['cmdpars'])
        args.append('-o')
        args.append(f'"{hashlist_out_path}"')

        full_cmd = ' '.join(args)

        full_cmd = f"{self.callPath} {full_cmd}"
      
        logging.debug(f"CALL: {full_cmd}")
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
            # we just calculate how far in the task the agent went during the benchmark time
            return (last_valid_status.get_progress() - last_valid_status.get_rejected()) / float(last_valid_status.get_progress_total())
        return 0

    def stream_watcher(self, identifier, stream):
        for line in stream:
            self.io_q.put((identifier, line))
        if not stream.closed:
            stream.close()

    def run_speed_benchmark(self, task):
        args = []
        args.append('--machine-readable')
        args.append('--quiet')
        args.append('--progress-only')
        
        args.append('--restore-disable')
        args.append('--potfile-disable')
        args.append('--session=hashtopolis')
        args.append('-p')
        args.append('"\t"')
        
        hashlist_path = Path(self.config.get_value('hashlists-path'), str(task['hashlistId']))
        hashlist_out_path = Path(self.config.get_value('hashlists-path'), f"{str(task['hashlistId'])}.out")

        if 'usePrince' in task and task['usePrince']:
            attackcmd = get_rules_and_hl(update_files(task['attackcmd']))
            # Replace #HL# with the real hashlist
            attackcmd = attackcmd.replace(task['hashlistAlias'], f'"{hashlist_path}"')
            
            args.append(attackcmd)

            # This dict is purely used for benchmarking with prince
            args.append('example.dict')
            args.append(task['cmdpars'])
        else:
            attackcmd = update_files(task['attackcmd'])

            # Replace #HL# with the real hashlist
            attackcmd = attackcmd.replace(task['hashlistAlias'], f'"{hashlist_path}"')

            args.append(attackcmd)
            args.append(task['cmdpars'])
        if 'usePreprocessor' in task and task['usePreprocessor']:
            args.append('example.dict')
        if 'useBrain' in task and task['useBrain']:
            args.append('-S')

        args.append('-o')
        args.append(f'"{hashlist_out_path}"')
        
        full_cmd = ' '.join(args)
        full_cmd = f"{self.callPath} {full_cmd}"

        output = b''
        try:
            logging.debug(f"CALL: {''.join(full_cmd)}")
            output = subprocess.check_output(full_cmd, shell=True, cwd=self.cracker_path, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error("Error during speed benchmark, return code: " + str(e.returncode) + " Output: " + output.decode(encoding='utf-8'))
            send_error("Speed benchmark failed!", self.config.get_value('token'), task['taskId'], None)
            return 0
        output = output.decode(encoding='utf-8').replace("\r\n", "\n").split("\n")
        benchmark_sum = [0, 0]
        for line in output:
            if not line:
                continue
            line = line.split(":")
            if len(line) != 3:
                continue
            # we need to do a weighted sum of all the time outputs of the GPUs
            try:
                benchmark_sum[0] += int(line[1])
                benchmark_sum[1] += float(line[2])*int(line[1])
            except ValueError:
                continue
        if benchmark_sum[0] == 0:
            return 0  # in this case some error happened on the benchmark
        return str(benchmark_sum[0]) + ":" + str(float(benchmark_sum[1]) / benchmark_sum[0])

    def output_watcher(self, file_path, process):
        while not os.path.exists(file_path):
            if process.poll() is not None:
                return
            time.sleep(1)
        file_handle = open(file_path, encoding="utf-8")
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

    def run_health_check(self, attack, hashlist_alias):
        args = " --machine-readable --quiet"
        args += " --restore-disable --potfile-disable --session=health "
        args += update_files(attack).replace(hashlist_alias, "'" + self.config.get_value('hashlists-path') + "/health_check.txt'")
        args += " -o '" + self.config.get_value('hashlists-path') + "/health_check.out'"
        full_cmd = f"'{self.callPath}'" + args
        if Initialize.get_os() == 1:
            full_cmd = full_cmd.replace("/", '\\')
        logging.debug(f"CALL: {''.join(full_cmd)}")
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cracker_path)
        output, error = proc.communicate()
        logging.debug("Started health check attack")
        # wait until done, on the health check we don't send any update during running. Maybe later we could at least
        # introduce some heartbeat update to make visible that the agent is still alive.
        proc.wait()
        errors = []
        states = []
        if error:
            error = escape_ansi(error.replace(b"\r\n", b"\n").decode('utf-8'))
            error = error.split('\n')
            for line in error:
                if not line:
                    continue
                errors.append(line)
        if output:
            output = escape_ansi(output.replace(b"\r\n", b"\n").decode('utf-8'))
            output = output.split('\n')
            for line in output:
                if not line:
                    continue
                logging.debug(line)
                status = HashcatStatus(line)
                if status.is_valid():
                    states.append(status)
        return [states, errors]
