from ..meta_controller.base_controller import WiderActorNet, DeeperActorNet, EncoderNet, BaseController
import tensorflow as tf
import os
from tensorflow.python.ops import array_ops
from ..models.basic_model import BasicModel
import shutil
import numpy as np


class RLNet2NetController(BaseController):
	def save(self, global_step=None):
		self.saver.save(self.sess, self.save_path, global_step=global_step)
	
	def load(self):
		if os.path.isfile('%s/model.ckpt.index' % self.path):
			try:
				self.saver.restore(self.sess, self.save_path)
			except Exception:
				print('Failed to to load model '
								'from save path: %s' % self.save_path)
			print('Successfully load model from save path: %s' % self.save_path)
		else:
			print('No model files in ' + '%s/model.ckpt.index' % self.path)
	
	def __init__(self, path, entropy_penalty,
				 encoder: EncoderNet, wider_actor: WiderActorNet, deeper_actor: DeeperActorNet, opt_config):
		BaseController.__init__(self, path)
		self.entropy_penalty = entropy_penalty
		
		self.encoder = encoder
		self.wider_actor = wider_actor
		self.deeper_actor = deeper_actor
		self.opt_config = opt_config
		
		self.graph = tf.Graph()
		self.obj, self.train_step = None, None
		with self.graph.as_default():
			self._define_input()
			self.build_forward()
			self.build_training_process()
			self.global_variables_initializer = tf.global_variables_initializer()
			self.saver = tf.train.Saver()
		self._initialize_session()
	
	def _define_input(self):
		self.learning_rate = tf.placeholder(
			tf.float32,
			shape=[],
			name='learning_rate')
		self.is_training = tf.placeholder(tf.bool, shape=[], name='is_training')
		self.wider_seg_deeper = tf.placeholder(tf.int32, shape=[], name='wider_seg_deeper')
		
		self.wider_decision_trajectory = tf.placeholder(
			tf.int32,
			shape=[None, self.encoder.num_steps],
			name='wider_decision_trajectory',
		)  # [wider_batch_size, num_steps]
		self.wider_decision_mask = tf.placeholder(
			tf.float32,
			shape=[None, self.encoder.num_steps],
			name='wider_decision_mask',
		)  # [wider_batch_size, num_steps]
		
		self.deeper_decision_trajectory = tf.placeholder(
			tf.int32,
			shape=[None, self.deeper_actor.decision_num],
			name='deeper_decision_trajectory',
		)  # [deeper_batch_size, deeper_decision_num]
		
		self.deeper_decision_mask = tf.placeholder(
			tf.float32,
			shape=[None, self.deeper_actor.decision_num],
			name='deeper_decision_mask',
		)  # [deeper_batch_size, deeper_decision_num]
		
		self.reward = tf.placeholder(
			tf.float32,
			shape=[None],
			name='reward',
		)  # [batch_size]
		self.has_deeper = tf.placeholder(
			tf.bool,
			shape=[],
			name='has_deeper',
		)
		
	def update_controller(self, learning_rate, wider_seg_deeper, wider_decision_trajectory, wider_decision_mask,
						  deeper_decision_trajectory, deeper_decison_mask, reward, block_layer_num, input_seq, seq_len):
		has_deeper = wider_seg_deeper < len(input_seq)
		feed_dict = {
			self.learning_rate: learning_rate,
			self.wider_seg_deeper: wider_seg_deeper,
			self.wider_decision_trajectory: wider_decision_trajectory,
			self.wider_decision_mask: wider_decision_mask,
			self.deeper_decision_trajectory: deeper_decision_trajectory,
			self.deeper_decision_mask: deeper_decison_mask,
			self.reward: reward,
			self.is_training: True and has_deeper,
			self.deeper_actor.block_layer_num: block_layer_num,
			self.encoder.input_seq: input_seq,
			self.encoder.seq_len: seq_len,
			self.has_deeper: has_deeper,
		}
		self.sess.run(self.train_step, feed_dict=feed_dict)
		
	def build_forward(self):
		encoder_output, encoder_state = self.encoder.build()
		feed2wider_output = encoder_output[:self.wider_seg_deeper]
		feed2deeper_output = encoder_output[self.wider_seg_deeper:]
		if isinstance(encoder_state, tf.contrib.rnn.LSTMStateTuple):
			encoder_state_c = encoder_state.c
			encoder_state_h = encoder_state.h
			
			feed2wider_c = encoder_state_c[:self.wider_seg_deeper]
			feed2wider_h = encoder_state_h[:self.wider_seg_deeper]
			feed2wider_state = tf.contrib.rnn.LSTMStateTuple(c=feed2wider_c, h=feed2wider_h)
			
			feed2deeper_c = encoder_state_c[self.wider_seg_deeper:]
			feed2deeper_h = encoder_state_h[self.wider_seg_deeper:]
			feed2deeper_state = tf.contrib.rnn.LSTMStateTuple(c=feed2deeper_c, h=feed2deeper_h)
		elif isinstance(encoder_state, tf.Tensor):
			feed2wider_state = encoder_state[:self.wider_seg_deeper]
			feed2deeper_state = encoder_state[self.wider_seg_deeper:]
		else:
			raise ValueError
		
		self.wider_actor.build_forward(feed2wider_output)
		self.deeper_actor.build_forward(feed2deeper_output, feed2deeper_state, self.is_training,
										self.deeper_decision_trajectory)
		
	def build_training_process(self):
		raise NotImplementedError
	
	def sample_wider_decision(self, input_seq, seq_len):
		batch_size = len(seq_len)
		wider_decision, wider_probs = self.sess.run(
			fetches=[self.wider_actor.decision, self.wider_actor.probs],
			feed_dict={
				self.encoder.input_seq: input_seq,
				self.encoder.seq_len: seq_len,
				self.wider_seg_deeper: batch_size,
			}
		)  # [batch_size, num_steps]
		return wider_decision, wider_probs
	
	def sample_deeper_decision(self, input_seq, seq_len, block_layer_num):
		deeper_decision, deeper_probs = self.sess.run(
			fetches=[self.deeper_actor.decision, self.deeper_actor.probs],
			feed_dict={
				self.encoder.input_seq: input_seq,
				self.encoder.seq_len: seq_len,
				self.wider_seg_deeper: 0,
				self.is_training: False,
				self.deeper_actor.block_layer_num: block_layer_num,
				self.deeper_decision_trajectory: -np.ones([len(seq_len), self.deeper_actor.decision_num])
			}
		)  # [batch_size, decision_num]
		return deeper_decision, deeper_probs
	
	def _initialize_session(self):
		config = tf.ConfigProto()
		# restrict model GPU memory utilization to min required
		config.gpu_options.allow_growth = True
		self.sess = tf.Session(graph=self.graph, config=config)
		
		self.sess.run(self.global_variables_initializer)
		shutil.rmtree(self.logs_path, ignore_errors=True)
		self.summary_writer = tf.summary.FileWriter(self.logs_path, graph=self.graph)

	def get_wider_entropy(self):
		wider_entropy = -tf.multiply(tf.log(self.wider_actor.probs), self.wider_actor.probs)
		wider_entropy = tf.reduce_sum(wider_entropy, axis=2)
		wider_entropy = tf.multiply(wider_entropy, self.wider_decision_mask)
		wider_entropy = tf.div(tf.reduce_sum(wider_entropy, axis=1), tf.reduce_sum(self.wider_decision_mask, axis=1))
		wider_entropy = tf.reduce_mean(wider_entropy)
		return wider_entropy
	
	def get_deeper_entropy(self):
		deeper_entropy = []
		for _i in range(self.deeper_actor.decision_num):
			deeper_probs = self.deeper_actor.probs[_i]
			entropy = -tf.multiply(tf.log(deeper_probs + 1e-10), deeper_probs)
			entropy = tf.reduce_sum(entropy, axis=1)
			deeper_entropy.append(entropy)
		deeper_entropy = tf.reduce_mean(deeper_entropy)
		return deeper_entropy
	

class ReinforceNet2NetController(RLNet2NetController):
	def build_training_process(self):
		wider_side_obj, wider_entropy = tf.cond(
			tf.greater(self.wider_seg_deeper, 0),
			lambda: self.get_wider_side_obj(),
			lambda: (tf.constant(0.0, dtype=tf.float32), tf.constant(0.0, dtype=tf.float32))
		)
		batch_size = array_ops.shape(self.reward)[0]
		deeper_side_obj, deeper_entropy = tf.cond(
			self.has_deeper,
			lambda: self.get_deeper_side_obj(),
			lambda: (tf.constant(0.0, dtype=tf.float32), tf.constant(0.0, dtype=tf.float32))
		)
		self.obj = wider_side_obj + deeper_side_obj
		entropy_term = wider_entropy * tf.cast(self.wider_seg_deeper, tf.float32) + \
					   deeper_entropy * tf.cast(batch_size - self.wider_seg_deeper, tf.float32)
		entropy_term /= tf.cast(batch_size, tf.float32)
		
		optimizer = BasicModel.build_optimizer(self.learning_rate, self.opt_config[0], self.opt_config[1])
		self.train_step = optimizer.minimize(- self.obj - self.entropy_penalty * entropy_term)
		
	def get_wider_side_obj(self):
		wider_side_reward = self.reward[:self.wider_seg_deeper]

		# obj from wider side
		wider_trajectory = tf.one_hot(self.wider_decision_trajectory, depth=max(self.wider_actor.out_dim, 2))
		wider_probs = tf.reduce_max(tf.multiply(wider_trajectory, self.wider_actor.probs), axis=2)
		wider_probs = tf.log(wider_probs)  # [wider_batch_size, num_steps]
		wider_probs = tf.multiply(wider_probs, self.wider_decision_mask)
		wider_probs = tf.multiply(wider_probs, tf.reshape(wider_side_reward, shape=[-1, 1]))
		
		wider_side_obj = tf.reduce_sum(wider_probs)
		return wider_side_obj, self.get_wider_entropy()
	
	def get_deeper_side_obj(self):
		deeper_side_reward = self.reward[self.wider_seg_deeper:]

		# obj from deeper side
		deeper_side_obj = []
		for _i in range(self.deeper_actor.decision_num):
			decision_trajectory = self.deeper_decision_trajectory[:, _i]
			deeper_decision_mask = self.deeper_decision_mask[:, _i]
			decision_trajectory = tf.one_hot(decision_trajectory, depth=self.deeper_actor.out_dims[_i])
			deeper_probs = tf.reduce_max(tf.multiply(decision_trajectory, self.deeper_actor.probs[_i]), axis=1)
			deeper_probs = tf.log(deeper_probs)  # [deeper_batch_size]
			deeper_probs = tf.multiply(deeper_probs, deeper_decision_mask)
			deeper_probs = tf.multiply(deeper_probs, deeper_side_reward)
			
			deeper_side_obj.append(tf.reduce_sum(deeper_probs))
		deeper_side_obj = tf.reduce_sum(deeper_side_obj)
		return deeper_side_obj, self.get_deeper_entropy()

