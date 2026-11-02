"""Fixed-role publication must preserve whole keys, VRAM and both NAME pages."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FixedRuntimeTests(unittest.TestCase):
    def test_prevalidated_resolver_checks_first_last_slots_without_writing_names(self):
        api=importlib.import_module('presentation_fixed_runtime_check');inputs,expected=api.fixtures();seen=set()
        for index in range(1,len(inputs)//api.INPUT_BYTES):
            data=inputs[index*api.INPUT_BYTES:(index+1)*api.INPUT_BYTES]
            if data[0]!=5:continue
            page,bank,identifier=data[1:4];seen.add((page,bank,identifier&63))
            before=expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES]
            after=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            self.assertEqual(after[2571:4107],before[2571:4107])
        self.assertEqual(seen,{(page,bank,slot) for page in (0,1) for bank,count in enumerate(api.COUNTS) for slot in (0,count-1)})

    def test_memo_fixture_changes_previously_unwritten_fusion_cells(self):
        api=importlib.import_module('presentation_fixed_runtime_check');inputs,expected=api.fixtures();witnesses=0
        for index in range(1,len(inputs)//api.INPUT_BYTES):
            data=inputs[index*api.INPUT_BYTES:(index+1)*api.INPUT_BYTES]
            if data[0]!=3:continue
            top,col,family,row,line,copy,coarse,footer=data[26:34]
            at=20491+(32 if top==20 else 0)+col
            before=expected[(index-1)*api.ROW_BYTES+at];after=expected[index*api.ROW_BYTES+at]
            self.assertEqual(after,copy*3+line);witnesses+=before!=after
        self.assertGreaterEqual(witnesses,12,'a stale fusion map must fail the native capture')

    def test_complete_capture_rejects_metadata_pixels_names_and_truncation(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_runtime_check'),'fixed publication proof missing')
        api=importlib.import_module('presentation_fixed_runtime_check');inputs,expected=api.fixtures()
        row=expected[api.ROW_BYTES:api.ROW_BYTES*2]
        api.verify_row(row,row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
        for at in (0,1,2,3,2571,4107,20491,20555):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bad,row)
