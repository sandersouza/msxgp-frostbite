"""A timing probe reports misses honestly and rejects incomplete raw rows."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PaceProbeTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_pace_probe'),'continuous timing probe missing')
        return importlib.import_module('presentation_pace_probe')

    def test_missed_frames_are_reported_without_qualifying_the_cartridge(self):
        api=self.api()
        good='0 10 10000 2000 1000 13000 0 1 -10 -5\n1 11 10000 2000 1000 13000 59736 1 -10 -5\n'
        result=api.verify_rows(good,2,'ntsc')
        self.assertTrue(result['deadline_met']);self.assertFalse(result['frame_deadline_accepted'])
        bad=good.replace('1 11 10000 2000 1000 13000 59736','1 13 10000 170000 1000 181000 179208')
        result=api.verify_rows(bad,2,'ntsc')
        self.assertFalse(result['deadline_met']);self.assertEqual(result['over_budget_frames'],1)
        self.assertEqual(result['skipped_vdp_frames'],2)
        visible=api.verify_rows(good.replace('-10 -5','20 25'),2,'ntsc')
        self.assertEqual(visible['visible_commits'],2);self.assertFalse(visible['deadline_met'])
        duplicate=api.verify_rows(good.replace('1 11','1 10'),2,'ntsc')
        self.assertEqual(duplicate['duplicate_vdp_frames'],1);self.assertFalse(duplicate['deadline_met'])

    def test_missing_unordered_and_inconsistent_measurements_fail(self):
        api=self.api();good='0 10 10000 2000 1000 13000 0 1 -10 -5\n1 11 10000 2000 1000 13000 59736 1 -10 -5\n'
        for text in (good.splitlines()[0],good.replace('1 11','0 11'),good.replace('13000','14000'),good.replace('2000','-2000'),good.replace('59736 1','0 1')):
            with self.assertRaises(ValueError):api.verify_rows(text,2,'ntsc')
