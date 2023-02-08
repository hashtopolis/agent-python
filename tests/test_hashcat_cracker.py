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
    @mock.patch('subprocess.check_output', side_effect=subprocess.check_output)
    @mock.patch('os.unlink', side_effect=os.unlink)
    @mock.patch('os.system', side_effect=os.system)
    def test_correct_flow(self, mock_system, mock_unlink, mock_check_output):
        # Clean up cracker folder
        if os.path.exists('crackers/1'):
            shutil.rmtree('crackers/1')

        #TODO: Delete tasks / hashlist to ensure clean

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
        chunk_resp = chunk.get_chunk(task.get_task()['taskId'])

        cracker.measure_keyspace(task, chunk)
        mock_check_output.assert_called_with(
            "'./hashcat.bin' --keyspace --quiet  -a3 ?l?l?l?l?l?l   --hash-type=0 ",
            shell=True,
            cwd=f"{Path(crackers_path, str(cracker_id))}/",
            stderr=-2
        )

        # benchmark
        result = cracker.run_benchmark(task.get_task())
        mock_check_output.assert_called_with(
            "'./hashcat.bin' --machine-readable --quiet --progress-only --restore-disable --potfile-disable --session=hashtopolis -p \"\t\"  '/app/src/hashlists/1'  -a3 ?l?l?l?l?l?l  --hash-type=0  -o '/app/src/hashlists/1.out'",
            shell=True,
            cwd=f"{Path(crackers_path, str(cracker_id))}/",
            stderr=-2
        )

        # Cleanup
        obj.delete()
        hashlist_v2.delete()

if __name__ == '__main__':
    unittest.main()
