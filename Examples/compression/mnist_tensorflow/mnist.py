#!/usr/bin/env python3

"""
MNIST convolutional network using pytorch
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

from aup import print_result, aup_args

import tensorflow as tf
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import tqdm

from math import log

import sys

import aup

num_epochs = 1
batch_size = 64
num_classes = 10
input_shape = (28, 28, 1)


def get_model(**kwargs):
    model = keras.Sequential(
      [
          keras.Input(shape=input_shape),
          layers.Conv2D(kwargs['conv1'], kernel_size=(3, 3), activation="relu"),
          layers.MaxPooling2D(pool_size=(2, 2)),
          layers.Conv2D(kwargs['conv2'], kernel_size=(3, 3), activation="relu"),
          layers.MaxPooling2D(pool_size=(2, 2)),
          layers.Flatten(),
          layers.Dropout(kwargs['dropout']),
          layers.Dense(num_classes, activation="softmax"),
      ]
    )

    return model

    
def test_model(model, test_dataset):
  correct = []
  for (batch, (images, labels)) in enumerate(test_dataset):
    logits = model(images)
    correct += list(labels.numpy() == np.argmax(logits.numpy(), axis=1))
  return np.mean(correct)


def main(config):
  (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.mnist.load_data()

  train_dataset = tf.data.Dataset.from_tensor_slices(
    (tf.cast(train_images[...,tf.newaxis]/255, tf.float32),
    tf.cast(train_labels,tf.int64)))
  train_dataset = train_dataset.shuffle(1000).batch(32)
  
  test_dataset = tf.data.Dataset.from_tensor_slices(
    (tf.cast(test_images[...,tf.newaxis]/255, tf.float32),
    tf.cast(test_labels,tf.int64)))
  test_dataset = test_dataset.shuffle(1000).batch(32)

  model = get_model(dropout=0.1, conv1=32, conv2=64)
  optimizer = tf.keras.optimizers.Adam()
  loss_object = tf.keras.losses.SparseCategoricalCrossentropy()

  model.load_weights("mnist_pretrained.h5")

  def train_step(images, labels):
    with tf.GradientTape() as tape:
      logits = model(images, training=True)
      tf.debugging.assert_equal(logits.shape, (32, 10))
      loss_value = loss_object(labels, logits)

    grads = tape.gradient(loss_value, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))

  compressor = aup.compression.create_compressor(model, config)
  compressor.compress()

  for epoch in range(num_epochs):
    for (batch, (images, labels)) in enumerate(train_dataset):
      train_step(images, labels)
    acc = test_model(model, test_dataset)
    print ('Epoch {} finished - test_acc={}'.format(epoch, acc))

  compressor.export_model("mnist_compressed.h5", **config)

  aup.print_result(acc - 1.)


if __name__ == '__main__':
  config = aup.BasicConfig().load(sys.argv[1])
  main(config)

