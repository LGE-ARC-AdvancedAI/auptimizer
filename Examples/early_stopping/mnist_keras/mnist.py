#!/usr/bin/env python3

"""
MNIST convolutional network using Keras
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import aup

import tensorflow as tf
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

from math import log

import sys

num_epochs = 5
batch_size = 64
num_classes = 10
input_shape = (28, 28, 1)

# Load example MNIST data and pre-process it
# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

# Scale images to the [0, 1] range
x_train = x_train.astype("float32") / 255
x_test = x_test.astype("float32") / 255
# Make sure images have shape (28, 28, 1)
x_train = np.expand_dims(x_train, -1)
x_test = np.expand_dims(x_test, -1)

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

def get_flops():
    run_meta = tf.RunMetadata()
    opts = tf.profiler.ProfileOptionBuilder.float_operation()

    # We use the Keras session graph in the call to the profiler.
    flops = tf.profiler.profile(graph=keras.backend.get_session().graph,
                                run_meta=run_meta, cmd='op', options=opts)

    return flops.total_float_ops  # Prints the "flops" of the model.
  
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

    model.compile(loss="categorical_crossentropy",
                optimizer=keras.optimizers.Adam(learning_rate=kwargs['learning_rate']),
                metrics=["accuracy"])

    return model

class CustomCallback(keras.callbacks.Callback):
    flops = None

    def on_train_batch_end(self, batch, logs=None):
      if batch % 10 == 0:
        val_acc = logs["acc"]
        aup.print_result((val_acc-1.0) / (log(self.flops)))

    def on_train_begin(self, logs=None):
      self.flops = get_flops()

def init(**kwargs):
  global model
  model = get_model(**kwargs)

@aup.aup_args
def do_train(learning_rate=0.001, dropout=0.1, conv1=32, conv2=64):
  global model

  model.fit(
    x_train,
    y_train,
    batch_size=batch_size,
    epochs=num_epochs,
    verbose=1,
    validation_split=0.5,
    callbacks=[CustomCallback()],
  )

  res = model.evaluate(
    x_test,
    y_test,
    batch_size=batch_size,
    verbose=1,
  )

  flops = get_flops()

  return (res[1]-1.0) / log(flops)


if __name__ == '__main__':

  if len(sys.argv) < 2:
      print("config file required")
      exit(1)

  do_train(sys.argv[1])

