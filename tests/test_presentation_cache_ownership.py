"""Every dynamic name owns exactly one reference in its own generation/bank."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class CacheOwnershipTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_cache_ownership'),'live-name ownership audit missing')
        return importlib.import_module('presentation_cache_ownership')

    def fixture(self):
        names=bytearray((128,))*1536;names[0]=names[1]=0;names[768+16*32+9]=64
        refs=bytearray(384);refs[0]=2;refs[320]=1
        return names,refs,bytes((1,0,0,0,0,1))

    def test_both_name_pages_and_screen_banks_determine_exact_reference_counts(self):
        api=self.api();names,refs,counts=self.fixture()
        self.assertEqual(api.audit_names(names,refs,counts)['dynamic_cells'],3)
        bad=refs.copy();bad[0]=1
        with self.assertRaises(ValueError):api.audit_names(names,bad,counts)
        with self.assertRaises(ValueError):api.audit_names(names,refs[:-1],counts)

    def test_wrong_generation_and_unallocated_slot_are_rejected(self):
        api=self.api();names,refs,counts=self.fixture()
        bad=names.copy();bad[768]=0
        with self.assertRaises(ValueError):api.audit_names(bad,refs,counts)
        bad=names.copy();bad[0]=1
        with self.assertRaises(ValueError):api.audit_names(bad,refs,counts)

    def test_byte_reference_overflow_cannot_wrap_to_zero(self):
        api=self.api();names,refs,counts=self.fixture();names[:256]=bytes(256);refs[0]=0
        with self.assertRaises(ValueError):api.audit_names(names,refs,counts)
