import os
import shutil
import tensorflow as tf
import numpy as np
import time
from datetime import timedelta
import json
import pickle
	

class BasicModel:
	def __init__(self, path, data_provider, run_config, net_config, pure=False, only_forward=False):
		if only_forward: pure = True
		self.graph = tf.Graph()
		
		self.data_provider = data_provider
		self._path = path
		self.run_config = run_config
		self.net_config = net_config
		
		self.data_shape = data_provider.data_shape
		self.n_classes = data_provider.n_classes
		
		self._save_path, self._logs_path = None, None
		self.batches_step = 0
		
		self.cross_entropy, self.train_step, self.accuracy = None, None, None
		with self.graph.as_default():
			self._define_inputs()
			self._build_graph(only_forward=only_forward)
			self.global_variables_initializer = tf.global_variables_initializer()
			if not pure:
				self._count_trainable_params()
				self.saver = tf.train.Saver()
		self._initialize_session(set_logs=(not pure))
	
	@property
	def save_path(self):
		if self._save_path is None:
			save_path = '%s/checkpoint' % self._path
			os.makedirs(save_path, exist_ok=True)
			save_path = os.path.join(save_path, 'model.ckpt')
			self._save_path = save_path
		return self._save_path
	
	@property
	def logs_path(self):
		if self._logs_path is None:
			logs_path = '%s/logs' % self._path
			if self.run_config.renew_logs:
				shutil.rmtree(logs_path, ignore_errors=True)
			os.makedirs(logs_path, exist_ok=True)
			self._logs_path = logs_path
		return self._logs_path
	
	def _build_graph(self, only_forward=False):
		raise NotImplementedError
	
	def _define_inputs(self):
		shape = [None]
		shape.extend(self.data_shape)
		self.images = tf.placeholder(
			tf.float32,
			shape=shape,
			name='input_images')
		self.labels = tf.placeholder(
			tf.float32,
			shape=[None, self.n_classes],
			name='labels')
		self.learning_rate = tf.placeholder(
			tf.float32,
			shape=[],
			name='learning_rate')
		self.is_training = tf.placeholder(tf.bool, shape=[], name='is_training')
		
	def _initialize_session(self, set_logs=True):
		"""Initialize session, variables"""
		config = tf.ConfigProto()
		# restrict model GPU memory utilization to min required
		config.gpu_options.allow_growth = True
		self.sess = tf.Session(graph=self.graph, config=config)
		
		self.sess.run(self.global_variables_initializer)
		if set_logs:
			logswriter = tf.summary.FileWriter
			self.summary_writer = logswriter(self.logs_path, graph=self.graph)
	
	def train_all_epochs(self, start_epoch=1):
		n_epochs = self.run_config.n_epochs
		learning_rate = self.run_config.init_lr
		batch_size = self.run_config.batch_size
		
		total_start_time = time.time()
		for epoch in range(start_epoch, n_epochs + 1):
			print('\n', '-' * 30, 'Train epoch: %d' % epoch, '-' * 30, '\n')
			start_time = time.time()
			new_lr = self.run_config.learning_rate(epoch)
			if new_lr != learning_rate:
				learning_rate = new_lr
				print('Decrease learning rate, new lr = %f' % learning_rate)
			
			print('Training...')
			loss, acc = self.train_one_epoch(
				self.data_provider.train, batch_size, learning_rate)
			# save logs about "loss" and "acc" if the option is true
			if self.run_config.should_save_logs:
				self.log_loss_accuracy(loss, acc, epoch, prefix='train')
			
			if self.run_config.validation_frequency and epoch % self.run_config.validation_frequency == 0:
				print('Validation...')
				loss, acc = self.test(self.data_provider.validation, batch_size)
				if self.run_config.should_save_logs:
					self.log_loss_accuracy(loss, acc, epoch, prefix='valid')
				if self.run_config.should_save_model:
					self.save_model()
					json.dump({'epoch': epoch + 1}, open('%s/checkpoint/epoch.info' % self._path, 'w'))
			
			time_per_epoch = time.time() - start_time
			seconds_left = int((n_epochs - epoch) * time_per_epoch)
			print('Time per epoch: %s, Est. complete in: %s' % (
				str(timedelta(seconds=time_per_epoch)),
				str(timedelta(seconds=seconds_left))))
		
		if self.run_config.should_save_model:
			self.save_model()
		
		total_training_time = time.time() - total_start_time
		print('\nTotal training time: %s' % str(timedelta(
			seconds=total_training_time)))
	
	def train_one_epoch(self, data, batch_size, learning_rate):
		num_examples = data.num_examples
		total_loss = []
		total_accuracy = []
		for i in range(num_examples // batch_size):
			batch = data.next_batch(batch_size)
			images, labels = batch
			feed_dict = {
				self.images: images,
				self.labels: labels,
				self.learning_rate: learning_rate,
				self.is_training: True,
			}
			fetches = [self.train_step, self.cross_entropy, self.accuracy]
			result = self.sess.run(fetches, feed_dict=feed_dict)
			_, loss, accuracy = result
			total_loss.append(loss)
			total_accuracy.append(accuracy)
			# save logs about "loss" and "acc" if the option is true
			if self.run_config.should_save_logs:
				self.batches_step += 1
				self.log_loss_accuracy(
					loss, accuracy, self.batches_step, prefix='per_batch',
					should_print=False)
		mean_loss = np.mean(total_loss)
		mean_accuracy = np.mean(total_accuracy)
		return mean_loss, mean_accuracy
	
	def test(self, data, batch_size):
		num_examples = data.num_examples
		total_loss = []
		total_accuracy = []
		for i in range(num_examples // batch_size):
			batch = data.next_batch(batch_size)
			feed_dict = {
				self.images: batch[0],
				self.labels: batch[1],
				self.is_training: False,
			}
			fetches = [self.cross_entropy, self.accuracy]
			loss, accuracy = self.sess.run(fetches, feed_dict=feed_dict)
			total_loss.append(loss)
			total_accuracy.append(accuracy)
		mean_loss = np.mean(total_loss)
		mean_accuracy = np.mean(total_accuracy)
		remain_num = num_examples % batch_size
		if remain_num != 0:
			batch = data.next_batch(remain_num)
			feed_dict = {
				self.images: batch[0],
				self.labels: batch[1],
				self.is_training: False,
			}
			fetches = [self.cross_entropy, self.accuracy]
			loss, accuracy = self.sess.run(fetches, feed_dict=feed_dict)
			
			mean_loss = (mean_loss * (num_examples - remain_num) + loss * remain_num) / num_examples
			mean_accuracy = (mean_accuracy * (num_examples - remain_num) + accuracy * remain_num) / num_examples
		return mean_loss, mean_accuracy
	
	def save_config(self, save_path, print_info=True):
		os.makedirs(save_path, exist_ok=True)
		net_save_path = os.path.join(save_path, 'net.config')
		json.dump(self.net_config.get_config(), open(net_save_path, 'w'), indent=4)
		if print_info: print('Network configs dump to %s' % save_path)
		run_save_path = os.path.join(save_path, 'run.config')
		json.dump(self.run_config.get_config(), open(run_save_path, 'w'), indent=4)
		if print_info: print('Run configs dump to %s' % run_save_path)
	
	def save_init(self, save_path, print_info=True):
		os.makedirs(save_path, exist_ok=True)
		save_path = os.path.join(save_path, 'init')
		to_save_init = self.net_config.renew_init(self)
		to_save_init['dataset'] = self.run_config.dataset
		pickle.dump(to_save_init, open(save_path, 'wb'))
		if print_info: print('Network weights dump to %s' % save_path)
	
	def pure_train(self):
		n_epochs = self.run_config.n_epochs
		batch_size = self.run_config.batch_size

		for epoch in range(1, n_epochs + 1):
			learning_rate = self.run_config.learning_rate(epoch)
			
			# train one epoch
			data = self.data_provider.train
			num_examples = data.num_examples
			for i in range(num_examples // batch_size):
				batch = data.next_batch(batch_size)
				images, labels = batch
				feed_dict = {
					self.images: images,
					self.labels: labels,
					self.learning_rate: learning_rate,
					self.is_training: True,
				}
				fetches = self.train_step
				self.sess.run(fetches, feed_dict=feed_dict)
	
	def save_model(self, global_step=None):
		self.saver.save(self.sess, self.save_path, global_step=global_step)
	
	def load_model(self):
		try:
			self.saver.restore(self.sess, self.save_path)
		except Exception:
			raise IOError('Failed to to load model '
						  'from save path: %s' % self.save_path)
		print('Successfully load model from save path: %s' % self.save_path)
	
	def log_loss_accuracy(self, loss, accuracy, epoch, prefix, should_print=True, write2file=True):
		if should_print:
			print('mean cross_entropy: %f, mean accuracy: %f' % (loss, accuracy))
		summary = tf.Summary(value=[
			tf.Summary.Value(
				tag='loss_%s' % prefix, simple_value=float(loss)),
			tf.Summary.Value(
				tag='accuracy_%s' % prefix, simple_value=float(accuracy))
		])
		self.summary_writer.add_summary(summary, epoch)
		if write2file and prefix == 'valid':
			with open('%s/console.txt' % self.logs_path, 'a') as fout:
				fout.write('%d: mean cross_entropy: %f, mean accuracy: %f\n' % (epoch, loss, accuracy))
	
	@staticmethod
	def _count_trainable_params():
		total_parameters = 0
		for variable in tf.trainable_variables():
			shape = variable.get_shape()
			variable_parameters = 1
			for dim in shape:
				variable_parameters *= dim.value
			total_parameters += variable_parameters
		print('Total training params: %.2fM' % (total_parameters / 1e6))
	
	@staticmethod
	def dropout(_input, keep_prob, is_training):
		if keep_prob < 1:
			output = tf.cond(
				is_training,
				lambda: tf.nn.dropout(_input, keep_prob),
				lambda: _input
			)
		else:
			output = _input
		return output
	
	@staticmethod
	def weight_variable(shape, name, initializer):
		return tf.get_variable(
			name,
			shape=shape,
			initializer=initializer,
		)
		
	@staticmethod
	def avg_pool(_input, k=2, s=2):
		ksize = [1, k, k, 1]
		strides = [1, s, s, 1]
		padding = 'VALID'
		# if stride = 1, keep the image size unchanged
		if s == 1: padding = 'SAME'
		output = tf.nn.avg_pool(_input, ksize, strides, padding)
		return output
	
	@staticmethod
	def max_pool(_input, k=2, s=2):
		ksize = [1, k, k, 1]
		strides = [1, s, s, 1]
		padding = 'VALID'
		# if stride = 1, keep the image size unchanged
		if s == 1: padding = 'SAME'
		output = tf.nn.max_pool(_input, ksize, strides, padding)
		return output

	@staticmethod
	def conv2d(_input, out_features, kernel_size, strides=1, padding='SAME', param_initializer=None):
		if kernel_size == 1: padding = 'VALID'
		
		in_features = int(_input.get_shape()[-1])
		if not param_initializer: param_initializer = {}
		kernel = BasicModel.weight_variable(
			[kernel_size, kernel_size, in_features, out_features],
			name='kernel',
			initializer=param_initializer.get('kernel', tf.contrib.layers.variance_scaling_initializer())
		)
		output = tf.nn.conv2d(_input, kernel, [1, strides, strides, 1], padding)
		return output
	
	@staticmethod
	def fc_layer(_input, out_units, use_bias=False, param_initializer=None):
		features_total = int(_input.get_shape()[-1])
		if not param_initializer: param_initializer = {}
		W = BasicModel.weight_variable(
			[features_total, out_units], name='W',
			initializer=param_initializer.get('W', tf.contrib.layers.xavier_initializer())
		)
		output = tf.matmul(_input, W)
		if use_bias:
			bias = BasicModel.weight_variable(
				[out_units], name='bias',
				initializer=param_initializer.get('bias', tf.constant_initializer([0.0] * out_units))
			)
			output += bias
		return output
		
	@staticmethod
	def batch_norm(_input, is_training, epsilon=1e-3, decay=0.999, param_initializer=None):
		output = tf.contrib.layers.batch_norm(
			_input, scale=True, is_training=is_training, param_initializers=param_initializer,
			updates_collections=None, epsilon=epsilon, decay=decay)
		return output

	@staticmethod
	def activation(_input, activation='relu'):
		if activation == 'relu':
			return tf.nn.relu(_input)
		elif activation == 'tanh':
			return tf.tanh(_input)
		elif activation == 'sigmoid':
			return tf.sigmoid(_input)
		elif activation == 'softmax':
			return tf.nn.softmax(_input)
		elif activation is None:
			return _input
		else:
			raise ValueError('Do not support %s' % activation)

	@staticmethod
	def build_optimizer(learning_rate, opt_name, opt_param):
		if opt_name == 'momentum':
			return tf.train.MomentumOptimizer(learning_rate, **opt_param)
		elif opt_name == 'adam':
			return tf.train.AdamOptimizer(learning_rate, **opt_param)
		else:
			raise ValueError('Do not support the optimizer type: %s' % opt_name)
	
	@staticmethod
	def flatten(_input):
		input_shape = _input.shape.as_list()
		if len(input_shape) != 2:
			return tf.reshape(_input, [-1, np.prod(input_shape[1:])])
		else:
			return _input
