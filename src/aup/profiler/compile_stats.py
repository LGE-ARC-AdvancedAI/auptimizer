#  Copyright (c) 2020 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

from aup.profiler import calculate
import sys
from tabulate import tabulate
from datetime import datetime
from os import path


"""
This function iterates over individual model outputs from statscript
and uses 'getUsageStats' from calculate.py to collect usage stats
and displays them together as table.
"""
def compile_results(env_file,model_names):
    today = datetime.now()
    f=open(env_file)
    line=f.readline()
    
    while line:
        if "OUTPUTFILE=" in line:
            output_file = line.split("=")[1][:-1]
            break
        line=f.readline()
        
    # handles the case for model text files.    
    if '.txt' in model_names:
        f=open(model_names)
        line = f.readline()
        results = []
        while line:
            if line[-1]=='\n':
                line=line[:-1]
            filename=line.split("/")[-1]
            filename=filename[:filename.rfind('.')]
            out=filename + "_" + output_file
            if not path.isfile(out):
                return 
            useStats = calculate.getUsageStats(out)
            stats = useStats[0]
            stats[0]=filename
            results.append(stats)
            headers = useStats[1]
            line = f.readline()

        fp=open(output_file,"a+")
        fp.write("Usage stats for Experiment ran on : "+ str(today))
        fp.write("\n")
        fp.write(tabulate(results, headers=headers))
        fp.write("\n")
        fp.write("\n")
        fp.close()
        print("Final Usage Stats")
        print(tabulate(results, headers=headers))
        
    #handles the case for model lists.
    else:
        f=model_names.split(',')
        results = []
        for model in f:
            filename=model.split("/")[-1]
            filename=filename[:filename.rfind('.')]
            out=filename + "_" + output_file
            if not path.isfile(out):
                return 
            useStats = calculate.getUsageStats(out)
            stats = useStats[0]
            stats[0]=filename
            results.append(stats)
            headers = useStats[1]

        fp=open(output_file,"a+")
        fp.write("Usage stats for Experiment ran on : "+ str(today))
        fp.write("\n")
        fp.write(tabulate(results, headers=headers))
        fp.write("\n")
        fp.write("\n")
        fp.close()
        print("Final Usage Stats")
        print(tabulate(results, headers=headers))

if __name__ == "__main__":
    env_file=sys.argv[1]
    model_names=sys.argv[2]
    compile_results(env_file,model_names)