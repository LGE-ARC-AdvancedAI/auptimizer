#!/bin/bash
set -e

BLUE='\033[1;34m'
NC='\033[0m' # No Color

echo "" > test_summary_tf1.out

docker build -t conv_tf1 -f Dockerfile_tf1 ../..
echo -e "${BLUE}#### Test conv_tf1 with eager execution ####${NC}"
docker run --rm -e TF2TEST=1 conv_tf1 | tee -a test_summary_tf1.out

echo -e "${BLUE}#### Test conv_tf1 without eager execution ####${NC}"
docker run --rm -e TF2TEST= conv_tf1 | tee -a test_summary_tf1.out