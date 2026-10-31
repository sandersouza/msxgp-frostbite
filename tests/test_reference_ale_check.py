import copy
from enum import Enum
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class ALEEvidenceTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('reference_ale_check'), 'secondary seeded ALE verifier missing')
        return importlib.import_module('reference_ale_check')

    def fixture(self):
        return {'mode': 0, 'policy': {'seed': 1, 'frame_skip': 1, 'repeat_action_probability': 0},
            'initial_sha256': 'a'*64, 'steps': [{'frame': 1, 'action': 0, 'ram': [0]*128,
            'state_sha256': 'b'*64, 'screen_sha256': 'c'*64, 'reward': 0}]}

    def test_repeated_full_state_is_required_not_only_identical_ram(self):
        first = self.fixture(); self.api().validate_ale_repeats(first, copy.deepcopy(first))
        changed = copy.deepcopy(first); changed['steps'][0]['state_sha256'] = 'd'*64
        with self.assertRaises(ValueError): self.api().validate_ale_repeats(first, changed)

    def test_native_enum_actions_are_read_by_value(self):
        class Action(Enum):
            NOOP = 0
            FIRE = 1
        self.assertTrue(hasattr(self.api(), 'legal_action_codes'), 'native action-enum adapter missing')
        self.assertEqual(self.api().legal_action_codes([Action.NOOP, Action.FIRE]), {0, 1})

    def test_skipped_frames_sticky_policy_and_unsupported_modes_are_refused(self):
        for kind in ('skip', 'sticky', 'mode', 'empty'):
            with self.subTest(kind=kind):
                first = self.fixture()
                if kind == 'skip': first['steps'][0]['frame'] = 2
                elif kind == 'sticky': first['policy']['repeat_action_probability'] = 0.25
                elif kind == 'mode': first['mode'] = 1
                elif kind == 'empty': first['steps'] = []
                with self.assertRaises(ValueError): self.api().validate_ale_repeats(first, copy.deepcopy(first))
