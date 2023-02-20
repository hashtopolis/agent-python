import pytest
from unittest import mock
import unittest
from unittest.mock import MagicMock
import os
import subprocess
import shutil
import requests
import json
from pathlib import Path
from argparse import Namespace
import sys

from htpclient.hashcat_cracker import HashcatCracker
from htpclient.binarydownload import BinaryDownload
from htpclient.session import Session
from htpclient.config import Config
from htpclient.initialize import Initialize
from htpclient.chunk import Chunk
from htpclient.hashlist import Hashlist
from htpclient.task import Task
from htpclient.dicts import copy_and_set_token
from htpclient.dicts import dict_sendBenchmark
from htpclient.jsonRequest import JsonRequest

from tests.hashtopolis import Hashlist as Hashlist_v2
from tests.hashtopolis import Task as Task_v2

# The default cmdparameters, some objects need those. Maybe move to a common helper so other tests can include this aswell.
# test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://example.com/api/server.php', version=False, voucher='devvoucher', zaps_path=None)

class HashcatCrackerTestLinux(unittest.TestCase):
    @mock.patch('subprocess.Popen', side_effect=subprocess.Popen)
    @mock.patch('subprocess.check_output', side_effect=subprocess.check_output)
    @mock.patch('os.unlink', side_effect=os.unlink)
    @mock.patch('os.system', side_effect=os.system)
    def test_correct_flow(self, mock_system, mock_unlink, mock_check_output, mock_Popen):
        if sys.platform != 'linux':
            return
        # Clean up cracker folder
        if os.path.exists('crackers/1'):
            shutil.rmtree('crackers/1')

        #TODO: Delete tasks / hashlist to ensure clean
        #TODO: Verify setup agent

        # Setup session object
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})

        # Create hashlist
        p = Path(__file__).parent.joinpath('create_hashlist_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        hashlist_v2 = Hashlist_v2(**payload)
        hashlist_v2.save()

        # Create Task
        for p in sorted(Path(__file__).parent.glob('create_task_001.json')):
            payload = json.loads(p.read_text('UTF-8'))
            payload['hashlistId'] = int(hashlist_v2._id)
            obj = Task_v2(**payload)
            obj.save()

        # Cmd parameters setup
        test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://hashtopolis/api/server.php', version=False, voucher='devvoucher', zaps_path=None)

        # Try to download cracker 1
        cracker_id = 1
        config = Config()
        crackers_path = config.get_value('crackers-path')

        binaryDownload = BinaryDownload(test_args)
        binaryDownload.check_version(cracker_id)
        
        cracker_zip = Path(crackers_path, f'{cracker_id}.7z')
        crackers_temp = Path(crackers_path, 'temp')
        zip_binary = './7zr'
        mock_unlink.assert_called_with(str(cracker_zip))

        mock_system.assert_called_with(f"{zip_binary} x -o'{crackers_temp}' '{cracker_zip}'")

        # --version
        cracker = HashcatCracker(1, binaryDownload)
        mock_check_output.assert_called_with("'./hashcat.bin' --version", shell=True, cwd=f"{Path(crackers_path, str(cracker_id))}/")

        # --keyspace
        chunk = Chunk()
        task = Task()
        task.load_task()
        hashlist = Hashlist()

        hashlist.load_hashlist(task.get_task()['hashlistId'])
        hashlist_id = task.get_task()['hashlistId']
        hashlists_path = config.get_value('hashlists-path')

        cracker.measure_keyspace(task, chunk)
        mock_check_output.assert_called_with(
            "'./hashcat.bin' --keyspace --quiet  -a3 ?l?l?l?l   --hash-type=0 ",
            shell=True,
            cwd=f"{Path(crackers_path, str(cracker_id))}/",
            stderr=-2
        )

        # benchmark
        result = cracker.run_benchmark(task.get_task())
        assert result != 0
        mock_check_output.assert_called_with(
            f"'./hashcat.bin' --machine-readable --quiet --progress-only --restore-disable --potfile-disable --session=hashtopolis -p \"\t\"  '{Path(hashlists_path, str(hashlist_id))}'  -a3 ?l?l?l?l  --hash-type=0  -o '{Path(hashlists_path, str(hashlist_id))}.out'",
            shell=True,
            cwd=f"{Path(crackers_path, str(cracker_id))}/",
            stderr=-2
        )

        # Sending benchmark to server
        query = copy_and_set_token(dict_sendBenchmark, config.get_value('token'))
        query['taskId'] = task.get_task()['taskId']
        query['result'] = result
        query['type'] = task.get_task()['benchType']
        req = JsonRequest(query)
        req.execute()

        # cracking
        chunk.get_chunk(task.get_task()['taskId'])
        cracker.run_chunk(task.get_task(), chunk.chunk_data(), task.get_preprocessor())
        zaps_path = config.get_value('zaps-path')
        zaps_dir = f"hashlist_{hashlist_id}"
        skip = str(chunk.chunk_data()['skip'])
        limit = str(chunk.chunk_data()['length'])
        mock_Popen.assert_called_with(
            f"./hashcat.bin --machine-readable --quiet --status --restore-disable --session=hashtopolis --status-timer 5 --outfile-check-timer=5 --outfile-check-dir='{Path(zaps_path, zaps_dir)}' -o '{Path(hashlists_path, str(hashlist_id))}.out' --outfile-format=1,2,3,4 -p \"\t\" -s {skip} -l {limit} --potfile-disable --remove --remove-timer=5  '{Path(hashlists_path, str(hashlist_id))}'  -a3 ?l?l?l?l  --hash-type=0 ",
            shell=True,
            stdout=-1,
            stderr=-1,
            cwd=f"{Path(crackers_path, str(cracker_id))}/",
            preexec_fn=mock.ANY
        )

        # Cleanup
        obj.delete()
        hashlist_v2.delete()

class HashcatCrackerTestWindows(unittest.TestCase):
    @mock.patch('subprocess.Popen', side_effect=subprocess.Popen)
    @mock.patch('subprocess.check_output', side_effect=subprocess.check_output)
    @mock.patch('os.unlink', side_effect=os.unlink)
    @mock.patch('os.system', side_effect=os.system)
    def test_correct_flow(self, mock_system, mock_unlink, mock_check_output, mock_Popen):
        if sys.platform != 'win32':
            return

        # Clean up cracker folder
        if os.path.exists('crackers/1'):
            shutil.rmtree('crackers/1')

        #TODO: Delete tasks / hashlist to ensure clean
        #TODO: Verify setup agent

        # Setup session object
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})

        # Create hashlist
        p = Path(__file__).parent.joinpath('create_hashlist_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        hashlist_v2 = Hashlist_v2(**payload)
        hashlist_v2.save()

        # Create Task
        for p in sorted(Path(__file__).parent.glob('create_task_001.json')):
            payload = json.loads(p.read_text('UTF-8'))
            payload['hashlistId'] = int(hashlist_v2._id)
            obj = Task_v2(**payload)
            obj.save()

        # Cmd parameters setup
        test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://hashtopolis/api/server.php', version=False, voucher='devvoucher', zaps_path=None)

        # Try to download cracker 1
        cracker_id = 1
        config = Config()
        crackers_path = config.get_value('crackers-path')

        binaryDownload = BinaryDownload(test_args)
        binaryDownload.check_version(cracker_id)

        cracker_zip = Path(crackers_path, f'{cracker_id}.7z')
        crackers_temp = Path(crackers_path, 'temp')
        zip_binary = '7zr.exe'
        mock_unlink.assert_called_with(cracker_zip)

        mock_system.assert_called_with(f'{zip_binary} x -o"{crackers_temp}" "{cracker_zip}"')

        executeable_path = Path(crackers_path, str(cracker_id), 'hashcat.exe')

        # --version
        cracker = HashcatCracker(1, binaryDownload)
        mock_check_output.assert_called_with([str(executeable_path), '--version'], cwd=Path(crackers_path, str(cracker_id)))

        # --keyspace
        chunk = Chunk()
        task = Task()
        task.load_task()
        hashlist = Hashlist()

        hashlist.load_hashlist(task.get_task()['hashlistId'])
        hashlist_id = task.get_task()['hashlistId']
        hashlists_path = config.get_value('hashlists-path')

        cracker.measure_keyspace(task, chunk)

        full_cmd = [str(executeable_path), '--keyspace', '--quiet', '-a3', '?l?l?l?l', '--hash-type=0']
        mock_check_output.assert_called_with(
            full_cmd,
            cwd=Path(crackers_path, str(cracker_id)),
            stderr=-2
        )

        # benchmark
        hashlist_path = Path(hashlists_path, str(hashlist_id))
        hashlist_out_path = Path(hashlists_path, f'{hashlist_id}.out')
        result = cracker.run_benchmark(task.get_task())
        assert result != 0
        mock_check_output.assert_called_with(
            [
                str(executeable_path),
                '--machine-readable',
                '--quiet',
                '--progress-only',
                '--restore-disable',
                '--potfile-disable',
                '--session=hashtopolis',
                '-p',
                '0x09',
                str(hashlist_path),
                '-a3',
                '?l?l?l?l',
                '--hash-type=0',
                '-o',
                str(hashlist_out_path)
            ],
            cwd=Path(crackers_path, str(cracker_id)),
            stderr=-2
        )

        # Sending benchmark to server
        query = copy_and_set_token(dict_sendBenchmark, config.get_value('token'))
        query['taskId'] = task.get_task()['taskId']
        query['result'] = result
        query['type'] = task.get_task()['benchType']
        req = JsonRequest(query)
        req.execute()

if __name__ == '__main__':
    unittest.main()
