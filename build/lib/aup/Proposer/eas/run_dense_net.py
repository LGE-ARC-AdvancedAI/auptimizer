import argparse
import os
from models.dense_net import DenseNet, DenseNetConfig
from data_providers.utils import get_data_provider_by_name
from models.utils import RunConfig
import json

run_config_cifar = {
	'batch_size': 64,
	'n_epochs': 30,
	'init_lr': 0.1,
	'reduce_lr_epochs': [0.5, 0.75],  # epochs * 0.5, epochs * 0.75
	'reduce_lr_factors': [10, 10],
	'opt_config': ['momentum', {'momentum': 0.9, 'use_nesterov': True}],
	'dataset': 'C10+',  # choices = [C10, C10+, C100, C100+]
	'validation_size': 10000,  # None or int
	'validation_frequency': 10,
	'shuffle': 'every_epoch',  # None, once_prior_train, every_epoch
	'normalization': 'by_channels',  # None, divide_256, divide_255, by_channels
	'should_save_logs': True,
	'should_save_model': True,
	'renew_logs': True,
	'other_lr_schedule': {'type': 'cosine'},  # None, or cosine
}

standard_net_config_cifar = {
	'model_type': 'DenseNet-BC',
	'weight_decay':  1e-4,
	'first_ratio': 2,
	'reduction': 0.5,
	'bc_ratio': 4,
	'bn_epsilon': 1e-5,
	'bn_decay': 0.9,
	'growth_rate': 4,
	'depth': 10,
	'total_blocks': 3,
	'keep_prob': 0.8,
	'pre_activation': True,
}


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--train', action='store_true')
	parser.add_argument(
		'--test', action='store_true',
		help='Test model for required dataset if pretrained model exists.')
	parser.add_argument(
		'--dataset', type=str, default='C10+', choices=['C10', 'C10+', 'C100', 'C100+'],
	)
	
	parser.add_argument('--path', type=str, default='')
	parser.add_argument('--save_config', action='store_true', help='Whether to save config in the path')
	parser.add_argument('--save_init', action='store_true')
	parser.add_argument('--load_model', action='store_true')
	
	args = parser.parse_args()
	if args.dataset in ['C10', 'C100', 'C10+', 'C100+']:
		run_config_cifar['dataset'] = args.dataset
		run_config = RunConfig(**run_config_cifar)
		net_config = standard_net_config_cifar
	else:
		raise ValueError
	if len(args.path) == 0:
		args.path = '../trained_nets/DenseNet/vs=%s_%s_%s_L=%d_K=%d_%s' % \
					(run_config.validation_size, os.uname()[1], net_config['model_type'], net_config['depth'],
					 net_config['growth_rate'], run_config.dataset)
	
	if run_config.dataset in ['C10+', 'C100+']:
		net_config['keep_prob'] = 1.0
	if standard_net_config_cifar['model_type'] == 'DenseNet':
		net_config['reduction'] = 1.0
	if args.test: args.load_model = True
	
	# print configurations
	print('Run config:')
	for k, v in run_config.get_config().items():
		print('\t%s: %s' % (k, v))
	print('Network config:')
	for k, v in net_config.items():
		print('\t%s: %s' % (k, v))
	
	print('Prepare training data...')
	data_provider = get_data_provider_by_name(run_config.dataset, run_config.get_config())
	
	# set net config
	net_config = DenseNetConfig().set_standard_dense_net(data_provider=data_provider, **net_config)
	print('Initialize the model...')
	model = DenseNet(args.path, data_provider, run_config, net_config)
	
	# save configs
	if args.save_config:
		model.save_config(args.path)
		
	if args.load_model: model.load_model()
	if args.test:
		# test
		print('Data provider test images: ', data_provider.test.num_examples)
		print('Testing...')
		loss, accuracy = model.test(data_provider.test, batch_size=200)
		print('mean cross_entropy: %f, mean accuracy: %f' % (loss, accuracy))
		json.dump({'test_loss': '%s' % loss, 'test_acc': '%s' % accuracy}, open('%s/output' % args.path, 'w'))
	elif args.train:
		# train the model
		print('Data provider train images: ', data_provider.train.num_examples)
		model.train_all_epochs()
		print('Data provider test images: ', data_provider.test.num_examples)
		print('Testing...')
		loss, accuracy = model.test(data_provider.test, batch_size=200)
		print('mean cross_entropy: %f, mean accuracy: %f' % (loss, accuracy))

		# save inits
		if args.save_init:
			model.save_init(os.path.join(args.path, 'snapshot'))
		json.dump({'test_loss': '%s' % loss, 'test_acc': '%s' % accuracy}, open('%s/output' % args.path, 'w'))
		

