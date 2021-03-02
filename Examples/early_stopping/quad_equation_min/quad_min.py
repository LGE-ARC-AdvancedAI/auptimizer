#!/usr/bin/env python
"""
Modified Rosenbrock function for HPO and aup
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import sys

import aup
from time import sleep

def rosenbrock(x, a=2, b=4, c=5):
    sleep(1)
    
    it = 1.0
    for _ in range(10):
        res = x*x*a + x*b + c
        res += it
        it -= 1.0 / 10
        aup.print_result(res)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    config = aup.BasicConfig().load(sys.argv[1])
    rosenbrock(config['x'])
