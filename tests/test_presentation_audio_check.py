"""Whole game observer evidence must retain every ordered source event."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class IntegratedAudioTests(unittest.TestCase):
    def test_order_values_intervals_and_physical_writes_are_required(self):
        api=importlib.import_module('presentation_audio_check')
        events=[(0,21,8),(0,25,15),(1,21,8)]
        writes=[(0,7,190),(0,8,15)]
        api.verify_streams(events,events,writes,writes)
        for wrong in (events[:-1],events[::-1],[(0,21,8),(0,25,14),(1,21,8)]):
            with self.assertRaises(ValueError):api.verify_streams(wrong,events,writes,writes)
        with self.assertRaises(ValueError):api.verify_streams(events,events,writes[:-1],writes)
