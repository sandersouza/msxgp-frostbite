import importlib
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

HEADER = struct.Struct('<8sIII')
RECORD = struct.Struct('<IHHHIIIH')
EVENT = struct.Struct('<IBB')


def fixture(ordinal=0, events=((18001, 0x19, 7), (18002, 0x19, 7)), phase=0xF019, cropped=False,
            visible_cycles=18000, interval_cycles=19912):
    snapshot = bytes((1, 2, 3, 0x30, 255)) + bytes(range(128))
    raster = bytearray(160 * 210)
    raster[20 * 160:21 * 160] = bytes([8]) * 160
    if cropped: raster[0] = 8
    return RECORD.pack(ordinal, phase, 0xF476, 0xF019, 42, visible_cycles, interval_cycles, len(events)) + snapshot * 3 + raster + b''.join(EVENT.pack(*event) for event in events)


def stream(*records):
    return HEADER.pack(b'FBPR0001', len(records), 3579545, 3) + b''.join(records) + b'FBPRDONE' + struct.pack('<I', len(records))


class PresentationReferenceTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_records'), 'phase-bound raster/audio record parser missing')
        return importlib.import_module('presentation_records')

    def test_complete_phase_raster_cpu_and_repeated_audio_writes_are_preserved(self):
        api = self.api(); raw = stream(fixture()); original = bytes(raw)
        records = api.parse_records(raw); self.assertEqual(raw, original)
        self.assertEqual(len(records), 1); point = records[0]
        self.assertEqual(point['index'], 0); self.assertEqual(point['source_frame'], 42)
        self.assertEqual(point['phases'], [0xF019, 0xF476, 0xF019])
        self.assertEqual(point['visible_cycles'], 18000); self.assertEqual(point['cycles'], 19912)
        self.assertEqual(point['before']['registers'], {'a': 1, 'x': 2, 'y': 3, 'p': 0x30, 'sp': 255})
        self.assertEqual(point['before']['ram'], list(range(128)))
        self.assertEqual(len(point['raster']), 160 * 210)
        self.assertEqual(point['audio'], [(18001, 0x19, 7), (18002, 0x19, 7)])

    def test_silent_interval_is_a_complete_record_not_a_missing_record(self):
        api = self.api(); result = api.parse_records(stream(fixture(events=())))
        self.assertEqual(result[0]['audio'], [])

    def test_seeded_cold_riot_interval_is_not_mislabeled_as_steady_frame_cadence(self):
        api = self.api()
        cold = stream(fixture(events=((140001, 0x19, 7),), visible_cycles=140000, interval_cycles=142059))
        self.assertEqual(api.parse_records(cold)[0]['cycles'], 142059)
        with self.assertRaises(ValueError): api.parse_records(stream(fixture(interval_cycles=524289)))

    def test_truncated_header_snapshot_raster_or_events_and_trailing_data_fail(self):
        api = self.api(); raw = stream(fixture())
        for length in (0, 10, HEADER.size, HEADER.size + RECORD.size + 132, len(raw) - 1, len(raw) - 20):
            with self.subTest(length=length), self.assertRaises(ValueError): api.parse_records(raw[:length])
        with self.assertRaises(ValueError): api.parse_records(raw + b'x')
        with self.assertRaises(ValueError): api.parse_records(stream())

    def test_duplicate_missing_or_reordered_ordinals_fail(self):
        api = self.api()
        for records in ((fixture(1),), (fixture(0), fixture(0)), (fixture(0), fixture(2)), (fixture(1), fixture(0))):
            with self.subTest(records=len(records)), self.assertRaises(ValueError): api.parse_records(stream(*records))
        self.assertEqual(len(api.parse_records(stream(fixture(0), fixture(1)))), 2)

    def test_wrong_drawing_phase_bad_cadence_or_unknown_audio_register_fails(self):
        api = self.api()
        for record in (fixture(phase=0xF476), fixture(events=((19913, 0x19, 7),)),
                       fixture(events=((18002, 0x19, 7), (18001, 0x19, 7))), fixture(events=((18001, 0x14, 7),))):
            with self.assertRaises(ValueError): api.parse_records(stream(record))
        bad = bytearray(stream(fixture())); bad[12:16] = struct.pack('<I', 1)
        with self.assertRaises(ValueError): api.parse_records(bytes(bad))

    def test_nonblack_pixels_in_omitted_source_rows_are_never_silently_cropped(self):
        with self.assertRaises(ValueError): self.api().parse_records(stream(fixture(cropped=True)))
