import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class CaptureTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('reference_traces'), 'bounded full-emulator harness missing')
        return importlib.import_module('reference_traces')

    def test_raw_both_controller_bits_use_electrical_pin_levels(self):
        commands = self.api().control_commands({'swcha': 0x7E, 'swchb': 0x3D, 'fire': [True, False]})
        self.assertIn('joy0Right 0', commands)
        self.assertIn('joy1Up 0', commands)
        self.assertIn('joy0Fire 0', commands)
        self.assertIn('joy1Fire 1', commands)
        self.assertIn('joy0Up 1', commands)
        self.assertIn('swchb $3d', commands)
        self.assertEqual(len(commands), 11)

    def test_slots_and_raw_inputs_are_bounded_before_emulation(self):
        api = self.api(); neutral = {'swcha': 255, 'swchb': 63, 'fire': [False, False]}
        for steps in ([], [neutral] * 11):
            with self.assertRaises(ValueError): api.batch_script(steps)
        for invalid in ({**neutral, 'swcha': 256}, {**neutral, 'fire': [0, 1]},
                        {**neutral, 'swchb': True}):
            with self.assertRaises(ValueError): api.control_commands(invalid)

    def test_route_expansion_preserves_explicit_inputs_and_refuses_bad_counts(self):
        api = self.api()
        self.assertTrue(hasattr(api, 'expand_route'), 'bounded route expansion missing')
        segment = {'count': 2, 'swcha': 255, 'swchb': 63, 'fire': [False, False]}
        self.assertEqual(api.expand_route([segment]), [
            {'swcha': 255, 'swchb': 63, 'fire': [False, False]},
            {'swcha': 255, 'swchb': 63, 'fire': [False, False]}])
        with self.assertRaises(ValueError): api.expand_route([{**segment, 'count': 0}])

    def test_wrong_rom_never_executes_backend_or_creates_capture(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); marker = root / 'executed'; backend = root / 'fake-stella'
            backend.write_text(f'#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n')
            backend.chmod(0o755); rom = root / 'bad.rom'; rom.write_bytes(bytes(4096))
            out = root / 'capture'
            with self.assertRaises(ValueError): api.run_debugger(rom, 'exitRom\n', out, stella=str(backend))
            self.assertFalse(marker.exists())
            self.assertFalse(out.exists())

    def test_public_output_destination_is_refused(self):
        api = self.api()
        with self.assertRaises(ValueError): api.private_output(api.ROOT / 'references/trace-raw')

    def test_changed_utility_fingerprint_invalidates_capture_identity(self):
        api = self.api()
        self.assertTrue(hasattr(api, 'verify_fingerprints'), 'source-identity drift guard missing')
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'utility.py'; source.write_bytes(b'old source\n')
            expected = {str(source): hashlib.sha256(source.read_bytes()).hexdigest()}
            api.verify_fingerprints(expected)
            source.write_bytes(b'changed source\n')
            with self.assertRaises(ValueError): api.verify_fingerprints(expected)

    def test_unsupported_backend_is_refused_before_rom_execution(self):
        api = self.api()
        self.assertTrue(hasattr(api, 'backend_identity'), 'preflight backend identity missing')
        with tempfile.TemporaryDirectory() as tmp:
            backend = Path(tmp) / 'unsupported'
            backend.write_text(f'#!{sys.executable}\nprint("Stella version 6.7\\n-debug option")\n')
            backend.chmod(0o755)
            with self.assertRaises(ValueError): api.backend_identity(str(backend))

    def test_observed_controller_pins_and_boundary_must_match_request(self):
        from test_reference_state import synthetic_state
        from reference_state import decode_state
        api = self.api(); state = decode_state(synthetic_state())
        sample = {'swcha': 255, 'swchb': 63, 'fire': [False, False]}
        with self.assertRaises(ValueError): api.validate_checkpoint(state, sample)
        state['cpu']['pc'] = 0xF019
        self.assertEqual(api.observed_input(state), sample)
        api.validate_checkpoint(state, sample)
        state['controllers'][1]['digital'][0] = False
        with self.assertRaises(ValueError): api.validate_checkpoint(state, sample)

    def test_selected_player_fixture_declares_only_one_ram_byte_injection(self):
        from test_reference_state import synthetic_state
        from reference_state import decode_state
        api = self.api()
        self.assertTrue(hasattr(api, 'selected_player_fixture'), 'explicit two-player fixture missing')
        raw = bytearray(synthetic_state()); raw[31:33] = (0xF019).to_bytes(2, 'little')
        offset = decode_state(bytes(raw))['_offsets']['ram']
        raw[offset] = 1; raw[offset+0x47] = 0
        changed = api.selected_player_fixture(bytes(raw), 1)
        self.assertEqual({i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b}, {offset+0x47})
        raw[offset] = 0
        with self.assertRaises(ValueError): api.selected_player_fixture(bytes(raw), 1)
