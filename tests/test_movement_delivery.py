import importlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class MovementDeliveryTests(unittest.TestCase):
    def test_version_package_is_identical_on_repeat_and_never_replaces_changed_bytes(self):
        write=importlib.import_module('movement_delivery').write_immutable
        with tempfile.TemporaryDirectory() as root:
            destination=Path(root)/'version'
            files={'test.rom':b'first','notes.md':b'tested'}
            write(destination,files);write(destination,files)
            with self.assertRaises(ValueError):write(destination,{**files,'test.rom':b'changed'})
            self.assertEqual((destination/'test.rom').read_bytes(),b'first')
            with self.assertRaises(ValueError):write(destination,{**files,'extra':b'new'})
