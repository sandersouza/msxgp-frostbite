import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class ProgressionCaseTests(unittest.TestCase):
    def api(self):
        return importlib.import_module('progression_cases')

    def test_score_carry_rollover_cap_and_attract_domains(self):
        cases = self.api().primitive_cases()
        ids = {c['id'] for c in cases}
        self.assertEqual(len(ids), len(cases))
        for name in ('score-4990-reserve8-active', 'score-4990-reserve9-active',
                     'score-999990-reserve8-active', 'score-999990-reserve9-attract',
                     'score-9990-reserve0-active'):
            self.assertIn(name, ids)
        awards = [c for c in cases if c['id'].startswith('block-level-')]
        self.assertEqual(len(awards), 256)
        for c in awards:
            level = int(c['ram']['CB'], 16)
            self.assertEqual(c['expect']['ram']['95'], f'{min(level + 1, 9) << 4:02X}')

    def test_dispatch_all_levels_records_priorities_and_switches(self):
        api = self.api()
        base = bytes(128)
        cases = api.phase_cases(base)
        ids = {name for name, _ in cases}
        self.assertEqual(len(ids), len(cases))
        self.assertTrue(all(len(ram) == 128 for _, ram in cases))
        for level in range(256):
            for player in (0, 1):
                self.assertIn(f'level-{level:02x}-p{player}', ids)
        for flag in (8, 16, 32, 64, 128, 24, 48, 96, 192, 255):
            self.assertIn(f'dispatch-{flag:02x}', ids)
        for variation in range(4):
            for player in (0, 1):
                for own in (0, 1, 8, 9):
                    for other in (0, 1, 8, 9):
                        self.assertIn(f'recover-v{variation}-p{player}-{own}-{other}', ids)
        with self.assertRaises(ValueError):
            api.phase_cases(bytes(127))

    def test_score_assertions_are_fail_closed_and_preserve_saved_record(self):
        api = self.api()
        cases = api.primitive_cases()
        case = next(c for c in cases if c['id'] == 'score-4990-reserve8-active')
        expected = {'ram': [0] * 128, 'registers': {'p': 0x30}}
        for address, value in case['expect']['ram'].items():
            expected['ram'][int(address, 16) - 128] = int(value, 16)
        api.validate_primitive(case, expected)
        expected['ram'][0x4C] = 8
        with self.assertRaisesRegex(ValueError, 'CC'):
            api.validate_primitive(case, expected)

    def test_phase_invariants_reject_lost_record_or_capped_level(self):
        api = self.api()
        cases = dict(api.phase_cases(bytes(128)))
        ram = cases['level-ff-p1']
        after = bytearray(ram)
        after[0x4B] = 0
        after[0x71] = 0
        api.validate_phase('level-ff-p1', ram, after)
        after[0x4B] = 255
        with self.assertRaises(ValueError):
            api.validate_phase('level-ff-p1', ram, after)
        ram = cases['recover-v1-p0-1-1']
        after = bytearray(ram)
        after[0x48:0x4E], after[0x4E:0x54] = ram[0x4E:0x54], ram[0x48:0x4E]
        after[0x47] = 1
        after[0x4C] -= 1
        after[0x71] = 0
        api.validate_phase('recover-v1-p0-1-1', ram, after)
        after[0x4F] ^= 1
        with self.assertRaises(ValueError):
            api.validate_phase('recover-v1-p0-1-1', ram, after)


if __name__ == '__main__':
    unittest.main()
