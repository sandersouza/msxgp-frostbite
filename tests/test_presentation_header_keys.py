"""Header keys must preserve source column intersections and all band fields."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HeaderKeyTests(unittest.TestCase):
    def test_source_geometry_covers_six_glyphs_and_every_fragment_class(self):
        api=importlib.import_module('presentation_header_keys_check');commands=api.columns()
        self.assertEqual(len(commands),10);self.assertEqual({kind for first,second,kind in commands},set(range(5)))
        used={first for first,second,kind in commands}
        used.update(second for first,second,kind in commands if kind in (1,3))
        self.assertEqual(used,set(range(6)))
        for index,(first,second,kind) in enumerate(commands):
            self.assertLessEqual(41+first*12,(5+index)*8+7)
            self.assertGreater(41+first*12+12,(5+index)*8)

    def test_all_selector_bytes_and_invalid_palette_leave_previous_outputs(self):
        api=importlib.import_module('presentation_header_keys_check');inputs,expected=api.fixtures()
        self.assertEqual(len(inputs)//api.INPUT_BYTES,3295)
        for field in range(12):
            self.assertEqual({inputs[(field*256+value)*19+7+field] for value in range(256)},set(range(256)))
        for index in range(3252,3261):
            previous=expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES];row=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            self.assertEqual(row[:-1],previous[:-1]);self.assertEqual(row[-1],1)

    def test_whole_capture_rejects_table_keys_and_flags(self):
        api=importlib.import_module('presentation_header_keys_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,39,40,42,43,222,223,228,229):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
