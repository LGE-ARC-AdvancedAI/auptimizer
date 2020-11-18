#!/usr/bin/env python3
"""
Job will fail when sleep time is 1
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import sys
from time import sleep

from aup import BasicConfig, print_result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    config = BasicConfig().load(sys.argv[1])
    sleep(1+config.time/10.)
    if config.time == 3:
        exit(1)
    print_result(config.time)
