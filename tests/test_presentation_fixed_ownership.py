"""Fixed-role audits must check real table bytes and both NAME generations."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FixedOwnershipTests(unittest.TestCase):
    def test_template_roles_require_the_raw_floe_namespace(self):
        api=importlib.import_module('presentation_fixed_ownership')
        raw=bytearray(bytes([128])*1536+bytes([255])*2568+bytes((56,60,50,56,60,50)))
        vram=bytearray(16384);vram[0x1800:0x1B00]=vram[0x1C00:0x1F00]=bytes([128])*768
        key=bytes((0,0,130,0,15,9));at=1536+(64+19)*6;raw[at:at+6]=key
        raw[11*32+4]=19;vram[0x1800+11*32+4]=19
        api.audit_row(bytes(raw),bytes(vram),lambda bank,key:bytes(16),templates=True)
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),lambda bank,key:bytes(16))
        raw[at+5]=7
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),lambda bank,key:bytes(16),templates=True)

    def test_invisible_active_tile_bytes_are_immutable_during_prepare(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_ownership'))
        api=importlib.import_module('presentation_fixed_ownership')
        before=bytearray(16384);before[0x1B00]=208;registers=bytes((2,194,6,255,3,54,7,1))
        prepared=bytearray(before);prepared[64*8]=1
        api.audit_active(bytes(before),bytes(prepared),registers)
        prepared[0]=1
        with self.assertRaises(ValueError):api.audit_active(bytes(before),bytes(prepared),registers)
        prepared=bytearray(before);prepared[0x1800]=1
        with self.assertRaises(ValueError):api.audit_active(bytes(before),bytes(prepared),registers)
        before[0x1B00:0x1B08]=bytes((15,10,4,0,208,0,0,0));prepared=bytearray(before)
        prepared[0x3800+4*8+31]=1
        with self.assertRaises(ValueError):api.audit_active(bytes(before),bytes(prepared),registers)

    def test_missing_generation_unpublished_key_and_changed_physical_tile_are_rejected(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_ownership'))
        api=importlib.import_module('presentation_fixed_ownership')
        names=bytes([128])*1536;metadata=bytes([255])*2568
        raw=bytearray(names+metadata+bytes((56,60,50,56,60,50)))
        vram=bytearray(16384);vram[0x1800:0x1B00]=vram[0x1C00:0x1F00]=names[:768]
        tile=lambda bank,key:bytes(16)
        api.audit_row(bytes(raw),bytes(vram),tile)
        with self.assertRaises(ValueError):api.audit_row(bytes(raw[:-1]),bytes(vram),tile)
        raw[6*32+2]=0;vram[0x1800+6*32+2]=0
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),tile)
        raw[1536:1542]=bytes((1,0,128,0,15,0))
        api.audit_row(bytes(raw),bytes(vram),tile)
        vram[0]=1
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),tile)
        vram[0]=0;raw[768+6*32+2]=0;vram[0x1C00+6*32+2]=0
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),tile)

    def test_a_valid_key_cannot_claim_another_role_or_footer_generation(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_ownership'))
        api=importlib.import_module('presentation_fixed_ownership')
        names=bytes([128])*1536;raw=bytearray(names+bytes([255])*2568+bytes((56,60,50,56,60,50)))
        vram=bytearray(16384);vram[0x1800:0x1B00]=vram[0x1C00:0x1F00]=names[:768]
        raw[1536:1542]=bytes((1,0,128,0,15,7))
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),lambda bank,key:bytes(16))
        raw[1536:1542]=bytes([255])*6
        raw[22*32+4]=182;vram[0x1800+22*32+4]=182
        with self.assertRaises(ValueError):api.audit_row(bytes(raw),bytes(vram),lambda bank,key:bytes(16))
