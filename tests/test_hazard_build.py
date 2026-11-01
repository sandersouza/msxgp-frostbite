import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardPresentationTests(unittest.TestCase):
    def test_original_nusiz_codes_select_copy_count_and_spacing_independently_of_direction(self):
        api=importlib.import_module('hazard_build');ram=bytearray(128)
        ram[0x58:0x5C]=bytes([0,1,2,3]);ram[0x11:0x15]=bytes([0,64,0,64]);before=bytes(ram)
        scene=api.presentation(ram)
        self.assertEqual(scene['counts'],[3,2,2,1]);self.assertEqual(scene['spacing'],[0,1,0,0])
        self.assertEqual(bytes(ram),before)
        ram[0x11:0x15]=bytes([64,0,64,0]);other=api.presentation(ram)
        self.assertEqual(other['counts'],scene['counts']);self.assertEqual(other['spacing'],scene['spacing'])
