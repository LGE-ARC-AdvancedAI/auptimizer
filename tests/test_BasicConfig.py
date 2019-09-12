import unittest

import json
import os
import pickle

from aup import BasicConfig


class BasicConfigTestCase(unittest.TestCase):
    json_read = os.path.join("tests", "data", "config", "test_read.json")
    pkl_read = os.path.join("tests", "data", "config", "test_read.pkl")
    wrong_read = os.path.join("tests", "data", "config", "test_wrong.json")
    json_write = os.path.join("tests", "test_write.json")
    pkl_write = os.path.join("tests", "test_write.pkl")

    d = {"a": 1}

    @classmethod
    def setUpClass(cls):
        with open(cls.json_read, 'w') as f:
            json.dump(cls.d, f)
        with open(cls.pkl_read, 'wb') as f:
            pickle.dump(cls.d, f)
        with open(cls.wrong_read, 'w') as f:
            json.dump([1,2,3], f)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.json_write)
        os.remove(cls.pkl_write)
        os.remove(cls.pkl_read)

    def test_access(self):
        data = BasicConfig(**self.d)
        del data.a
        self.assertFalse('a' in data)

    def test_compare(self):
        data = BasicConfig(**self.d)
        self.assertTrue(data == self.d)

    def test_init(self):
        data = BasicConfig(**self.d)
        self.assertDictEqual(data, self.d)

        data = BasicConfig(a=1)
        self.assertDictEqual(data, self.d)

        self.assertRaises(ValueError, data.load, "wrong.data")

    def test_json(self):
        data = BasicConfig()
        data.load(self.json_read)
        self.assertDictEqual(self.d, data)

        data["b"] = 2
        data.c = 3
        data.save(self.json_write)

        data = BasicConfig().load(self.json_write)
        self.assertEqual(data.b, 2)
        self.assertEqual(data["c"], 3)

    def test_pkl(self):
        data = BasicConfig()
        data.load(self.pkl_read)
        self.assertDictEqual(self.d, data)

        data["b"] = 2
        data.c = 3
        data.save(self.pkl_write)

        data = BasicConfig().load(self.pkl_write)
        self.assertEqual(data.b, 2)
        self.assertEqual(data["c"], 3)

    def test_type(self):
        data = BasicConfig()
        self.assertRaises(TypeError, data.load, self.wrong_read)

    def test_hash(self):
        a = {"a": 1}
        b = BasicConfig(a=1)
        self.assertDictEqual(a, b)


if __name__ == '__main__':
    unittest.main()
