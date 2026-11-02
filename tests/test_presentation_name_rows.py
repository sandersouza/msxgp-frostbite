"""Whole NAME-row rotation must preserve source bytes and both page borders."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NameRowTests(unittest.TestCase):
    def test_fixtures_visit_both_cached_rows_of_every_owner_for_each_root_and_page(self):
        api=importlib.import_module('presentation_name_rows_check');inputs,_=api.fixtures();seen={}
        for at in range(0,7680*api.INPUT_BYTES,api.INPUT_BYTES):
            page,root=inputs[at:at+2];source=int.from_bytes(inputs[at+2:at+4],'little')
            seen.setdefault((page,root),set()).add(source)
        self.assertEqual(len(seen),320)
        for sources in seen.values():self.assertEqual(len(sources),8)

    def test_expected_rotation_clips_only_after_wrapping(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_name_rows_check'))
        api=importlib.import_module('presentation_name_rows_check');row=bytes(range(30))
        self.assertEqual(api.rotated(row,0),bytes((128,128))+bytes(range(1,30))+bytes((128,)))
        self.assertEqual(api.rotated(row,16),bytes((128,128,28,29))+bytes(range(27))+bytes((128,)))
        with self.assertRaises(ValueError):api.rotated(row,160)

    def test_whole_capture_rejects_changed_name_cache_page_or_error(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_name_rows_check'))
        api=importlib.import_module('presentation_name_rows_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,767,768,1535,1536,2047,2048,2049):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
