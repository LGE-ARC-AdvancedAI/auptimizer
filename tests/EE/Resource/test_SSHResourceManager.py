import unittest
from aup.EE.Resource.SSHResourceManager import *


class SSHResourceManagerTestCase(unittest.TestCase):
    def test_parse_hostname(self):
        self.assertRaises(ValueError, parse_hostname, "testip")
        self.assertRaises(Exception, parse_hostname, "a@b:cc")

        self.assertRaises(IOError, parse_hostname, "a@b non-file")
        self.assertTupleEqual(('a', 'b', 22, None), parse_hostname("a@b"))


if __name__ == '__main__':
    unittest.main()
