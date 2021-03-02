import unittest
import os
from shutil import copyfile, rmtree
from subprocess import call

from aup import compression, Experiment, BasicConfig
from aup.utils import get_default_username
from aup.compression.utils import verify_compression_config, run_non_automatic_experiment, adjust_compression_config

class CompressorMainTest(unittest.TestCase):
    path = os.path.join("tests", "data", "exp7.json")
    auppath = os.path.join("tests", "data", ".aup")
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        # clean test files
        os.remove(self.bk_db)
        if os.path.isfile(os.path.join(os.getcwd(), "exp2.pkl")):
            os.remove(os.path.join(os.getcwd(), "exp2.pkl"))

    def test_verify_config(self):
        compression = {
            "framework": None,
            "type": None,
            "compressor": None,
            "config_list": None,
        }
        config = {
            "name": None,
            "script": None,
            "resource": None,
            "compression": compression,
        }
        _config = verify_compression_config(config)
        self.assertEqual(_config, config)

    def test_verify_config_missing_config(self):

        config = {}
        self.assertRaises(KeyError, verify_compression_config, config)

    def test_verify_config_missing_compression_config(self):
    
        config = {
            "name": None,
            "script": None,
            "resource": None,
            "compression": None,
        }
        self.assertRaises(TypeError, verify_compression_config, config)


    def test_adjust_config(self):

        compression = {
            "compression_framework": None,
            "compression_type": None,
            "compressor": None,
            "config_list": None,
        }

        old_compression = {
            "framework": None,
            "type": None,
            "compressor": None,
            "config_list": None,
        }

        adjusted_config = adjust_compression_config(old_compression)
        self.assertEqual(adjusted_config, compression)

    def test_non_automatic_ra_no_script(self):

        exp_config = BasicConfig().load(self.path)
        exp_config = verify_compression_config(exp_config)
        exp_config["compression"] = adjust_compression_config(exp_config["compression"])
        exp_config["workingdir"] = os.getcwd()
        exp_config["script"] = None
        self.assertRaises(TypeError, lambda: run_non_automatic_experiment()[1](), exp_config, self.auppath, "test")
  
class CompressorTestCase(unittest.TestCase):

    model = None
    nni_compressor = None
    c_str = None
    model_path = 'temp'

    def test_create_compressor_no_cf(self):

        config = {
            "compression_framework": "fail",
            "compression_type": "fail",
            "compressor": "fail",
        }

        self.assertRaises(ValueError, compression.create_compressor, self.model, config)

    def test_create_compressor_no_ct(self):

        config = {
            "compression_framework": "tensorflow",
            "compression_type": "fail",
            "compressor": "fail",
        }

        self.assertRaises(ValueError, compression.create_compressor, self.model, config)

    def test_create_compressor_no_c(self):
    
        config = {
            "compression_framework": "tensorflow",
            "compression_type": "pruning",
            "compressor": "fail",
        }

        self.assertRaises(ValueError, compression.create_compressor, self.model, config)
    
    def test_compressor_export_model(self):

        c_framework = "torch"
        c_type = "pruning"
        mask_path = None

        c = compression.Compressor(self.model, self.nni_compressor, c_framework, c_type, self.c_str)
        self.assertRaises(AttributeError, c.export_model, self.model_path, mask_path, save_model=True)


if __name__ == '__main__':
    unittest.main()