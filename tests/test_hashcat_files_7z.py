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
import time
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

import py7zr

from tests.hashtopolis import Hashlist as Hashlist_v2
from tests.hashtopolis import Task as Task_v2
from tests.hashtopolis import FileImport as FileImport_v2
from tests.hashtopolis import File as File_v2

class HashcatFiles7z(unittest.TestCase):
    @mock.patch('subprocess.Popen', side_effect=subprocess.Popen)
    @mock.patch('subprocess.check_output', side_effect=subprocess.check_output)
    @mock.patch('os.unlink', side_effect=os.unlink)
    @mock.patch('os.system', side_effect=os.system)
    def test_files_7z_linux(self, mock_system, mock_unlink, mock_check_output, mock_Popen):
        if sys.platform != 'linux':
            return

        # Setup session object
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})

         # Cmd parameters setup
        test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://hashtopolis/api/server.php', version=False, voucher='devvoucher', zaps_path=None, max_log_size=5_000_000, max_log_backups=5)

        # Set config and variables
        cracker_id = 1
        config = Config()

        crackers_path = config.get_value('crackers-path')
        files_path = config.get_value('files-path')

        # Create hashlist
        p = Path(__file__).parent.joinpath('create_hashlist_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        hashlist_v2 = Hashlist_v2(**payload)
        hashlist_v2.save()

        # Create 7z file
        stamp = datetime.datetime.now().isoformat()
        wordlist = f'wordlist-{stamp}.txt'
        sevenzip = f'wordlist-{stamp}.7z'

        with open(wordlist, 'w') as file_obj:
            file_obj.write('12345678\n123456\nprincess\n')

        with py7zr.SevenZipFile(sevenzip, 'w') as z:
            z.writeall(f'./{wordlist}')

        # Upload wordlist
        file_import = FileImport_v2()
        with open(sevenzip, 'rb') as fs:
            file_import.do_upload(sevenzip, fs)

        # Create wordlist
        p = Path(__file__).parent.joinpath('create_file_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        payload['sourceData'] = sevenzip
        payload['filename'] = sevenzip
        payload['fileType'] = 0
        file_obj = File_v2(**payload)
        file_obj.save()

        wordlist_id = file_obj.id

        # Create task
        p = Path(__file__).parent.joinpath('create_task_004.json')
        payload = json.loads(p.read_text('UTF-8'))
        payload['hashlistId'] = int(hashlist_v2._id)
        payload['attackCmd'] = f'#HL# -a0 {wordlist}'
        payload['files'] = [wordlist_id]
        task_obj = Task_v2(**payload)
        task_obj.save()

        # Cleanup files
        os.remove(wordlist)
        os.remove(sevenzip)
        wordlist_path = Path(files_path, wordlist)
        if os.path.isfile(wordlist_path):
            os.remove(wordlist_path)

        # Try to download cracker 1
        executeable_path = Path(crackers_path, str(cracker_id), 'hashcat.bin')

        binaryDownload = BinaryDownload(test_args)
        binaryDownload.check_version(cracker_id)

        # --version
        cracker = HashcatCracker(1, binaryDownload)
        mock_check_output.assert_called_with([str(executeable_path), '--version'], cwd=Path(crackers_path, str(cracker_id)))

        # --keyspace
        chunk = Chunk()
        task = Task()
        task.load_task()
        hashlist = Hashlist()
        files = Files()

        hashlist.load_hashlist(task.get_task()['hashlistId'])
        hashlist_id = task.get_task()['hashlistId']
        hashlists_path = config.get_value('hashlists-path')

        # Download required files
        assert files.check_files(task.get_task()['files'], task.get_task()['taskId'])

        file_path = Path(files_path, sevenzip)

        mock_system.assert_called_with(f"./7zr{Initialize.get_os_extension()} x -aoa -o'{files_path}' -y '{file_path}'")

        # Test if the files are really downloaded
        assert os.path.isfile(wordlist_path) == True

        cracker.measure_keyspace(task, chunk)
        mock_check_output.assert_called_with(
            f"'./hashcat.bin' --keyspace --quiet  -a0 \"{wordlist_path}\"   --hash-type=0 ",
            shell=True,
            cwd=Path(crackers_path, str(cracker_id)),
            stderr=-2
        )

        # benchmark
        result = cracker.run_benchmark(task.get_task())
        assert result != 0
        mock_check_output.assert_called_with(
            f"'./hashcat.bin' --machine-readable --quiet --progress-only --restore-disable --potfile-disable --session=hashtopolis -p \"\t\"  \"{Path(hashlists_path, str(hashlist_id))}\" -a0 \"{wordlist_path}\"   --hash-type=0  -o \"{Path(hashlists_path, str(hashlist_id))}.out\"",
            shell=True,
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

        # cracking
        chunk.get_chunk(task.get_task()['taskId'])
        cracker.run_chunk(task.get_task(), chunk.chunk_data(), task.get_preprocessor())
        zaps_path = config.get_value('zaps-path')
        zaps_dir = f"hashlist_{hashlist_id}"
        skip = str(chunk.chunk_data()['skip'])
        limit = str(chunk.chunk_data()['length'])

        full_cmd = [
            "'./hashcat.bin'",
            '--machine-readable',
            '--quiet',
            '--status',
            '--restore-disable',
            '--session=hashtopolis',
            '--status-timer 5',
            '--outfile-check-timer=5',
            f'--outfile-check-dir="{Path(zaps_path, zaps_dir)}"',
            f'-o "{Path(hashlists_path, str(hashlist_id))}.out"',
            '--outfile-format=1,2,3,4',
            f'-p "\t"',
            f'-s {skip} -l {limit}',
            '--potfile-disable',
            '--remove',
            '--remove-timer=5 ',
            f'"{Path(hashlists_path, str(hashlist_id))}"',
            f'-a0 "{wordlist_path}" ',
            ' --hash-type=0 ',
        ]

        full_cmd = ' '.join(full_cmd)

        mock_Popen.assert_called_with(
            full_cmd,
            shell=True,
            stdout=-1,
            stderr=-1,
            cwd=Path(crackers_path, str(cracker_id)),
            preexec_fn=mock.ANY
        )

        # Cleanup
        task_obj.delete()
        hashlist_v2.delete()
        file_obj.delete()
        if os.path.isfile(wordlist_path):
            os.remove(wordlist_path)


    @mock.patch('subprocess.Popen', side_effect=subprocess.Popen)
    @mock.patch('subprocess.check_output', side_effect=subprocess.check_output)
    @mock.patch('os.unlink', side_effect=os.unlink)
    @mock.patch('os.system', side_effect=os.system)
    def test_files_7z_windows(self, mock_system, mock_unlink, mock_check_output, mock_Popen):
        if sys.platform != 'win32':
            return

        # Setup session object
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})

         # Cmd parameters setup
        test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://hashtopolis/api/server.php', version=False, voucher='devvoucher', zaps_path=None)

        # Set config and variables
        cracker_id = 1
        config = Config()

        crackers_path = config.get_value('crackers-path')
        files_path = config.get_value('files-path')

        # Create hashlist
        p = Path(__file__).parent.joinpath('create_hashlist_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        hashlist_v2 = Hashlist_v2(**payload)
        hashlist_v2.save()

        # Create 7z file
        stamp = int(time.time())
        wordlist = f'wordlist-{stamp}.txt'
        sevenzip = f'wordlist-{stamp}.7z'

        with open(wordlist, 'w') as file_obj:
            file_obj.write('12345678\n123456\nprincess\n')

        with py7zr.SevenZipFile(sevenzip, 'w') as z:
            z.writeall(f'./{wordlist}')

        # Upload wordlist
        file_import = FileImport_v2()
        with open(sevenzip, 'rb') as fs:
            file_import.do_upload(sevenzip, fs)

        # Create wordlist
        p = Path(__file__).parent.joinpath('create_file_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        payload['sourceData'] = sevenzip
        payload['filename'] = sevenzip
        payload['fileType'] = 0
        file_obj = File_v2(**payload)
        file_obj.save()

        wordlist_id = file_obj.id

        # Create task
        p = Path(__file__).parent.joinpath('create_task_004.json')
        payload = json.loads(p.read_text('UTF-8'))
        payload['hashlistId'] = int(hashlist_v2._id)
        payload['attackCmd'] = f'#HL# -a0 {wordlist}'
        payload['files'] = [wordlist_id]
        task_obj = Task_v2(**payload)
        task_obj.save()

        # Cleanup files
        os.remove(wordlist)
        os.remove(sevenzip)
        wordlist_path = Path(files_path, wordlist)
        if os.path.isfile(wordlist_path):
            os.remove(wordlist_path)

        # Try to download cracker 1
        executeable_path = Path(crackers_path, str(cracker_id), 'hashcat.exe')

        binaryDownload = BinaryDownload(test_args)
        binaryDownload.check_version(cracker_id)

        # --version
        cracker = HashcatCracker(1, binaryDownload)
        mock_check_output.assert_called_with([str(executeable_path), '--version'], cwd=Path(crackers_path, str(cracker_id)))

        # --keyspace
        chunk = Chunk()
        task = Task()
        task.load_task()
        hashlist = Hashlist()
        files = Files()

        hashlist.load_hashlist(task.get_task()['hashlistId'])
        hashlist_id = task.get_task()['hashlistId']
        hashlists_path = config.get_value('hashlists-path')

        # Download required files
        assert files.check_files(task.get_task()['files'], task.get_task()['taskId'])

        file_path = Path(files_path, sevenzip)

        mock_system.assert_called_with(f'7zr{Initialize.get_os_extension()} x -aoa -o"{files_path}" -y "{file_path}"')

        # Test if the files are really downloaded
        assert os.path.isfile(wordlist_path) == True

        cracker.measure_keyspace(task, chunk)
        mock_check_output.assert_called_with(
            f'"hashcat.exe" --keyspace --quiet  -a0 "{wordlist_path}"   --hash-type=0 ',
            shell=True,
            cwd=Path(crackers_path, str(cracker_id)),
            stderr=-2
        )

        # benchmark
        result = cracker.run_benchmark(task.get_task())
        assert result != 0
        mock_check_output.assert_called_with(
            f'"hashcat.exe" --machine-readable --quiet --progress-only --restore-disable --potfile-disable --session=hashtopolis -p \"\t\"  \"{Path(hashlists_path, str(hashlist_id))}\" -a0 "{wordlist_path}"   --hash-type=0  -o \"{Path(hashlists_path, str(hashlist_id))}.out\"',
            shell=True,
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

        # cracking
        chunk.get_chunk(task.get_task()['taskId'])
        cracker.run_chunk(task.get_task(), chunk.chunk_data(), task.get_preprocessor())
        zaps_path = config.get_value('zaps-path')
        zaps_dir = f"hashlist_{hashlist_id}"
        skip = str(chunk.chunk_data()['skip'])
        limit = str(chunk.chunk_data()['length'])

        full_cmd = [
            '"hashcat.exe"',
            '--machine-readable',
            '--quiet',
            '--status',
            '--restore-disable',
            '--session=hashtopolis',
            '--status-timer 5',
            '--outfile-check-timer=5',
            f'--outfile-check-dir="{Path(zaps_path, zaps_dir)}"',
            f'-o "{Path(hashlists_path, str(hashlist_id))}.out"',
            '--outfile-format=1,2,3,4',
            f'-p "\t"',
            f'-s {skip} -l {limit}',
            '--potfile-disable',
            '--remove',
            '--remove-timer=5 ',
            f'"{Path(hashlists_path, str(hashlist_id))}"',
            f'-a0 "{wordlist_path}" ',
            ' --hash-type=0 ',
        ]

        full_cmd = ' '.join(full_cmd)

        mock_Popen.assert_called_with(
            full_cmd,
            shell=True,
            stdout=-1,
            stderr=-1,
            cwd=Path(crackers_path, str(cracker_id)),
        )

        # Cleanup
        task_obj.delete()
        hashlist_v2.delete()
        file_obj.delete()
        if os.path.isfile(wordlist_path):
            os.remove(wordlist_path)
