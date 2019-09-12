from .basic_model import BasicModel
from ..data_providers.base_provider import DataProvider
from .layers import ConvLayer, PoolLayer, FCLayer
from .layer_cascade import LayerCascade
import tensorflow as tf
import numpy as np


class SimpleConvnetConfig:
	def __init__(self):
		self.net_config = {
			'weight_decay': None,
			'bn_epsilon': None,
			'bn_decay': None,
			'drop_scheme': None,
		}
		self.layer_cascade = None
	
	@property
	def weight_decay(self): return self.net_config['weight_decay']
	
	@property
	def bn_epsilon(self): return self.net_config['bn_epsilon']
	
	@property
	def bn_decay(self): return self.net_config['bn_decay']
	
	@property
	def drop_scheme(self): return self.net_config['drop_scheme']
	
	@property
	def depth(self): return self.layer_cascade.depth
	
	def get_config(self):
		return {
			'name': 'SimpleConvnet',
			**self.net_config,
			'layer_cascade': self.layer_cascade.get_config()
		}

	def copy(self):
		net_config = SimpleConvnetConfig()
		net_config.set_net_from_config(self.get_config(), self.renew_init(None), print_info=False)
		return net_config
	
	def renew_init(self, convnet):
		return {
			'layer_cascade': self.layer_cascade.renew_init(convnet)
		}
	
	def set_standard_convnet(self, data_provider: DataProvider, conv_blocks_config, fc_block_config, weight_decay,
							 drop_scheme, bn_epsilon, bn_decay, print_info=True, **kwargs):
		self.net_config = {
			'weight_decay': weight_decay,
			'bn_epsilon': bn_epsilon,
			'bn_decay': bn_decay,
			'drop_scheme': drop_scheme,
		}
		
		image_size = data_provider.data_shape[0]
		
		layers = []
		conv_id = 0
		for _i, block_config in enumerate(conv_blocks_config):
			num_layers, kernel_size, filter_num = block_config
			for _j in range(num_layers):
				keep_prob = 1.0
				if 'conv' in drop_scheme['type']:
					keep_prob = 1.0 if _i + _j == 0 else drop_scheme.get('conv_drop', 1.0)
				conv_layer = ConvLayer('conv_%d' % conv_id, filter_num, kernel_size=kernel_size, keep_prob=keep_prob,
									   pre_activation=False)
				conv_id += 1
				layers.append(conv_layer)
			if _i < len(conv_blocks_config) - 1:
				keep_prob = 1.0
				if 'pool' in drop_scheme['type']:
					keep_prob = drop_scheme.get('pool_drop', 1.0)
				pool_layer = PoolLayer('pool_%d' % _i, 'max', keep_prob=keep_prob, pre_activation=False)
				layers.append(pool_layer)
				image_size = image_size // 2
		global_avg_pool = PoolLayer('pool_%d' % len(conv_blocks_config), 'avg',
									kernel_size=image_size, strides=image_size, pre_activation=False)
		layers.append(global_avg_pool)
		for _i, units in enumerate(fc_block_config):
			keep_prob = 1.0
			if 'fc' in drop_scheme['type']:
				keep_prob = drop_scheme.get('fc_drop', 1.0)
			fc_layer = FCLayer('fc_%d' % _i, units, keep_prob=keep_prob)
			layers.append(fc_layer)
		final_fc_layer = FCLayer('fc_%d' % len(fc_block_config), data_provider.n_classes, use_bn=False, use_bias=True,
								 activation=None)
		layers.append(final_fc_layer)
		self.layer_cascade = LayerCascade('SimpleConvNet', layers)
		
		if print_info:
			pass
		return self
	
	def set_net_from_config(self, net_config_json, init=None, print_info=True):
		for key in self.net_config.keys():
			self.net_config[key] = net_config_json[key]
		init = init['layer_cascade'] if init is not None else None
		self.layer_cascade = LayerCascade.set_from_config(net_config_json['layer_cascade'], init)
		if print_info:
			pass
		return self
	
	def widen(self, layer_idx, new_width, widen_type='output_dim', noise=None):
		change_out_dim, _, _ = self.layer_cascade.widen(layer_idx, new_width, widen_type, noise)
		if change_out_dim:
			raise ValueError('Can not change the final logits number')
	
	def deepen(self, layer_idx, new_layer_config):
		return self.layer_cascade.deepen(layer_idx, new_layer_config, None)
	
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
			model = SimpleConvnet(None, data_provider, None, net_config=self, only_forward=True)
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
	
	
class SimpleConvnet(BasicModel):
	def _build_graph(self, only_forward=False):
		_input = self.images
		output = _input
		
		output = self.net_config.layer_cascade.build(output, self, store_output_op=only_forward)
		
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
