from .dense_net import DenseNetConfig, DenseNet
from .convnet import SimpleConvnetConfig, SimpleConvnet
import numpy as np


def get_model_config_by_name(name):
	if name == 'DenseNet':
		return DenseNetConfig
	elif name == 'SimpleConvnet':
		return SimpleConvnetConfig
	else:
		raise ValueError('Unknown model type %s' % name)


def get_model_by_name(name):
	if name == 'DenseNet':
		return DenseNet
	elif name == 'SimpleConvnet':
		return SimpleConvnet
	else:
		raise ValueError('Unknown model type %s' % name)


class RunConfig:
	def __init__(self, batch_size, n_epochs, init_lr, reduce_lr_epochs, reduce_lr_factors, opt_config,
				 dataset, validation_size, validation_frequency, shuffle, normalization, should_save_logs,
				 should_save_model, renew_logs=False, other_lr_schedule=None, include_extra=True, **kwargs):
		
		self.batch_size = batch_size
		self.n_epochs = n_epochs
		self.init_lr = init_lr
		self.reduce_lr_epochs = reduce_lr_epochs
		self.reduce_lr_factors = reduce_lr_factors
		self.opt_config = opt_config
		self.dataset = dataset
		self.validation_size = validation_size
		self.validation_frequency = validation_frequency
		self.shuffle = shuffle
		self.normalization = normalization
		self.should_save_logs = should_save_logs
		self.should_save_model = should_save_model
		self.renew_logs = renew_logs
		self.other_lr_schedule = other_lr_schedule
		self.include_extra = include_extra
	
	def get_config(self):
		return self.__dict__
	
	def update(self, new_config):
		self.__dict__.update(new_config)
	
	def copy(self):
		return RunConfig(**self.get_config())
		
	def learning_rate(self, epoch):
		if self.other_lr_schedule is None or self.other_lr_schedule.get('type') is None:
			lr = self.init_lr
			for reduce_lr_epoch, reduce_factor in zip(self.reduce_lr_epochs, self.reduce_lr_factors):
				if epoch >= reduce_lr_epoch * self.n_epochs:
					lr /= reduce_factor
		else:
			if self.other_lr_schedule['type'] == 'cosine':
				lr_max = self.init_lr
				lr_min = self.other_lr_schedule.get('lr_min', 0)
				lr = lr_min + 0.5 * (lr_max - lr_min) * (1 + np.cos((epoch - 1) / self.n_epochs * np.pi))
			else:
				raise ValueError('Do not support %s' % self.other_lr_schedule['type'])
		return lr

	@staticmethod
	def get_default_run_config(dataset='C10+'):
		if dataset in ['C10', 'C10+', 'C100', 'C100+']:
			run_config = {
				'batch_size': 64,
				'n_epochs': 30,
				'init_lr': 0.1,
				'reduce_lr_epochs': [0.5, 0.75],  # epochs * 0.5, epochs * 0.75
				'reduce_lr_factors': [10, 10],
				'opt_config': ['momentum', {'momentum': 0.9, 'use_nesterov': True}],
				'dataset': dataset,  # choices = [C10, C10+, C100, C100+]
				'validation_size': None,  # None or int
				'validation_frequency': 10,
				'shuffle': 'every_epoch',  # None, once_prior_train, every_epoch
				'normalization': 'by_channels',  # None, divide_256, divide_255, by_channels
				'should_save_logs': True,
				'should_save_model': True,
				'renew_logs': True,
				'other_lr_schedule': {'type': 'cosine'},  # None, or cosine
			}
		elif dataset in ['SVHN']:
			run_config = {
				'batch_size': 64,
				'n_epochs': 40,
				'init_lr': 0.1,
				'reduce_lr_epochs': [0.5, 0.75],  # epochs * 0.5, epochs * 0.75
				'reduce_lr_factors': [10, 10],
				'opt_config': ['momentum', {'momentum': 0.9, 'use_nesterov': True}],
				'dataset': dataset,  # choices = [C10, C10+, C100, C100+]
				'validation_size': None,  # None or int
				'validation_frequency': 1,
				'shuffle': True,
				'normalization': 'divide_255',  # None, divide_256, divide_255, by_channels
				'should_save_logs': True,
				'should_save_model': True,
				'renew_logs': True,
				'other_lr_schedule': {'type': 'cosine'},  # None, or cosine
				'include_extra': False,
			}
		else:
			raise ValueError
		return run_config

