#!/usr/bin/env python

import numpy as np



def create_tf():
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.python.util import deprecation
    deprecation._PRINT_DEPRECATION_WARNINGS = False
    tf.compat.v1.disable_eager_execution()
    a = layers.Input(shape=(224,224,3), name="input")
    b = layers.Conv2D(kernel_size=(3,3), filters=16, activation="relu")(a)
    b = layers.MaxPool2D(pool_size=(5,5))(b)
    b = layers.Conv2D(kernel_size=(3,3), filters=64, activation="relu")(b)
    b = layers.Flatten()(b)
    b = layers.Dense(10, activation='softmax', name="output")(b)
    model = keras.Model(inputs=a, outputs=b)

    model.compile(optimizer='sgd', loss='categorical_crossentropy')
    # save TF checkpoint
    model.save_weights("./test_model_ckpt/ckpt")
    tf.compat.v1.train.export_meta_graph(filename="./test_model_ckpt/ckpt.meta")
    # save keras model
    model.save("./test_model.h5")
    # save TF savedmodel
    model.save("./test_savedmodel", save_format='tf')

    print(model.input)
    print(model.output)

def create_pytorch():
    import torch
    from pytorch_model import Net

    x = torch.randn(1, 3, 224, 224)
    m = Net()
    y = m(x)
    m.eval()
    torch.save(m, 'test_model.pt')


if __name__ == "__main__":
    create_tf()
    create_pytorch()
