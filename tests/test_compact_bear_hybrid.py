import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import unittest
from compact_bear_hybrid import pack, unpack


class HybridRows(unittest.TestCase):
    def test_shared_planes_and_exact_keys(self):
        k=lambda n: n.to_bytes(2,'little')+bytes((136,0,15,0))
        a=bytes(range(16))+bytes([0xf1])*16+k(12)+k(15)
        b=bytes(range(16))+bytes([0xf1])*16+k(20)+k(15)
        packed=pack([a,b,a])
        self.assertEqual(len(packed['recipes']),30)
        self.assertEqual(len(packed['patterns']),16)
        self.assertEqual(len(packed['colors']),8)
        self.assertEqual(unpack(packed),[a,b,a])

    def test_empty_cell_stays_all_ff_key(self):
        p=bytes(32)+bytes([255])*12
        self.assertEqual(unpack(pack([p])),[p])

    def test_mixed_context_is_rejected(self):
        key=bytes((1,0,136,0,15,0))
        with self.assertRaisesRegex(ValueError,'context'):
            pack([bytes(32)+key+bytes((2,0,129,0,15,0))])

    def test_invalid_key_and_partial_row_are_rejected(self):
        with self.assertRaises(ValueError):pack([bytes(43)])
        with self.assertRaises(ValueError):pack([bytes(32)+bytes((1,0,136,1,15,0))*2])
