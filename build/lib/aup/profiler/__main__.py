

"""
..
  Copyright (c) 2020 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Profiler main entry
=====================

:mod:`aup.profiler.__main__` is the Profiler main entry point.

Use it as::

  python -m aup.profiler -e <experiment configuration> -m <model list>

The usage is detailed in :doc:`profiler`.

"""



# python wrapper for profiler.sh. This wrapper allows profiler to be installed using pip install.

import argparse
import sys
import os

def main():
    
    # read in the arguments
    # environment file is required
    # either modelfile or modellist can be present but not both. If neither, then the environment file should contain info on the script.
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--environment", help="The environment file that contains all the information on what and how to profile.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--modelfile", help="A file containing the list of models to profile. Use only -m or -f but not both.")
    group.add_argument("-m", "--modellist", help="comma separated list of models to profile. Use only -m or -f but not both.")
    args = parser.parse_args()

    if not args.environment:
        print("Profiler needs an environment file. Please see documentation for more information.")
        print("Exiting.")
        sys.exit(2)
    
    script_flags = " -e "+args.environment

    if args.modellist:
        script_flags += " -m "+args.modellist
    elif args.modelfile:
        script_flags += " -f "+args.modelfile
    else:
        print("**Warning**: If modellist or modelfile not provided, environment file should have script info. Please see documentation for more information.")
    
    script_command = 'profiler.sh' + script_flags 

    # run script command
    os.system(script_command)


if __name__ == "__main__":
    main()
