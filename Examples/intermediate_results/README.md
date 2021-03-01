# Intermediate Results

## Usage

Intermediate results are non-final results for each job of an experiment used
in order to better tell the evolution of a job through time. Each intermediate
"result" can be one or multiple values.

In order to let auptimizer know that intermediate results are to be tracked,
the flag "track_intermediate_results" should be passed in the experiment config
under "resource_args":

    "resource_args":
    {
        "track_intermediate_results": true
    }

The script used in the experiment then has to call `aup.print_result` each time 
an intermediate result is to be saved. The last reported result will always be taken 
as the final result of a job. Please refer to `quad_euation_min/quad_min.py` for training script modification.

The intermediate results will be shown on the dashboard if tracked.

## Examples

Take the following main function in a user script:

    def main(x, a=2, b=4, c=5, n=10):
        it = 1.0
        for _ in range(n):
            res = x*x*a + x*b + c
            res += it
            it -= 1.0 / 10
            aup.print_result(res)

1. If "track_intermediate_results" is `false` or missing, all results except the last one will be discarded:

```json
{
    "proposer": ...,
    "script": ...,
    "resource": ...,
    "n_parallel": ...,
    "target": "min",
    "n_samples": ...,
    "parameter_config": [
        {
            "name": "x",
            "range": [-1.0, 100.0],
            "type": "float"
        }
    ]
}  
```
```
sqlite> SELECT COUNT(*) FROM intermediate_result;
COUNT(*)
0
```

2. If "track_intermediate_results" is present in the config and is set to `true`, then the values will be found in the database (200 jobs with 10 intermediate results each):

```json
{
    "proposer": ...,
    "script": ...,
    "resource": ...,
    "n_parallel": ...,
    "target": "min",
    "n_samples": ...,
    "resource_args": 
    {
        "track_intermediate_results": true
    },
    "parameter_config": [
        {
            "name": "x",
            "range": [-1.0, 100.0],
            "type": "float"
        }
    ]
}  
```
```
sqlite> SELECT COUNT(*) FROM intermediate_result;
2000
```