import pytest
from unittest import mock

from htpclient.hashcat_cracker import HashcatCracker
from htpclient.binarydownload import BinaryDownload

from argparse import Namespace

# The default cmdparameters, some objects need those. Maybe move to a common helper so other tests can include this aswell.
test_args = Namespace( cert=None,  cpu_only=False, crackers_path=None, de_register=False, debug=True, disable_update=False, files_path=None, hashlists_path=None, number_only=False, preprocessors_path=None, url='http://example.com/api/server.php', version=False, voucher='devvoucher', zaps_path=None)


@mock.patch('htpclient.initialize.Initialize.get_os')
@mock.patch('subprocess.check_output')
@mock.patch('htpclient.jsonRequest.JsonRequest.execute')
@mock.patch('htpclient.download.Download.download')
@mock.patch('os.system')
@mock.patch('os.unlink')
def test_hashcat_cracker_linux(mock_unlink, mock_system, mock_download, mock_get, mock_check_output, mock_get_os):
    #TODO: Make paths based on environment
    #TODO: Clean all cracker folders etc

    # Force Linux OS
    mock_get_os.return_value = 0

    binaryDownload = BinaryDownload(test_args)

    # When calling binaryDownload.check_version(1), this will make a request for executable name
    # Download the 7z if the cracker is not there
    # Extract the 7z
    # And cleanup the temp file
    
    mock_get.return_value = {'response': 'SUCCESS', 'url': 'leeg', 'executable': 'hashcat.bin'}
    mock_download.return_value = True
    mock_check_output.return_value = 'v6.2.6\n'.encode()
    binaryDownload.check_version(1)

    # Checking if system and unlink were called correctly.
    mock_system.assert_called_with("./7zr x -o'/app/src/crackers/temp' '/app/src/crackers/1.7z'")
    mock_unlink.assert_called_with("/app/src/crackers/1.7z")
    
    # This will call 'hashcat --version'
    hashcat = HashcatCracker(1, binaryDownload)
    mock_check_output.assert_called_with("'./hashcat64.bin' --version", shell=True, cwd='/app/src/crackers/1/')
