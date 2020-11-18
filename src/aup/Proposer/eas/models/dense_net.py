import tensorflow as tf
from .basic_model import BasicModel
from .layers import ConvLayer, FCLayer, PoolLayer, get_magnifier, apply_noise
from ..data_providers.base_provider import DataProvider
from .layer_cascade import LayerCascade
from .layer_multi_branch import LayerMultiBranch
import numpy as np


def get_block_by_name(name):
	if name == 'transition':
		return TransitionBlock
	elif name == 'dense_block':
		return DenseBlock
	else:
		raise ValueError('Unsupported block type: %s' % name)
	

class TransitionBlock(LayerCascade):
	def get_config(self):
		return {
			'name': 'transition',
			**super(TransitionBlock, self).get_config(),
		}
		
	@staticmethod
	def set_from_config(config_json, init=None, return_class=True):
		_id, layers = LayerCascade.set_from_config(config_json, init, return_class=False)
		return TransitionBlock(_id, layers)
	
	def prev_widen(self, indices, magnifier, noise=None):
		super(TransitionBlock, self).prev_widen(indices, magnifier, noise=noise)
		return False, None, None
	
	def widen(self, loc, new_width, widen_type='output_dim', noise=None, input_dim=None):
		return super(TransitionBlock, self).widen(loc['layer'], new_width, widen_type, noise=noise)
	
	def deepen(self, loc, new_layer_config, input_dim):
		return super(TransitionBlock, self).deepen(loc['layer'], new_layer_config, input_dim)
	

class DenseBlock:
	def __init__(self, _id, miniblocks):
		self._id = _id
		self.miniblocks = miniblocks
		
		self.output_op = None
	
	@property
	def id(self):
		return self._id
	
	@id.setter
	def id(self, value):
		self._id = value
	
	@property
	def depth(self):
		depth = 0
		for miniblock in self.miniblocks:
			depth += miniblock.depth
		return depth
	
	def out_features_dim(self, in_features_dim):
		out_features_dim = in_features_dim
		for miniblock in self.miniblocks:
			out_features_dim += miniblock.out_features_dim
		return out_features_dim
	
	def build(self, _input, densenet, store_output_op=False):
		output = _input
		with tf.variable_scope(self._id):
			for miniblock in self.miniblocks:
				comp_out = miniblock.build(output, densenet, store_output_op=store_output_op)
				output = tf.concat(axis=3, values=(output, comp_out))
		if store_output_op:
			self.output_op = output
		return output
	
	def get_config(self):
		return {
			'name': 'dense_block',
			'_id': self._id,
			'miniblocks': [miniblock.get_config() for miniblock in self.miniblocks]
		}
	
	def renew_init(self, densenet):
		return {
			'_id': self._id,
			'miniblocks': [miniblock.renew_init(densenet) for miniblock in self.miniblocks]
		}
	
	@staticmethod
	def set_from_config(config_json, init=None):
		_id = config_json['_id']
		miniblocks = []
		for _i, miniblock_config in enumerate(config_json['miniblocks']):
			miniblock_init = init['miniblocks'][_i] if init is not None else None
			miniblock = LayerMultiBranch.set_from_config(miniblock_config, miniblock_init)
			miniblocks.append(miniblock)
		return DenseBlock(_id, miniblocks)
	
	"""
	Network Transformation Operations
	"""
	def insert_miniblock(self, idx, miniblock_config, input_dim, noise=None, scheme=0):
		assert 0 <= idx < len(self.miniblocks), 'Invalid miniblock index %d' % idx
		if miniblock_config['bc_mode']:
			# DenseNet-BC
			if scheme == 0:
				copy_idx = idx
				copy_miniblock = self.miniblocks[copy_idx]
				new_in_bottle = copy_miniblock.in_bottle.copy()
				new_in_layer = new_in_bottle.layers[0]
				pad_kernel_shape = list(new_in_layer.init['kernel'].shape)
				pad_kernel_shape[2] = copy_miniblock.out_features_dim
				new_in_layer.init['kernel'] = \
					np.concatenate([new_in_layer.init['kernel'], np.zeros(pad_kernel_shape)], axis=2)
				if new_in_layer.pre_activation and new_in_layer.use_bn:
					new_in_layer.init['beta'] = \
						np.concatenate([new_in_layer.init['beta'], np.zeros([copy_miniblock.out_features_dim])])
					new_in_layer.init['gamma'] = \
						np.concatenate([new_in_layer.init['gamma'], np.ones([copy_miniblock.out_features_dim])])
					new_in_layer.init['moving_mean'] = \
						np.concatenate([new_in_layer.init['moving_mean'], np.zeros([copy_miniblock.out_features_dim])])
					new_in_layer.init['moving_variance'] = \
						np.concatenate([new_in_layer.init['moving_variance'], np.ones([copy_miniblock.out_features_dim])])
				new_in_layer.init['kernel'] = apply_noise(new_in_layer.init['kernel'], noise.get('wider'))
				if copy_miniblock.out_bottle is None:
					new_branches, indices = copy_miniblock.remapped_branches(noise=noise)
					new_miniblock = LayerMultiBranch('M_%d' % (idx + 2), new_branches,
													 merge=copy_miniblock.merge, in_bottle=new_in_bottle)
					old_size = len(indices)
					indices = np.concatenate([np.arange(old_size), indices])
					magnifier = get_magnifier(old_size, indices)
					
					prev_miniblock_out_dim = input_dim
					for _i in range(0, idx):
						prev_miniblock_out_dim += self.miniblocks[_i].out_features_dim
					indices = np.concatenate([
						np.arange(prev_miniblock_out_dim),
						indices + prev_miniblock_out_dim,
					])
					magnifier = np.concatenate([
						[1] * prev_miniblock_out_dim,
						magnifier,
					])
					prev_miniblock_out_dim += old_size
					for _i in range(idx + 1, len(self.miniblocks)):
						miniblock_out_dim = self.miniblocks[_i].out_features_dim
						self.miniblocks[_i].id = 'M_%d' % (_i + 2)
						self.miniblocks[_i].prev_widen(indices, magnifier, noise=noise)
						indices = np.concatenate([
							indices,
							np.arange(prev_miniblock_out_dim, prev_miniblock_out_dim + miniblock_out_dim)
						])
						magnifier = np.concatenate([
							magnifier,
							[1] * miniblock_out_dim,
						])
						prev_miniblock_out_dim += miniblock_out_dim
					self.miniblocks = self.miniblocks[:idx + 1] + [new_miniblock] + self.miniblocks[idx + 1:]
					return indices, magnifier
				else:
					raise NotImplementedError
			else:
				# identity scheme
				raise NotImplementedError
		else:
			# DenseNet without BC
			raise NotImplementedError
	
	def prev_widen(self, indices, magnifier, noise=None):
		old_size = np.max(indices) + 1
		prev_miniblock_out_dim = old_size
		for miniblock in self.miniblocks:
			miniblock_out_dim = miniblock.out_features_dim
			miniblock.prev_widen(indices, magnifier, noise=noise)
			indices = np.concatenate([
				indices,
				np.arange(prev_miniblock_out_dim, prev_miniblock_out_dim + miniblock_out_dim)
			])
			magnifier = np.concatenate([
				magnifier,
				[1] * miniblock_out_dim,
			])
			prev_miniblock_out_dim += miniblock_out_dim
		return True, indices, magnifier
	
	def widen(self, loc, new_width, widen_type='output_dim', noise=None, input_dim=3):
		miniblock_idx = loc['miniblock']
		miniblock = self.miniblocks[miniblock_idx]
		old_miniblock_out_dim = miniblock.out_features_dim
		change_out_dim, indices, magnifier = miniblock.widen(loc, new_width, widen_type, noise=noise)
		if change_out_dim:
			prev_miniblock_out_dim = input_dim
			for _i in range(0, miniblock_idx):
				prev_miniblock_out_dim += self.miniblocks[_i].out_features_dim
			indices = np.concatenate([
				np.arange(prev_miniblock_out_dim),
				indices + prev_miniblock_out_dim,
			])
			magnifier = np.concatenate([
				[1] * prev_miniblock_out_dim,
				magnifier,
			])
			prev_miniblock_out_dim += old_miniblock_out_dim
			for _i in range(miniblock_idx + 1, len(self.miniblocks)):
				miniblock_out_dim = self.miniblocks[_i].out_features_dim
				self.miniblocks[_i].prev_widen(indices, magnifier, noise=noise)
				indices = np.concatenate([
					indices,
					np.arange(prev_miniblock_out_dim, prev_miniblock_out_dim + miniblock_out_dim)
				])
				magnifier = np.concatenate([
					magnifier,
					[1] * miniblock_out_dim,
				])
				prev_miniblock_out_dim += miniblock_out_dim
			return True, indices, magnifier
		else:
			return False, None, None
	
	def deepen(self, loc, new_layer_config, input_dim):
		miniblock_idx = loc['miniblock']
		for _i in range(0, miniblock_idx):
			input_dim += self.miniblocks[_i].out_features_dim
		return self.miniblocks[miniblock_idx].deepen(loc, new_layer_config, input_dim)
		

class DenseNetConfig:
	def __init__(self):
		self.net_config = {
			'model_type': None,
			'weight_decay': None,
			'first_ratio': None,
			'reduction': None,
			'bc_ratio': None,
			'bn_epsilon': None,
			'bn_decay': None,
			'pre_activation': None,
		}
		self.blocks = None
	
	@property
	def model_type(self): return self.net_config['model_type']
	
	@property
	def weight_decay(self): return self.net_config['weight_decay']
	
	@property
	def first_ratio(self): return self.net_config['first_ratio']
	
	@property
	def reduction(self): return self.net_config['reduction']
	
	@property
	def bc_ratio(self): return self.net_config['bc_ratio']
	
	@property
	def bn_epsilon(self): return self.net_config['bn_epsilon']
	
	@property
	def bn_decay(self): return self.net_config['bn_decay']
	
	@property
	def depth(self):
		depth = 0
		for block in self.blocks:
			depth += block.depth
		return depth
	
	@property
	def average_growth_rate(self):
		growth_rate_list = []
		for block in self.blocks:
			if isinstance(block, DenseBlock):
				for miniblock in block.miniblocks:
					growth_rate = miniblock.out_features_dim
					growth_rate_list.append(growth_rate)
		return np.mean(growth_rate_list)
	
	def copy(self):
		net_config = DenseNetConfig()
		net_config.set_net_from_config(self.get_config(), self.renew_init(None), print_info=False)
		return net_config
	
	def get_config(self):
		return {
			'name': 'DenseNet',
			**self.net_config,
			'blocks': [block.get_config() for block in self.blocks]
		}

	def renew_init(self, densenet):
		return {
			'blocks': [block.renew_init(densenet) for block in self.blocks]
		}
	
	def set_standard_dense_net(self, data_provider: DataProvider, growth_rate, depth, total_blocks,
							   keep_prob, weight_decay, model_type,
							   first_ratio=2, reduction=1.0, bc_ratio=4,
							   bn_epsilon=1e-5, bn_decay=0.9, print_info=True,
							   pre_activation=True, **kwargs):
		self.net_config = {
			'model_type': model_type,
			'weight_decay': weight_decay,
			'first_ratio': first_ratio,
			'reduction': reduction,
			'bc_ratio': bc_ratio,
			'bn_epsilon': bn_epsilon,
			'bn_decay': bn_decay,
			'pre_activation': pre_activation,
		}
		
		image_size = data_provider.data_shape[0]
		
		first_output_features = growth_rate * first_ratio
		bc_mode = (model_type == 'DenseNet-BC')
		layers_per_block = (depth - (total_blocks + 1)) // total_blocks
		if bc_mode: layers_per_block = layers_per_block // 2
		
		# initial conv
		if pre_activation:
			init_conv_layer = ConvLayer('conv_0', first_output_features, kernel_size=3, activation=None, use_bn=False)
		else:
			init_conv_layer = ConvLayer('conv_0', first_output_features, kernel_size=3, pre_activation=False)
		init_transition = TransitionBlock('T_0_first', [init_conv_layer])
		self.blocks = [init_transition]
		
		# Dense Blocks
		in_features_dim = first_output_features
		for block_idx in range(1, total_blocks + 1):
			miniblocks = []
			block_id = 'D_%d' % block_idx
			for miniblock_idx in range(1, layers_per_block + 1):
				miniblock_id = 'M_%d' % miniblock_idx
				in_bottle = None
				if bc_mode:
					bottelneck_layer = ConvLayer('conv_0', growth_rate * bc_ratio, kernel_size=1, keep_prob=keep_prob,
												 pre_activation=pre_activation)
					in_bottle = LayerCascade('in_bottle', [bottelneck_layer])
				
				branch_0 = LayerCascade('B_0', [
					ConvLayer('conv_0', growth_rate, kernel_size=3,
							  keep_prob=keep_prob, pre_activation=pre_activation)
				])
				miniblocks.append(LayerMultiBranch(miniblock_id, [branch_0], in_bottle=in_bottle))
			dense_block = DenseBlock(block_id, miniblocks)
			self.blocks += [dense_block]
			
			out_features_dim = dense_block.out_features_dim(in_features_dim)
			if block_idx != total_blocks:
				out_features_dim = int(out_features_dim * reduction)
				transition_id = 'T_%d_middle' % block_idx
				conv_layer = ConvLayer('conv_0', out_features_dim, kernel_size=1, keep_prob=keep_prob,
									   pre_activation=pre_activation)
				avg_pool_layer = PoolLayer('pool_0', 'avg', kernel_size=2, strides=2)
				transition = TransitionBlock(transition_id, [conv_layer, avg_pool_layer])
				self.blocks.append(transition)
				image_size = image_size // 2
			in_features_dim = out_features_dim
		
		# Transition to classes
		if pre_activation:
			global_avg_pool = PoolLayer('pool_0', 'avg', kernel_size=image_size, strides=image_size,
										activation='relu', use_bn=True)
		else:
			global_avg_pool = PoolLayer('pool_0', 'avg', kernel_size=image_size, strides=image_size,
										pre_activation=False)
		final_fc_layer = FCLayer('fc_0', data_provider.n_classes, use_bn=False, use_bias=True, activation=None)
		transition_to_classes = TransitionBlock('T_to_classes', [global_avg_pool, final_fc_layer])
		self.blocks.append(transition_to_classes)
		
		# print information about the network
		if print_info:
			print('Set Standard %s' % model_type)
		
			if not bc_mode:
				print('Build %s model with %d blocks, '
					  '%d composite layers each.' % (model_type, total_blocks, layers_per_block))
			if bc_mode:
				print('Build %s model with %d blocks, '
					  '%d bottleneck layers and %d composite layers each.' % (
						  model_type, total_blocks, layers_per_block, layers_per_block))
			print('Reduction at transition layers: %.2f' % reduction)
		return self
		
	def set_net_from_config(self, net_config_json, init=None, print_info=True):
		# load config and init (if exist)
		for key in self.net_config.keys():
			self.net_config[key] = net_config_json[key]
		self.blocks = []
		for _i, block_config in enumerate(net_config_json['blocks']):
			block_init = init['blocks'][_i] if init is not None else None
			block = get_block_by_name(block_config['name'])
			self.blocks.append(block.set_from_config(block_config, block_init))
		if print_info:
			print('Set DenseNet from config:')
			for k, v in self.net_config.items():
				print('\t%s: %s' % (k, v))
			print('\t%s: %d' % ('depth', self.depth))
		return self
	
	def widen(self, loc, new_width, widen_type='output_dim', noise=None, image_channel=3):
		"""
		widen_type: "output_dim" or "kernel"
		"""
		block_idx = loc['block']
		if block_idx == 0:
			input_dim = image_channel
		elif isinstance(self.blocks[block_idx - 1], TransitionBlock):
			input_dim = self.blocks[block_idx - 1].out_features_dim
		else:
			input_dim = self.blocks[block_idx - 1].out_features_dim(self.blocks[block_idx - 2].out_features_dim)
		
		change_out_dim, indices, magnifier = \
			self.blocks[block_idx].widen(loc, new_width, widen_type, noise=noise, input_dim=input_dim)
		while change_out_dim:
			change_out_dim, indices, magnifier = self.blocks[block_idx + 1].prev_widen(indices, magnifier, noise=noise)
			block_idx += 1
		
	def deepen(self, loc, new_layer_config, image_channel=3):
		new_layer_config['pre_activation'] = self.net_config['pre_activation']
		block_idx = loc['block']
		if block_idx == 0:
			input_dim = image_channel
		elif isinstance(self.blocks[block_idx - 1], TransitionBlock):
			input_dim = self.blocks[block_idx - 1].out_features_dim
		else:
			input_dim = self.blocks[block_idx - 1].out_features_dim(self.blocks[block_idx - 2].out_features_dim)
		
		return self.blocks[block_idx].deepen(loc, new_layer_config, input_dim)
	
	def set_identity4deepen(self, to_set_layers, data_provider, batch_size, batch_num=1, strict=True, noise=None):
		"""
		to_set_layers = [(new_layer, prev_layer), ...]
		"""
		task_list = {}
		for new_layer, prev_layer in to_set_layers:
			if new_layer.ready: continue
			if new_layer.use_bn and strict:
				task_id = id(prev_layer)
				if task_id in task_list:
					task_list[task_id][1].append(new_layer)
				else:
					task_list[task_id] = (prev_layer, [new_layer])
			else:
				new_layer.set_identity_layer(strict=strict, noise=noise)
		if len(task_list) > 0:
			model = DenseNet(None, data_provider, None, net_config=self, only_forward=True)
			task_list = list(task_list.values())
			fetches = [prev_layer.output_op for prev_layer, _ in task_list]
			statistics = [[0, 0] for _ in task_list]
			for _i in range(batch_num):
				input_images, _ = data_provider.train.next_batch(batch_size)
				outputs = model.sess.run(fetches, feed_dict={model.images: input_images, model.is_training: False})
				for _j, out in enumerate(outputs):
					out = out.astype('float32')
					axis = tuple(range(len(out.shape) - 1))
					mean = np.mean(out, axis=axis, keepdims=True)
					variance = np.mean(np.square(out - mean), axis=axis, keepdims=True)
					mean, variance = np.squeeze(mean), np.squeeze(variance)
					statistics[_j][0] += mean
					statistics[_j][1] += variance
			for _j, (prev_layer, new_layers) in enumerate(task_list):
				mean, variance = statistics[_j][0] / batch_num, statistics[_j][1] / batch_num
				for new_layer in new_layers:
					if new_layer.ready: continue
					param = {
						'moving_mean': mean,
						'moving_variance': variance,
						'epsilon': self.bn_epsilon,
					}
					new_layer.set_identity_layer(strict=strict, param=param, noise=noise)
	
	def insert_miniblock(self, loc, miniblock_config, image_channel=3, noise=None):
		block_idx = loc['block']
		if block_idx == 0:
			input_dim = image_channel
		elif isinstance(self.blocks[block_idx - 1], TransitionBlock):
			input_dim = self.blocks[block_idx - 1].out_features_dim
		else:
			input_dim = self.blocks[block_idx - 1].out_features_dim(self.blocks[block_idx - 2].out_features_dim)
		
		assert isinstance(self.blocks[block_idx], DenseBlock), 'Invalid'
		indices, magnifier = \
			self.blocks[block_idx].insert_miniblock(loc['miniblock'], miniblock_config, input_dim, noise=noise)
		self.blocks[block_idx + 1].prev_widen(indices, magnifier, noise=noise)
		
		
class DenseNet(BasicModel):
	def _build_graph(self, only_forward=False):
		_input = self.images
		output = _input
		# building blocks (transition and dense)
		for block in self.net_config.blocks:
			output = block.build(output, self, store_output_op=only_forward)
		
		if not only_forward:
			logits = output
			with tf.variable_scope('L2_Loss'):
				l2_loss = tf.add_n([tf.nn.l2_loss(var) for var in tf.trainable_variables()])
			
			prediction = tf.nn.softmax(logits)
			
			# losses
			cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
				logits=logits, labels=self.labels))
			self.cross_entropy = cross_entropy
			
			# optimizer and train step
			optimizer = self.build_optimizer(self.learning_rate,
											 self.run_config.opt_config[0], self.run_config.opt_config[1])
			self.train_step = optimizer.minimize(
				cross_entropy + l2_loss * self.net_config.weight_decay)
			correct_prediction = tf.equal(
				tf.argmax(prediction, 1),
				tf.argmax(self.labels, 1))
			self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
