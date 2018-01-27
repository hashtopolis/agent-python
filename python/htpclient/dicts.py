from types import MappingProxyType

"""
These dictionaries are defined using MappingProxyType() which makes them read-only.
If you need to change a value you must create a copy of it. E.g.
foo = dict_foo.copy()
foo["key"] = "value"
"""

dict_os = MappingProxyType(
          {"Linux":   0,  
           "Windows": 1,
           "Darwin":  2})

dict_ext = MappingProxyType(
           {0: "",     # Linux
            1: ".exe", # Windows
            2: ""})    # Mac OS

dict_sendBenchmark = MappingProxyType(
                     {"action": "sendBenchmark",
                      "token":  "",
                      "taskId": "",
                      "type":   "run",
                      "result": ""})
