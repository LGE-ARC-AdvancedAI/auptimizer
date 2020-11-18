#!/usr/bin/env python
"""
Modified from https://github.com/han-cai/EAS

The file to run in the client side
Train the network and return the validation performance
"""
import os
from expdir_monitor.expdir_monitor import ExpdirMonitor
import time
import sys
from aup import BasicConfig, print_result
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


def run(expdir):
	start_time = time.time()
	expdir_monitor = ExpdirMonitor(expdir)
	valid_performance = expdir_monitor.run(pure=True, restore=False)
	end_time = time.time()
	print('running time: %s' % (end_time - start_time))
	print('valid performance: %s' % valid_performance)
	print_result(valid_performance)


def main():
	print("Starting Client")
	config = BasicConfig().load(sys.argv[1])
	run(config["expdir"])


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		pass
