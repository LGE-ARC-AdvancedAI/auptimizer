from .expdir_monitor.expdir_monitor import ExpdirMonitor
import argparse


"""
Given a expdir, run the exp
"""
parser = argparse.ArgumentParser()
parser.add_argument(
	'--test', action='store_true',
	help='Test model for required dataset if pretrained model exists.'
)
parser.add_argument(
	'--valid', action='store_true',
)
parser.add_argument(
	'--valid_size', type=int, default=-1,
)
parser.add_argument('--path', type=str)
parser.add_argument('--restore', action='store_true')
args = parser.parse_args()
expdir_monitor = ExpdirMonitor(args.path)
test_performance = expdir_monitor.run(pure=False, restore=args.restore, test=args.test, valid=args.valid,
                                      valid_size=args.valid_size)
if args.valid:
	print('validation performance: %s' % test_performance)
else:
	print('test performance: %s' % test_performance)
