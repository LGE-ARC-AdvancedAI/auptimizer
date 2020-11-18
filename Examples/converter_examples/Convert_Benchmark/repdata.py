"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Create a synthetic tf.dataset for inference speed measure
"""
import numpy as np
from absl import flags
import sys

def parse_arg():
    try:
        idx = sys.argv.index("--custom_data")
        custom_data = str(sys.argv[idx+1:][0])
    except ValueError:
        custom_data = "1,224,224,3,1000"
    return custom_data

def get_dataset():
    custom_data = parse_arg()
    print(custom_data)
    batch_size, img_len, img_wid, channel_size, label_size = [int(x) for x in custom_data.split(",")] 

    labels = np.random.randint(0, label_size, size=batch_size).astype(np.float)
    imgs = np.random.random(size=(batch_size, img_len, img_wid, channel_size))
    
    class Dataset:
        def __init__(self, data):
            self.data = data
        
        def numpy(self):
            return self.data[np.newaxis,:]

    for i in range(batch_size):
        yield Dataset(imgs[i]), Dataset(labels[i])
