#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

# Compute the overall inference time for a given tflite model
import tensorflow as tf
from tflite_runtime.interpreter import Interpreter
import tensorflow.random
import numpy as np
import time
import os


WARMUP = 1
ITER = 500
CONSTANT = 0.5


def compute(model_path):
    now = time.monotonic()
    intp = Interpreter(model_path)
    x = intp.tensor(intp.get_input_details()[0]['index'])
    iy = intp.get_output_details()[0]['index']
    intp.allocate_tensors()
    t1 = time.monotonic() - now
    now = time.monotonic()
    
    for i in range(WARMUP):
        #x().fill(CONSTANT)
        x =np.random.rand()
        intp.invoke()
        y = intp.get_tensor(iy)
    t2 = time.monotonic() - now
    now = time.monotonic()
    for i in range(ITER):
        #x().fill(CONSTANT)
        x =np.random.rand()
        intp.invoke()
        y = intp.get_tensor(iy)
    t3 = time.monotonic() - now    
    return t1, t2/float(WARMUP), t3/float(ITER)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("test_acc.py <model_path>")
        
    print(compute(sys.argv[1]))