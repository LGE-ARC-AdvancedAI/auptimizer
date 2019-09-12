# For developing purpose only

Demonstrate that when job failed, the experiment will end peacefully.

## job failure case

`test.py` will fail to return result when `time=3`.
When we search with `experiment_test.json` as :

    python3 -m aup experiment_test.json
    
It will print something like:

    2018-10-17 12:02:02 - aup.EE.Resource.CPUResourceManager - CRITICAL - Failed to run job:
    ******/Examples/job_failure_control/test.py
    ******/Examples/job_failure_control/jobs/79.json
    2018-10-17 12:02:02 - aup.EE.Experiment - CRITICAL - Stop Experiment due to job failure
    Best job (80) with score 4.000000 in experiment 14
    
And if we run with `--ignore_fail`, **Auptimizer** will skip the failed one, and keep running.


    2018-10-17 12:04:56 - aup.EE.Resource.CPUResourceManager - CRITICAL - Failed to run job:
    Examples/job_failure_control/test.py
    Examples/job_failure_control/jobs/83.json
    Best job (90) with score 10.000000 in experiment 15

The second experiment finishes all planned jobs.


## experiment ill-configuration

Other `experiment_no_*.json` files demonstrate ill-configured experiment setup.