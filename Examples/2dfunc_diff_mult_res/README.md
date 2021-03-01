# Return multiple results

This feature allows the user to save and track multiple secondary results along with the primary result for the HPO experiment. 
Auptimizer still uses the main result for the HPO algorithm, but saves the secondary records in the database under the table `multiple_results`.

## Usage 

The feature can be used by adding the following parameter to the experiment configuration file:

    "resource_args": {
      "multi_res_labels": ["x", "y", …]
    }
    
In the above example, {"x", "y", …} are the secondary parameters the user wants to track and record. 
The user script would then return the results as a list including the primary result 'res' along with the secondary parameters as follows:

    @aup_args
    def HPO():
        res = calculate_results()
        return [res, x, y, …]
        
In the above example 'res' is the primary result which is always the first index of the returned array when using multiple results, and is used by HPO algorithm.
The other indices are matched directly with the array provided in the `multi_res_labels` parameter. 
Hence, The length of the returned array from HPO script is '1 + length of multi_res_labels' parameter.


## Example code 

    python -m aup.setup cpu.ini
	python -m aup exp_cpu.json

The code will create the job configuration file, interactively ask you to run the script, and ask for the result from your training code.
e.g. 

    # Job running path is Examples/2dfunc_diff_mult_res
    # Config is at Examples/2dfunc_diff_mult_res/jobs/452.json
    Job command is:
    Examples/2dfunc_diff_mult_res/rosenbrock_hpo.py
    Return results:

Then you should run the command in another terminal like:
    
    ./rosenbrock_hpo.py ./jobs/452.json
    
You will see something like:
 
    #Auptimizer:232.78278278806914,-0.8297799529742598,2.2032449344215808

The first result is the main result, the next are "x" and "y" defined by multi_res_labels.
 
Once you paste the result back to **Auptimizer**, it will ask you for the next one.

