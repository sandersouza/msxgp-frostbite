"""Structural cartridge checks; runtime acceptance belongs to the emulator smoke."""
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


class RomTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('rom'), 'ROM utility missing')
        return importlib.import_module('rom')

    def image(self):
        data=bytearray(b'AB\x10\x40'+bytes(12)+bytes([0xf3])+b'FROSTBITE MSX1 DIAGNOSTIC')
        return data+bytes([255])*(16384-len(data))

    def test_plain_diagnostic_structure(self):
        api=self.api()
        self.assertEqual(api.validate_rom(self.image()),[])

    def test_truncated_or_banked_size_is_rejected(self):
        api=self.api()
        for image in (self.image()[:-1],self.image()*2):
            self.assertTrue(any('size' in problem for problem in api.validate_rom(image)))

    def test_bad_header_or_entry_is_rejected(self):
        api=self.api()
        data=self.image()
        data[0]=0
        self.assertTrue(any('header' in problem for problem in api.validate_rom(data)))
        data=self.image()
        data[2:4]=b'\x00\xc0'
        self.assertTrue(any('entry' in problem for problem in api.validate_rom(data)))

    def test_unrelated_plain_rom_is_not_this_diagnostic(self):
        api=self.api()
        data=self.image()
        data[17:31]=b'X'*14
        self.assertTrue(any('diagnostic' in problem for problem in api.validate_rom(data)))


if __name__=='__main__':
    unittest.main()
