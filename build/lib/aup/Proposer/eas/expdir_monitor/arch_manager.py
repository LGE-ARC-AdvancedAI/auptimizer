"""
Manage the folder for architecture search
"""
import os
import subprocess
import json
import pickle
import numpy as np
from ..data_providers.utils import get_data_provider_by_name
from .expdir_monitor import ExpdirMonitor
from ..expdir_monitor import distributed


class NetPool:
	def __init__(self, path):
		self.path = os.path.realpath(path)
		os.makedirs(self.path, exist_ok=True)
		
		self.net_str2id = {}
		self.net_id2val = {}
		self.running_set = {'stone': 0}
		
		self.on_load()
	
	@property
	def str2id_path(self):
		return '%s/net.str2id' % self.path
	
	@property
	def id2val_path(self):
		return '%s/net.id2val' % self.path
	
	def on_load(self):
		if os.path.isfile(self.str2id_path):
			self.net_str2id = json.load(open(self.str2id_path, 'r'))
		if os.path.isfile(self.id2val_path):
			net_id2val = json.load(open(self.id2val_path, 'r'))
			for key in net_id2val:
				self.net_id2val[int(key)] = net_id2val[key]
		to_rename = []
		for folder in os.listdir(self.path):
			if folder.startswith('#'):
				out_file = '%s/%s/output' % (self.path, folder)
				if not os.path.isfile(out_file):
					subprocess.run(['rm', '-rf', os.path.join(self.path, folder)])
				else:
					net_str = json.load(open('%s/%s/net.str' % (self.path, folder), 'r'))['net_str']
					if self.net_str2id.get(net_str) is None:
						record = json.load(open(out_file, 'r'))
						net_val = float(record['valid_acc'])
						net_id = self.add_net(net_str, net_val)
						folder_path = self.get_net_folder(net_id)
					else:
						net_id = self.net_str2id[net_str]
						folder_path = self.get_net_folder(net_id)
					if folder_path != folder:
						to_rename.append([folder, folder_path])
		for src_folder, dst_folder in to_rename:
			src_folder = os.path.join(self.path, src_folder)
			dst_folder = os.path.join(self.path, dst_folder)
			os.rename(src_folder, dst_folder)
	
	def add_net(self, net_str, net_val):
		assert self.net_str2id.get(net_str) is None, '%s exists' % net_str
		net_id = net_str.__hash__()
		while net_id in self.net_id2val:
			net_id += 1
		self.net_str2id[net_str] = net_id
		self.net_id2val[net_id] = net_val
		return net_id
	
	def get_net_val(self, net_str):
		net_id = self.net_str2id.get(net_str)
		if net_id is None:
			if net_str in self.running_set:
				running_id = self.running_set[net_str]
			else:
				running_id = net_str.__hash__()
				while running_id in self.running_set.values():
					running_id += 1
				self.running_set[net_str] = running_id
			net_folder = '%s/#Running_%s' % (self.path, running_id)
			return None, net_folder
		else:
			net_val = self.net_id2val[net_id]
			net_folder = '%s/%s' % (self.path, self.get_net_folder(net_id))
			return net_val, net_folder
	
	def on_running_finished(self, net_str, net_folder, net_val):
		net_id = self.add_net(net_str, net_val)
		# folder_path = self.get_net_folder(net_id)
		# self.running_set.pop(net_str)
		# os.rename(net_folder, os.path.join(self.path, folder_path))
	
	def save(self):
		json.dump(self.net_str2id, open(self.str2id_path, 'w'), indent=4)
		json.dump(self.net_id2val, open(self.id2val_path, 'w'), indent=4)
	
	@staticmethod
	def get_net_folder(net_id):
		return '#%s' % net_id
		

class ArchManager:
	def __init__(self, start_net_path, arch_path, net_pool_path):
		self.start_net_monitor = ExpdirMonitor(start_net_path)

		self.start_net_config, self.data_provider = None, None
		self.net_pool = NetPool(net_pool_path)
		
		self.arch_path = os.path.realpath(arch_path)
		os.makedirs(self.arch_path, exist_ok=True)
		
		self.episode = 0
		self.net_val_wrt_episode = []
		
		self.val_log_writer = open(self.val_logs_path, 'a')
		self.net_log_writer = open(self.net_logs_path, 'a')
		self.on_load()
	
	@property
	def meta_controller_path(self):
		return '%s/controller' % self.arch_path

	@property
	def val_logs_path(self):
		return '%s/val.log' % self.arch_path
	
	@property
	def net_logs_path(self):
		return '%s/net.log' % self.arch_path
	
	def on_load(self):
		if os.path.isfile(self.val_logs_path):
			with open(self.val_logs_path, 'r') as fin:
				for line in fin.readlines():
					line = line[:-1]
					self.episode += 1
					net_val_list = line.split('\t')[4:]
					net_val_list = [float(net_val) for net_val in net_val_list]
					self.net_val_wrt_episode.append(net_val_list)
				
	def get_start_net(self, copy=False):
		if self.start_net_config is None:
			# prepare start net
			print('Load start net from %s' % self.start_net_monitor.expdir)
			init = self.start_net_monitor.load_init()
			dataset = 'C10+' if init is None else init.get('dataset', 'C10+')
			run_config = self.start_net_monitor.load_run_config(print_info=True, dataset=dataset)
			run_config.renew_logs = False

			net_config, model_name = self.start_net_monitor.load_net_config(init, print_info=True)
			self.data_provider = get_data_provider_by_name(run_config.dataset, run_config.get_config())
			self.start_net_config = [net_config, run_config, model_name]
		if copy:
			net_config, run_config, model_name = self.start_net_config[:3]
			return [
				net_config.copy(), run_config.copy(), model_name
			]
		else:
			return self.start_net_config
	
	@staticmethod
	def prepare_folder_for_valid(net_str, net_config, run_config, exp_dir):
		os.makedirs(exp_dir, exist_ok=True)
		monitor = ExpdirMonitor(exp_dir)
		json.dump(net_config.get_config(), open(monitor.net_config_path, 'w'), indent=4)
		json.dump(run_config.get_config(), open(monitor.run_config_path, 'w'), indent=4)
		pickle.dump(net_config.renew_init(None), open(monitor.init, 'wb'))
		json.dump({'net_str': net_str}, open(os.path.join(monitor.expdir, 'net.str'), 'w'), indent=4)
	
	def get_net_tasks(self, net_str_list, net_configs, run_configs):
		net_val_list = [-1] * len(net_str_list)
		
		to_run = {}
		for _i, net_str in enumerate(net_str_list):
			net_val, net_folder = self.net_pool.get_net_val(net_str)
			if net_val is None:
				if net_folder in to_run: to_run[net_folder] += [_i]
				else:
					to_run[net_folder] = [_i]
					self.prepare_folder_for_valid(net_str, net_configs[_i], run_configs[_i], net_folder)
			else:
				net_val_list[_i] = net_val
		
		task_list = [[net_folder, to_run[net_folder]] for net_folder in to_run]
		return task_list
		#distributed.run(task_list)
		"""episode_total_running_time = 0
		for net_folder, idx, net_val in task_list:
			net_str = net_str_list[idx[0]]
			net_val, running_time = net_val
			episode_total_running_time += running_time
			self.net_pool.on_running_finished(net_str, net_folder, net_val)
			for _id in idx:
				net_val_list[_id] = net_val
		self.log_nets(net_str_list, episode_total_running_time)
		self.net_pool.save()
		return net_val_list"""
	
	def val2reward(self, net_val_list, func=None):
		rewards = []
		for net_val in net_val_list:
			if func is None:
				rewards.append(net_val)
			elif func == 'tan':
				reward = np.tan(net_val * np.pi / 2)
				rewards.append(reward)
			else:
				raise NotImplementedError
		return rewards
		
	def reward(self, net_val_list, reward_config):
		rewards = self.val2reward(net_val_list, reward_config.get('func'))
		rewards = np.array(rewards)
		# baseline function
		decay = reward_config['decay']
		if 'exp_moving_avg' not in self.__dict__:
			self.exp_moving_avg = 0
			for old_net_val_list in self.net_val_wrt_episode[:-1]:
				old_rewards = self.val2reward(old_net_val_list, reward_config.get('func'))
				self.exp_moving_avg += decay * (np.mean(old_rewards) - self.exp_moving_avg)
		self.exp_moving_avg += decay * (np.mean(rewards) - self.exp_moving_avg)
		return rewards - self.exp_moving_avg
	
	def log_nets(self, net_str_list, running_time, print_info=True):
		net_id_list = [self.net_pool.net_str2id[net_str] for net_str in net_str_list]
		nets_num = len(net_id_list)
		new_nets_num = len(set(net_id_list))
		
		net_val_list = [self.net_pool.net_id2val[net_id] for net_id in net_id_list]
		mean_val, max_val = np.mean(net_val_list), np.max(net_val_list)
		self.net_log_writer.write('%d.\t nets=%d (total=%d)\t%s\n' % (self.episode, new_nets_num, nets_num,
														'\t'.join([str(net_id) for net_id in net_id_list])))
		log_str = '%d.\t nets=%d (total=%d)\t mean_val=%s (max_val=%s)\t using %s(min)\t%s' % \
				  (self.episode + 1, new_nets_num, nets_num, mean_val, max_val, running_time,
				   '\t'.join([str(net_val) for net_val in net_val_list]))
		if print_info:
			print(log_str)
		self.val_log_writer.write(log_str + '\n')
		
		self.val_log_writer.flush()
		self.net_log_writer.flush()
		self.net_val_wrt_episode.append(net_val_list)
		self.episode += 1
