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
import datetime
from io import BytesIO

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
from htpclient.files import Files

from tests.hashtopolis import Hashlist as Hashlist_v2
from tests.hashtopolis import Task as Task_v2
from tests.hashtopolis import FileImport as FileImport_v2
from tests.hashtopolis import File as File_v2



class HashcatRuntime(unittest.TestCase):
    @mock.patch('subprocess.Popen', side_effect=subprocess.Popen)
    @mock.patch('subprocess.check_output', side_effect=subprocess.check_output)
    def test_runtime_windows(self, mock_check_output, moch_popen):
        if sys.platform != 'win32':
            return

        # Setup session object
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})

        # Create hashlist
        p = Path(__file__).parent.joinpath('create_hashlist_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        hashlist_v2 = Hashlist_v2(**payload)
        hashlist_v2.save()

        # Create Task
        for p in sorted(Path(__file__).parent.glob('create_task_002.json')):
            payload = json.loads(p.read_text('UTF-8'))
            payload['hashlistId'] = int(hashlist_v2._id)
            obj = Task_v2(**payload)
            obj.save()

        # Cmd parameters setup
        test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://hashtopolis/api/server.php', version=False, voucher='devvoucher', zaps_path=None, max_log_size=5_000_000, max_log_backups=5)

        # Try to download cracker 1
        cracker_id = 1
        config = Config()
        crackers_path = config.get_value('crackers-path')

        binaryDownload = BinaryDownload(test_args)
        binaryDownload.check_version(cracker_id)

        # --version
        cracker = HashcatCracker(1, binaryDownload)

        # --keyspace
        chunk = Chunk()
        task = Task()
        task.load_task()
        hashlist = Hashlist()

        hashlist.load_hashlist(task.get_task()['hashlistId'])
        hashlist_id = task.get_task()['hashlistId']
        hashlists_path = config.get_value('hashlists-path')

        cracker.measure_keyspace(task, chunk)

        full_cmd = f'"hashcat.exe" --keyspace --quiet  -a3 ?l?l?l?l   --hash-type=0 '
        mock_check_output.assert_called_with(
            full_cmd,
            shell=True,
            cwd=Path(crackers_path, str(cracker_id)),
            stderr=-2
        )

        # benchmark
        hashlist_path = Path(hashlists_path, str(hashlist_id))
        hashlist_out_path = Path(hashlists_path, f'{hashlist_id}.out')
        result = cracker.run_benchmark(task.get_task())
        assert result != 0

        full_cmd = [
            '"hashcat.exe"',
            '--machine-readable',
            '--quiet',
            '--runtime=30',
            '--restore-disable',
            '--potfile-disable',
            '--session=hashtopolis',
            '-p',
            '"\t"',
            f' "{hashlist_path}"',
            '-a3 ?l?l?l?l',
            '  --hash-type=0 ',
            '-o',
            f'"{hashlist_out_path}"'
        ]

        full_cmd = ' '.join(full_cmd)

        moch_popen.assert_called_with(
            full_cmd,
            shell=True,
            cwd=Path(crackers_path, str(cracker_id)),
            stdout=-1,
            stderr=-1
        )

        task_id = task.get_task()['taskId']

        # Sending benchmark to server
        query = copy_and_set_token(dict_sendBenchmark, config.get_value('token'))
        query['taskId'] = task_id
        query['result'] = result
        query['type'] = task.get_task()['benchType']
        req = JsonRequest(query)
        req.execute()

        assert chunk.get_chunk(task_id) == 1

        # Cleanup
        obj.delete()
        hashlist_v2.delete()

if __name__ == '__main__':
    unittest.main()
