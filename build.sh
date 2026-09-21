#!/usr/bin/env bash

if [ -f hashtopolis.zip ]; then
  rm hashtopolis.zip
fi

# Make sure tags are available locally (some CI/PR checkouts or forks only
# have a single branch without tags), so git describe can actually find the
# latest release tag instead of silently failing.
git fetch --tags --quiet 2>/dev/null || true

# write commit count since release into version number when compiling into zip
latest_tag=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$latest_tag" ]; then
  count=$(git log "${latest_tag}"..HEAD --oneline | wc -l)
else
  count=0
fi

if [ "$count" -gt 0 ]; then
  sed -i -E 's/return "([0-9]+)\.([0-9]+)\.([0-9]+)"/return "\1.\2.\3.'$count'"/g' htpclient/initialize.py
fi

zip -r hashtopolis.zip __main__.py htpclient -x "*__pycache__*"

if [ "$count" -gt 0 ]; then
  sed -i -E 's/return "([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)"/return "\1.\2.\3"/g' htpclient/initialize.py
fi
