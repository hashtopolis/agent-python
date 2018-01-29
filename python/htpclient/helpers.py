import sys
import logging
from types import MappingProxyType


def logErrorAndExit(message):
    logging.error(message)
    sys.exit(1)


def printSpeed(speed):
    prefixes = MappingProxyType(
        {0: "",
         1: "k",
         2: "M",
         3: "G",
         4: "T"})
    exponent = 0
    while speed > 1024:
        exponent += 1
        speed = float(speed) / 1024
    return str("{:6.2f}".format(speed)) + prefixes[exponent] + "H/s"
