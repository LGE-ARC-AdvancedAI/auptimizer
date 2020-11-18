import tensorflow as tf
from tensorflow.contrib import rnn
from tensorflow.python.ops import array_ops
from ..models.basic_model import BasicModel
import numpy as np
import os


class BaseController:
	def __init__(self, path):
		self.path = os.path.realpath(path)
		os.makedirs(self.path, exist_ok=True)
		
	def load(self):
		raise NotImplementedError
	
	def save(self, global_step=None):
		raise NotImplementedError
	
	@property
	def save_path(self):
		return '%s/model.ckpt' % self.path
	
	@property
	def logs_path(self):
		return '%s/logs' % self.path


class Vocabulary:
	def __init__(self, token_list):
		token_list = ['PAD'] + token_list
		self.vocab = {}
		for idx, token in enumerate(token_list):
			self.vocab[token] = idx
			self.vocab[idx] = token
	
	@property
	def size(self):
		return len(self.vocab) // 2
	
	def get_code(self, token_list):
		return [self.vocab[token] for token in token_list]
	
	def get_token(self, code_list):
		return [self.vocab[code] for code in code_list]
	
	@property
	def pad_code(self):
		return self.vocab['PAD']


def embedding(_input, vocab_size, embedding_dim, name='embedding'):
	"""
	_input: [batch_size, max_num_steps]
	output: [batch_size, max_num_steps, embedding_dim]
	"""
	# embedding
	embedding_var = tf.get_variable(
		name=name,
		shape=[vocab_size, embedding_dim],
		initializer=tf.random_uniform_initializer(-np.sqrt(3), np.sqrt(3)),
		dtype=tf.float32,
	)  # Initialize embeddings to have variance=1.
	output = tf.nn.embedding_lookup(embedding_var, _input)
	return output


def build_cell(units, cell_type='lstm', num_layers=1):
	if num_layers > 1:
		cell = rnn.MultiRNNCell([
			build_cell(units, cell_type, 1) for _ in range(num_layers)
		])
	else:
		if cell_type == "lstm":
			cell = rnn.LSTMCell(units)
		elif cell_type == "gru":
			cell = rnn.GRUCell(units)
		else:
			raise ValueError('Do not support %s' % cell_type)
	return cell


def seq_len(sequence):
	"""
	assume padding with zero vectors
	sequence: [batch_size, num_steps, features]
	length: [batch_size]
	"""
	used = tf.sign(tf.reduce_max(tf.abs(sequence), 2))
	length = tf.reduce_sum(used, 1)
	length = tf.cast(length, tf.int32)
	return length


class EncoderNet:
	def __init__(self, num_steps, vocab, embedding_dim, rnn_units, rnn_type='bi_lstm', rnn_layers=1):
		self.num_steps = num_steps
		self.vocab = vocab
		self.embedding_dim = embedding_dim
		
		self.rnn_units = rnn_units
		self.rnn_type = rnn_type
		self.rnn_layers = rnn_layers
		
		# placeholder
		self.seq_len, self.input_seq = None, None
		# op
		self.encoder_output, self.encoder_state = None, None
	
	@property
	def bidirectional(self):
		return self.rnn_type.startswith('bi')
	
	@property
	def cell_type(self):
		return self.rnn_type.split('_')[-1]
	
	def _define_input(self):
		self.seq_len = tf.placeholder(
			tf.int32,
			[None],
			'seq_len'
		)  # length of each sequence, shape = [batch_size, ]
		
		self.input_seq = tf.placeholder(
			tf.int32,
			[None, self.num_steps],
			'input_seq'
		)  # input sequence, shape = [batch_size, num_steps]
	
	def build(self):
		self._define_input()
		
		output = self.input_seq
		output = embedding(output, self.vocab.size, self.embedding_dim, name='layer_embedding')
		input_dim = self.embedding_dim
		
		# Prepare data shape to match rnn function requirements
		# Current data input shape: [batch_size, num_steps, input_dim]
		# Required shape: 'num_steps' tensors list of shape [batch_size, input_dim]
		output = tf.transpose(output, [1, 0, 2])
		output = tf.reshape(output, [-1, input_dim])
		output = tf.split(output, self.num_steps, 0)
		
		if self.bidirectional:
			# 'num_steps' tensors list of shape [batch_size, rnn_units * 2]
			fw_cell = build_cell(self.rnn_units, self.cell_type, self.rnn_layers)
			bw_cell = build_cell(self.rnn_units, self.cell_type, self.rnn_layers)
			output, state_fw, state_bw = rnn.static_bidirectional_rnn(
				fw_cell, bw_cell, output, dtype=tf.float32, sequence_length=self.seq_len, scope='encoder')
			
			if isinstance(state_fw, tf.contrib.rnn.LSTMStateTuple):
				encoder_state_c = tf.concat([state_fw.c, state_bw.c], axis=1, name='bidirectional_concat_c')
				encoder_state_h = tf.concat([state_fw.h, state_bw.h], axis=1, name='bidirectional_concat_h')
				state = tf.contrib.rnn.LSTMStateTuple(c=encoder_state_c, h=encoder_state_h)
			elif isinstance(state_fw, tf.Tensor):
				state = tf.concat([state_fw, state_bw], axis=1, name='bidirectional_concat')
			else:
				raise ValueError
		else:
			# 'num_steps' tensors list of shape [batch_size, rnn_units]
			cell = build_cell(self.rnn_units, self.cell_type, self.rnn_layers)
			output, state = rnn.static_rnn(cell, output, dtype=tf.float32, sequence_length=self.seq_len,
										   scope='encoder')
		
		output = tf.stack(output, axis=0)  # [num_steps, batch_size, rnn_units]
		output = tf.transpose(output, [1, 0, 2])  # [batch_size, num_steps, rnn_units]
		self.encoder_output = output
		self.encoder_state = state
		return output, state


class WiderActorNet:
	def __init__(self, out_dim, num_steps, net_type='simple', net_config=None):
		self.out_dim = out_dim
		self.num_steps = num_steps
		self.net_type = net_type
		self.net_config = net_config
		
		# placeholder
		self.decision, self.probs = None, None
	
	def build_forward(self, _input):
		output = _input  # [batch_size, num_steps, rnn_units]
		feature_dim = int(output.get_shape()[2])  # rnn_units
		output = tf.reshape(output, [-1, feature_dim])  # [batch_size * num_steps, rnn_units]
		final_activation = 'sigmoid' if self.out_dim == 1 else 'softmax'
		if self.net_type == 'simple':
			net_config = [] if self.net_config is None else self.net_config
			with tf.variable_scope('wider_actor'):
				for layer in net_config:
					units, activation = layer.get('units'), layer.get('activation', 'relu')
					output = BasicModel.fc_layer(output, units, use_bias=True)
					output = BasicModel.activation(output, activation)
				logits = BasicModel.fc_layer(output, self.out_dim, use_bias=True)  # [batch_size * num_steps, out_dim]
			probs = BasicModel.activation(logits, final_activation)  # [batch_size * num_steps, out_dim]
			probs_dim = self.out_dim
			if self.out_dim == 1:
				probs = tf.concat([1 - probs, probs], axis=1)
				probs_dim = 2
				
			self.decision = tf.multinomial(tf.log(probs), 1)  # [batch_size * num_steps, 1]
			self.decision = tf.reshape(self.decision, [-1, self.num_steps])  # [batch_size, num_steps]
			self.probs = tf.reshape(probs, [-1, self.num_steps, probs_dim])  # [batch_size, num_steps, out_dim]
		else:
			raise ValueError('Do not support %s' % self.net_type)


class DeeperActorNet:
	def __init__(self, decision_num, out_dims, embedding_dim,
				 cell_type='lstm', rnn_layers=1, attention_config=None):
		self.decision_num = decision_num
		self.out_dims = out_dims
		self.embedding_dim = embedding_dim
		
		self.cell_type = cell_type
		self.rnn_layers = rnn_layers
		self.attention_config = attention_config
		
		# placeholder
		self.block_layer_num = None
		# op
		self.decision, self.probs = None, None
	
	def _define_input(self):
		self.block_layer_num = tf.placeholder(
			tf.int32,
			shape=[None, self.out_dims[0]]
		)  # [batch_size, block_num]
	
	def build_decoder_cell(self, encoder_state):
		if isinstance(encoder_state, tf.contrib.rnn.LSTMStateTuple):
			rnn_units = int(encoder_state.c.get_shape()[1])
			assert self.cell_type == 'lstm', 'Do not match'
		else:
			rnn_units = int(encoder_state.get_shape()[1])
		cell = build_cell(rnn_units, self.cell_type, self.rnn_layers)
		return cell
	
	def build_forward(self, encoder_output, encoder_state, is_training, decision_trajectory):
		self._define_input()
		self.decision, self.probs = [], []
		
		batch_size = array_ops.shape(encoder_output)[0]
		if self.attention_config is None:
			cell = self.build_decoder_cell(encoder_state)
			cell_state = encoder_state
			cell_input = tf.zeros(shape=[batch_size], dtype=tf.int32)
			with tf.variable_scope('deeper_actor'):
				for _i in range(self.decision_num):
					cell_input_embed = embedding(cell_input, 1 if _i == 0 else self.out_dims[_i - 1],
												 self.embedding_dim, name='deeper_actor_embedding_%d' % _i)
					with tf.variable_scope('rnn', reuse=(_i > 0)):
						cell_output, cell_state = cell(cell_input_embed, cell_state)
					with tf.variable_scope('classifier_%d' % _i):
						logits_i = BasicModel.fc_layer(cell_output, self.out_dims[_i], use_bias=True)
					act_i = 'softmax'
					probs_i = BasicModel.activation(logits_i, activation=act_i)  # [batch_size, out_dim_i]
					if _i == 1:
						# determine the layer index for deeper actor
						# require mask
						one_hot_block_decision = tf.one_hot(cell_input, depth=self.out_dims[0], dtype=tf.int32)
						max_layer_num = tf.multiply(self.block_layer_num, one_hot_block_decision)
						max_layer_num = tf.reduce_max(max_layer_num, axis=1)  # [batch_size]
						layer_mask = tf.sequence_mask(max_layer_num, self.out_dims[1], dtype=tf.float32)
						probs_i = tf.multiply(probs_i, layer_mask)
						# rescale the sum to 1
						probs_i = tf.divide(probs_i, tf.reduce_sum(probs_i, axis=1, keep_dims=True))
					decision_i = tf.multinomial(tf.log(probs_i), 1)  # [batch_size, 1]
					decision_i = tf.cast(decision_i, tf.int32)
					decision_i = tf.reshape(decision_i, shape=[-1])  # [batch_size]
					
					cell_input = tf.cond(
						is_training,
						lambda: decision_trajectory[:, _i],
						lambda: decision_i,
					)
					self.decision.append(decision_i)
					self.probs.append(probs_i)
				self.decision = tf.stack(self.decision, axis=1)  # [batch_size, decision_num]
		else:
			raise NotImplementedError


