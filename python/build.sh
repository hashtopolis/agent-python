#!/usr/bin/env bash

rm hashtopolis.zip
zip -r hashtopolis.zip __main__.py htpclient -x "*__pycache__*"