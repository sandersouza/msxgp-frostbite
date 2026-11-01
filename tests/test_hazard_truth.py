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


if __name__=='__main__':unittest.main()
