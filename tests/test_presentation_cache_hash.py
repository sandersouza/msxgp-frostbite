"""Constructor-cache CRC table is original-free and covers every input byte."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class PresentationCacheHashTests(unittest.TestCase):
    def test_all_table_entries_and_forced_collision_keys(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_cache_hash'),'cache hash constructor missing')
        api=importlib.import_module('presentation_cache_hash');table=api.table()
        self.assertEqual(len(table),256);self.assertEqual(len(set(table)),256)
        for value in range(256):
            expect=value
            for bit in range(8):expect=((expect<<1)^(7 if expect&128 else 0))&255
            self.assertEqual(table[value],expect)
        keys=api.collisions(32)
        self.assertEqual(len(set(keys)),32)
        self.assertTrue(all(len(k)==6 and api.hash_key(k)==0 for k in keys))
