import json
import os
import subprocess
from ..models.utils import RunConfig, get_model_config_by_name, get_model_by_name
from ..data_providers.utils import get_data_provider_by_name
import pickle


class ExpdirMonitor:
	def __init__(self, expdir):
		self.expdir = os.path.realpath(expdir)
		os.makedirs(self.expdir, exist_ok=True)

	@property
	def logs(self): return '%s/logs' % self.expdir
	
	@property
	def checkpoint(self): return '%s/checkpoint' % self.expdir
	
	@property
	def snapshot(self): return '%s/snapshot' % self.expdir
	
	@property
	def output(self): return '%s/output' % self.expdir
	
	@property
	def init(self): return '%s/init' % self.expdir
	
	@property
	def run_config_path(self): return '%s/run.config' % self.expdir
	
	@property
	def net_config_path(self): return '%s/net.config' % self.expdir
	
	def load_run_config(self, print_info=False, dataset='C10+'):
		if os.path.isfile(self.run_config_path):
			run_config = json.load(open(self.run_config_path, 'r'))
		else:
			print('Use Default Run Config for %s' % dataset)
			run_config = RunConfig.get_default_run_config(dataset)
		if print_info:
			print('Run config:')
			for k, v in run_config.items():
				print('\t%s: %s' % (k, v))
		return RunConfig(**run_config)
	
	def load_init(self):
		init_path = '%s/init' % self.expdir
		if os.path.isfile(init_path):
			return pickle.load(open(self.init, 'rb'))
		else:
			return None

	def load_net_config(self, init, print_info=False):
		assert os.path.isfile(self.net_config_path), \
			'Net configs do not exist in the given expdir <%s>' % self.expdir
		net_config_json = json.load(open(self.net_config_path, 'r'))
		net_config = get_model_config_by_name(net_config_json['name'])()
		net_config.set_net_from_config(net_config_json, init=init, print_info=print_info)
		return net_config, net_config_json['name']
	
	def run(self, pure=True, restore=False, test=False, valid=False, valid_size=-1):
		if not restore:
			_clear_files = ['logs', 'checkpoint', 'snapshot', 'output']
			for file in _clear_files:
				subprocess.run(['rm', '-rf', os.path.join(self.expdir, file)])
		init = self.load_init()
		dataset = 'C10+' if init is None else init.get('dataset', 'C10+')
		run_config = self.load_run_config(print_info=(not pure), dataset=dataset)
		run_config.renew_logs = False
		if valid_size > 0:
			run_config.validation_size = valid_size
		
		data_provider = get_data_provider_by_name(run_config.dataset, run_config.get_config())
		net_config, model_name = self.load_net_config(init, print_info=(not pure))
		model = get_model_by_name(model_name)(self.expdir, data_provider, run_config, net_config, pure=pure)
		start_epoch = 1
		if restore:
			model.load_model()
			epoch_info_file = '%s/checkpoint/epoch.info' % self.expdir
			if os.path.isfile(epoch_info_file):
				start_epoch = json.load(open(epoch_info_file, 'r'))['epoch']
				if not pure:
					print('start epoch: %d' % start_epoch)
		if test:
			print('Testing...')
			loss, accuracy = model.test(data_provider.test, batch_size=200)
			print('mean cross_entropy: %f, mean accuracy: %f' % (loss, accuracy))
			json.dump({'test_loss': '%s' % loss, 'test_acc': '%s' % accuracy}, open(self.output, 'w'))
		elif valid:
			print('validating...')
			loss, accuracy = model.test(data_provider.validation, batch_size=200)
			print('mean cross_entropy: %f, mean accuracy: %f' % (loss, accuracy))
			json.dump({'valid_loss': '%s' % loss, 'valid_acc': '%s' % accuracy}, open(self.output, 'w'))
		elif pure:
			model.pure_train()
			loss, accuracy = model.test(data_provider.validation, batch_size=200)
			json.dump({'valid_loss': '%s' % loss, 'valid_acc': '%s' % accuracy}, open(self.output, 'w'))
			model.save_init(self.snapshot, print_info=(not pure))
			model.save_config(self.expdir, print_info=(not pure))
		else:
			# train the model
			print('Data provider train images: ', data_provider.train.num_examples)
			model.train_all_epochs(start_epoch)
			print('Data provider test images: ', data_provider.test.num_examples)
			print('Testing...')
			loss, accuracy = model.test(data_provider.test, batch_size=200)
			print('mean cross_entropy: %f, mean accuracy: %f' % (loss, accuracy))
			json.dump({'test_loss': '%s' % loss, 'test_acc': '%s' % accuracy}, open(self.output, 'w'))
			model.save_init(self.snapshot, print_info=(not pure))
			model.save_config(self.expdir, print_info=(not pure))
		return accuracy
