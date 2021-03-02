#!/usr/bin/env python3

import sys
from aup import aup_args
from time import sleep

def init(**kwargs):
  global var

  var = kwargs["x"]

@aup_args
def iteration(x):
  global var

  var += 1
  sleep(1)
  return [var, var+1, var+2]

iteration(sys.argv[1])