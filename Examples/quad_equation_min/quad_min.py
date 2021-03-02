#!/usr/bin/env python
"""
Modified Rosenbrock function for HPO and aup
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import sys
""" # ver 1.0 - modify existing code
from aup import BasicConfig, print_result

def rosenbrock(conf, a=1, b=100):
    x = conf.x
    y = conf.y
    return (a-x)*(a-x) + b*(y-x*x)*(y-x*x)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    config = BasicConfig().load(sys.argv[1])
    val = rosenbrock(config)
    print_result(val)
"""

from aup import aup_args
from time import sleep

@aup_args
def rosenbrock(x, a=2, b=4, c=5):
    global it

    it = 1.0
    res = None

    for _ in range(0, 10):
        sleep(1)
        res = x*x*a + x*b + c
        res += it
        it -= 1.0 / 10

    return res

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    
    rosenbrock(sys.argv[1])
