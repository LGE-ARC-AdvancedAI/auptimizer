# Demo for tf.app.flags

Tensorflow flags is widely used for tensorflow to parse input arguments.
It is naturally supported by **Auptimizer** with minor modification on you existing code.

Similar to adopting **Auptimizer** for plain python training code, there are two parts of changes.

A working example is shown as `rosenbrock_hpo.py`, whereas the plain code is `rosenbrock_tf.py`.

## Modification on training code

Because `tf.flags` already takes care of the input argument, we just insert `aup.BasicConfig` properly:

```python
def main(unused_arguments):
  config = BasicConfig().load(unused[1])
  config.to_flags(FLAGS)	
	
if __name__ == "__main__"
  tf.app.run()
```

`config = BasicConfig().load(unused[1])` parses the input file for the parameter values.
And `config.to_flags(FLAGS)` assigns the value to `tensorflow.app.flags.FLAGS`, thus it can be used without changing how to access those values in the original code.

Similar to other examples, you need to call `aup.print_result()` at the end of the program to return your target to optimize.

## Modification on experiment configuration

The same configuration of experiment can be used.  See other examples for reference.


## Run

Same to other example, you now can run **Auptimizer** as

```bash
python -m aup experiment.json
```

to initiate your continuous training experiment.






