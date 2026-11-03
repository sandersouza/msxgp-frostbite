"""Original-free tests for raw, phase-associated source video observations."""
import struct
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from presentation_records import parse_records
import presentation_records as api

RECORD = struct.Struct('<IHHHIIIIIHH')
VIDEO = struct.Struct('<IHHHH')


def video(cycle, height=228, start=23, lines=262, pixel=132):
    return VIDEO.pack(cycle, 160, height, start, lines) + bytes([pixel]) * (160 * height)


def stream(frames=None, end_frame=44):
    if frames is None: frames = [video(500), video(19900)]
    snapshot = bytes((1, 2, 3, 0x30, 255)) + bytes(range(128))
    return (struct.pack('<8sIII', b'FBPR0002', 1, 3579545, 3)
            + RECORD.pack(0, 0xF019, 0xF476, 0xF019, 42, 43, end_frame, 18000, 19912, 0, len(frames))
            + snapshot * 3 + video(18000) + b''.join(frames) + b'FBPRDONE' + struct.pack('<I', 1))


class PhysicalFrameTests(unittest.TestCase):
    def test_every_completed_frame_and_partial_visible_buffer_are_retained_without_cropping(self):
        point = parse_records(stream())[0]
        self.assertEqual(point['source_frame'], 42)
        self.assertEqual(point['visible_frame'], 43)
        self.assertEqual(point['after_frame'], 44)
        self.assertEqual([p['frame'] for p in point['frames']], [43, 44])
        self.assertEqual([p['cycle'] for p in point['frames']], [500, 19900])
        self.assertEqual(point['visible_raster']['height'], 228)
        self.assertEqual(point['visible_raster']['start_line'], 23)
        self.assertEqual(point['visible_raster']['pixels'], bytes([132]) * (160 * 228))
        self.assertNotIn('raster', point, 'unqualified raw viewport must not masquerade as the mapped 210-row view')

    def test_lost_frames_wrong_phase_order_or_dimensions_fail(self):
        for raw in (stream(end_frame=45), stream(frames=[video(19000), video(19001)]),
                    stream(frames=[video(500), video(19913)]), stream(frames=[video(500, 321), video(19900)]),
                    stream()[:-1], stream() + b'x'):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): parse_records(raw)

    def test_measured_viewport_alignment_preserves_all_pixels_and_rejects_partial_or_unsteady_video(self):
        pixels = bytearray(160 * 228); pixels[18 * 160 + 20] = 132
        frame = {'frame': 43, 'width': 160, 'height': 228, 'start_line': 23, 'scanlines': 262, 'pixels': bytes(pixels)}
        normalized = api.normalize_frame(frame)
        self.assertEqual(normalized, bytes(pixels[11 * 160:221 * 160]))
        self.assertEqual(normalized[7 * 160 + 20], 132)
        for changes in ({'frame': None}, {'start_line': 24}, {'height': 227}, {'scanlines': 310}):
            with self.subTest(changes=changes), self.assertRaises(ValueError): api.normalize_frame({**frame, **changes})
        for y in (0, 10, 11, 17, 197, 198, 199, 213, 220, 221, 227):
            wrong = bytearray(pixels); wrong[y * 160] = 8
            with self.subTest(row=y), self.assertRaises(ValueError): api.normalize_frame({**frame, 'pixels': bytes(wrong)})

    def test_original_right_edge_263_line_frame_keeps_the_same_measured_viewport(self):
        pixels = bytearray(160 * 228); pixels[212 * 160 + 150] = 12
        frame = {'frame': 43, 'width': 160, 'height': 228, 'start_line': 23, 'scanlines': 263, 'pixels': bytes(pixels)}
        self.assertEqual(api.normalize_frame(frame)[201 * 160 + 150], 12)
        self.assertEqual(api.normalize_frame(frame), bytes(pixels[11 * 160:221 * 160]))


if __name__ == '__main__': unittest.main()
