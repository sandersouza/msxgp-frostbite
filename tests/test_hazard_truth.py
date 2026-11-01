import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardTruthTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('hazard_truth'),'complete hazard protocol is missing')
        return importlib.import_module('hazard_truth')

    def fixture(self):
        raw=bytearray(674)
        raw[522:650]=bytes(range(128))
        raw[570:578]=bytes([7,71,135,199,7,71,135,199])
        raw[650:655]=bytes([17,34,51,48,255])
        raw[655:674]=bytes(range(19))
        return raw

    def test_all_windows_complete_cpu_ram_and_strict_padding(self):
        api=self.api();raw=self.fixture();record=api.full_record(raw)
        self.assertEqual(len(record['truth']),9)
        self.assertEqual(record['ram'],bytes(raw[522:650]))
        self.assertEqual(record['registers'],{'a':17,'x':34,'y':51,'p':48,'sp':255})
        self.assertEqual(record['glyph'],bytes(range(19)))
        for invalid in (raw[:-1],raw+b'\0'):
            with self.assertRaises(ValueError):api.full_record(invalid)
        for offset in (28,57,7*58+28,8*58+57):
            corrupt=bytearray(raw);corrupt[offset]=16
            with self.assertRaises(ValueError):api.full_record(corrupt)
        corrupt=bytearray(raw);corrupt[571]=128
        with self.assertRaises(ValueError):api.full_record(corrupt)

    def test_actual_literal_view_selects_odd_even_and_shore_independently(self):
        api=self.api();raw=self.fixture()
        raw[0]=1                 # view0 hits even window0
        raw[58+29]=1             # view0 has bit6 in odd window1
        raw[7*58+28]=8           # view227 hits odd window7
        raw[8*58]=1              # view0 hits shore
        raw[8*58+29+28]=8        # view227 has independent shore bit6
        record=api.full_record(raw);ram=bytearray(128)
        self.assertEqual(api.contacts(record,ram),{'rows':bytes([135,71,7,7,7,7,7,7]),'shore':135})
        ram[0x6E]=5;ram[0x6B]=18;ram[0x6C]=8
        self.assertEqual(api.contacts(record,ram),{'rows':bytes([7,7,7,7,7,7,7,135]),'shore':71})
        ram[0x6E]=6
        with self.assertRaises(ValueError):api.contacts(record,ram)
        with self.assertRaises(ValueError):api.contacts(record,ram[:-1])

    def test_cached_window_must_equal_complete_truth_latch_and_glyph(self):
        api=self.api();raw=self.fixture()
        roi=raw[7*58:8*58]+raw[577:578]+raw[655:674]
        self.assertEqual(api.compare_roi(raw,roi),1)
        for offset in (0,29,58,59):
            corrupt=bytearray(roi);corrupt[offset]^=128
            with self.assertRaises(ValueError):api.compare_roi(raw,corrupt)
        with self.assertRaises(ValueError):api.compare_roi(raw,roi[:-1])
        with self.assertRaises(ValueError):api.compare_roi(raw[:-1],roi)

    def test_invariance_cannot_ignore_either_channel_or_bad_window_indexes(self):
        api=self.api();a=api.full_record(self.fixture());b=api.full_record(self.fixture())
        links=[(0,1,7,1,'row translation')]
        self.assertEqual(api.validate_invariants([a,b],links),1)
        b['truth'][1]=bytes(29)+b'\x01'+bytes(28)
        with self.assertRaises(ValueError):api.validate_invariants([a,b],links)
        with self.assertRaises(ValueError):api.validate_invariants([a,b],[(0,1,7,9,'bad window')])
        with self.assertRaises(ValueError):api.validate_invariants([a,b],[(0,2,7,1,'missing case')])


if __name__=='__main__':unittest.main()
