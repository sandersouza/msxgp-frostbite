"""Batched live font masks retain complete three-band tile semantics."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HeaderBatchTests(unittest.TestCase):
    def test_all_glyph_pairs_parts_bands_and_whole_capture_are_required(self):
        api=importlib.import_module('presentation_header_batch_check')
        inputs,expected,font=api.fixtures()
        self.assertEqual(len(font),34*5*8)
        self.assertGreater(len(inputs),34*34*5*3*api.INPUT_BYTES)
        self.assertEqual(len(expected),len(inputs)//api.INPUT_BYTES*api.ROW_BYTES)
        row=expected[:api.ROW_BYTES];api.verify_row(row,row)
        for at in (0,159,160,175,176,177,235,236,237):
            wrong=bytearray(row);wrong[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(wrong),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)

    def test_repeated_font_masks_must_fit_the_cache_hit_budget(self):
        api=importlib.import_module('presentation_header_batch_check')
        inputs,_,_=api.fixtures();count=len(inputs)//api.INPUT_BYTES
        with self.assertRaises(ValueError):api.verify_cache_timing(inputs,[(i,3954) for i in range(count)])
        result=api.verify_cache_timing(inputs,[(i,1400) for i in range(count)])
        self.assertGreater(result['mask_cache_hits'],100)
