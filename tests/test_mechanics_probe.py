"""Synthetic CPU/bus checks; no original ROM is required."""
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class ProbeTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('mechanics_probe'), 'slice tool is missing')
        return importlib.import_module('mechanics_probe')

    def test_ram_stack_mirrors_and_read_write_decoding(self):
        api = self.api()
        bus = api.SliceBus(bytes(4096), {0x0c: 0x80, 0x280: 0xef})
        bus[0x01fa] = 0x42
        self.assertEqual(bus[0xfa], 0x42)
        self.assertEqual(bus[0x04fa], 0x42)
        self.assertEqual(bus[0x0c], 0x80)
        self.assertEqual(bus[0x280], 0xef)
        self.assertEqual(bus[0x288], 0xef)  # RIOT read selection uses only low three bits.
        bus[0x0c] = 8
        self.assertEqual(bus[0x0c], 0x80)  # REFP1 write does not replace INPT4.
        self.assertEqual(bus.writes, [{'address': '000C', 'value': '08'}])

    def test_unknown_hardware_read_and_rom_write_fail(self):
        api = self.api()
        bus = api.SliceBus(bytes(4096), {})
        with self.assertRaisesRegex(ValueError, 'undeclared hardware read'):
            _ = bus[0x07]
        with self.assertRaisesRegex(ValueError, 'ROM write'):
            bus[0xf000] = 0

    @unittest.skipUnless(importlib.util.find_spec('py65'), 'CPU tests require requirements-reference.txt')
    def test_synthetic_decimal_and_stack_execution(self):
        api = self.api()
        # JSR F010; STA E5; stop. Subroutine: SED; SEC; LDA #10; SBC #01; CLD; RTS.
        rom = bytearray(4096)
        rom[:5] = bytes.fromhex('20 10 f0 85 e5')
        rom[16:24] = bytes.fromhex('f8 38 a9 10 e9 01 d8 60')
        result = api.execute_slice(bytes(rom), {'id': 'synthetic', 'start': 'F000',
            'stops': ['F005'], 'watch': ['E5'], 'limit': 20})
        self.assertEqual(result['ram'], {'E5': '09'})
        self.assertEqual(result['registers']['sp'], 255)
        self.assertEqual(result['registers']['p'] & 8, 0)
        self.assertEqual(result['stop_pc'], 'F005')

    @unittest.skipUnless(importlib.util.find_spec('py65'), 'CPU tests require requirements-reference.txt')
    def test_nonterminating_slice_is_bounded(self):
        api = self.api()
        rom = bytes.fromhex('4c 00 f0') + bytes(4093)
        with self.assertRaisesRegex(ValueError, 'instruction limit'):
            api.execute_slice(rom, {'id': 'loop', 'start': 'F000', 'stops': ['F003'], 'limit': 8})

    @unittest.skipUnless(importlib.util.find_spec('py65'), 'CPU tests require requirements-reference.txt')
    def test_wrong_expected_ram_fails(self):
        api = self.api()
        rom = bytes.fromhex('a9 07 85 80') + bytes(4092)
        with self.assertRaisesRegex(ValueError, 'expected RAM'):
            api.execute_slice(rom, {'id': 'negative', 'start': 'F000', 'stops': ['F004'],
                'watch': ['80'], 'expect': {'ram': {'80': '08'}}})

    @unittest.skipUnless(importlib.util.find_spec('py65'), 'CPU tests require requirements-reference.txt')
    def test_operand_byte_cannot_be_used_as_slice_entry(self):
        api = self.api()
        self.assertTrue(hasattr(api, 'instruction_boundaries'), 'instruction boundary validation missing')
        rom = bytes.fromhex('a9 07 85 80') + bytes(4092)
        boundaries = api.instruction_boundaries(rom, [['F000', 'F003']])
        self.assertEqual(boundaries, {0xf000, 0xf002})
        with self.assertRaisesRegex(ValueError, 'instruction boundary'):
            api.execute_slice(rom, {'id': 'operand', 'start': 'F001', 'stops': ['F002']},
                              boundaries=boundaries)

    def test_bad_rom_rejected_before_loading_cpu_backend(self):
        self.api()
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / 'bad.bin'
            rom.write_bytes(bytes(4096))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/mechanics_probe.py'),
                '--rom', str(rom)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Mechanics probe failed', result.stderr)
            self.assertNotIn('py65', result.stderr)


if __name__ == '__main__':
    unittest.main()
