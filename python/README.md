# Hashtopolis Python Agent

This Hashtopolis agent is only compatible with Hashtopolis versions 0.5.0 and higher.

## Prerequisites

You need python3 installed on your agent system. 
Following python packages are required:

* requests

## Manual

You can either download the agent from the Hashtopolis new agent page or you can use the url shown there to download the agent with 
wget/curl.

### Run

To run the agent you simply need to call `python3 hashtopolis.zip`. There are no command line options accepted, all 
settings/configurations are done via the config file, described in the following section.

Please note that the client does not correctly recognize the OS when you are running in Cygwin or similar on Windows. You need to run it in Windows command line.

### Config

When you run the client for the first time it will ask automatically for all the requirement settings and then saves it automatically to a config file called `config.json`. This could for example look like this:

```
{
  "url": "https://coray.org/htp-test/src/api/server.php", 
  "token": "7RNDqtnPxm", 
  "uuid": "49dcd31c-3637-4f2a-8df1-b545202df5b3"
}
```

Optional you can manually set the `debug` property to display more information on the console and the log.

```
{
  "url": "https://coray.org/htp-test/src/api/server.php", 
  "token": "7RNDqtnPxm",
  "debug": true,
  "uuid": "49dcd31c-3637-4f2a-8df1-b545202df5b3"
}
```

## Hashcat Compatibility

The list contains all Hashcat versions with which the client was tested and is able to work with (other versions might work):

* 4.1.0
* 4.0.1
* 4.0.0

## Generic Crackers

This client is able to run generic Hashtopolis cracker binaries which fulfill the minimal functionality requirements, described [here](https://github.com/s3inlc/hashtopolis/tree/master/doc/README.md). An example implementation can be found [here](https://github.com/s3inlc/hashtopolis-generic-cracker)
