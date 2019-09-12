import unittest

from os import path
from shutil import rmtree
from six.moves.configparser import ConfigParser

from aup import setup


# if the package is not installed, it aup.setupdb will throw errors because it is triggered by command line.
# It is safe to ignore those errors if unittest jobs are passed.
def _setup_wrapper(filename, *args):
    config = ConfigParser()
    config.optionxform = str
    config.read(filename)
    try:
        setup.setup(config, *args)
    except OSError:
        print("Above 'No module named aup.setupdb' error can be ignored")


def _read_file(filename):
    with open(filename, 'r') as f:
        return f.readlines()


class SetupTestCase(unittest.TestCase):
    plain_env_path = path.join("tests", "data", "plain_env.ini")
    target_plain_env_path = path.join("tests", "data", "target_plain_env.ini")
    gpu_path = path.join("tests", "data", "gpus.txt")
    target_gpu_env_path = path.join("tests", "data", "target_gpu_env.ini")

    def test_folder_creation(self):  # make sure the aup folder can be created
        tmp_path = path.join("~", ".aup_test")

        while path.exists(path.expanduser(tmp_path)):
            tmp_path += "%d" % hash(tmp_path)
            print(tmp_path)

        os_ind_path = path.expanduser(tmp_path)
        setup._create_folder(tmp_path)
        self.assertTrue(path.exists(os_ind_path), "failed to create %s" % os_ind_path)
        rmtree(os_ind_path)

    def test_update_resource(self):
        _setup_wrapper(self.plain_env_path, 4, self.gpu_path, "none", "none", "test", False, "error")
        d1 = _read_file(path.join(".aup", "env.ini"))
        d2 = _read_file(self.target_gpu_env_path)
        self.assertListEqual(d1, d2, "content of env.ini is problematic with resource")
        rmtree(".aup")

    def test_setup(self):
        _setup_wrapper(self.plain_env_path, 4, "none", "none", "none", "test", False, "error")
        self.assertTrue(path.exists(".aup"), "failed to create aup")
        d1 = _read_file(self.target_plain_env_path)
        d2 = _read_file(path.join(".aup", "env.ini"))
        self.assertListEqual(d1, d2, "content of env.ini is problematic")
        rmtree(".aup")

    def test_overwrite(self):
        _setup_wrapper(self.plain_env_path, 4, "none", "none", "none", "test", False, "error")
        self.assertRaises(SystemExit,
                          _setup_wrapper, self.plain_env_path, 4, "none", "none", "none", "test", False, "error")
        _setup_wrapper(self.plain_env_path, 4, "none", "none", "none", "test", True, "error")
        self.assertTrue(path.exists(".aup"), "failed to create aup")
        rmtree(".aup")

    def test_resource_conflict(self):
        _setup_wrapper(self.target_gpu_env_path, 4, "none", "0,1", "", "test", False, "error")

    def tearDown(self):
        rmtree(".aup", ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
