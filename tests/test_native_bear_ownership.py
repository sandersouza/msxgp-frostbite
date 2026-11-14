import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native_bear_keys import make_key
from presentation_fixed import COUNTS
from presentation_fixed_ownership import audit_row


class Ownership(unittest.TestCase):
    def fixture(self,bank=0,slot=0,key=None,name_row=6):
        key=key or make_key(0,0,0,0,0,128,1)
        names=bytearray([128])*1536
        names[name_row*32+5]=slot
        keys=bytearray([255])*2304
        at=(bank*64+slot)*6
        keys[at:at+6]=key
        tile=bytes([85])*8+bytes([31])*8
        vram=bytearray(16384)
        vram[0x1800:0x1B00]=names[:768]
        vram[0x1C00:0x1F00]=names[768:]
        at=bank*2048+slot*8
        vram[at:at+8]=tile[:8]
        vram[0x2000+at:0x2008+at]=tile[8:]
        return bytes(names+keys+bytes([255])*264+bytes(COUNTS*2)),bytes(vram),lambda b,k:tile

    def test_flag_is_explicit(self):
        with self.assertRaises(ValueError):
            audit_row(*self.fixture())

    def test_correct_role_is_admitted_with_flag(self):
        result=audit_row(*self.fixture(),native_bear=True)
        self.assertEqual(result['published_slots'],1)

    def test_wrong_role_rejected_even_with_flag(self):
        with self.assertRaises(ValueError):
            audit_row(*self.fixture(slot=1),native_bear=True)

    def test_wrong_name_row_rejected(self):
        with self.assertRaises(ValueError):
            audit_row(*self.fixture(name_row=7),native_bear=True)

    def test_tile_bytes_remain_exact(self):
        raw,vram,tile=self.fixture()
        vram=bytearray(vram);vram[0]^=1
        with self.assertRaises(ValueError):
            audit_row(raw,bytes(vram),tile,native_bear=True)
