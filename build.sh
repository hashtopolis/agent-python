#!/usr/bin/env bash

if [ -f hashtopolis.zip ]; then
  rm hashtopolis.zip
fi

# write commit count since release into version number when compiling into zip
count=$(git log $(git describe --tags --abbrev=0)..HEAD --oneline | wc -l)
if [ ${count} \> 0 ];
then
    sed -i -E 's/return "([0-9]+)\.([0-9]+)\.([0-9]+)"/return "\1.\2.\3.'$count'"/g' htpclient/initialize.py
fi;
zip -r hashtopolis.zip __main__.py htpclient -x "*__pycache__*"
if [ ${count} \> 0 ];
then
    sed -i -E 's/return "([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)"/return "\1.\2.\3"/g' htpclient/initialize.py
fi;