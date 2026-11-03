"""Artifact-chain regression tests built entirely from original-free state/video."""
import hashlib
import importlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_reference_state import synthetic_state
from reference_state import decode_state
from presentation_reference import fixture_batch


def digest(data): return hashlib.sha256(data).hexdigest()


def capsule(frame=0, cycles=0, accumulator=0x12):
    data = bytearray(synthetic_state())
    struct.pack_into('<Q', data, 17, cycles)
    data[26] = accumulator
    struct.pack_into('<H', data, 31, 0xF019)
    struct.pack_into('<I', data, 541, frame)
    state = decode_state(bytes(data))
    assert state['tia']['frame']['total'] == frame and state['cpu']['pc'] == 0xF019
    return bytes(data)


def fixture(root):
    initial = capsule(); after = capsule(1, 19912, 0x13)
    state = decode_state(initial); after_state = decode_state(after)
    def snapshot(s):
        return bytes(s['cpu'][k] for k in ('a', 'x', 'y', 'p', 'sp')) + bytes(s['ram'])
    pixels = bytearray(160 * 228); pixels[18 * 160 + 20] = 132
    def video(cycle): return struct.pack('<IHHHH', cycle, 160, 228, 23, 262) + pixels
    raw = (struct.pack('<8sIII', b'FBPR0002', 1, 3579545, 3)
           + struct.pack('<IHHHIIIIIHH', 0, 0xF019, 0xF476, 0xF019, 0, 0, 1, 18000, 19912, 0, 1)
           + snapshot(state) * 2 + snapshot(after_state) + video(18000) + video(19746)
           + b'FBPRDONE' + struct.pack('<I', 1))
    sample = {'name': 'fixture', 'ram': state['ram'], 'input': {'swcha': 255, 'swchb': 63, 'fire': [False, False]}}
    directory = root / 'batch-00000'; directory.mkdir()
    for name, probe in (('plain', False), ('observed', True)):
        settings = directory / name / 'settings'; states = settings / 'state'; states.mkdir(parents=True)
        (settings / 'autoexec.script').write_text(fixture_batch([sample], probe))
        (states / 'Frostbite (1983) (Activision).st0').write_bytes(after)
        (states / 'Frostbite (1983) (Activision).st9').write_bytes(initial)
    (directory / 'observed/stella.log').write_text('FROSTBITE_PRESENTATION_COMPLETE 1\n')
    (directory / 'records.bin').write_bytes(raw)
    normalized = bytes(pixels[11 * 160:221 * 160]); (root / '0000-fixture.tia').write_bytes(normalized)
    point = {'name': 'fixture', 'requested_ram_sha256': digest(bytes(state['ram'])),
             'before_ram_sha256': digest(bytes(state['ram'])), 'raster_sha256': digest(normalized),
             'state_sha256': digest(after), 'audio_writes': 0}
    return directory, initial, [sample], [point], digest(raw)


class SourceArtifactTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_source_check'), 'independent persisted source artifact checker missing')
        return importlib.import_module('presentation_source_check')

    def test_complete_persisted_original_free_fixture_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = fixture(Path(tmp)); result = self.api().audit_batch(*args, fixture=True)
            self.assertEqual(result, {'intervals': 1, 'physical_frames': 1, 'normalized_frames': 1,
                                      'unmapped_startup_frames': 0, 'audio_writes': 0})

    def test_forged_rehashed_phase_register_or_last_ram_byte_is_rejected(self):
        for offset in (20 + 34, 20 + 34 + 132):
            with self.subTest(offset=offset), tempfile.TemporaryDirectory() as tmp:
                args = list(fixture(Path(tmp))); path = args[0] / 'records.bin'
                wrong = bytearray(path.read_bytes()); wrong[offset] ^= 1; path.write_bytes(wrong); args[4] = digest(wrong)
                with self.assertRaises(ValueError): self.api().audit_batch(*args, fixture=True)

    def test_missing_or_changed_capsule_script_raster_raw_stream_or_marker_is_rejected(self):
        for name in ('capsule', 'script', 'raster', 'raw', 'marker'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                args = fixture(Path(tmp)); directory = args[0]
                if name == 'capsule':
                    path = directory / 'observed/settings/state/Frostbite (1983) (Activision).st0'
                    path.write_bytes(capsule(1, 19912, 0x14))
                elif name == 'script': (directory / 'observed/settings/autoexec.script').write_text('runToPc $f019\n')
                elif name == 'raster': (Path(tmp) / '0000-fixture.tia').write_bytes(bytes(160 * 210))
                elif name == 'raw': (directory / 'records.bin').write_bytes((directory / 'records.bin').read_bytes() + b'x')
                else: (directory / 'observed/stella.log').write_text('FROSTBITE_PRESENTATION_COMPLETE 2\n')
                with self.assertRaises(ValueError): self.api().audit_batch(*args, fixture=True)


if __name__ == '__main__': unittest.main()
