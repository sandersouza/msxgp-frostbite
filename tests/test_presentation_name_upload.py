"""Whole-page NAME transfers retain every byte and the external list contract."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NameUploadTests(unittest.TestCase):
    def test_both_entries_cover_every_interval_and_reject_invalid_lists(self):
        api=importlib.import_module('presentation_name_upload_check');inputs,expected=api.fixtures()
        seen=set()
        for at in range(0,len(inputs),api.INPUT_BYTES):
            mode,page,count,*rows=inputs[at:at+api.INPUT_BYTES]
            if count and count<=24 and rows[:count]==list(range(rows[0],rows[0]+count)) and rows[count-1]<24:
                seen.add((mode,page,rows[0],count))
        required={(mode,page,start,count) for mode in (0,1) for page in (0,1) for start in range(24) for count in range(1,25-start)}
        self.assertTrue(required<=seen)
        cases=len(inputs)//api.INPUT_BYTES
        self.assertEqual(len(expected),cases*api.ROW_BYTES)
        for index in range(cases-7,cases):
            row=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            previous=expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES]
            self.assertEqual(row[:-1],previous[:-1]);self.assertEqual(row[-1],1)

    def test_whole_vram_cpu_carry_or_truncated_capture_cannot_pass(self):
        api=importlib.import_module('presentation_name_upload_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,0x17ff,0x1800,0x1aff,0x1c00,0x1eff,0x3fff,16384,17919,17920):
            bad=bytearray(row);bad[at]=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
