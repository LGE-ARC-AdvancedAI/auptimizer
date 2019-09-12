import tensorflow as tf
import numpy as np
from .layer_cascade import LayerCascade


class LayerMultiBranch:
	def __init__(self, _id, branches, merge=None, in_bottle=None, out_bottle=None):
		self._id = _id
		self.in_bottle = in_bottle
		self.branches = branches
		self.out_bottle = out_bottle
		self.merge = merge
		if self.merge == 'add':
			out_dim = []
			for branch in self.branches:
				out_dim.append(branch.out_features_dim)
			assert np.std(out_dim) == 0, '<%s> require the output dim of all branches are the same' % self.merge
		elif self.merge is None:
			assert len(self.branches) == 1, 'Invalid'
		
		self.output_op = None
	
	@property
	def id(self):
		return self._id
	
	@id.setter
	def id(self, value):
		self._id = value
	
	@property
	def out_features_dim(self):
		if self.out_bottle:
			return self.out_bottle.out_features_dim
		out_dim = []
		for branch in self.branches:
			out_dim.append(branch.out_features_dim)
		if self.merge == 'concat':
			return np.sum(out_dim)
		elif self.merge == 'add' or self.merge is None:
			return out_dim[0]
		else:
			pass
	
	@property
	def depth(self):
		depth = 0
		if self.in_bottle:
			depth += self.in_bottle.depth
		if self.out_bottle:
			depth += self.out_bottle.depth
		branch_depth = []
		for branch in self.branches:
			branch_depth.append(branch.depth)
		depth += np.max(branch_depth)
		return depth
	
	def get_str(self):
		in_bottle_str = 'N' if self.in_bottle is None else self.in_bottle.get_str()
		branches_str = [branch.get_str() for branch in self.branches]
		branches_str = '+'.join(branches_str)
		out_bottle_str = 'N' if self.out_bottle is None else self.out_bottle.get_str()
		return '%s~%s~%s' % (in_bottle_str, branches_str, out_bottle_str)
	
	def build(self, _input, densenet, store_output_op=False):
		with tf.variable_scope(self._id):
			output = _input
			# in bottle
			if self.in_bottle:
				output = self.in_bottle.build(output, densenet, store_output_op=store_output_op)
			# branches
			branch_out = []
			for branch in self.branches:
				branch_out.append(branch.build(output, densenet, store_output_op=store_output_op))
			if self.merge == 'concat':
				output = tf.concat(branch_out, axis=3)
			elif self.merge == 'add':
				output = tf.add_n(branch_out)
			elif self.merge is None:
				output = branch_out[0]
			else:
				raise ValueError('Do not support <%s>' % self.merge)
			# out bottle
			if self.out_bottle:
				output = self.out_bottle.build(output, densenet, store_output_op=store_output_op)
		if store_output_op:
			self.output_op = output
		return output
	
	def get_config(self):
		return {
			'_id': self._id,
			'merge': self.merge,
			'branches': [branch.get_config() for branch in self.branches],
			'in_bottle': None if self.in_bottle is None else self.in_bottle.get_config(),
			'out_bottle': None if self.out_bottle is None else self.out_bottle.get_config(),
		}
	
	def renew_init(self, densenet):
		return {
			'_id': self._id,
			'branches': [branch.renew_init(densenet) for branch in self.branches],
			'in_bottle': None if self.in_bottle is None else self.in_bottle.renew_init(densenet),
			'out_bottle': None if self.out_bottle is None else self.out_bottle.renew_init(densenet),
		}
	
	@staticmethod
	def set_from_config(config_json, init=None):
		_id = config_json['_id']
		merge = config_json['merge']
		branches = []
		for _i, branch_config in enumerate(config_json['branches']):
			branch_init = init['branches'][_i] if init is not None else None
			branch = LayerCascade.set_from_config(branch_config, branch_init)
			branches.append(branch)
		in_bottle = config_json['in_bottle']
		if in_bottle:
			in_bottle_init = init['in_bottle'] if init is not None else None
			in_bottle = LayerCascade.set_from_config(in_bottle, in_bottle_init)
		out_bottle = config_json['out_bottle']
		if out_bottle:
			out_bottle_init = init['out_bottle'] if init is not None else None
			out_bottle = LayerCascade.set_from_config(out_bottle, out_bottle_init)
		return LayerMultiBranch(_id, branches, merge, in_bottle=in_bottle, out_bottle=out_bottle)
	
	"""
	Network Transformation Operations
	"""
	
	def prev_widen(self, indices, magnifier, noise=None):
		if self.in_bottle:
			self.in_bottle.prev_widen(indices, magnifier, noise=noise)
		else:
			for branch in self.branches:
				branch.prev_widen(indices, magnifier, noise=noise)
	
	def widen(self, loc, new_width, widen_type='output_dim', noise=None):
		if loc['multi-branch'] == 'in_bottle':
			assert self.in_bottle is not None, 'Invalid'
			change_out_dim, indices, magnifier = self.in_bottle.widen(loc['layer'], new_width, widen_type, noise=noise)
			if change_out_dim:
				for branch in self.branches:
					branch.prev_widen(indices, magnifier, noise=noise)
			return False, None, None
		elif loc['multi-branch'] == 'out_bottle':
			assert self.out_bottle is not None, 'Invalid'
			change_out_dim, indices, magnifier = self.out_bottle.widen(loc['layer'], new_width, widen_type, noise=noise)
			return change_out_dim, indices, magnifier
		elif loc['multi-branch'] == 'branch':
			branch_idx = loc['branch']
			branch = self.branches[branch_idx]
			old_branch_out_dim = branch.out_features_dim
			change_out_dim, indices, magnifier = branch.widen(loc['layer'], new_width, widen_type, noise=noise)
			if change_out_dim:
				assert self.merge != 'add', 'Invalid'
				prev_branch_out_dim = 0
				for _i in range(0, branch_idx):
					prev_branch_out_dim += self.branches[_i].out_features_dim
				post_branch_out_dim = 0
				for _i in range(branch_idx + 1, len(self.branches)):
					post_branch_out_dim += self.branches[_i].out_features_dim
				old_size = prev_branch_out_dim + old_branch_out_dim + post_branch_out_dim
				base = np.arange(old_size)
				indices = np.concatenate([
					base[:prev_branch_out_dim],
					indices + prev_branch_out_dim,
					base[prev_branch_out_dim + old_branch_out_dim:]
				])
				magnifier = np.concatenate([
					[1] * prev_branch_out_dim,
					magnifier,
					[1] * post_branch_out_dim,
				])
				if self.out_bottle is None:
					return True, indices, magnifier
				else:
					self.out_bottle.prev_widen(indices, magnifier, noise=noise)
					return False, None, None
			else:
				return False, None, None
		else:
			raise ValueError('Do not support %s' % loc['multi-branch'])
	
	def deepen(self, loc, new_layer_config, input_dim):
		if loc['multi-branch'] == 'in_bottle':
			assert self.in_bottle is not None, 'Invalid'
			return self.in_bottle.deepen(loc['layer'], new_layer_config, input_dim)
		elif loc['multi-branch'] == 'out_bottle':
			assert self.out_bottle is not None, 'Invalid'
			if self.merge == 'concat': input_dim = np.sum([branch.out_features_dim for branch in self.branches])
			else: input_dim = self.branches[0].out_features_dim
			return self.out_bottle.deepen(loc['layer'], new_layer_config, input_dim)
		elif loc['multi-branch'] == 'branch':
			if self.in_bottle is not None: input_dim = self.in_bottle.out_features_dim
			return self.branches[loc['branch']].deepen(loc['layer'], new_layer_config, input_dim)
		else:
			raise ValueError('Do not support %s' % loc['multi-branch'])
		
	def remapped_branches(self, noise=None):
		if self.merge == 'add' or self.merge is None:
			size = self.out_features_dim
			indices = np.random.choice(np.arange(size), size)
			new_branches = []
			for branch in self.branches:
				new_layers = [layer.copy() for layer in branch.layers[:-1]]
				last_layer = branch.layers[-1].copy().remap(indices, noise=noise)
				new_layers.append(last_layer)
				new_branch = LayerCascade(branch.id, new_layers)
				new_branches.append(new_branch)
		elif self.merge == 'concat':
			new_branches = []
			offset = 0
			indices = []
			for branch in self.branches:
				size = branch.out_features_dim
				sub_indices = np.random.choice(np.arange(size), size)
				new_layers = [layer.copy() for layer in branch.layers[:-1]]
				last_layer = branch.layers[-1].copy().remap(sub_indices, noise=noise)
				new_layers.append(last_layer)
				new_branch = LayerCascade(branch.id, new_layers)
				new_branches.append(new_branch)
				indices.append(sub_indices + offset)
				offset += size
			indices = np.concatenate(indices)
		else:
			raise NotImplementedError
		return new_branches, indices
