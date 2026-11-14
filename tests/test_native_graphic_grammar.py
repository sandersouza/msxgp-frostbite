import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    from native_graphic_grammar import floes,p0
except ImportError:
    floes=p0=None
from presentation_sprites import expand_pair


class Graphics(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(floes,'native graphic grammar is missing')

    def test_exact_floe_union_and_zero(self):
        values=[bytes(8),b'\x80'*7+b'\0',b'\x01'*7+b'\0',b'\x81'*7+b'\0']
        data=floes(b''.join(values),b'\x00\x00\x08\x00\x10\x00\x18\x00')
        self.assertEqual(len(data['indices']),8)
        for i,value in enumerate(values):
            a,b=data['indices'][i*2:i*2+2]
            self.assertEqual(bytes(x|y for x,y in zip(data['basis'][a*8:a*8+8],data['basis'][b*8:b*8+8])),value)

    def test_malformed_or_out_of_range_indices_are_rejected(self):
        for patterns,indices in ((bytes(7),bytes(2)),(bytes(8),b'\x01\0'),(bytes(8),b'\x08\0'),(bytes(8),b'\0')):
            with self.assertRaises(ValueError):floes(patterns,indices)

    def test_three_way_irreducible_union_is_not_silently_changed(self):
        values=[bytes([v])*7+b'\0' for v in (1,2,4,7)]
        with self.assertRaises(ValueError):floes(b''.join(values),b'\0\0')

    def test_p0_inverse_keeps_both_horizontal_parities(self):
        expansion=b''.join(bytes(expand_pair(x,p)) for p in range(2) for x in range(256))
        row=bytes(range(16));patterns=[]
        for parity in range(2):
            pairs=[expand_pair(x,parity) for x in row]
            patterns.append(bytes(v[0] for v in pairs)+bytes(v[1] for v in pairs))
        data=p0(b''.join(patterns),expansion)
        for i,pattern in enumerate(patterns):
            word=int.from_bytes(data['directory'][i*2:i*2+2],'little');phase=word>>15;at=word&32767
            source=data['rows'][at:at+16];pairs=[expand_pair(x,phase) for x in source]
            self.assertEqual(bytes(v[0] for v in pairs)+bytes(v[1] for v in pairs),pattern)

    def test_unsupported_p0_pixels_are_rejected(self):
        expansion=b''.join(bytes(expand_pair(x,p)) for p in range(2) for x in range(256))
        with self.assertRaises(ValueError):p0(bytes([255])*32,expansion)
