"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.profiler.calculate module
=================

Parse profiling results obtained using :mod:`aup.profiler`.

APIs
----
"""
import sys
from tabulate import tabulate

#################################################
# see: http://goo.gl/kTQMs
SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'non_standard'  : ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'doc'           : ('B', 'kB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}

def bytes2human(n, format='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs

      >>> bytes2human(0)
      '0.0 B'
      >>> bytes2human(0.9)
      '0.0 B'
      >>> bytes2human(1)
      '1.0 B'
      >>> bytes2human(1.9)
      '1.0 B'
      >>> bytes2human(1024)
      '1.0 K'
      >>> bytes2human(1048576)
      '1.0 M'
      >>> bytes2human(1099511627776127398123789121)
      '909.5 Y'

      >>> bytes2human(9856, symbols="customary")
      '9.6 K'
      >>> bytes2human(9856, symbols="customary_ext")
      '9.6 kilo'
      >>> bytes2human(9856, symbols="iec")
      '9.6 Ki'
      >>> bytes2human(9856, symbols="iec_ext")
      '9.6 kibi'

      >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
      '9.8 K/sec'

      >>> # precision can be adjusted by playing with %f operator
      >>> bytes2human(10000, format="%(value).5f %(symbol)s")
      '9.76562 K'
    """
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776

      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]:1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])
##########################################

def getUsageStats(filename):
    """
    Function that takes an input file generated from 
    statscript.sh with usage stats sampled over certain 
    timestamps, and calculates peak and average values 
    of different parameters such as compute and memory.
    It uses tabulate library to form the table to display 
    the final stats
    """
    
    fp = open(filename, "r+")
    oline = fp.readline()

    acpu=0
    amem=0
    amemlim=0
    aneti=0
    aneto=0
    ablocki=0
    ablocko=0
    count=0
    mmem=0
    mcpu=0
    starttime = 0
    endtime=0
    name=""
    
    zero_error=0
    basic_error=0

    line = fp.readline()
    while (line):
        #print (line)
        try:
            line1 = line[:-1].split(" ")
            if(line1[2]=='--'):
                break
            cpu = float(line1[2][:-1])
            mem = human2bytes(line1[4])
            memlim = human2bytes(line1[6])
            neti = human2bytes(line1[8])
            neto = human2bytes(line1[10])
            blocki = human2bytes(line1[12])
            blocko = human2bytes(line1[14])
            name = line1[0]
            if starttime==0:
                starttime = int(line1[16])
            endtime = int(line1[16])

            if(cpu == 0.0 and mem == 0):
                zero_error=1
                break
            count+=1
            acpu = acpu + ((cpu - acpu)/count)
            amem = amem + ((mem - amem)/count)
            amemlim = amemlim + ((memlim - amemlim)/count)
            mcpu = max(mcpu, cpu)
            mmem = max(mmem, mem)
            aneti = aneti + ((neti - aneti)/count)
            aneto = aneto + ((neto - aneto)/count)
            ablocki = ablocki + ((blocki - ablocki)/count)
            ablocko = ablocko + ((blocko - ablocko)/count)

        except:
            basic_error=1

        line = fp.readline()
        
    if zero_error:
        fp.write("\nEncountered time stamps with 0 CPU and 0 Mem, process has probabaly finished; Hence discarding the timestamp.")
    #if basic_error:
        #fp.write("\nAn error occurred when processing this file")
        
    if count==0:
        fp.write("Profiler could not sample usage stats for the experiment because the sample time is too long compared to the runtime of the experiment or the experiment is too fast and finishes before sampling could start.")

    fp.write("\nUsage Stats: ")
    print("\nUsage Stats: ")

    h = ["NAME","AVG CPU %","PEAK CPU","AVG MEM USAGE / LIMIT","PEAK MEM","NET I/O","BLOCK I/O","TOTAL TIME (ms)"]

    p=[name, str(round(acpu,3))+"%", str(round(mcpu,3)), str(bytes2human(amem, symbols="doc")) + " / " + str(bytes2human(amemlim, symbols="doc")), str(bytes2human(mmem, symbols="doc")), str(bytes2human(aneti, symbols="doc")) + " / " + str(bytes2human(aneto, symbols="doc")), str(bytes2human(ablocki, symbols="doc")) + " / " + str(bytes2human(ablocko, symbols="doc")), str(endtime-starttime)]
    fp.write("\n")
    fp.write(tabulate([p], headers=h))
    print(tabulate([p], headers=h))

    fp.write("\nRefer to the documentation on how to interpret the results.")
    print("Refer to the documentation on how to interpret the results.")
    print("\n")
    fp.close()
    return (p,h)

if __name__ == "__main__":
    filename = sys.argv[1]
    getUsageStats(filename)

