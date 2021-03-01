#!/usr/bin/env python3

import sys
from aup import aup_args, print_result
from time import sleep

def init(**kwargs):
  global var

  var = kwargs["x"]

@aup_args
def iteration(x):
  global var

  sleep(1)

  for _ in range(5):
    var += 1
    print_result(var)

  var += 1
  return var

iteration(sys.argv[1])
