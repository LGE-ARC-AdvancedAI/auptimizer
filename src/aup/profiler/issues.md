# Known issues

+ Remove any dangling Dockerfiles in the working directory before executing Profiler as they might interfere.
 
+ Once Docker has started running, if you hit Ctrl+Z, you will only exit from the Profiler script. Docker will continue to run in the background until completion unless you stop the Docker process separately.