from subprocess import Popen, PIPE
from threading import Thread, Lock
from queue import Queue
from time import sleep
from sys import stderr
import re
import json
#import shlex
#import ipdb
#import os
#import signal

max_running_machine = 2

_max_used_mem = 0.3
_max_used_gpu = 0.3
config_file = 'server_config'


class GpuChecker:
	def __init__(self, nvidia_getter, gpuid):
		self.nvidia_getter = nvidia_getter
		self.gpuid = gpuid
	
	def state_parser(self, state_str):
		result = []
		for line in state_str.split('\n'):
			# .*?(\d*)C.*\|(.*?)MiB.*?/(.*?)MiB.*?\|.*?(\d*)\%
			# .*?(\d*)C.*\|(.*?)MiB.*?/(.*?)MiB.*?\|.*?(\d*)%
			pattern = re.search('.*?(\d*)C.*\|(.*?)MiB.*?/(.*?)MiB.*?\|.*?(\d*)%', line)
			if pattern is not None:
				result.append([int(x) for x in pattern.groups()])
		if self.gpuid >= len(result):
			return None
		# assert self.gpuid < len(result), 'Parsing error or not enough gpus.'
		return result[self.gpuid]
	
	def instance_available(self, state_str):
		parse_result = self.state_parser(state_str)
		if parse_result is None: return False
		_, used_mem, total_mem, occupation = parse_result
		occupation /= 100
		return used_mem / total_mem < _max_used_mem and occupation < _max_used_gpu
	
	def check(self):
		_check_times = 3
		try:
			for _i in range(_check_times):
				assert self.instance_available(self.nvidia_getter())
				if _i < _check_times - 1:
					sleep(0.5)
		except AssertionError:
			return False
		return True
	
	def is_on(self):
		try:
			parse_result = self.state_parser(self.nvidia_getter())
			if parse_result is None:
				return False
			else:
				return True
		except Exception:
			return False


class RemoteController:
	def __init__(self, remote, gpuid, executive):
		self.remote = remote
		self.gpuid = gpuid
		self.executive = executive
		
		self.gpu_checker = GpuChecker(lambda: self.run('nvidia-smi'), self.gpuid)
		
		self._lock = Lock()
		self._occupied = False
		self._on_running = None
		self.proc_pid = -1
	
	@property
	def occupied(self):
		#print("Here Check 4 yy")
		with self._lock:
			return self._occupied
	
	@occupied.setter
	def occupied(self, val):
		assert isinstance(val, bool), 'Occupied must be True or False, but {} received.'.format(val)
		print("Here Check 3 yy")
		with self._lock:
			self._occupied = val
	
	def run(self, cmd, stdin=None):
		proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,
					 universal_newlines=True)
		#print("**********************Process id****************")
		#print(proc.pid)
		self.proc_pid = proc.pid
		return proc.communicate(input=stdin)[0]
	
	@property
	def gpu_state(self):
		return self.gpu_checker.check()
	
	@property
	def exe_cmd(self):
		return 'CUDA_VISIBLE_DEVICES={gpuid} python3 {executive}'.format(
			executive=self.executive,
			gpuid=self.gpuid
		)
	
	def check_on(self, queue):
		#print("Here Check 1 yy")
		if not self.gpu_checker.is_on():
			print("Here Check 2")
			if self._on_running is not None:
				queue.put(self._on_running)
				self._on_running = None
				print('Remote Error.')
			return False
		return True
	
	def remote_executer(self, idx, expdir, queue):
		self.occupied = True
		cmd = self.exe_cmd
		print('{}: {} {}'.format(self.remote, cmd, expdir), file=stderr)
		result = self.run(cmd, stdin=expdir)
		#ipdb.set_trace()
		try:
			result = str(result).split('\n')
			used_time = result[-3]
			result = result[-2]
			assert result.startswith('valid performance: ') and used_time.startswith('running time: '), \
				'Invalid return: %s, %s' % (used_time, result)
			used_time = used_time[len('running time: '):]
			used_time = float(used_time) / 60  # minutes
			result = result[len('valid performance: '):]
			print("**********************Putting queue*******************")
			print(queue.qsize())
			result = float(result)
			queue.put([idx, (result, used_time)])
			print("**********************Printing queue*******************")
			print(queue.qsize())
			print('{}th task: {} is successfully executed, result is {}, using {} min.'.
				  format(idx, expdir, result, used_time), file=stderr)
		except Exception:
			queue.put([idx, expdir])
			print('{}th task: {} fails, with return: %s.'.format(idx, expdir, result), file=stderr)

		#os.kill(pid,signal.SIGKILL)

		self.occupied = False
		self.check_on(queue)
	
	def execute(self, idx, expdir, queue):
		if self.occupied or not self.gpu_state:
			queue.put([idx, expdir])
			print("*********************Queue Waiting*******************")
			print(queue.qsize())
		else:
			self._on_running = [idx, expdir]
			thr = Thread(target=self.remote_executer, args=(idx, expdir, queue))
			thr.start()
			self._on_running = None
			print("*********************Queue Starting*******************")
			print(queue.qsize())


class ClusterController:
	def __init__(self, config_list):
		#ipdb.set_trace()
		self.cluster = [RemoteController(*config) for config in config_list]
		self._pt = 0
	
	def choice(self, queue):
		remotes_available, occupy_num = self.get_available(queue)
		print("Here Check 5 yy")
		while occupy_num >= max_running_machine:
			sleep(0.5)
			remotes_available, occupy_num = self.get_available(queue)
		while not remotes_available[self._pt]:
			self._pt = (self._pt + 1) % len(self.cluster)
		print("Here Check 6 yy")
		choose_remote = self.cluster[self._pt]
		self._pt = (self._pt + 1) % len(self.cluster)
		return choose_remote
		# return random.choice(self.cluster)
	
	def get_available(self, queue):
		remotes_available = [False] * len(self.cluster)
		occupy_num = len(self.cluster)
		#print("Here Check 7 yy")
		for _i, remote in enumerate(self.cluster):
			#print("Here Check 8 yy")
			if not remote.check_on(queue):
				occupy_num -= 1
				continue
			if not remote.occupied:
				remotes_available[_i] = True
				occupy_num -= 1

		return remotes_available, occupy_num
	
	def execute(self, idx, expdir, queue):
		print("Here Check 9 yy")
		self.choice(queue).execute(idx, expdir, queue)


def run_tasks(config_list, expdir_list):
	controller = ClusterController(config_list)
	result_list = [None for _ in expdir_list]
	
	queue = Queue()
	for idx, expdir in enumerate(expdir_list):
		queue.put([idx, expdir])
	print("Here Check 10 yy")
	remained = len(result_list)
	print(remained)
	while remained > 0:
		idx, val = queue.get()
		print(idx)
		print(val)
		print("Here Check 11 yy")
		if isinstance(val, str):
			# expdir, need to execute
			print("Here Check 14 yy")
			controller.execute(idx, val, queue)
			print("Here Check 15 yy")
		elif isinstance(val, tuple):
			# result, need to be put in result_list
			result_list[idx] = val
			remained -= 1
			print("Here Check 16 yy")
	return result_list


def run(task_list):
	with open(config_file, 'r') as f:
		config_list = json.load(f)
	print("Here Check 12 yy")
	expdir_list = [expdir for expdir, *_ in task_list]
	result_list = run_tasks(config_list, expdir_list)
	for idx, _ in enumerate(task_list):
		task_list[idx].append(result_list[idx])
		print("Here Check 13 yy")
