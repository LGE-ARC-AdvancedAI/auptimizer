#!/bin/bash

#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

#get user arguments for environment files and model data
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -e|--environment)
    ENVIRONMENT="$2"
    shift
    shift
    ;;
    -f|--modelfile)
    TEXTFILE="$2"
    shift
    shift
    ;;
    -m|--modellist)
    MODELS="$2"
    shift
    shift
    ;;
esac
done
set -- "${POSITIONAL[@]}"

#check if environment file is available
if [[ -z $ENVIRONMENT ]]; then
    echo "Profiler needs an environment file. Please see documentation."
    echo "Exiting."
    exit 1
fi

#check if no model is provided
if [[ -z $TEXTFILE ]] && [[ -z $MODELS ]]; then
    statscript.sh $ENVIRONMENT
    source $ENVIRONMENT #need the OUTPUTFILE Variable.
    if test -f "$OUTPUTFILE"; then
        python3 -m aup.profiler.calculate $OUTPUTFILE
    fi
    exit 1
fi

set +e

#run statscript for model textfile and compile usage stats
if [[ -n $TEXTFILE ]]; then
    for model in $(< "$TEXTFILE") ; do
        echo "Running $model" 
        statscript.sh $ENVIRONMENT $model
    done
    python3 -m aup.profiler.compile_stats $ENVIRONMENT $TEXTFILE

fi

#run statscript for model list and compile usage stats
if [[ -n $MODELS ]]; then 
    IFS=',' read -ra MODELSARR <<< "$MODELS"
    for model in "${MODELSARR[@]}" ; do
        echo "Running $model" 
        statscript.sh $ENVIRONMENT $model
    done
    python3 -m aup.profiler.compile_stats $ENVIRONMENT $MODELS
fi





