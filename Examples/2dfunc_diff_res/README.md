# Rosenbrock demo for different resources

## CPU

    python -m aup.setup cpu.ini
	python -m aup exp_cpu.json

## GPU

Using a file contains the GPU ID per line will create GPU resources accordingly

	python -m aup.setup cpu.ini --gpu gpu.txt --overwrite
	python -m aup exp_gpu.json
	
## multi-node

For multi node environment, first set up the ssh key (see [here](https://help.ubuntu.com/community/SSH/OpenSSH/Keys) as example), then either use IP for node, or use node name with IP in `/etc/hosts` file.  In `node.txt`, each line contains `<username>:<nodename/IP>[:port]`, where port number is optional (default 22).

	python -m aup.setup cpu.ini --node node.txt --overwrite
	python -m aup exp_node.json
	
Also, it is important to add `workingdir` for remote execution.

## Passive mode

Passive mode is used for debugging purpose.  It helps users to run training code manually and check potential problem in
the training code.

    python -m aup experiment_passive.json

The code will create the job configuration file, interactively ask you to run the script, and ask for the result from your training code.
e.g. 

    # Job running path is Examples/2dfunc_diff_res
    # Config is at Examples/2dfunc_diff_res/jobs/452.json
    Job command is:
    Examples/2dfunc_diff_res/rosenbrock_hpo.py
    Return results:

Then you should run the command in another terminal like:
    
    ./rosenbrock_hpo.py ./jobs/452.json
    
You will see something like:
 
    #Auptimizer:232.78278278806914
    
Once you paste the result back to **Auptimizer**, it will ask you for the next one.

