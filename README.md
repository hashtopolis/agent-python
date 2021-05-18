# Hashtopolis Python Agent

[![CodeFactor](https://www.codefactor.io/repository/github/hashtopolis/agent-python/badge)](https://www.codefactor.io/repository/github/hashtopolis/agent-python)
[![LoC](https://tokei.rs/b1/github/hashtopolis/agent-python?category=code)](https://github.com/hashtopolis/agent-python)
[![Build Status](https://travis-ci.com/hashtopolis/agent-python.svg?branch=master)](https://travis-ci.com/hashtopolis/agent-python)

This agent is used with [Hashtopolis](https://github.com/hashtopolis/server), read the wiki or create issues there, visit the [Forum](https://hashtopolis.org).
This Hashtopolis agent is only compatible with Hashtopolis versions 0.5.0 and higher.

## Prerequisites

You need python3 installed on your agent system. 
Following python packages are required:

* requests
* psutil

## Manual

You can either download the agent from the Hashtopolis new agent page or you can use the url shown there to download the agent with 
wget/curl.

### Run

To run the agent you simply need to call `python3 hashtopolis.zip`. The settings/configurations normally are done via the config file, described in one of the following sections.

Please note:
- The client does not correctly recognize the OS when you are running in Cygwin or similar on Windows. You need to run it in Windows command line.
- If you unpack the agent out of the .zip file, the automatic updating from the server won't work correctly.

### Command Line Arguments

```
usage: python3 hashtopolis.zip [-h] [--de-register] [--version]
                               [--number-only] [--disable-update] [--debug]
                               [--voucher VOUCHER] [--url URL]

Hashtopolis Client v0.6.0

optional arguments:
  -h, --help         show this help message and exit
  --de-register      client should automatically de-register from server now
  --version          show version information
  --number-only      when using --version show only the number
  --disable-update   disable retrieving auto-updates of the client from the
                     server
  --debug, -d        enforce debugging output
  --voucher VOUCHER  voucher to use to automatically register
  --url URL          URL to Hashtopolis client API
```

### Config

When you run the client for the first time it will ask automatically for all the requirement settings and then saves it automatically to a config file called `config.json`. This could for example look like this:

```
{
  "url": "https://example.org/hashtopolis/api/server.php", 
  "token": "ABCDEFGHIJ", 
  "uuid": "49dcd31c-3637-4f2a-8df1-b545202df5b3"
}
```

### Config Options

| field                 | type    | default | description                                                                |
|-----------------------|---------|---------|----------------------------------------------------------------------------|
| voucher               | string  |         | Used for agent registration (will be prompted on first start)              |
| url                   | string  |         | The hashtopolis API endpoint (will be prompted on first start)             |
| token                 | string  |         | The access token for the API (sent by server on registration)              |
| uuid                  | string  |         | Unique identifier of the agent (generated on registration)                 |
| debug                 | boolean | false   | Enables debug output                                                       |
| allow-piping          | boolean | false   | Allows hashcat to read password candidates from stdin                      |
| piping-threshold      | integer | 95      | Restarts chunk in piping mode when GPU UTIL is below this value            |
| rsync                 | boolean | false   | Enables download of wordlists and rules via rsync                          |
| rsync-path            | string  |         | Remote path to hashtopolis files directory                                 |
| multicast-device      | string  | eth0    | Device which is used to retrieve UDP multicast file distribution           |
| file-deletion-disable | boolean | false   | Disable requesting the server for files to delete                          |
| file-deletion-interval| integer | 600     | Interval time in seconds in which the agent should check for deleted files |
| proxies               | object  |         | Specify proxies e.g. `"proxies": {"https": "localhost:8433"}`              |
| auth-user             | string  |         | HTTP Basic Auth user                                                       |
| auth-password         | string  |         | HTTP Basic Auth password                                                   |
| outfile-history       | boolean | false   | Keep old hashcat outfiles with founds and not getting them overwritten     |

### Debug example

```
{
  "url": "https://example.org/hashtopolis/api/server.php", 
  "token": "7RNDqtnPxm",
  "uuid": "49dcd31c-3637-4f2a-8df1-b545202df5b3",
  "debug": true
}
```

### rsync

You need a user on the server which can automatically login (e.g. SSH keys) and has read access to the files directory of hashtopolis. On the client side you need rsync installed and set the following lines in your agent config.

```
  "rsync": true,
  "rsync-path": "user@yourserver:/path/to/hashtopolis/files"
```

### Multicast

In order to use the multicast distribution for files, please make sure that the agents and server are prepared according to this:https://github.com/hashtopolis/runner

## Hashcat Compatibility

The list contains all Hashcat versions with which the client was tested and is able to work with (other versions might work):

* 6.1.1
* 6.1.0
* 6.0.0
* 5.1.0
* 5.0.0
* 4.2.1
* 4.2.0
* 4.1.0
* 4.0.1
* 4.0.0

## Generic Crackers

This client is able to run generic Hashtopolis cracker binaries which fulfill the minimal functionality requirements, described [here](https://github.com/s3inlc/hashtopolis/tree/master/doc/README.md). An example implementation can be found [here](https://github.com/hashtopolis/generic-cracker)
