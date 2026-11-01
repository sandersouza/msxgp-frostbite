import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeBenchTests(unittest.TestCase):
    def test_transitions_follow_requested_initial_mode_without_relaxing_cadence(self):
        api=importlib.import_module('floe_bench');period=59736
        report={'complete':True,'cases':240,'frames':list(range(240)),'busy_cycles':[50000]*240,
            'commit_y':[-20]*240,'commit_end_y':[-15]*240,'commit_cycles':[1500]*240,'period_cycles':[period]*240,
            'step_counts':list(range(1,241)),'mode_samples':[0 if (i//4)%2==0 else 3 for i in range(240)],
            'pal_flag':0,'source_steps':241,'source_cycles':[20000]*241,'min_spacing':29,'max_sprites_per_line':4,'stack_min':0xF370}
        api.validate_receipt(report,period,1,1,True)
        with self.assertRaises(ValueError):api.validate_receipt({**report,'mode_samples':[3]*240},period,1,1,True)
