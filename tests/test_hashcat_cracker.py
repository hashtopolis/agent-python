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

from tests.hashtopolis import Hashlist, Task

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

        # Setup session object
        session = Session(requests.Session()).s
        session.headers.update({'User-Agent': Initialize.get_version()})

        # Create hashlist
        p = Path(__file__).parent.joinpath('create_hashlist_001.json')
        payload = json.loads(p.read_text('UTF-8'))
        hashlist = Hashlist(**payload)
        hashlist.save()

        # Create Task
        for p in sorted(Path(__file__).parent.glob('create_task_001.json')):
            payload = json.loads(p.read_text('UTF-8'))
            payload['hashlistId'] = int(hashlist._id)
            obj = Task(**payload)
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

        # 
        hashcat = HashcatCracker(1, binaryDownload)
        mock_check_output.assert_called_with("'./hashcat.bin' --version", shell=True, cwd='/app/src/crackers/1/')

        # Cleanup
        obj.delete()
        hashlist.delete()

if __name__ == '__main__':
    unittest.main()
