import unittest
import os
from aup.EE.Resource import AbstractResourceManager


class AbsResourceManagerTestCase(unittest.TestCase):
    connector = None
    n_parallel = None
    auppath = os.path.join("tests", "data", ".aup")

    def test_import(self):
        self.assertRaises(KeyError, AbstractResourceManager.get_resource_manager, "none", None, 1)
        for k in AbstractResourceManager._SupportResource.keys():
            if k == "aws":
                continue
            t = AbstractResourceManager.get_resource_manager(k, self.connector, self.n_parallel, auppath=self.auppath)
            self.assertIsInstance(t, AbstractResourceManager.AbstractResourceManager)


if __name__ == '__main__':
    unittest.main()
