import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import copy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationBackendTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_reference'), 'independent source observer wrapper missing')
        return importlib.import_module('presentation_reference')

    def fixture(self, root, api):
        binary = root / 'stella'; binary.write_bytes(b'original-free backend identity fixture')
        patch = root / 'observer.patch'; patch.write_bytes(b'original-free sidecar patch fixture')
        metadata = {'revision': api.REVISION, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                    'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
                    'producer_commit': 'a' * 40, 'producer_dirty': False}
        receipt = root / 'frostbite-presentation-observer.json'; receipt.write_text(json.dumps(metadata))
        return binary, patch, metadata, receipt

    def test_exact_binary_patch_revision_and_clean_producer_are_required(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as directory:
            binary, patch, metadata, receipt = self.fixture(Path(directory), api)
            self.assertEqual(api.verify_backend(binary, patch), metadata)
            for changes in ({'revision': 'b' * 40}, {'binary_sha256': 'b' * 64},
                            {'patch_sha256': 'b' * 64}, {'producer_dirty': True}, {'producer_commit': 'main'}):
                receipt.write_text(json.dumps({**metadata, **changes}))
                with self.subTest(changes=changes), self.assertRaises(ValueError): api.verify_backend(binary, patch)

    def test_changed_binary_or_patch_is_not_an_equivalent_observer(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as directory:
            binary, patch, _, _ = self.fixture(Path(directory), api)
            old = binary.read_bytes(); binary.write_bytes(old + b'x')
            with self.assertRaises(ValueError): api.verify_backend(binary, patch)
            binary.write_bytes(old); patch.write_bytes(patch.read_bytes() + b'x')
            with self.assertRaises(ValueError): api.verify_backend(binary, patch)

    def test_duplicate_missing_or_wrong_completion_markers_fail(self):
        api = self.api(); good = 'FROSTBITE_PRESENTATION_COMPLETE 3\n'
        api.validate_marker(good, 3)
        for log in ('', good + good, 'FROSTBITE_PRESENTATION_COMPLETE 2\n', good + 'FROSTBITE_PRESENTATION_FAIL frame\n'):
            with self.assertRaises(ValueError): api.validate_marker(log, 3)

    def test_observer_cannot_change_a_single_source_register_ram_byte_or_full_capsule(self):
        api = self.api()
        def state(value):
            return {'cpu': {'a': value, 'x': 2, 'y': 3, 'p': 0x30, 'sp': 255}, 'ram': list(range(128))}
        before, after = state(1), state(4)
        record = {'before': {'registers': before['cpu'], 'ram': before['ram']},
                  'after': {'registers': after['cpu'], 'ram': after['ram']}}
        api.validate_equivalence([record], before, [after], [b'complete capsule'], [b'complete capsule'])
        for phase in ('before', 'after'):
            for kind in ('registers', 'ram'):
                wrong = copy.deepcopy(record)
                if kind == 'registers': wrong[phase][kind]['p'] ^= 1
                else: wrong[phase][kind][127] ^= 1
                with self.subTest(phase=phase, kind=kind), self.assertRaises(ValueError):
                    api.validate_equivalence([wrong], before, [after], [b'complete capsule'], [b'complete capsule'])
        with self.assertRaises(ValueError):
            api.validate_equivalence([record], before, [after], [b'complete capsule'], [b'changed capsule'])
