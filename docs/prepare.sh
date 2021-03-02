#!/usr/bin/env bash
# this file is used for generating doc for github CI environment

cd docs
pip install -r requirements.txt
pip install tensorflow==2.3.1

mkdir ~/.aws
cat > ~/.aws/config << EOL
[default]
region=us-east-1
output=json
EOL

cd ..