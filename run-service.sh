#!/bin/bash

##
# Helper script to run orfodon-service.py
# You must change the path when using this file!
#
# Working directory must be script location when running the script
# to allow relative testing
#
# To be run from a cron job
#

## Location of orfodon_service.py
SERVICE_PATH="/usr/local/orfodon-service/orfodon_service/"

## Lockfile to use for singleton
LOCKFILE="/var/lock/.orfodon-service.exclusivelock"

## Logfile to report actions to
LOGFILE="orfodon_service.log"

# Execute script as singleton
(
  flock -x -w 10 200 || exit 1
    cd "$SERVICE_PATH" || exit 1
    python3 orfodon_service.py 2>&1 | tee -a "$LOGFILE"
) 200>"$LOCKFILE"
