import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeRouteTests(unittest.TestCase):
    def test_completed_igloo_is_not_entry_or_next_level(self):
        api=importlib.import_module('floe_routes')
        ram=[0]*128;ram[0x4d]=15;ram[0x4c]=3
        with self.assertRaises(ValueError):api.assess([{'ram':ram}]*32)
        entry=ram.copy();entry[0x71]=64;entry[0x64]=0
        with self.assertRaises(ValueError):api.assess([{'ram':ram},{'ram':entry}])
    def test_terminal_or_missing_first_level_cannot_pass(self):
        api=importlib.import_module('floe_routes')
        ram=[0]*128;ram[0x4b]=1;ram[0x4d]=255;ram[0x64]=27;ram[0x65]=69
        with self.assertRaises(ValueError):api.assess([{'ram':ram}])
