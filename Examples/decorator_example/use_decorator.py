#----------------------------------
#!/usr/bin/env python
import sys
from aup import aup_args

@aup_args
def func(hyperparameter):
    return 'training results'

if __name__ == "__main__":
    func(sys.argv[1])
#----------------------------------
#!/usr/bin/env python
import tensorflow as tf
from aup import aup_flags

FLAGS = tf.app.flags.FLAGS
# some arguments defined in flags

@aup_flags(FLAGS)
def main():
    return "training results"

if __name__ == "__main__":
    tf.app.run()
#----------------------------------




