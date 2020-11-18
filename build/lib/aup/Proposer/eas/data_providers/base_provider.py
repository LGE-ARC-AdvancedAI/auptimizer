import numpy as np


class DataSet:
	"""Class to represent some dataset: train, validation, test"""
	
	@property
	def num_examples(self):
		"""Return qtty of examples in dataset"""
		raise NotImplementedError
	
	def next_batch(self, batch_size):
		"""Return batch of required size of data, labels"""
		raise NotImplementedError


class ImagesDataSet(DataSet):
	"""Dataset for images that provide some often used methods"""
	
	@staticmethod
	def measure_mean_and_std(images):
		# for every channel in image
		means = []
		stds = []
		# for every channel in image(assume this is last dimension)
		for ch in range(images.shape[-1]):
			means.append(np.mean(images[:, :, :, ch]))
			stds.append(np.std(images[:, :, :, ch]))
		return means, stds
	
	@staticmethod
	def shuffle_images_and_labels(images, labels):
		rand_indexes = np.random.permutation(images.shape[0])
		shuffled_images = images[rand_indexes]
		shuffled_labels = labels[rand_indexes]
		return shuffled_images, shuffled_labels
	
	@staticmethod
	def normalize_images(images, normalization_type, meanstd=None):
		"""
		Args:
			images: numpy 4D array
			normalization_type: `str`, available choices:
				- divide_255
				- divide_256
				- by_channels
			meanstd
		"""
		if normalization_type is not None:
			if normalization_type == 'divide_255':
				images = images / 255
			elif normalization_type == 'divide_256':
				images = images / 256
			elif normalization_type == 'by_channels':
				images = images.astype('float64')
				# for every channel in image(assume this is last dimension)
				means, stds = meanstd
				for i in range(images.shape[-1]):
					images[:, :, :, i] = ((images[:, :, :, i] - means[i]) / stds[i])
			else:
				raise Exception('Unknown type of normalization')
		return images
	
	
class DataProvider:
	_SEED = 88
	
	@property
	def data_shape(self):
		"""Return shape as python list of one data entry"""
		raise NotImplementedError
	
	@property
	def n_classes(self):
		"""Return `int` of num classes"""
		raise NotImplementedError
	
	def labels_to_one_hot(self, labels):
		"""Convert 1D array of labels to one hot representation
		
		Args:
			labels: 1D numpy array
		"""
		new_labels = np.zeros((labels.shape[0], self.n_classes))
		new_labels[range(labels.shape[0]), labels] = np.ones(labels.shape)
		return new_labels
	
	@staticmethod
	def labels_from_one_hot(labels):
		"""Convert 2D array of labels to 1D class based representation
		
		Args:
			labels: 2D numpy array
		"""
		return np.argmax(labels, axis=1)
