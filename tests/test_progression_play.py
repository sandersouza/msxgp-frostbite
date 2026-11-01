import copy
import importlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reference_traces import NEUTRAL


class ProgressionPlayTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('progression_play'), 'progression replay adapter missing')
        return importlib.import_module('progression_play')

    def test_original_inactive_pins_are_preserved_after_a_real_turn(self):
        api = self.api()
        inputs = [dict(NEUTRAL), {**NEUTRAL, 'swcha': 223}, {**NEUTRAL, 'swcha': 253, 'fire': [False, True]}]
        points = [{'input': s, 'ram': [0] * 128} for s in inputs]
        points[1]['ram'][0x47] = 1
        points[2]['ram'][0x47] = 1
        self.assertEqual(api.input_records(inputs, points), bytes((255, 63, 0, 0, 223, 63, 0, 0, 253, 63, 0, 1)))
        bad = copy.deepcopy(points); bad[-1]['input']['swcha'] = 255
        with self.assertRaises(ValueError): api.input_records(inputs, bad)
        with self.assertRaises(ValueError): api.input_records(inputs[:-1], points)

    def test_paced_verifier_uses_the_supplied_route_contract_after_full_state_comparison(self):
        api = importlib.import_module('hazard_paced')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / 'source'; out = root / 'out'; source.mkdir(); out.mkdir()
            cpu = {'a': 0, 'x': 0, 'y': 0, 'p': 48, 'sp': 255}
            points = [{'cpu': cpu, 'ram': [0] * 128}] * 2
            (source / 'route.json').write_text(json.dumps({'kind': 'progression', 'assessment': {}}))
            (source / 'trace.json').write_text(json.dumps({'steps': points}))
            (source / 'inputs.json').write_text(json.dumps([NEUTRAL] * 2))
            record = bytes((0, 0, 0, 48, 255)) + bytes(128) + struct.pack('<I', 0)
            (out / 'states.bin').write_bytes(record * 2)
            (out / 'frames.bin').write_bytes(bytes(49364))
            report = {'complete': True, 'source_steps': 2, 'frames': 1, 'canonical_ram_injections': 0,
                'clock_hz': 3579545, 'ram_bytes': 65536, 'min_spacing': 29, 'max_sprites_per_line': 4,
                'stack_min': 0xF340, 'pal_flag': 0, 'layout': 0, 'width': 0}

            def reject(actual, receipt):
                self.assertEqual(len(actual), 2)
                self.assertEqual(actual[-1]['registers'], cpu)
                self.assertEqual(receipt['kind'], 'progression')
                raise ValueError('progression route refused')

            with self.assertRaisesRegex(ValueError, 'progression route refused'):
                api.verify_saved(out, source, 'ntsc', report, assessor=reject)

