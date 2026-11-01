import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeBuildTests(unittest.TestCase):
    def test_empty_sentinel_and_incomplete_igloo_never_show_the_completed_door(self):
        api=importlib.import_module('floe_build');ram=bytearray(128)
        ram[0x4d]=255;self.assertEqual(api.presentation(ram)['igloo'],0)
        for progress in range(15):
            ram[0x4d]=progress;self.assertIn(api.presentation(ram)['igloo'],(1,2))
        ram[0x4d]=15;self.assertEqual(api.presentation(ram)['igloo'],3)
