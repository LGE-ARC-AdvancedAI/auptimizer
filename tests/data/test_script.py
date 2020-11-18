#!/usr/bin/env python

"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""

import random


RUNS = 0

def func(x):
    global RUNS
    RUNS += 1
    if RUNS % 5 == 0:
        raise SystemError
    return x**2

def aup_wrapper(config):
    res = func(x=config['x']) 
    print_result(res)

if __name__ == "__main__":
    import sys
    from aup import BasicConfig, print_result
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    config = BasicConfig().load(sys.argv[1])
    aup_wrapper(config)
