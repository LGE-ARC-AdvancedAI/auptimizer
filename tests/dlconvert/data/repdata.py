"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Create a synthetic tf.dataset for testing
"""
import numpy as np


def get_dataset():
    labels = np.random.randint(0,10, size=10).astype(np.float)
    imgs = np.random.random(size=(10, 224, 224, 3))
    
    class Dataset:
        def __init__(self, data):
            self.data = data
        
        def numpy(self):
            return self.data[np.newaxis,:]


    for i in range(10):
        yield Dataset(imgs[i]), Dataset(labels[i])
        