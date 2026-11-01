import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeTableTests(unittest.TestCase):
    def test_mapper_blobs_never_cross_and_dedup_is_exact(self):
        api=importlib.import_module('floe_tables');pack=api.BankPacker(14)
        a=pack.put(bytes(16000));b=pack.put(bytes([1])*480);self.assertEqual(a,(14,0x8000));self.assertEqual(b,(15,0x8000))
        self.assertEqual(pack.put(bytes(16000)),a)
        self.assertEqual(api.pointer(b),bytes([0,128,15]))
        with self.assertRaises(ValueError):pack.put(bytes(16385))
    def test_uniform_shadow_channel_must_represent_all228_views(self):
        api=importlib.import_module('floe_tables')
        self.assertEqual(api.shadow_byte(bytes(29)),0)
        self.assertEqual(api.shadow_byte(bytes([255])*28+bytes([15])),64)
        with self.assertRaises(ValueError):api.shadow_byte(bytes([1])+bytes(28))
