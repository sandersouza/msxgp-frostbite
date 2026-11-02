"""Cached constant colours must match all eight physical CGT bytes."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class CgtShadowTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_cgt_shadow'),'physical colour ownership audit missing')
        return importlib.import_module('presentation_cgt_shadow')

    def test_each_bank_and_generation_checks_every_byte_of_each_known_slot(self):
        api=self.api();vram=bytearray(16384);shadow=bytearray([255])*384
        for group in range(6):
            for slot in (0,31,63):
                color=20+group*16;shadow[group*64+slot]=color
                bank=group%3;identifier=slot+64*(group//3)
                address=0x2000+2048*bank+8*identifier
                vram[address:address+8]=bytes([color])*8
        self.assertEqual(api.audit(shadow,vram),18)
        for group in range(6):
            address=0x2000+2048*(group%3)+8*(63+64*(group//3))
            for offset in range(8):
                bad=vram.copy();bad[address+offset]^=1
                with self.assertRaises(ValueError):api.audit(shadow,bad)

    def test_unknown_slots_make_no_colour_claim_and_truncation_is_rejected(self):
        api=self.api();vram=bytes((i*37)&255 for i in range(16384));shadow=bytes([255])*384
        self.assertEqual(api.audit(shadow,vram),0)
        with self.assertRaises(ValueError):api.audit(shadow[:-1],vram)
        with self.assertRaises(ValueError):api.audit(shadow,vram[:-1])
