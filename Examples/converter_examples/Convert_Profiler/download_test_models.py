#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

import os
import json
import argparse
import logging
import requests
import shutil

all_urls = {"densenet": "https://storage.googleapis.com/download.tensorflow.org/models/tflite/model_zoo/upload_20180427/densenet_2018_04_27.tgz",
      "squeezenet": "https://storage.googleapis.com/download.tensorflow.org/models/tflite/model_zoo/upload_20180427/squeezenet_2018_04_27.tgz",
      "nasnet_mobile": "https://storage.googleapis.com/download.tensorflow.org/models/tflite/model_zoo/upload_20180427/nasnet_mobile_2018_04_27.tgz"}
model_folder = "input_models"

def download_all_url(all_urls, model_folder):

    for model, url in all_urls.items():
        tarFilename = url.split('/')[-1]

        # check if the tar file already exists on disk
        # if not tarFilename[0].isdigit() and os.path.isfile(tarFilename):
        if os.path.isfile(tarFilename):
            print ("File already exists, skipping ", url)
            continue
        print("Downloading ", url)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(tarFilename, 'wb') as f:
                f.write(response.raw.read())
        save_folder = model_folder
        shutil.unpack_archive(tarFilename, save_folder)



if __name__ == '__main__':
    download_all_url(all_urls, model_folder)
