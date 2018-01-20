# Hashtopussy Python Agent

This Hashtopussy agent is only compatible with Hashtopussy versions 0.5.0 and higher.

## Prerequisites

You need python3 installed on your agent system. 
Following python packages are required:

* requests

## Manual

You can either download the agent from the Hashtopussy new agent page or you can use the url shown there to download the agent with 
wget/curl.

### Run

To run the agent you simply need to call `python3 hashtopussy.zip`. There are no command line options accepted, all 
settings/configurations are done via the config file, described in the following section.

Please not that the client does not correctly recognize the OS when you are running in Cygwin or similar on Windows. You need to run it in Windows command line.

### Config

TODO

## Hashcat Compatibility

The list contains all Hashcat version with which the client was tested and is able to work with (other versions might work):

* 4.0.1
* 4.0.0

## Generic Crackers

This client is able to run generic Hashtopussy cracker binaries which fulfill the minimal functionality requirements, described [here](https://github.com/s3inlc/hashtopussy/tree/master/doc/README.md). An example implementation can be found [here](https://github.com/s3inlc/hashtopussy-generic-cracker)
