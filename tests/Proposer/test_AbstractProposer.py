import unittest
from aup.Proposer import AbstractProposer as AP


class AbstractTestCase(unittest.TestCase):
    def test_create_param_config(self):
        self.assertRaises(ValueError, AP.create_param_config, 'name', [0, 1], 'wrong_type')
        self.assertRaises(ValueError, AP.create_param_config, 'name', [0, 1, 2], 'int')
        self.assertRaises(ValueError, AP.create_param_config, 'name', [0], 'float')
        self.assertDictEqual(AP.create_param_config('v1', [0, 1], 'float'),
                             {'name': 'v1', 'range': [0, 1], 'type': 'float'})
