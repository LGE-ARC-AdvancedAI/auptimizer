#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

import torchvision.models as models
import torch
import torch.nn as nn
import tensorflow.keras.applications as applications
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.python.util import deprecation
import string
deprecation._PRINT_DEPRECATION_WARNINGS = False

keras_model_list = [
    "VGG16", "ResNet50", "InceptionV3", "MobileNet", "MobileNetV2", "DenseNet121", "NASNetMobile"
]

classification_model_list = [
    "resnet18", "alexnet", "squeezenet1_0", "densenet161", "inception_v3",
    "googlenet", "shufflenet_v2_x1_0", "mobilenet_v2", "resnext50_32x4d",
    "wide_resnet50_2", "mnasnet1_0"
]

segmentation_model_list = [
    "fcn_resnet50", "deeplabv3_resnet50"
]

video_model_list = [
    "r3d_18", "mc3_18", "r2plus1d_18"
]

class Test_Model_Classification(object):
    def __init__(self, model_name):
        self.func = getattr(models, model_name)

    def create_model(self):
        model = self.func()
        return model

class Test_Model_Segmentation(object):
    def __init__(self, model_name):
        self.func = getattr(models.segmentation, model_name)

    def create_model(self):
        model = self.func()
        return model

class Test_Model_Video(object):
    def __init__(self, model_name):
        self.func = getattr(models.video, model_name)

    def create_model(self):
        model = self.func()
        return model

def create_torch_cnn_models():
    
    for model_name in classification_model_list:
        if model_name == "inception_v3":
            x = torch.randn(1, 3, 299, 299)
        else:
            x = torch.randn(1, 3, 224, 224)
        print("Creating model", model_name)
        model = Test_Model_Classification(model_name).create_model()
        model.eval()
        y = model(x)
        save_path = "test_models/" + model_name + ".pt"
        torch.save(model, save_path)
        print("Created Pytorch model saved to", save_path)

    for model_name in segmentation_model_list:
        x = torch.randn(1, 3, 224, 224)
        print("Creating model", model_name)
        model = Test_Model_Segmentation(model_name).create_model()
        model.eval()
        y = model(x)
        save_path = "test_models/" + model_name + ".pt"
        torch.save(model, save_path)
        print("Created Pytorch model saved to", save_path)

    for model_name in video_model_list:
        x = torch.randn(1, 3, 16, 112, 112)
        print("Creating model", model_name)
        model = Test_Model_Video(model_name).create_model()
        model.eval()
        y = model(x)
        save_path = "test_models/" + model_name + ".pt"
        torch.save(model, save_path)
        print("Created Pytorch model saved to", save_path)

def create_keras_cnn_models():
    for cls_name in keras_model_list:
        model_func = getattr(applications, cls_name)
        model = model_func(weights = None)
        save_path = "test_models/" + cls_name + ".h5"
        model.save(save_path) 
        print("Created Keras model saved to", save_path)

def create_tf_lstm_model():
    tf.compat.v1.disable_eager_execution()
    
    # Create a test lstm network based on Pytorch doc
    model = keras.Sequential()
    # Add an Embedding layer expecting input vocab of size 1000, and
    # output embedding dimension of size 64.
    model.add(layers.Embedding(input_dim=1000, output_dim=64))
    model.add(layers.LSTM(128))
    model.add(layers.Dense(10))
    
    # save checkpoint
    model.save_weights("test_models/lstm_ckpt/ckpt")
    ckpt_meta = "test_models/lstm_ckpt/ckpt.meta"
    tf.compat.v1.train.export_meta_graph(filename=ckpt_meta)

    # save keras model
    model.save("test_models/lstm.h5")

    # save TF savedmodel
    model.save("test_models/lstm_savedmodel", save_format='tf')

    # print model input/output names
    print("lstm model input name:", model.input)
    print("lstm model output name:",model.output)


def create_tf_gru_model():
    tf.compat.v1.disable_eager_execution()

    # Create a test rnn network based on Pytorch doc
    model = keras.Sequential()
    model.add(layers.Embedding(input_dim=1000, output_dim=64))
    # The output of GRU will be a 3D tensor of shape (batch_size, timesteps, 256)
    model.add(layers.GRU(256, return_sequences=True))
    # The output of SimpleRNN will be a 2D tensor of shape (batch_size, 128)
    model.add(layers.SimpleRNN(128))
    model.add(layers.Dense(10))
    
    # save keras model
    model.save("test_models/gru_TF1.h5")
    # save TF savedmodel
    model.save("test_models/gru_savedmodel",save_format='tf')
    # print model input/output names
    print("gru model input name:", model.input)
    print("gru model output name:", model.output)


if __name__ == "__main__":
    create_torch_cnn_models()
    create_keras_cnn_models()
    create_tf_lstm_model()
    create_tf_gru_model()