#!/bin/bash

#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

set -e
#trap "kill 0" EXIT
#exit 0
#Check if environment file containing profiling details is present.
if [[ $# -ne 1 && $# -ne 2 ]]; then
  echo "Missing environment file; use it as \`statscript.sh <env file>\`"
  exit 1
fi

echo "*********************************************************"
echo "Environment Variables"
echo "*********************************************************"

grep -v "^#" $1
source $1

#Intermediate Variables - 'test_container' and 'test_image' to help the user with debugging.
CONTAINERNAME="test_container"
IMAGENAME="test_image"

#If we are running for multiple models, model name is the second argument.
if [ $2 ]; then
    SCRIPT=$SCRIPT"\" , \""$2
    FULLPATH="${2##*/}"
    MODELNAME="${FULLPATH%.*}" 
    DOCFILE=$DOCFILE"_"$MODELNAME
    OUTPUTFILE=$MODELNAME"_"$OUTPUTFILE
    CONTAINERNAME=$MODELNAME"_con"
    IMAGENAME=$MODELNAME"_img"
fi

echo "*********************************************************"
echo "BUILDING DOCKER IMAGE"
echo "*********************************************************"


time_command="python -c 'import time; print(int(1000*time.time()))'"
#time_command='$(($(date +%s%N)/1000000))'
#time_command='$(($(gdate +%s%N)/1000000))'
rm -f $OUTPUTFILE

#Check if user-specified Dockerfile is present, otherwise create a new one using environment file. 
#Note is Dockerfile is present, it is given priority over information in the environment file.
if test ! -f "$DOCFILE"; then
    touch $DOCFILE
    echo "FROM $IMAGEREPO" >> $DOCFILE
    if [ ! -z "$APTREQUIREMENTS" ]; then
        echo "RUN apt-get update && apt-get install -y \\" >> $DOCFILE
        IFS=' ' read -r -a aptreq <<< "$APTREQUIREMENTS"
        arraylength=${#aptreq[@]}
        for (( i=1; i<${arraylength}; i++ ));
        do
           echo "${aptreq[$i-1]} \\ " >> $DOCFILE
        done
        echo "${aptreq[$arraylength-1]} " >> $DOCFILE
    fi
    echo "RUN mkdir /app" >> $DOCFILE
    echo "WORKDIR /app" >> $DOCFILE
    echo "copy $DIR ." >> $DOCFILE
    if [ ! -z "$PRERUN" ]; then 
        echo "RUN $PRERUN" >> $DOCFILE
    fi
    if [ ! -z "$PIPREQUIREMENTS" ]; then
        echo "RUN pip install $PIPREQUIREMENTS" >> $DOCFILE
    fi
    echo "CMD [\"$COMMAND\", \"$SCRIPT\"]" >> $DOCFILE

    echo "*********************************************************"
    echo "DOCKERFILE CREATED - PRINTING"
    echo "*********************************************************"
    cat $DOCFILE
fi

#Build the docker image using the Dockerfile.
docker build -f $DOCFILE -t $IMAGENAME .

#Exit if the build was unsuccessful.
if [[ $? -ne 0 ]] || [[ "$(docker images -q $IMAGENAME 2> /dev/null)" == "" ]]; then
    echo "*********************************************************"
    echo "DOCKER IMAGE FAILED. EXITING"
    echo "*********************************************************"
    exit 1
fi

#Add CPU and Memory constraints specified in the environment file.
if [ -z "$DOCKCPUS" ]; then
    CPULIMSTR=""
else
    CPULIMSTR="--cpus=$DOCKCPUS"
fi

if [ -z "$DOCKMEMORY" ]; then
    MEMLIMSTR=""
else
    MEMLIMSTR="-m=$DOCKMEMORY"
fi

#Run the docker container using the created docker image
echo "*********************************************************"
echo "RUNNING DOCKER CONTAINER"
echo "*********************************************************"

docker run $DOCKER_ARGS $CPULIMSTR $MEMLIMSTR --name $CONTAINERNAME --rm $IMAGENAME &

pid=$!
touch ${OUTPUTFILE}

#running docker stats on the container
echo "*********************************************************"
echo "RUNNING DOCKER STAT ANALYSIS"
echo "*********************************************************"


echo -e "\n"
echo -e "Profiling script: "$SCRIPT"\n" >> ${OUTPUTFILE}
echo "NAME | AVG CPU % | AVG MEM USAGE / LIMIT | NET I/O | BLOCK I/O | TIMESTAMP" | column -t -s "|" >> ${OUTPUTFILE}
echo "NAME | AVG CPU % | AVG MEM USAGE / LIMIT | NET I/O | BLOCK I/O" | column -t -s "|"


#Time counter set up
inittime=$(eval $time_command)
starttime=$(eval $time_command)

#While the script executes in the dockercontainer, repeatedly call docker stats on the container every sampletime milliseconds.
#Record the output of the docker stats in the output file.
while ps -p $pid &>/dev/null; do
    if [ "$(eval $time_command)" -gt "$((starttime + $SAMPLETIME*1000))" ]; then
        starttime=$(eval $time_command)

        #get stats for docker process
        IFS=, read -r name pids cpu mem net block <<<  "$(docker stats ${CONTAINERNAME} --no-stream --format "{{.Name}},{{.PIDs}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}")" 
        if [ "$(eval $time_command)" -gt "$((starttime + $SAMPLETIME*1000))" ]; then
            echo "WARNING: Your Query Time is too short, Docker stats take longer to compute."
        fi
        if [ -z "$name" ]; then
            break
        fi
        echo  $name"|"$cpu"|"$mem"|"$net"|"$block"|"$(eval $time_command)"" | column -t -s "|" >> ${OUTPUTFILE}
        echo  $name"|"$cpu"|"$mem"|"$net"|"$block"" | column -t -s "|"
    fi
done

endtime=$(eval $time_command)
echo "Total time taken for command = $(($endtime-$inittime)) milliseconds"

#if [ ! $2 ]; then
#Calculate the Usage stats for profiler using the output file.
#    python3 calculate.py $OUTPUTFILE
#fi

echo "*********************************************************"
echo "FINISHED"
echo "*********************************************************"
echo -e "FINISHED \n********************************************************* \n" >> ${OUTPUTFILE}
echo -e "\n"
echo -e "\n"
wait