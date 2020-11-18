from ..expdir_monitor.arch_manager import ArchManager
from ..meta_controller.base_controller import Vocabulary, EncoderNet, WiderActorNet, DeeperActorNet
from ..meta_controller.rl_controller import ReinforceNet2NetController
from time import gmtime, strftime, time
from datetime import timedelta
from ..models.layers import ConvLayer, FCLayer, PoolLayer
import re
import numpy as np


def get_net_str(net_configs):
	if isinstance(net_configs, list):
		if len(net_configs) == 1:
			net_config = net_configs[0]
			net_str = []
			for layer in net_config.layer_cascade.layers[:-1]:
				if isinstance(layer, ConvLayer):
					net_str.append('conv-%d-%d' % (layer.filter_num, layer.kernel_size))
				elif isinstance(layer, FCLayer):
					net_str.append('fc-%d' % layer.units)
				else:
					net_str.append('pool')
			return ['_'.join(net_str)]
		else:
			net_str_list = []
			for net_config in net_configs:
				net_str_list += get_net_str([net_config])
			return net_str_list
	else:
		return get_net_str([net_configs])[0]


def get_net_seq(net_configs, vocabulary, num_steps):
	net_str_list = get_net_str(net_configs)
	net_seq = []
	seq_len = []
	for net_str in net_str_list:
		net_str = re.split('_', net_str)
		net_code = vocabulary.get_code(net_str)
		_len = len(net_code)
		net_code += [vocabulary.pad_code for _ in range(len(net_code), num_steps)]
		net_seq.append(net_code)
		seq_len.append(_len)
	return np.array(net_seq), np.array(seq_len)


def get_block_layer_num(net_configs):
	if len(net_configs) == 1:
		net_config = net_configs[0]
		block_layer_num = []
		_count = 0
		for layer in net_config.layer_cascade.layers[:-1]:
			if isinstance(layer, PoolLayer):
				block_layer_num.append(_count)
				_count = 0
			else:
				_count += 1
		block_layer_num.append(_count)
		return np.array([block_layer_num])
	else:
		block_layer_num = []
		for net_config in net_configs:
			block_layer_num.append(get_block_layer_num([net_config]))
		return np.concatenate(block_layer_num, axis=0)


def apply_wider_decision(wider_decision, net_configs, filter_num_list, units_num_list, noise):
	if len(net_configs) == 1:
		decision = wider_decision[0]
		net_config = net_configs[0]
		decision_mask = []
		for _i, layer in enumerate(net_config.layer_cascade.layers[:-1]):
			if isinstance(layer, ConvLayer):
				if layer.filter_num >= filter_num_list[-1]:
					decision_mask.append(0.0)
				else:
					decision_mask.append(1.0)
					if decision[_i]:
						new_filter_number = layer.filter_num
						for fn in filter_num_list:
							if fn > new_filter_number:
								new_filter_number = fn
								break
						net_config.widen(
							layer_idx=_i, new_width=new_filter_number, noise=noise
						)
			elif isinstance(layer, FCLayer):
				if layer.units >= units_num_list[-1]:
					decision_mask.append(0.0)
				else:
					decision_mask.append(1.0)
					if decision[_i]:
						new_units_num = layer.units
						for un in units_num_list:
							if un > new_units_num:
								new_units_num = un
								break
						net_config.widen(
							layer_idx=_i, new_width=new_units_num, noise=noise,
						)
			else:
				decision_mask.append(0.0)
		decision_mask += [0.0] * (len(decision) - len(decision_mask))
		return np.array([decision_mask])
	else:
		decision_mask = []
		for _i, net_config in enumerate(net_configs):
			decision = wider_decision[_i]
			mask = apply_wider_decision([decision], [net_config], filter_num_list, units_num_list, noise)
			decision_mask.append(mask)
		return np.concatenate(decision_mask, axis=0)


def apply_deeper_decision(deeper_decision, net_configs, kernel_size_list, noise):
	if len(net_configs) == 1:
		decision = deeper_decision[0]
		net_config = net_configs[0]

		block_decision, layer_idx_decision, ks_decision = decision
		decision_mask = [1.0, 1.0]
		block_idx, _pt = 0, 0
		to_set_layers = []
		for _i, layer in enumerate(net_config.layer_cascade.layers[:-1]):
			if _pt == block_decision:
				real_layer_idx = _i + layer_idx_decision
				prev_layer = net_config.layer_cascade.layers[real_layer_idx]
				if isinstance(prev_layer, ConvLayer):
					if 'conv' in net_config.drop_scheme['type']:
						keep_prob = net_config.drop_scheme.get('conv_drop', 1.0)
					else:
						keep_prob = 1.0
					decision_mask.append(1.0)
					ks = kernel_size_list[ks_decision]
					new_layer, prev_layer = net_config.deepen(
						layer_idx=real_layer_idx,
						new_layer_config={'name': 'conv', 'kernel_size': ks, 'pre_activation': False,
										  'keep_prob': keep_prob},
					)
					to_set_layers.append([new_layer, prev_layer])
				elif isinstance(prev_layer, FCLayer):
					if 'fc' in net_config.drop_scheme['type']:
						keep_prob = net_config.drop_scheme.get('fc_drop', 1.0)
					else:
						keep_prob = 1.0
					decision_mask.append(0.0)
					new_layer, prev_layer = net_config.deepen(
						layer_idx=real_layer_idx,
						new_layer_config={'name': 'fc', 'keep_prob': keep_prob},
					)
					to_set_layers.append([new_layer, prev_layer])
				else:
					raise ValueError
				break
			if isinstance(layer, PoolLayer):
				_pt += 1
		return np.array([decision_mask]), to_set_layers
	else:
		decision_mask = []
		to_set_layers = []
		for _i, net_config in enumerate(net_configs):
			decision = deeper_decision[_i]
			mask, to_set = apply_deeper_decision([decision], [net_config], kernel_size_list, noise)
			decision_mask.append(mask)
			to_set_layers.append(to_set)
		return np.concatenate(decision_mask, axis=0), to_set_layers
	

def arch_search_convnet(start_net_path, arch_search_folder, net_pool_folder, max_episodes, random=False):
	filter_num_list = [_i for _i in range(4, 44, 4)]
	units_num_list = [_i for _i in range(8, 88, 8)]
	# filter_num_list = [16, 32, 64, 96, 128, 192, 256, 320, 384, 448, 512, 576, 640]
	# units_num_list = [64, 128, 256, 384, 512, 640, 768, 896, 1024, 1152, 1280]
	kernel_size_list = [1, 3, 5]
	
	# encoder config
	layer_token_list = ['conv-%d-%d' % (f, k) for f in filter_num_list for k in [1, 3, 5]]
	layer_token_list += ['fc-%d' % u for u in units_num_list] + ['pool']
	encoder_config = {
		'num_steps': 50,
		'vocab': Vocabulary(layer_token_list),
		'embedding_dim': 16,
		'rnn_units': 50,
		'rnn_type': 'bi_lstm',
		'rnn_layers': 1,
	}
	
	# wider actor config
	wider_actor_config = {
		'out_dim': 1,
		'num_steps': encoder_config['num_steps'],
		'net_type': 'simple',
		'net_config': None,
	}
	
	# deeper actor config
	deeper_actor_config = {
		'decision_num': 3,
		'out_dims': [5, 10, len(kernel_size_list)],
		'embedding_dim': encoder_config['embedding_dim'],
		'cell_type': 'lstm',
		'rnn_layers': 1,
		'attention_config': None,
	}
	
	# meta-controller config
	entropy_penalty = 1e-5
	learning_rate = 2e-3
	opt_config = ['adam', {}]
	
	# net2net noise config
	noise_config = {
		'wider': {'type': 'normal', 'ratio': 1e-2},
		'deeper': {'type': 'normal', 'ratio': 1e-3},
	}
	
	# episode config
	episode_config = {
		'batch_size': 10,
		'wider_action_num': 4,
		'deeper_action_num': 5,
	}
	
	# arch search run config
	arch_search_run_config = {
		'n_epochs': 20,
		'init_lr': 0.02,
		'validation_size': 5000,
		'other_lr_schedule': {'type': 'cosine'},
		'batch_size': 64,
		'include_extra': False,
	}
	
	# reward config
	reward_config = {
		'func': 'tan',
		'decay': 0.95,
	}
	
	arch_manager = ArchManager(start_net_path, arch_search_folder, net_pool_folder)
	_, run_config, _ = arch_manager.get_start_net()
	run_config.update(arch_search_run_config)
	
	encoder = EncoderNet(**encoder_config)
	wider_actor = WiderActorNet(**wider_actor_config)
	deeper_actor = DeeperActorNet(**deeper_actor_config)
	meta_controller = ReinforceNet2NetController(arch_manager.meta_controller_path, entropy_penalty,
												 encoder, wider_actor, deeper_actor, opt_config)
	meta_controller.load()
	
	for _i in range(arch_manager.episode + 1, max_episodes + 1):
		print('episode. %d start. current time: %s' % (_i, strftime("%a, %d %b %Y %H:%M:%S", gmtime())))
		start_time = time()
		
		nets = [arch_manager.get_start_net(copy=True) for _ in range(episode_config['batch_size'])]
		net_configs = [net_config for net_config, _, _ in nets]
		
		# feed_dict for update the controller
		wider_decision_trajectory, wider_decision_mask = [], []
		deeper_decision_trajectory, deeper_decision_mask = [], []
		deeper_block_layer_num = []
		encoder_input_seq, encoder_seq_len = [], []
		wider_seg_deeper = 0
		
		if random:
			# random search
			remain_wider_num = episode_config['wider_action_num']
			remain_deeper_num = episode_config['deeper_action_num']
			while remain_wider_num > 0 or remain_deeper_num > 0:
				rand_idx = np.random.randint(0, remain_wider_num + remain_deeper_num)
				if rand_idx < remain_wider_num:
					wider_decision = np.random.choice(2, [episode_config['batch_size'], encoder.num_steps])
					apply_wider_decision(wider_decision, net_configs, filter_num_list, units_num_list, noise_config)
					remain_wider_num -= 1
				else:
					block_layer_num = get_block_layer_num(net_configs)
					deeper_decision = np.zeros([episode_config['batch_size'], deeper_actor.decision_num], np.int)
					deeper_decision[:, 0] = np.random.choice(deeper_actor.out_dims[0], deeper_decision[:, 0].shape)
					for _k, block_decision in enumerate(deeper_decision[:, 0]):
						available_layer_num = block_layer_num[_k, block_decision]
						deeper_decision[_k, 1] = np.random.randint(0, available_layer_num)
					deeper_decision[:, 2] = np.random.choice(deeper_actor.out_dims[2],  deeper_decision[:, 2].shape)
					
					_, to_set_layers = apply_deeper_decision(deeper_decision, net_configs,
					                                         kernel_size_list, noise_config)
					for _k, net_config in enumerate(net_configs):
						net_config.set_identity4deepen(to_set_layers[_k], arch_manager.data_provider,
						                               batch_size=64, batch_num=1, noise=noise_config)
					remain_deeper_num -= 1
		else:
			# on-policy training
			for _j in range(episode_config['wider_action_num']):
				input_seq, seq_len = get_net_seq(net_configs, encoder.vocab, encoder.num_steps)
				wider_decision, wider_probs = meta_controller.sample_wider_decision(input_seq, seq_len)
				# modify net config according to wider_decision
				wider_mask = apply_wider_decision(wider_decision, net_configs, filter_num_list,
												  units_num_list, noise_config)
				
				wider_decision_trajectory.append(wider_decision)
				wider_decision_mask.append(wider_mask)
				wider_seg_deeper += len(net_configs)
				encoder_input_seq.append(input_seq)
				encoder_seq_len.append(seq_len)
			
			to_set_layers = [[] for _ in range(episode_config['batch_size'])]
			for _j in range(episode_config['deeper_action_num']):
				input_seq, seq_len = get_net_seq(net_configs, encoder.vocab, encoder.num_steps)
				block_layer_num = get_block_layer_num(net_configs)
				deeper_decision, deeper_probs = meta_controller.sample_deeper_decision(input_seq, seq_len,
				                                                                       block_layer_num)
				# modify net config according to deeper_decision
				deeper_mask, to_set = apply_deeper_decision(deeper_decision, net_configs,
				                                            kernel_size_list, noise_config)
				for _k in range(episode_config['batch_size']):
					to_set_layers[_k] += to_set[_k]
				
				deeper_decision_trajectory.append(deeper_decision)
				deeper_decision_mask.append(deeper_mask)
				deeper_block_layer_num.append(block_layer_num)
				encoder_input_seq.append(input_seq)
				encoder_seq_len.append(seq_len)
			
			for _k, net_config in enumerate(net_configs):
				net_config.set_identity4deepen(to_set_layers[_k], arch_manager.data_provider,
				                               batch_size=64, batch_num=1, noise=noise_config)
			# prepare feed dict
			encoder_input_seq = np.concatenate(encoder_input_seq, axis=0)
			encoder_seq_len = np.concatenate(encoder_seq_len, axis=0)
			if episode_config['wider_action_num'] > 0:
				wider_decision_trajectory = np.concatenate(wider_decision_trajectory, axis=0)
				wider_decision_mask = np.concatenate(wider_decision_mask, axis=0)
			else:
				wider_decision_trajectory = -np.ones([1, meta_controller.encoder.num_steps])
				wider_decision_mask = -np.ones([1, meta_controller.encoder.num_steps])
			if episode_config['deeper_action_num'] > 0:
				deeper_decision_trajectory = np.concatenate(deeper_decision_trajectory, axis=0)
				deeper_decision_mask = np.concatenate(deeper_decision_mask, axis=0)
				deeper_block_layer_num = np.concatenate(deeper_block_layer_num, axis=0)
			else:
				deeper_decision_trajectory = - np.ones([1, meta_controller.deeper_actor.decision_num])
				deeper_decision_mask = - np.ones([1, meta_controller.deeper_actor.decision_num])
				deeper_block_layer_num = np.ones([1, meta_controller.deeper_actor.out_dims[0]])
		
		run_configs = [run_config] * len(net_configs)
		net_str_list = get_net_str(net_configs)
		
		net_vals = arch_manager.get_net_vals(net_str_list, net_configs, run_configs)
		rewards = arch_manager.reward(net_vals, reward_config)
		
		rewards = np.concatenate([rewards for _ in range(episode_config['wider_action_num'] +
														 episode_config['deeper_action_num'])])
		rewards /= episode_config['batch_size']
		
		# update the agent
		if not random:
			meta_controller.update_controller(learning_rate, wider_seg_deeper, wider_decision_trajectory,
											  wider_decision_mask, deeper_decision_trajectory, deeper_decision_mask,
											  rewards, deeper_block_layer_num, encoder_input_seq, encoder_seq_len)
			
			meta_controller.save()
		# episode end
		time_per_episode = time() - start_time
		seconds_left = int((max_episodes - _i) * time_per_episode)
		print('Time per Episode: %s, Est. complete in: %s' % (
			str(timedelta(seconds=time_per_episode)),
			str(timedelta(seconds=seconds_left))))
