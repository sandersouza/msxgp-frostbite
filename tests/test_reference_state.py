"""Hand-serialized synthetic Stella format; no original-game state bytes."""
import importlib
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


def synthetic_state(queue_event=False):
    data = bytearray()
    def emit(pattern, *values):
        if not values:
            values = [1 if letter == '?' else 0 for letter in pattern]
        # Stella booleans are 01/FE rather than C99 00/01.
        for letter, value in zip(pattern, values):
            data.extend(struct.pack('<B' if letter == '?' else '<' + letter,
                                    (0xFE if value is True else 1) if letter == '?' else value))
    emit('I', 13); data.extend(b'07000000state')
    emit('QB', 0, 0)
    emit('BBBBBH', 0x12, 0x34, 0x56, 0xFD, 0, 0xF000)
    emit('???????', False, True, False, True, False, True, True)
    emit('BI', 0, 9)
    emit('HHHHIIIIB?Q')
    data.extend(range(128))
    emit('III?QQIBBBBB?BBBB', 127, 0, 1024, False, 0, 0, 0, 0, 0, 0, 0, 0, False, 0, 0, 0, 0)
    emit('I', 16)
    for index in range(16):
        emit('B', 1 if queue_event and index == 0 else 0)
        if queue_event and index == 0: emit('BB', 0x1B, 0xAA)
    emit('B', 0); data.extend([255] * 255)
    emit('???IIIII', False, False, False, 0, 0, 0, 0, 0)
    emit('I' * 7)  # jitter
    emit('I' * 12 + '?')  # frame manager
    emit('BBB?')  # background
    emit('III?BBBBBB?B?II??BBBI')  # playfield
    for _ in range(2): emit('III???BBB?BB??BBBBBB??')  # missiles
    for _ in range(2): emit('IIIBBB??BB??BBBBBBBBBBB???')  # players
    emit('IIIBBB???????BB?BBB?B?')  # ball
    emit('B')
    for _ in range(2): emit('BBB????BBB')  # audio channels
    emit('IIIQ')  # accumulators + sample count
    for _ in range(4): emit('ddIIQId?')  # analog readouts
    for _ in range(2): emit('?B')  # latched input
    emit('IIII??II??IIBQBBBQ')
    data.extend(bytes(64))  # TIA shadow register file
    emit('QQIIBBBB')
    emit('I', 0)  # plain4K bank offset
    emit('I', 1)  # host PRNG
    for _ in range(2):
        emit('?????', True, True, True, True, True)
        emit('IIII', 2, 0, 2, 0)
    emit('B', 0x3F)
    return bytes(data)


class StateTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('reference_state'), 'complete reference state codec missing')
        return importlib.import_module('reference_state')

    def test_cpu_ram_timer_and_controllers_are_decoded_without_search(self):
        result = self.api().decode_state(synthetic_state())
        self.assertEqual(result['cpu']['pc'], 0xF000)
        self.assertEqual(result['cpu']['p'], 0x69)
        self.assertEqual(result['ram'], list(range(128)))
        self.assertEqual(result['riot']['timer'], 127)
        self.assertEqual(result['controllers'][0]['digital'], [True] * 5)
        self.assertEqual(result['switches'], 0x3F)
        self.assertEqual(result['host_rng'], 1)

    def test_variable_delay_queue_keeps_tail_and_full_tia_aligned(self):
        result = self.api().decode_state(synthetic_state(True))
        self.assertEqual(result['tia']['queue'][0], [[0x1B, 0xAA]])
        self.assertEqual(result['host_rng'], 1)

    def test_truncated_wrong_header_and_trailing_data_are_rejected(self):
        data = synthetic_state()
        for damaged in (data[:-1], data[:100], b'bad' + data[3:], data + b'junk'):
            with self.subTest(size=len(damaged)), self.assertRaises(ValueError):
                self.api().decode_state(damaged)

    def test_poweron_freeze_edits_only_declared_bookkeeping_and_host_seed(self):
        api = self.api(); data = synthetic_state(); frozen = api.freeze_poweron(data, 42)
        changed = {i for i, (a, b) in enumerate(zip(data, frozen)) if a != b}
        self.assertEqual(changed, {41, len(data) - 47})
        result = api.decode_state(frozen)
        self.assertEqual(result['host_rng'], 42)
        self.assertEqual(result['cpu']['a'], 0x12)
        bad = bytearray(data); bad[31:33] = (0xF019).to_bytes(2, 'little')
        with self.assertRaises(ValueError): api.freeze_poweron(bytes(bad), 42)
