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

@aup_args
def rosenbrock(x, y, a=1, b=100):
    return (a-x)*(a-x) + b*(y-x*x)*(y-x*x)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    
    rosenbrock(sys.argv[1])
