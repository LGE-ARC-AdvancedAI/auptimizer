#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

# Compute the overall inference time for a given tflite model

import onnxruntime as rt
import numpy as np
import time


WARMUP = 10
ITER = 600
CONSTANT = 0.5


def compute(model_path):
    now = time.monotonic()
    sess = rt.InferenceSession(model_path)
    input_det = sess.get_inputs()[0]
    label_det = sess.get_outputs()[0]
    input_name = input_det.name
    input_shape = input_det.shape
    
    if 'N' in input_shape:
        input_shape[input_shape.index('N')] = 1
    input_shape[0] = 1
    print("input_shape", input_shape)    
    t1 = time.monotonic() - now
    now = time.monotonic()
    
    for i in range(WARMUP):
        X_test = np.random.random(size=input_shape).astype(np.float32)
        pred_onx = sess.run(None, {input_name: X_test})[0]
    t2 = time.monotonic() - now
    now = time.monotonic()
    for i in range(ITER):
        X_test = np.random.random(size=input_shape).astype(np.float32)
        pred_onx = sess.run(None, {input_name: X_test})[0]
    t3 = time.monotonic() - now    
    return t1, t2/float(WARMUP), t3/float(ITER)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("test_perf_onnx.py <model_path>")
        
    print(compute(sys.argv[1]))