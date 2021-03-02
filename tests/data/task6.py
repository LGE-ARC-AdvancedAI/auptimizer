#!/usr/bin/env python3

import sys
import os
from aup import aup_args, aup_save_model


@aup_args
def iteration(x):
  aup_save_model(user_def_fn, x)
  return x

def user_def_fn(x):
  os.makedirs(str(x))

iteration(sys.argv[1])
