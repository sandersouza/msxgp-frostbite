"""The real RAM lookup page must be the exact validated ROM data."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class CrcGuardTests(unittest.TestCase):
    def test_rom_table_identity_and_ram_ownership_are_required(self):
        api=importlib.import_module('presentation_check')
        self.assertTrue(hasattr(api,'crc_page'),'actual CRC-page guard missing')
        from presentation_build import pack_crc_shadow
        packed=pack_crc_shadow({'bank':bytes([255])*16384,'used_bytes':15993,'assembly':''})
        rom=bytes(16384)+packed['bank'];meta={'cache_crc':packed['cache_crc']}
        self.assertEqual(len(api.crc_page(meta,rom)),256)
        self.assertIsNone(api.crc_page({},rom))
        damaged=bytearray(rom);damaged[16384+15993]^=1
        with self.assertRaises(ValueError):api.crc_page(meta,damaged)
        for key,value in (('ram_start',0xE200),('size',255),('offset',16129),('sha256','wrong')):
            bad={'cache_crc':{**meta['cache_crc'],key:value}}
            with self.assertRaises(ValueError):api.crc_page(bad,rom)
