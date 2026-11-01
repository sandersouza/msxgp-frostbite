import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardBenchTests(unittest.TestCase):
    def test_seeded_crowded_state_retains_three_real_copies_and_all_hazards(self):
        api=importlib.import_module('hazard_bench');initial={'ram':[0]*128,'registers':{'sp':255}}
        dense=api.dense_initial(initial)
        self.assertEqual(dense['ram'][0x58:0x5C],[3]*4)
        self.assertEqual(dense['ram'][0x5C:0x60],[7]*4)
        self.assertEqual(dense['ram'][0x11:0x15],[0,65,2,67])
        self.assertEqual((dense['ram'][0x4B],dense['ram'][0x64]),(4,53))
        self.assertEqual(initial['ram'],[0]*128)

    def test_mixed_canonical_counts_keep_the_source_segment_offsets(self):
        api=importlib.import_module('hazard_bench');initial={'ram':[0]*128,'registers':{'sp':255}}
        mixed=api.mixed_initial(initial)
        self.assertEqual(mixed['ram'][0x58:0x5C],[0,1,2,3])
        self.assertEqual(mixed['ram'][0x5C:0x60],[1,3,5,7])
        self.assertEqual(mixed['ram'][0x54:0x58],[48,64,80,112])
