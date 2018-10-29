#!/usr/bin/env bash

if [ -f hashtopolis.zip ]; then
  rm hashtopolis.zip
fi
zip -r hashtopolis.zip __main__.py htpclient -x "*__pycache__*"
