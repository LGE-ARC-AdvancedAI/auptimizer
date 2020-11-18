#!/usr/bin/env python3

# Modified from https://github.com/aymericdamien/TensorFlow-Examples/blob/master/examples/3_NeuralNetworks/convolutional_network.py
# The trained model is evaluated by a combination of accuracy and FLOP.
#
# Original License
"""
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

All contributions by Aymeric Damien:
Copyright (c) 2015, Aymeric Damien.
All rights reserved.

All other contributions:
Copyright (c) 2015, the respective contributors.
All rights reserved.

Each contributor holds copyright over their respective contributions.
The project versioning (Git) records all such contribution source information.
"""


from __future__ import division, print_function, absolute_import

import argparse
import os
import sys
from datetime import datetime
from math import log

import tensorflow as tf
# Import MNIST data
from tensorflow.examples.tutorials.mnist import input_data

from aup import BasicConfig, print_result

# Training Parameters
num_steps = 2000
batch_size = 128

# Network Parameters
num_input = 784 # MNIST data input (img shape: 28*28)
num_classes = 10 # MNIST total classes (0-9 digits)


# Create the neural network
def conv_net(x_dict, n_classes, reuse, is_training):
    # Define a scope for reusing the variables
    with tf.variable_scope('ConvNet', reuse=reuse):
        # TF Estimator input is a dict, in case of multiple inputs
        x = x_dict['images']

        # MNIST data input is a 1-D vector of 784 features (28*28 pixels)
        # Reshape to match picture format [Height x Width x Channel]
        # Tensor input become 4-D: [Batch Size, Height, Width, Channel]
        x = tf.reshape(x, shape=[-1, 28, 28, 1])

        # Convolution Layer with 32 filters and a kernel size of 5
        conv1 = tf.layers.conv2d(x, FLAGS.conv1, 5, activation=tf.nn.relu)
        # Max Pooling (down-sampling) with strides of 2 and kernel size of 2
        conv1 = tf.layers.max_pooling2d(conv1, 2, 2)

        # Convolution Layer with 64 filters and a kernel size of 3
        conv2 = tf.layers.conv2d(conv1, FLAGS.conv2, 3, activation=tf.nn.relu)
        # Max Pooling (down-sampling) with strides of 2 and kernel size of 2
        conv2 = tf.layers.max_pooling2d(conv2, 2, 2)

        # Flatten the data to a 1-D vector for the fully connected layer
        fc1 = tf.contrib.layers.flatten(conv2)

        # Fully connected layer (in tf contrib folder for now)
        fc1 = tf.layers.dense(fc1, FLAGS.fc1)
        # Apply Dropout (if is_training is False, dropout is not applied)
        fc1 = tf.layers.dropout(fc1, rate=FLAGS.dropout, training=is_training)

        # Output layer, class prediction
        out = tf.layers.dense(fc1, n_classes)

    return out


# Define the model function (following TF Estimator Template)
def model_fn(features, labels, mode):
    # Build the neural network
    # Because Dropout have different behavior at training and prediction time, we
    # need to create 2 distinct computation graphs that still share the same weights.
    logits_train = conv_net(features, num_classes, reuse=False,
                            is_training=True)
    logits_test = conv_net(features, num_classes, reuse=True,
                           is_training=False)

    # Predictions
    pred_classes = tf.argmax(logits_test, axis=1)
    pred_probas = tf.nn.softmax(logits_test)

    # If prediction mode, early return
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=pred_classes)

        # Define loss and optimizer
    loss_op = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
        logits=logits_train, labels=tf.cast(labels, dtype=tf.int32)))
    optimizer = tf.train.AdamOptimizer(learning_rate=FLAGS.learning_rate)
    train_op = optimizer.minimize(loss_op,
                                  global_step=tf.train.get_global_step())

    # Evaluate the accuracy of the model
    acc_op = tf.metrics.accuracy(labels=labels, predictions=pred_classes)

    # TF Estimators requires to return a EstimatorSpec, that specify
    # the different ops for training, evaluating, ...
    estim_specs = tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=pred_classes,
        loss=loss_op,
        train_op=train_op,
        eval_metric_ops={'accuracy': acc_op})

    return estim_specs

def train():
    # Build the Estimator
    mnist = input_data.read_data_sets("./input_data/", one_hot=False)
    
    model = tf.estimator.Estimator(model_fn)

    # Define the input function for training
    input_fn = tf.estimator.inputs.numpy_input_fn(
        x={'images': mnist.train.images}, y=mnist.train.labels,
        batch_size=batch_size, num_epochs=None, shuffle=True)
    # Train the Model
    model.train(input_fn, steps=num_steps)

    # Evaluate the Model
    # Define the input function for evaluating
    input_fn = tf.estimator.inputs.numpy_input_fn(
        x={'images': mnist.test.images}, y=mnist.test.labels,
        batch_size=batch_size, shuffle=False)
    # Use the Estimator 'evaluate' method
    e = model.evaluate(input_fn)

    print("Testing Accuracy:", e['accuracy'])
    
    
    return e['accuracy']

def get_flop():
    run_meta = tf.RunMetadata()
    with tf.Session(graph=tf.Graph()) as sess:
        x = tf.zeros([1,784])
        out = conv_net({'images':x}, 10, False, False)
        
        opts = tf.profiler.ProfileOptionBuilder.float_operation()    
        flops = tf.profiler.profile(sess.graph, run_meta=run_meta, cmd='op', options=opts)
    print("Model FLOPs is %d"%flops.total_float_ops)
    return flops.total_float_ops


def main(_):
    log_dir = FLAGS.log_dir + "%s" % datetime.now()
    if tf.gfile.Exists(log_dir):
        tf.gfile.DeleteRecursively(log_dir)
    tf.gfile.MakeDirs(log_dir)
    acc =  train()
    flop = get_flop()
    return (acc-1)/log(flop)  # metric used in AMC


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("config file required")
        exit(1)
        
    import random
    if random.random()>0.75:
        raise Exception('failed', 'test123')

    parser = argparse.ArgumentParser()
    parser.add_argument('--learning_rate', type=float, default=0.001,
                        help='Initial learning rate')
    parser.add_argument('--dropout', type=float, default=0.1,
                        help='drop probability for training dropout.')
    parser.add_argument('--conv1', type=int, default=32,
                        help='Conv1 layer size.')
    parser.add_argument('--conv2', type=int, default=64,
                        help='Conv2 layer size.')
    parser.add_argument('--fc1', type=int, default=1024,
                        help='FC1 layer size.')
    parser.add_argument(
        '--data_dir',
        type=str,
        default=os.path.join(os.getenv('TEST_TMPDIR', './'),
                            'input_data/'),
        help='Directory for storing input data')
    parser.add_argument(
        '--log_dir',
        type=str,
        default=os.path.join(os.getenv('TEST_TMPDIR', './'),
                            'logs/'),
        help='Summaries log directory')

    FLAGS, unparsed = parser.parse_known_args()

    config = BasicConfig(**FLAGS.__dict__).load(sys.argv[1])
    FLAGS.__dict__.update(config)
    # for hyperband
    if "n_iterations" in FLAGS:
        FLAGS.max_steps = int(FLAGS.n_iterations * 100)  # 100 times n_iteration units
    print("FLAGS => " + str(FLAGS))

    val = main(config)
    print(str(val))
    
    
    print_result(val)
