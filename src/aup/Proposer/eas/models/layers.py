from .basic_model import BasicModel
import tensorflow as tf
import numpy as np
import copy


def apply_noise(weights, noise_config):
	if noise_config is None:
		return weights
	noise_type = noise_config.get('type', 'normal')
	if noise_type == 'normal':
		ratio = noise_config.get('ratio', 1e-3)
		std = np.std(weights)
		noise = np.random.normal(0, std * ratio, size=weights.shape)
	elif noise_type == 'uniform':
		ratio = noise_config.get('ratio', 1e-3)
		mean, _max = np.mean(weights), np.max(weights)
		width = (_max - mean) * ratio
		noise = np.random.uniform(-width, width, size=weights.shape)
	else:
		raise NotImplementedError
	return weights + noise


def get_layer_by_name(name):
	if name == 'conv':
		return ConvLayer
	elif name == 'fc':
		return FCLayer
	elif name == 'pool':
		return PoolLayer
	else:
		raise ValueError('Unknown layer type: %s' % name)


def get_magnifier(old_size, indices):
	_l = np.zeros(old_size)
	for x in indices:
		_l[x] += 1
	magnifier = (1.0 / _l)[indices]
	return magnifier


def get_random_remapping(old_size, new_size):
	base = np.arange(old_size)
	indices = np.concatenate([base, np.random.choice(base, new_size - old_size)])
	
	magnifier = get_magnifier(old_size, indices)
	return indices, magnifier


class BaseLayer:
	"""
	_id, batch normalization, activation, dropout, ready
	"""
	def __init__(self, _id, use_bn=True, activation='relu', keep_prob=1.0, ready=True, pre_activation=True):
		self._id = _id
		self.use_bn = use_bn
		self.activation = activation
		self.keep_prob = keep_prob
		self.ready = ready
		self.pre_activation = pre_activation
		
		self._scope = None
		self._init = None
		self.output_op = None
	
	@property
	def id(self): return self._id
	
	@id.setter
	def id(self, value): self._id = value
	
	@property
	def init(self):
		return self._init
	
	@property
	def param_initializer(self):
		if self._init is None:
			return None
		param_initializer = {}
		for key in self.variable_list.keys():
			if self._init[key] is not None:
				param_initializer[key] = tf.constant_initializer(self._init[key])
		if len(param_initializer) == 0:
			param_initializer = None
		return param_initializer
	
	def renew_init(self, net: BasicModel):
		if net is None:
			return copy.deepcopy(self._init)
		
		self._init = {}
		for key, var_name in self.variable_list.items():
			var = net.graph.get_tensor_by_name('%s/%s' % (self._scope, var_name))
			self._init[key] = net.sess.run(var)
		if len(self._init) == 0:
			self._init = None
		return copy.deepcopy(self._init)
	
	def copy(self):
		return self.set_from_config(self.get_config(), layer_init=copy.deepcopy(self._init))
	
	def get_config(self):
		return {
			'_id': self.id,
			'use_bn': self.use_bn,
			'activation': self.activation,
			'keep_prob': self.keep_prob,
			'pre_activation': self.pre_activation,
		}
	
	@property
	def variable_list(self):
		"""
		beta: mean scale
		gamma: variance scale
		y = gamma * (x - moving_mean) / sqrt(epsilon + moving_variance) + beta
		"""
		if self.use_bn:
			return {
				'moving_mean': 'BatchNorm/moving_mean:0',
				'moving_variance': 'BatchNorm/moving_variance:0',
				'beta': 'BatchNorm/beta:0',
				'gamma': 'BatchNorm/gamma:0',
			}
		else:
			return {}
	
	@staticmethod
	def set_from_config(layer_config, layer_init):
		raise NotImplementedError
	
	def build(self, _input, net, store_output_op):
		raise NotImplementedError
	
	def prev_widen(self, indices, magnifier, noise=None):
		raise NotImplementedError
	
	def set_identity_layer(self, strict, param, noise):
		raise NotImplementedError
	
	def widen_bn(self, indices, magnifier, noise=None):
		if self.use_bn:
			self._init['beta'] = self._init['beta'][indices]
			self._init['gamma'] = self._init['gamma'][indices]
			self._init['moving_mean'] = self._init['moving_mean'][indices]
			self._init['moving_variance'] = self._init['moving_variance'][indices]
	
	def set_bn_identity(self, strict=True, param=None, noise=None):
		if self.use_bn:
			if strict:
				self._init['moving_mean'] = param['moving_mean']
				self._init['moving_variance'] = param['moving_variance']
				self._init['beta'] = self._init['moving_mean']
				self._init['gamma'] = np.sqrt(self._init['moving_variance'] + param['epsilon'])
			else:
				# use default initialization for batch normalization layer
				self._init['moving_mean'], self._init['moving_variance'] = None, None
				self._init['beta'], self._init['gamma'] = None, None
	
	
class ConvLayer(BaseLayer):
	def __init__(self, _id, filter_num, kernel_size=3, strides=1,
				 use_bn=True, activation='relu', keep_prob=1.0, ready=True, pre_activation=True, **kwargs):
		BaseLayer.__init__(self, _id, use_bn, activation, keep_prob, ready, pre_activation)
		self.filter_num = filter_num
		self.kernel_size = kernel_size
		self.strides = strides
	
	@property
	def layer_str(self):
		return 'C%d,%d,%d' % (self.filter_num, self.kernel_size, self.strides)
		
	@property
	def variable_list(self):
		var_list = {'kernel': 'kernel:0'}
		var_list.update(super(ConvLayer, self).variable_list)
		return var_list
	
	def get_config(self):
		return {
			'name': 'conv',
			'filter_num': self.filter_num,
			'kernel_size': self.kernel_size,
			'strides': self.strides,
			**super(ConvLayer, self).get_config(),
		}
	
	@staticmethod
	def set_from_config(layer_config, layer_init=None):
		conv_layer = ConvLayer(**layer_config)
		conv_layer._init = layer_init
		return conv_layer
	
	def build(self, _input, net: BasicModel, store_output_op=False):
		output = _input
		if not self.ready:
			return output
		with tf.variable_scope(self._id):
			self._scope = tf.get_variable_scope().name
			param_initializer = self.param_initializer
			if self.pre_activation:
				# batch normalization
				if self.use_bn:
					output = BasicModel.batch_norm(output, net.is_training, net.net_config.bn_epsilon,
												   net.net_config.bn_decay, param_initializer=param_initializer)
				# activation
				output = BasicModel.activation(output, self.activation)
				# convolutional
				output = BasicModel.conv2d(output, self.filter_num, self.kernel_size, self.strides,
										   param_initializer=param_initializer)
			else:
				# convolutional
				output = BasicModel.conv2d(output, self.filter_num, self.kernel_size, self.strides,
										   param_initializer=param_initializer)
				# batch normalization
				if self.use_bn:
					output = BasicModel.batch_norm(output, net.is_training, net.net_config.bn_epsilon,
												   net.net_config.bn_decay, param_initializer=param_initializer)
				# activation
				output = BasicModel.activation(output, self.activation)
			# dropout
			output = BasicModel.dropout(output, self.keep_prob, net.is_training)
		if store_output_op:
			self.output_op = output
		return output
	
	def widen_filters(self, new_filter_num, noise=None):
		"""
		Increase the filter number of a conv layer while preserving the functionality
		Proposed in 'Net2Net': https://arxiv.org/abs/1511.05641
		"""
		assert new_filter_num > self.filter_num, 'Invalid new filter number: %d' % new_filter_num
		assert self._init is not None, 'Uninitialized layer'
		old_size, new_size = self.filter_num, new_filter_num
		indices, magnifier = get_random_remapping(old_size, new_size)
		# more filters
		self.filter_num = new_filter_num
		new_kernel = self._init['kernel'][:, :, :, indices]
		new_kernel[:, :, :, old_size:] = apply_noise(new_kernel[:, :, :, old_size:], noise.get('wider'))
		self._init['kernel'] = new_kernel
		if not self.pre_activation:
			# widen batch norm variables if use batch norm
			self.widen_bn(indices, magnifier, noise=noise)
		return indices, magnifier
	
	def prev_widen(self, indices, magnifier, noise=None):
		assert self._init is not None, 'Uninitialized layer'
		# rescale kernel
		self._init['kernel'] = self._init['kernel'][:, :, indices, :] * magnifier.reshape([1, 1, -1, 1])
		if self.pre_activation:
			self.widen_bn(indices, magnifier, noise=noise)
		
	def set_identity_layer(self, strict=True, param=None, noise=None):
		self._init = {}
		self.set_bn_identity(strict, param, noise=noise)
		mid = self.kernel_size // 2
		self._init['kernel'] = np.zeros([self.kernel_size, self.kernel_size, self.filter_num, self.filter_num])
		self._init['kernel'][mid, mid] = np.eye(self.filter_num)
		self._init['kernel'] = apply_noise(self._init['kernel'], noise.get('deeper'))
		self.ready = True

	def remap(self, indices, noise=None):
		self.filter_num = len(indices)
		self._init['kernel'] = self._init['kernel'][:, :, :, indices]
		self._init['kernel'] = apply_noise(self._init['kernel'], noise.get('wider'))
		if not self.pre_activation:
			self.widen_bn(indices, None, noise=noise)
		return self
		
		
class FCLayer(BaseLayer):
	def __init__(self, _id, units, use_bn=True, use_bias=False, activation='relu', keep_prob=1.0, ready=True,
				 pre_activation=False, **kwargs):
		BaseLayer.__init__(self, _id, use_bn, activation, keep_prob, ready, pre_activation)
		self.units = units
		self.use_bias = use_bias
	
	@property
	def layer_str(self):
		return 'FC%d' % self.units
	
	@property
	def variable_list(self):
		var_list = {'W': 'W:0'}
		if self.use_bias:
			var_list['bias'] = 'bias:0'
		var_list.update(super(FCLayer, self).variable_list)
		return var_list
	
	def get_config(self):
		return {
			'name': 'fc',
			'units': self.units,
			'use_bias': self.use_bias,
			**super(FCLayer, self).get_config(),
		}
	
	@staticmethod
	def set_from_config(layer_config, layer_init=None):
		fc_layer = FCLayer(**layer_config)
		fc_layer._init = layer_init
		return fc_layer
	
	def build(self, _input, net: BasicModel, store_output_op=False):
		output = _input
		if not self.ready:
			return output
		with tf.variable_scope(self._id):
			self._scope = tf.get_variable_scope().name
			param_initializer = self.param_initializer
			# flatten if not
			output = BasicModel.flatten(output)
			if self.pre_activation:
				# batch normalization
				if self.use_bn:
					output = BasicModel.batch_norm(output, net.is_training, net.net_config.bn_epsilon,
												   net.net_config.bn_decay, param_initializer=param_initializer)
				# activation
				output = BasicModel.activation(output, self.activation)
				# FC
				output = BasicModel.fc_layer(output, self.units, self.use_bias, param_initializer=param_initializer)
			else:
				# FC
				output = BasicModel.fc_layer(output, self.units, self.use_bias, param_initializer=param_initializer)
				# batch normalization
				if self.use_bn:
					output = BasicModel.batch_norm(output, net.is_training, net.net_config.bn_epsilon,
												   net.net_config.bn_decay, param_initializer=param_initializer)
				# activation
				output = BasicModel.activation(output, self.activation)
			# dropout
			output = BasicModel.dropout(output, self.keep_prob, net.is_training)
		if store_output_op:
			self.output_op = output
		return output
	
	def widen_units(self, new_units_num, noise=None):
		"""
		Increase the units number of a fc layer while preserving the functionality
		Proposed in 'Net2Net': https://arxiv.org/abs/1511.05641
		W: [in_dim, out_units]
		bias: [out_units]
		"""
		assert new_units_num > self.units, 'Invalid new units number: %d' % new_units_num
		assert self._init is not None, 'Uninitialized layer'
		old_size, new_size = self.units, new_units_num
		indices, magnifier = get_random_remapping(old_size, new_size)
		# more units
		self._init['W'] = self._init['W'][:, indices]
		self._init['W'][:, old_size:] = apply_noise(self._init['W'][:, old_size:], noise.get('wider'))
		self.units = new_units_num
		# widen bias variable if exist
		if self.use_bias:
			self._init['bias'] = self._init['bias'][indices]
			self._init['bias'][old_size:] = apply_noise(self._init['bias'][old_size:], noise.get('wider'))
		if not self.pre_activation:
			# widen batch norm variables if use batch norm
			self.widen_bn(indices, magnifier, noise=noise)
		return indices, magnifier
			
	def prev_widen(self, indices, magnifier, noise=None):
		assert self._init is not None, 'Uninitialized layer'
		# rescale W
		self._init['W'] = self._init['W'][indices] * magnifier.reshape([-1, 1])
		if self.pre_activation:
			self.widen_bn(indices, magnifier, noise=noise)
	
	def set_identity_layer(self, strict=True, param=None, noise=None):
		self._init = {}
		self.set_bn_identity(strict, param, noise=noise)
		if self.use_bias:
			self._init['bias'] = [0.0] * self.units
		self._init['W'] = np.eye(self.units)
		self._init['W'] = apply_noise(self._init['W'], noise.get('deeper'))
		self.ready = True
	
	def remap(self, indices, noise=None):
		self.units = len(indices)
		self._init['W'] = self._init['W'][:, indices]
		self._init['W'] = apply_noise(self._init['W'], noise.get('wider'))
		if self.use_bias:
			self._init['bias'] = self._init['bias'][indices]
		if not self.pre_activation:
			self.widen_bn(indices, None, noise=noise)
		return self
	
		
class PoolLayer(BaseLayer):
	def __init__(self, _id, _type, kernel_size=2, strides=2, use_bn=False, activation=None, keep_prob=1.0,
				 ready=True, pre_activation=True, **kwargs):
		BaseLayer.__init__(self, _id, use_bn, activation, keep_prob, ready, pre_activation)
		
		self._type = _type
		self.kernel_size = kernel_size
		self.strides = strides
	
	@property
	def layer_str(self):
		return 'P%d,%d' % (self.kernel_size, self.strides)
		
	def get_config(self):
		return {
			'name': 'pool',
			'_type': self._type,
			'kernel_size': self.kernel_size,
			'strides': self.strides,
			**super(PoolLayer, self).get_config(),
		}
	
	@staticmethod
	def set_from_config(layer_config, layer_init=None):
		pool_layer = PoolLayer(**layer_config)
		pool_layer._init = layer_init
		return pool_layer
	
	def build(self, _input, net: BasicModel, store_output_op=False):
		output = _input
		if not self.ready:
			return output
		with tf.variable_scope(self._id):
			self._scope = tf.get_variable_scope().name
			param_initializer = self.param_initializer
			if self.pre_activation:
				# batch normalization
				if self.use_bn:
					output = BasicModel.batch_norm(output, net.is_training, net.net_config.bn_epsilon,
												   net.net_config.bn_decay, param_initializer=param_initializer)
				# activation
				output = BasicModel.activation(output, self.activation)
				# Pooling
				if self._type == 'avg':
					output = BasicModel.avg_pool(output, k=self.kernel_size, s=self.strides)
				elif self._type == 'max':
					output = BasicModel.max_pool(output, k=self.kernel_size, s=self.strides)
				else:
					raise ValueError('Do not support the pooling type: %s' % self._type)
			else:
				# Pooling
				if self._type == 'avg':
					output = BasicModel.avg_pool(output, k=self.kernel_size, s=self.strides)
				elif self._type == 'max':
					output = BasicModel.max_pool(output, k=self.kernel_size, s=self.strides)
				else:
					raise ValueError('Do not support the pooling type: %s' % self._type)
				# batch normalization
				if self.use_bn:
					output = BasicModel.batch_norm(output, net.is_training, net.net_config.bn_epsilon,
												   net.net_config.bn_decay, param_initializer=param_initializer)
				# activation
				output = BasicModel.activation(output, self.activation)
			# dropout
			output = BasicModel.dropout(output, self.keep_prob, net.is_training)
		if store_output_op:
			self.output_op = output
		return output

	def set_identity_layer(self, strict=True, param=None, noise=None):
		raise ValueError('Pooling layer can never be an identity layer')
	
	def prev_widen(self, indices, magnifier, noise=None):
		self.widen_bn(indices, magnifier, noise=noise)
