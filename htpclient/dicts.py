from types import MappingProxyType


def copy_and_set_token(dictionary, token):
    dict_copy = dictionary.copy()
    dict_copy["token"] = token
    return dict_copy


"""
These dictionaries are defined using MappingProxyType() which makes them read-only.
If you need to change a value you must create a copy of it. E.g.
foo = dict_foo.copy()
foo["key"] = "value"
"""

dict_os = MappingProxyType(
    {'Linux': 0,
     'Windows': 1,
     'Darwin': 2})

dict_ext = MappingProxyType(
    {0: '',  # Linux
     1: '.exe',  # Windows
     2: ''})  # Mac OS

dict_sendBenchmark = MappingProxyType(
    {'action': 'sendBenchmark',
     'token': '',
     'taskId': '',
     'type': '',
     'result': ''})

dict_getHealthCheck = MappingProxyType(
    {'action': 'getHealthCheck',
     'token': ''}
)

dict_sendHealthCheck = MappingProxyType(
    {'action': 'sendHealthCheck',
     'token': '',
     'numCracked': 0,
     'start': 0,
     'end': 0,
     'numGpus': 0,
     'errors': '',
     'checkId': 0}
)

dict_checkVersion = MappingProxyType(
    {'action': 'checkClientVersion',
     'token': '',
     'version': '',
     'type': 'python'})

dict_downloadBinary = MappingProxyType(
    {'action': 'downloadBinary',
     'token': '',
     'type': ''})

dict_login = MappingProxyType(
    {'action': 'login',
     'token': '',
     'clientSignature': ''})

dict_updateInformation = MappingProxyType(
    {'action': 'updateInformation',
     'token': '',
     'uid': '',
     'os': '',
     'devices': ''})

dict_register = MappingProxyType(
    {'action': 'register',
     'voucher': '',
     'name': ''})

dict_testConnection = MappingProxyType(
    {'action': 'testConnection'})

dict_getChunk = MappingProxyType(
    {'action': 'getChunk',
     'token': '',
     'taskId': ''})

dict_sendKeyspace = MappingProxyType(
    {'action': 'sendKeyspace',
     'token': '',
     'taskId': '',
     'keyspace': 0})

dict_getTask = MappingProxyType(
    {'action': 'getTask',
     'token': ''})

dict_sendProgress = MappingProxyType(
    {'action': 'sendProgress',
     'token': '',
     'chunkId': '',
     'keyspaceProgress': '',
     'relativeProgress': '',
     'speed': '',
     'state': '',
     'cracks': ''})

dict_clientError = MappingProxyType(
    {'action': 'clientError',
     'token': '',
     'taskId': '',
     'chunkId': None,
     'message': ''})

dict_getHashlist = MappingProxyType(
    {'action': 'getHashlist',
     'token': '',
     'hashlistId': ''})

dict_getFound = MappingProxyType(
    {'action': 'getFound',
     'token': '',
     'hashlistId': ''})

dict_getFile = MappingProxyType(
    {'action': 'getFile',
     'token': '',
     'taskId': '',
     'file': ''})

dict_getFileStatus = MappingProxyType(
    {'action': 'getFileStatus',
     'token': ''})

dict_deregister = MappingProxyType(
    {'action': 'deregister',
     'token': ''})
