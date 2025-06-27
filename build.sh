#!/usr/bin/env bash

if [ -f hashtopolis.zip ]; then
  rm hashtopolis.zip
fi

# Get latest tag, fallback to initial commit hash if no tags found
latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo $(git rev-list --max-parents=0 HEAD))
count=$(git log ${latest_tag}..HEAD --oneline | wc -l)

if [ "$count" -gt 0 ]; then
  sed -i -E 's/return "([0-9]+)\.([0-9]+)\.([0-9]+)"/return "\1.\2.\3.'$count'"/g' htpclient/initialize.py
fi

zip -r hashtopolis.zip __main__.py htpclient -x "*__pycache__*"

if [ "$count" -gt 0 ]; then
  sed -i -E 's/return "([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)"/return "\1.\2.\3"/g' htpclient/initialize.py
fi
