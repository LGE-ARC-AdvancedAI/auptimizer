#!/usr/bin/env python
# Demonstration code for 1D function, centered around a=1
from time import sleep
from aup import aup_args
import sys

@aup_args
def demo_func(x, a=1, b=0):
    sleep(1)
    return (x-a)*(x-a)+b


if __name__ == "__main__":
    demo_func(sys.argv[1])
