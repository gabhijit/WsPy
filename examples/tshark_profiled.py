import os
import sys
import time
import struct
import socket
from datetime import datetime as dt
import warnings
import logging

_MAX_TO_PROCESS = 10000000

from wishpy.wireshark.lib.dissector import WishpyDissectorFile
from wishpy.wireshark.lib.dissector import setup_process, cleanup_process
from wishpy.utils.profiler import WishpyContextProfiler

if __name__ == '__main__':

    logger = logging.getLogger()
    logging.basicConfig()

    if not len(sys.argv) >= 2:
        print("Usage: tshark.py <filepath>")
        sys.exit(1)

    input_filepath = sys.argv[1]

    setup_process()

    dissector = WishpyDissectorFile(input_filepath)

    then = dt.now()

    try:
        then = time.time()
        with WishpyContextProfiler(enabled=True, contextstr="dissector-run") as p:
            for dissected in dissector.run(count=10000, skip=0):
                pass #print(dissected)

        now = time.time()
        print(p.get_profile_data())
        print(now - then)

    except KeyboardInterrupt:
        cleanup_process()

    now = dt.now()
