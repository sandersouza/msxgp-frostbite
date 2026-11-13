"""Hand-derived pixels pin the small geometry compiler's boundary behavior."""
import unittest
import importlib.util
from pathlib import Path


class FloeGeometryTests(unittest.TestCase):
    def model(self):
        path = Path(__file__).resolve().parents[1] / 'scripts/compact_floe.py'
        self.assertTrue(path.exists(), 'compact floe model missing')
        spec = importlib.util.spec_from_file_location('compact_floe_model', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_filled_rectangles_union_and_wrap_before_player(self):
        model = self.model()
        directory, groups = model.compile_footprints([(0, 0)], [0] * 7)
        self.assertEqual(len(directory), 160)
        self.assertEqual(groups[directory[0]], b'\xff' * 7)
        self.assertEqual(groups[directory[8]], bytes(7))
        self.assertEqual(groups[directory[159]], b'\xff' * 7)
        self.assertEqual(groups[directory[153]], b'\xf8' * 7)
        self.assertEqual(groups[directory[152]], b'\xf0' * 7)

    def test_vertical_clipping_and_reflection_use_real_glyph_bits(self):
        model = self.model()
        glyph = bytes([128] + [0] * 18)
        first = bytes([128] + [0] * 6)
        second = bytes([0, 1] + [0] * 5)
        self.assertTrue(model.convolve(glyph, first, 50))
        self.assertFalse(model.convolve(glyph, first, 49))
        self.assertFalse(model.convolve(glyph, first, 51))
        self.assertFalse(model.convolve(glyph, first, 0))
        self.assertFalse(model.convolve(glyph, second, 51))
        self.assertTrue(model.convolve(glyph, second, 51, reflect=True))

    def test_rejects_partial_footprints_and_glyphs(self):
        model = self.model()
        for glyph, masks in ((bytes(18), bytes(7)), (bytes(19), bytes(6))):
            with self.assertRaises(ValueError):
                model.convolve(glyph, masks, 50)
        with self.assertRaises(ValueError):
            model.compile_footprints([(0, 0)], [0] * 6)

    def test_shadow_rule_keeps_vertical_and_absolute_x_exceptions(self):
        model = self.model()
        shadow = getattr(model, 'shadow_channel', None)
        self.assertIsNotNone(shadow, 'exact scalar shadow rule missing')
        self.assertEqual(shadow(0, 0, 0), 64)
        self.assertEqual(shadow(1, 45, 94), 0)
        for y, expected in ((0, 64), (49, 64), (50, 0), (68, 0), (69, 64), (77, 64)):
            self.assertEqual(shadow(4, y, 94), expected)
        self.assertEqual(shadow(4, 49, 93), 0)
        self.assertEqual(shadow(4, 49, 95), 0)
        self.assertEqual(shadow(4, 49, 126), 64)
        self.assertEqual(shadow(4, 49, 158), 64)
        self.assertEqual(shadow(5, 49, 95), 64)
        self.assertEqual(shadow(5, 49, 159), 64)


if __name__ == '__main__':
    unittest.main()
