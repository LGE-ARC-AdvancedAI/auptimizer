#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

PyTorch to TFLite
=================

Use https://github.com/nerox8664/pytorch2keras for conversion.

Example
-------

.. code-block:: bash

   $ python -m dlconvert.pytorch_to_keras -i model.pt -o model.h5 \\
       --input_shape 1,3,224,224 --net net.py --net_name Net

"""
import tf2onnx # to resolve potential import error of pytorch2keras
from pytorch2keras import pytorch_to_keras
from tensorflow import lite, keras, __version__ 
from typing import List
from os import path, remove
import torch
from absl import flags, app
from .utils import reset_flag

FLAGS = flags.FLAGS
reset_flag()

from .utils import load_package
from .to_tflite import create_converter

flags.DEFINE_string("model", "model.pt", "input model", short_name="i")
flags.DEFINE_string("output", "model.h5", "output keras model", short_name="o")
flags.DEFINE_list("input_shape", "1,3,224,224", "input tensor shape")
flags.DEFINE_string("net", "net.py", "network definition file")
flags.DEFINE_string("net_name", "Net", "class name of the defined network")
flags.register_validator("model", path.isfile, message="missing input model")
flags.register_validator("net", path.isfile, message="missing model definition file")

def model_loader(filename: str) -> lite.TFLiteConverter:
    """TF 1.x and 2.x tflite converter loading function

    Args:
        filename (str): Keras model file

    Returns:
        lite.TFLiteConverter: TFLite converter to be used
    """
    if __version__[0] == "2":
        model = keras.models.load_model(filename)
        return lite.TFLiteConverter.from_keras_model(model)
    return lite.TFLiteConverter.from_keras_model_file(filename)

def convert(model: str, output: str, input_shape: List[int], net_path, net_name):
    """Convert PyTorch model to tfLite model
    
    Args:
        model (str): PyTorch model file path  
        output (str): output file name for Keras  
        input_shape (List[int]): Tensor shape for input  
        net_path ([type]): Python script defines the model  
        net_name ([type]): PyTorch model class in the `net_path` file.
    """
    
    x = torch.randn(*input_shape, requires_grad=True) # pylint: disable=no-member
    load_package(net_path, net_name)
    model = torch.load(model)
    
    # convert to keras model first
    # change_ordering experimental, change BCHW to BHWC to enable conversion to tflite
    k_model = pytorch_to_keras(model, x, [input_shape[1:]], verbose=False, change_ordering = True)
    k_model.save("tmp.h5")

    # convert to tflite model
    converter = create_converter("tmp.h5", model_loader)
    tflite_model = converter.convert()
    with open(output, "wb") as f:
        f.write(tflite_model) 
    remove("tmp.h5")
      

def _main(_):
    input_shape = [int(i) for i in FLAGS.input_shape]
    convert(FLAGS.model, FLAGS.output, input_shape, FLAGS.net, FLAGS.net_name)

if __name__ == "__main__":
    app.run(_main)