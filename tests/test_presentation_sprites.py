"""Finite foreground tables preserve source bits at both pixel-scale phases."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationSpritesTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_sprites'),'foreground sprite table constructor missing')
        return importlib.import_module('presentation_sprites')
    def test_each_source_mask_expands_to_twelve_bits_at_both_parities(self):
        api=self.api()
        for parity in (0,1):
            for mask in range(256):
                got=api.expand_pair(mask,parity)
                positions={x for x in range(16) if got[x//8]&(128>>(x%8))}
                expected={tx for x in range(8) if mask&(128>>x) for tx in range((parity+x)*3//2-parity*3//2,(parity+x+1)*3//2-parity*3//2)}
                self.assertEqual(positions,expected)
    def test_door_reflection_and_logo_rows_decode_against_synthetic_source_bits(self):
        api=self.api();rom=bytearray(4096)
        rom[0xEF3:0xEFF]=bytes((0x81,0x42,0x24,0x18))*3
        for n in range(5):rom[0xF68+n*8:0xF70+n*8]=bytes(((n*41+y*29)&255) for y in range(8))
        palette={c:(0,0,0) for c in range(0,256,2)};data=api.tables(bytes(rom),palette)
        self.assertEqual(len(data['expansion']),1024);self.assertEqual(len(data['door']),64);self.assertEqual(len(data['logo']),64)
        for reflection in (0,1):
            raw=data['door'][reflection*32:(reflection+1)*32]
            for y in range(16):
                row=0 if y<4 else rom[0xEF3+15-y]
                if reflection:row=int(f'{row:08b}'[::-1],2)
                expected=api.expand_pair(row,1)
                self.assertEqual(bytes((raw[y],raw[y+16])),expected)
        for y in range(8):
            want=set()
            for glyph in range(5):
                row=rom[0xF68+glyph*8+7-y]
                for x in range(8):
                    if row&(128>>x):want.update(range((glyph*8+x)*3//2,(glyph*8+x+1)*3//2))
            got=set()
            for col in range(4):
                row=data['logo'][col*16+y*2:col*16+y*2+2]
                got.update(col*16+x for x in range(16) if row[x//8]&(128>>(x%8)))
            self.assertEqual(got,want)
        self.assertEqual(len(data['holds']),135);self.assertEqual(len(data['tails']),135)
