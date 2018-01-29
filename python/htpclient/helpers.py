import sys
import logging

def logErrorAndExit(message):
    logging.error(message)
    sys.exit(1)
