"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
import os
import sys
from six import StringIO
from aup import utils
import tempfile


class UtilTestCase(unittest.TestCase):
    def test_check_missing_key(self):
        config = {"a": "b"}
        self.assertRaises(KeyError, utils.check_missing_key, config, "missing", "test")

    def test_get_default_connector(self):
        folder = tempfile.mkdtemp()
        env_file = os.path.join(folder, "env.ini")
        with open(env_file, 'w') as f:
            f.write("[Auptimizer]\n")
        self.assertRaises(KeyError, utils.get_default_connector, folder)
        with open(env_file, 'w') as f:
            f.write("[Auptimizer]\nSQL_ENGINE = wrong")
        self.assertRaises(KeyError, utils.get_default_connector, folder)
        with open(env_file, 'w') as f:
            f.write("[Auptimizer]\nSQL_ENGINE = sqlite")
        self.assertRaises(KeyError, utils.get_default_connector, folder)
        os.remove(env_file)
        os.rmdir(folder)

    def test_default_username(self):
        if "USER" in os.environ:
            username = os.environ["USER"]
            u = utils.get_default_username()
            self.assertEqual(u, username)

            del os.environ["USER"]
            u = utils.get_default_username()
            self.assertEqual(u, "default")
            os.environ["USER"] = username
        else:
            u = utils.get_default_username()
            self.assertEqual(u, "default")
            os.environ["USER"] = "test"
            u = utils.get_default_username()
            self.assertEqual("test", u)
            del os.environ["USER"]

        u = utils.get_default_username(username="new")
        self.assertEqual("new", u)

    def test_load_default_env(self):
        folder = tempfile.mkdtemp()
        if os.path.isdir(os.path.join(os.path.expanduser("~"), ".aup")):
            self.assertRaises(ValueError, utils.load_default_env, folder, use_default=False)
            self.assertIsInstance(utils.load_default_env(folder), dict)
        else:
            self.assertRaises(Exception, utils.load_default_env, folder)

    def test_parse_result(self):
        self.assertEqual(0.1, utils.parse_result("#Auptimizer:0.1"))
        self.assertEqual(0.1, utils.parse_result("#Auptimizer:0.1,0.2"))
        self.assertRaises(ValueError, utils.parse_result, "no aup result")

    def test_print_result(self):
        tmp_out = sys.stderr
        sys.stderr = StringIO()

        utils.print_result("0.1")
        v = sys.stderr.getvalue()
        self.assertEqual(v.strip(), "#Auptimizer:0.1")
        sys.stderr = tmp_out

    def test_set_default_keyvalue(self):
        d = {}
        nd = utils.set_default_keyvalue("a", "b", d, inplace=False)
        self.assertDictEqual(nd, {"a": "b"})
        self.assertDictEqual(d, {})
        utils.set_default_keyvalue("a", "c", d, inplace=True)
        self.assertDictEqual(d, {"a": "c"})
        utils.set_default_keyvalue("a", "c", nd, inplace=True)
        self.assertDictEqual(nd, {"a": "b"})


if __name__ == '__main__':
    unittest.main()
