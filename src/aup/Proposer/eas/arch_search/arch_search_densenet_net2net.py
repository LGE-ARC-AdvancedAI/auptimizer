from ..expdir_monitor.arch_manager import ArchManager
from ..meta_controller.base_controller import Vocabulary, EncoderNet, WiderActorNet, DeeperActorNet
from ..meta_controller.rl_controller import ReinforceNet2NetController
from time import gmtime, strftime, time
from datetime import timedelta
from ..models.dense_net import DenseBlock, TransitionBlock
import re
import numpy as np


def get_net_str(net_configs):
	if len(net_configs) == 1:
		net_config = net_configs[0]
		net_str = []
		for block in net_config.blocks:
			if isinstance(block, DenseBlock):
				block_str = []
				for miniblock in block.miniblocks:
					block_str.append('g%d' % miniblock.out_features_dim)
				block_str = '-'.join(block_str)
				net_str.append(block_str)
			else:
				net_str.append('t')
		return ['_'.join(net_str)]
	else:
		net_str_list = []
		for net_config in net_configs:
			net_str_list += get_net_str([net_config])
		return net_str_list


def get_net_seq(net_configs, vocabulary, num_steps):
	net_str_list = get_net_str(net_configs)
	net_seq = []
	seq_len = []
	for net_str in net_str_list:
		net_str = re.split('_|-', net_str)
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
		for block in net_config.blocks:
			if isinstance(block, DenseBlock):
				block_layer_num.append(len(block.miniblocks))
		return np.array([block_layer_num])
	else:
		block_layer_num = []
		for net_config in net_configs:
			block_layer_num.append(get_block_layer_num([net_config]))
		return np.concatenate(block_layer_num, axis=0)


def apply_wider_decision(wider_decision, net_configs, growth_rate_list, noise):
	if len(net_configs) == 1:
		decision = wider_decision[0]
		net_config = net_configs[0]
		_pt = 0
		decision_mask = []
		for block_idx, block in enumerate(net_config.blocks):
			if isinstance(block, DenseBlock):
				for miniblock_idx, miniblock in enumerate(block.miniblocks):
					growth_rate = miniblock.out_features_dim
					if growth_rate >= growth_rate_list[-1]:
						decision_mask.append(0.0)
					else:
						decision_mask.append(1.0)
						new_gr = growth_rate
						for gr in growth_rate_list:
							if gr > new_gr:
								new_gr = gr
								break
						if decision[_pt]:
							net_config.widen(
								loc={'block': block_idx, 'miniblock': miniblock_idx,
									 'multi-branch': 'in_bottle', 'layer': 0},
								new_width=net_config.bc_ratio * new_gr,
								noise=noise,
							)
							net_config.widen(
								loc={'block': block_idx, 'miniblock': miniblock_idx,
									 'multi-branch': 'branch', 'branch': 0, 'layer': 0},
								new_width=new_gr,
								noise=noise,
							)
					_pt += 1
			else:
				decision_mask.append(0.0)
				_pt += 1
		decision_mask += [0.0] * (len(decision) - len(decision_mask))
		return np.array([decision_mask])
	else:
		decision_mask = []
		for _i, net_config in enumerate(net_configs):
			decision = wider_decision[_i]
			mask = apply_wider_decision([decision], [net_config], growth_rate_list, noise)
			decision_mask.append(mask)
		return np.concatenate(decision_mask, axis=0)


def apply_deeper_decision(deeper_decision, net_configs, noise):
	if len(net_configs) == 1:
		decision = deeper_decision[0]
		net_config = net_configs[0]

		block_decision, layer_idx_decision = decision
		decision_mask = [1.0, 1.0]
		block_idx, _pt = 0, 0
		for _i, block in enumerate(net_config.blocks):
			if isinstance(block, DenseBlock):
				if _pt == block_decision:
					block_idx = _i
					break
				_pt += 1
		net_config.insert_miniblock(
			loc={'block': block_idx, 'miniblock': layer_idx_decision},
			miniblock_config={'bc_mode': True},
			noise=noise,
		)
		return np.array([decision_mask])
	else:
		decision_mask = []
		for _i, net_config in enumerate(net_configs):
			decision = deeper_decision[_i]
			mask = apply_deeper_decision([decision], [net_config], noise)
			decision_mask.append(mask)
		return np.concatenate(decision_mask, axis=0)


def widen_transition(net_configs, noise):
	for net_config in net_configs:
		new_out_dim = int(net_config.average_growth_rate * net_config.first_ratio)
		if new_out_dim > net_config.blocks[0].out_features_dim:
			net_config.widen(
				loc={'block': 0, 'layer': 0},
				new_width=new_out_dim,
				noise=noise,
			)
		out_features_dim = new_out_dim
		for _i, block in enumerate(net_config.blocks[2:-1], 2):
			if isinstance(block, TransitionBlock):
				new_out_dim = int(net_config.blocks[_i - 1].out_features_dim(net_config.blocks[_i - 2].out_features_dim)
								  * net_config.reduction)
				if new_out_dim > block.out_features_dim:
					net_config.widen(
						loc={'block': _i, 'layer': 0},
						new_width=new_out_dim,
						noise=noise,
					)
				out_features_dim = block.out_features_dim
			else:
				out_features_dim = block.out_features_dim(out_features_dim)
			

def arch_search_densenet(start_net_path, arch_search_folder, net_pool_folder, max_episodes):
	growth_rate_list = [_i for _i in range(4, 50, 2)]
	# encoder config
	layer_token_list = ['g%d' % growth_rate for growth_rate in growth_rate_list]
	encoder_config = {
		'num_steps': 50,
		'vocab': Vocabulary(layer_token_list + ['t']),
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
		'decision_num': 2,
		'out_dims': [3, 20],
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
		'wider_action_num': 10,
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
		
		# on-policy training
		for _j in range(episode_config['wider_action_num']):
			input_seq, seq_len = get_net_seq(net_configs, encoder.vocab, encoder.num_steps)
			wider_decision, wider_probs = meta_controller.sample_wider_decision(input_seq, seq_len)
			# modify net config according to wider_decision
			wider_mask = apply_wider_decision(wider_decision, net_configs, growth_rate_list, noise_config)
			
			wider_decision_trajectory.append(wider_decision)
			wider_decision_mask.append(wider_mask)
			wider_seg_deeper += len(net_configs)
			encoder_input_seq.append(input_seq)
			encoder_seq_len.append(seq_len)
		
		for _j in range(episode_config['deeper_action_num']):
			input_seq, seq_len = get_net_seq(net_configs, encoder.vocab, encoder.num_steps)
			block_layer_num = get_block_layer_num(net_configs)
			deeper_decision, deeper_probs = meta_controller.sample_deeper_decision(input_seq, seq_len, block_layer_num)
			# modify net config according to deeper_decision
			deeper_mask = apply_deeper_decision(deeper_decision, net_configs, noise_config)
			
			deeper_decision_trajectory.append(deeper_decision)
			deeper_decision_mask.append(deeper_mask)
			deeper_block_layer_num.append(block_layer_num)
			encoder_input_seq.append(input_seq)
			encoder_seq_len.append(seq_len)
		
		widen_transition(net_configs, noise_config)
		
		run_configs = [run_config] * len(net_configs)
		net_str_list = get_net_str(net_configs)
		
		net_vals = arch_manager.get_net_vals(net_str_list, net_configs, run_configs)
		rewards = arch_manager.reward(net_vals, reward_config)
		
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
		rewards = np.concatenate([rewards for _ in range(episode_config['wider_action_num'] +
														 episode_config['deeper_action_num'])])
		rewards /= episode_config['batch_size']
		
		# update the agent
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

