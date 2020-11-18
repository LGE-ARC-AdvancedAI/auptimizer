#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

import os
import json
import argparse
import logging
import requests
import shutil

def download_all_url(url_file, model_folder):
    try:
        with open(url_file) as f:
           all_urls = json.load(f)
    except Exception as e:
        logging.fatal("The url json file could not be opened")
        raise e

    for model_type in all_urls:
        url_list = all_urls[model_type]
        for model_name in url_list:
            url = url_list[model_name]
            # print(url)
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
            if tarFilename[0].isdigit():
                save_folder = model_folder + "/" + model_name
            else:
                save_folder = model_folder
            shutil.unpack_archive(tarFilename, save_folder)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_file", required=True, help="Json file with urls for downloading models")
    parser.add_argument("--model_folder", default="test_models", help="folder path for saving downloaded models")
    args, unknownargs = parser.parse_known_args()
    download_all_url(args.url_file, "test_models")
