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
    def test_replay_preserves_backend_restore_journal_and_exact_pins(self):
        api=importlib.import_module('floe_routes')
        ram=[0]*128;ram[0x4d]=255;ram[0x64]=27;ram[0x66]=64
        neutral={'swcha':255,'swchb':63,'fire':[False,False]};down={**neutral,'swcha':223}
        inputs=[neutral]*113+[down]*20
        trace={'policy':{'preparation_intervals':113},'steps':[{'ram':ram} for _ in inputs]}
        self.assertEqual([len(part) for part in api.replay_segments(trace,inputs)],[113,10,10])
        with self.assertRaises(ValueError):api.replay_segments(trace,inputs[:-1]+[neutral])
