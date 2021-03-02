# Job Failure control Examples

This folder contains examples that demonstrate the different scenarios under job failure conditions and how Auptimizer handles them gracefully. 
The examples can be broadly divided into two categories - 

## 1. Job failures based on incorrect or incomplete experiment configuration (For debugging purposes only) 

`experiment_no_*.json` files demonstrate an ill-configured experiment setup. They will result in standard error conditions and Auptimizer will report them, providing users with detailed description of the failure.

- `experiment_no_nsample.json` : Auptimizer Error ( KeyError: "Specify number of samples to randomly draw")
- `experiment_no_param_config.json` : Auptimizer Error (KeyError: "Specify the parameter configuration 'parameter_config' to be searched")
- `experiment_no_proposer.json` : Auptimizer Error (KeyError: "Specify the optimization 'proposer'")
- `experiment_no_resource.json` : Auptimizer Error (KeyError: "Missing required value for 'resource'")
- `experiment_no_script.json` : Auptimizer Error (KeyError: "Missing required value for 'script'")
- `experiment_extra_argument.json` : No Auptimizer Error (for extra variable c)

## 2. Experiment persistence and job retries upon job failure

The following examples show how Auptimizer provides control for allowing job retries and experiment continuation upon job failures. 

- `experiment_job_retries.json` : Auptimizer retries failed job 3 times.
- `experiment_job_ignore_fail.json` : Auptimizer ignores failed job, and continues the experiment
- `experiment_job_retries_ignore_fail.json` : Auptimizer retries failed job 3 times. If all retries fail, Auptimizer ignores the failed job and continues the experiment.

Auptimizer uses the `job_failure` variable to control this behavior, with the following parameters:
- `job_retries` : number of times to retry a failed job, default is 0. Preference is given to a different resource, if multiple resources are available.
- `ignore_fail` : whether to continue the experiment if a job fails, default is False. Currently [BOHB, EAS, Hyperband] proposers do not support experiment continuation upon job failure.

The examples use `test.py` file, which will fail to return any result when `time=3`. When we run the base case `experiment_test.json` as:

    python3 -m aup experiment_test.json
    
It will print something like:

    2018-10-17 12:02:02 - aup.EE.Resource.CPUResourceManager - CRITICAL - Failed to run job:
    ******/Examples/job_failure_control/test.py
    ******/Examples/job_failure_control/jobs/79.json
    2018-10-17 12:02:02 - aup.EE.Experiment - CRITICAL - Stop Experiment due to job failure
    Best job (80) with score 4.000000 in experiment 14


## experiment ill-configuration

Other `experiment_no_*.json` files demonstrate ill-configured experiment setup.
