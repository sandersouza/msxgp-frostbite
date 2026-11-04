"""Synthetic trust-boundary tests; never load original cartridges in public CI."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from atari800_reference import cartridge, capture


class Atari800ReferenceTests(unittest.TestCase):
    def image(self):
        payload = bytes(8186)+struct.pack('<HBBH', 0xa000, 0, 4, 0xa000)
        return b'CART'+struct.pack('>III', 1, sum(payload), 0)+payload

    def test_header_checksum_mapper_and_vectors(self):
        data = self.image()
        self.assertEqual(cartridge(data)['run'], 0xa000)
        for bad in (data[:-1], b'BAD!'+data[4:], data[:7]+b'\x02'+data[8:],
                    data[:8]+bytes(4)+data[12:], data[:15]+b'\x01'+data[16:]):
            with self.assertRaises(ValueError):
                cartridge(bad)

    def sample(self):
        states = []
        for i in range(5):
            ram = bytearray(8192);ram[0x81] = (254+i)&255;states.append(bytes(ram))
        timing = '\n'.join(f'{i} 59.9227 {(254+i)&255} 0 0 0 0' for i in range(5))
        antic = '\n'.join(f'{i} 100 20 0000 {a:04x} 7' for i in range(5)
                           for a in (0xd404, 0xd405, 0xd409))
        return b''.join(states), timing, antic

    def test_counter_wrap_and_real_trace_required(self):
        ram, timing, antic = self.sample()
        result = capture(ram, timing, antic, start=1, frames=5)
        self.assertEqual(result['loop_counter_increments'], {1: 3})
        for values in ((ram[:-1], timing, antic), (ram, timing, ''),
                       (ram, timing.replace('2 59.9227 0', '2 59.9227 1'), antic),
                       (ram, timing, antic+'\n5 100 20 0000 d404 7')):
            with self.assertRaises(ValueError):
                capture(*values, start=1, frames=5)

    def test_gaps_are_reported_not_normalized(self):
        ram, timing, antic = self.sample();ram = bytearray(ram);ram[3*8192+0x81] = 3
        timing = timing.replace('3 59.9227 1', '3 59.9227 3')
        result = capture(bytes(ram), timing, antic, start=1, frames=5)
        self.assertNotEqual(result['loop_counter_increments'], {1: 3})

    def test_gtia_events_do_not_claim_returned_values(self):
        ram, timing, antic = self.sample()
        gtia = '2 100 5 R d004 0\n2 100 6 W d01e 0'
        result = capture(ram, timing, antic, start=1, frames=5, gtia=gtia)
        self.assertEqual(result['gtia']['read_counts'], {'d004': 1})
        for bad in ('', '5 100 5 R d004 0', '2 100 5 X d004 0'):
            with self.assertRaises(ValueError):
                capture(ram, timing, antic, start=1, frames=5, gtia=bad)
