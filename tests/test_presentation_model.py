"""Source field and primitive contracts, using no original ROM bytes."""
import copy
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationModelTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_model'), 'general source presentation model missing')
        return importlib.import_module('presentation_model')

    def state(self, **patch):
        ram = [0] * 128; ram[0x4D] = 255; ram[0x45] = 0; ram[0x65] = 0x45; ram[0x4C] = 3
        for address, value in patch.items(): ram[int(address, 16) - 128] = value
        return ram

    def rom(self):
        rom = bytearray(4096); rom[0xFF9:0xFFC] = bytes((10, 12, 14))
        return bytes(rom)

    def addresses(self, glyphs): return [glyph['address'] for glyph in glyphs]

    def test_source_score_leading_blanks_bcd_rollover_and_selected_player_are_read_only(self):
        api = self.api(); rom = self.rom(); ram = self.state(c8=0x12, c9=0x34, ca=0x56, c7=1)
        saved = copy.deepcopy(ram); hud = api.hud(rom, ram)
        self.assertEqual(self.addresses(hud['score']), [0xFF00 + n * 8 for n in (1, 2, 3, 4, 5, 6)])
        self.assertEqual([(g['x'], g['y']) for g in hud['score']], [(22 + 8 * n, 10) for n in range(6)])
        self.assertEqual({g['color'] for g in hud['score']}, {12}); self.assertEqual(ram, saved)
        top = api.hud(rom, self.state(c8=0x99, c9=0x99, ca=0x99))
        self.assertEqual(self.addresses(top['score']), [0xFF48] * 6)
        zero = api.hud(rom, self.state())
        self.assertEqual(self.addresses(zero['score']), [0xFF50] * 5 + [0xFF00])
        literal = api.hud(rom, self.state(c8=0xA0))
        self.assertEqual(self.addresses(literal['score']), [0xFF50] + [0xFF00] * 5)

    def test_full_literal_temperature_domain_status_icon_reserves_and_original_blink_predicate(self):
        api = self.api(); rom = self.rom()
        for value in range(256):
            ram = self.state(e5=value, cc=9, cb=24); saved = copy.deepcopy(ram); hud = api.hud(rom, ram)
            high = 0xFF50 if value >> 4 == 0 else 0xFF00 + (value >> 4) * 8
            expected = [high, 0xFF00 + (value & 15) * 8, 0xFF53, 0xFD6D, 0xFF50, 0xFF48]
            self.assertEqual(self.addresses(hud['status']), expected)
            self.assertEqual({g['color'] for g in hud['status']}, {132 if high == 0xFF50 else 10})
            self.assertEqual(ram, saved)
        self.assertEqual(self.addresses(api.hud(rom, self.state(cc=0))['status'])[-1], 0xFF50)
        self.assertEqual(self.addresses(api.hud(rom, self.state(cb=19))['status'])[3], 0xFF50)
        self.assertEqual(self.addresses(api.hud(rom, self.state(cb=20))['status'])[3], 0xFD6D)
        for field, value in (('81', 8), ('f1', 1)):
            hud = api.hud(rom, self.state(e5=9, **{field: value}))
            self.assertEqual({g['color'] for g in hud['status']}, {10})

    def test_all_level_bytes_bonus_night_early_bear_and_door_source_selectors(self):
        api = self.api()
        for level in range(256):
            for bonus in (0, 128):
                ram = self.state(cb=level, c5=bonus, cd=15); saved = copy.deepcopy(ram)
                palette = api.palette(ram); night = bool(bonus or level & 4)
                self.assertEqual(palette['sky'], 128 if night else 132)
                self.assertEqual(palette['shore'], 2 if night else 10)
                self.assertEqual(palette['bear'], (2 if night else 10) if level < 3 else (12 if night else 4))
                self.assertEqual(palette['door'], 56 if night else 0); self.assertEqual(ram, saved)
        self.assertEqual(api.palette(self.state(cb=7, cd=15, **{'81': 8}))['door'], 0)
        self.assertEqual(api.palette(self.state(cb=7, cd=14))['door'], 2)

    def test_original_font_rows_reflection_and_wide_pixels_are_explicit(self):
        api = self.api(); rom = bytearray(4096); rom[0x100:0x102] = bytes((0x80, 0x03))
        glyph = api.glyph(bytes(rom), 0xF100, 2)
        self.assertEqual(glyph['pixels'], [0, 0, 0, 0, 0, 0, 1, 1] + [1, 0, 0, 0, 0, 0, 0, 0])
        reflected = api.glyph(bytes(rom), 0xF100, 2, reflect=True, scale=2)
        self.assertEqual(reflected['width'], 16)
        self.assertEqual(reflected['pixels'][:16], [1, 1, 1, 1] + [0] * 12)

    def test_footer_source_phase_uses_finite_glyph_slices_and_retains_coarse_edge_shift(self):
        api = self.api(); rom = bytearray(self.rom()); rom[0xFC0:0xFC8] = bytes(2 * n for n in range(8))
        for value in range(256):
            ram = self.state(c6=value); phase = min(7, max(0, (value & 31) - 12))
            result = api.footer(bytes(rom), ram)
            self.assertEqual(result['phase'], phase)
            self.assertEqual([(g['address'], g['height'], g['x'], g['y']) for g in result['prefix']],
                             [(0xFF90 + n * 8, phase + 1, 22 + n * 8, 189) for n in range(6)])
            self.assertEqual([(g['address'], g['height'], g['x'], g['y']) for g in result['logo']],
                             [(0xFF68 + n * 8 + phase, 8 - phase, 30 + n * 8, 191 + phase) for n in range(5)])
            self.assertEqual([r['color'] for r in result['playfield']], [2 * (7 - n) for n in range(8 - phase)])
        shifted = api.footer(bytes(rom), self.state(e8=150))
        self.assertEqual(shifted['prefix'][0]['y'], 190); self.assertEqual(shifted['logo'][0]['y'], 192)

    def player_rom(self):
        rom = bytearray(self.rom()); rom[0xCAA] = 0; rom[0xCB0] = 0x40
        for n in range(19): rom[0xC00 + n] = 128 >> (n % 8); rom[0xC40 + n] = 2 + n * 2
        return bytes(rom)

    def test_player_rows_retain_original_hold_lines_clear_lines_shore_update_and_pointer_carry(self):
        api = self.api(); rom = self.player_rom()
        player = api.player(rom, self.state(e4=60, e6=64)); rows = {row['y']: row for row in player['rows']}
        self.assertEqual((rows[106]['pattern'], rows[107]['pattern'], rows[108]['pattern']), (128, 128, 0))
        self.assertEqual((rows[106]['color'], rows[107]['color']), (2, 2))
        held = {row['y']: row for row in api.player(rom, self.state(e4=59))['rows']}
        self.assertEqual([held[y]['pattern'] for y in (105, 106, 107, 108)], [128, 128, 128, 0])
        shore = {row['y']: row for row in api.player(rom, self.state(e4=10))['rows']}
        self.assertEqual(shore[47]['prefix_pattern'], 0); self.assertEqual(shore[48]['prefix_pattern'], shore[47]['pattern'])
        self.assertEqual(shore[47]['update_x'], 16)
        wrapped = bytearray(rom); wrapped[0xCAA] = 0xF8; wrapped[0xCB0] = 0xF8
        pointers = api.player(bytes(wrapped), self.state(eb=8, f0=3))
        self.assertEqual(pointers['pattern_address'], 0xFC00)
        self.assertEqual(pointers['color_address'], 0xFC04)

    def test_source_object_copy_order_reflection_color_mask_and_wrap_are_explicit(self):
        api = self.api(); ram = self.state(d4=158, d8=3, a3=64, a7=15, **{'91': 128})
        objects = [g for g in api.objects(self.rom(), ram) if g['row'] == 0]
        self.assertEqual([g['x'] for g in objects], [158, 14, 30])
        self.assertEqual({(g['y'], g['address'], g['color'], g['reflect']) for g in objects}, {(160, 0xFD40, 14, True)})
        self.assertEqual({g['y'] for g in api.objects(self.rom(), ram)}, {160, 134, 108, 82})

    def test_floe_planes_use_actual_motion_nibbles_and_source_scanline_shapes(self):
        api = self.api(); rom = bytearray(self.rom()); rom[0xDD2:0xDD9] = bytes((0, 0x10, 0x10, 0xF0, 0x20, 0x10, 0x20))
        rows = [r for r in api.floes(bytes(rom), self.state(**{'9f': 16, '9c': 0x40, '9d': 0xC0, 'ab': 13})) if r['row'] == 0]
        first = [r for r in rows if r['y'] == 174]
        self.assertEqual([r['x'] for r in first], [12, 24, 44, 56, 76, 88])
        self.assertEqual({r['color'] for r in rows}, {12})
        self.assertEqual([next(r['x'] for r in rows if r['y'] == y) for y in range(174, 181)], [12, 10, 9, 7, 8, 7, 6])

    def test_background_gradient_and_igloo_prepared_bytes_follow_source_order(self):
        api = self.api(); rom = bytearray(self.rom()); rom[0xCB7:0xCC0] = bytes(10 + 2 * n for n in range(9))
        ram = self.state(**{'82': 129, 'c0': 15, 'c4': 60})
        colors = api.background_rows(bytes(rom), ram)
        self.assertEqual(colors[:7], [0] * 7); self.assertEqual(colors[7:33], [132] * 26)
        self.assertEqual(colors[33:35], [26, 26]); self.assertEqual(colors[42:77], [10] * 35)
        self.assertEqual(colors[77], 0); self.assertEqual(colors[78:185], [144] * 107)
        blocks = api.igloo(ram)
        self.assertEqual([(b['x'], b['y'], b['width'], b['height']) for b in blocks if b['y'] == 51],
                         [(112, 51, 4, 4), (116, 51, 4, 4), (120, 51, 4, 4), (124, 51, 4, 4)])
        self.assertEqual([b['x'] for b in blocks if b['y'] == 35], [120, 124, 128, 132])

    def test_general_description_is_read_only_diagnostic_view_does_not_change_source_coordinates(self):
        api = self.api(); state = {'ram': self.state(e4=60, e6=64), 'cpu': {'a': 19}}
        saved = copy.deepcopy(state); first = api.describe(self.player_rom(), state)
        other = api.describe(self.player_rom(), state, layout=1, width=1)
        self.assertEqual(state, saved); self.assertNotEqual(first['target_view'], other['target_view'])
        self.assertEqual({k: v for k, v in first.items() if k != 'target_view'}, {k: v for k, v in other.items() if k != 'target_view'})
        self.assertEqual(len(api.pixels(self.player_rom(), first)), 160 * 210)
        blank = api.describe(self.player_rom(), {'ram': self.state(bf=128)})
        self.assertEqual(api.pixels(self.player_rom(), blank), bytes(160 * 210))

    def test_compositor_keeps_player_priority_and_source_black_comb_with_wrapped_objects(self):
        api = self.api(); rom = bytearray(self.player_rom()); rom[0xD40:0xD48] = bytes([255] * 8); rom = bytes(rom)
        ram = self.state(e4=62, e6=64, a5=64, a9=14, d6=64)
        pixels = api.pixels(rom, api.describe(rom, {'ram': ram}))
        self.assertEqual(pixels[108 * 160 + 64], 2); self.assertEqual(pixels[108 * 160 + 65], 14)
        self.assertEqual(pixels[109 * 160 + 64], 14)
        wrapped = api.pixels(rom, api.describe(rom, {'ram': self.state(a3=64, a7=14, d4=158)}))
        self.assertEqual(wrapped[160 * 160 + 158], 14); self.assertEqual(wrapped[160 * 160 + 159], 14)
        self.assertEqual(wrapped[160 * 160:160 * 160 + 8], bytes(8))

    def test_completed_igloo_door_has_the_measured_narrow_player_reset_origin(self):
        api = self.api(); rom = bytearray(self.player_rom()); rom[0xEF3:0xEFF] = bytes([128] * 12); rom = bytes(rom)
        state = {'ram': self.state(cd=15, c2=255)}; description = api.describe(rom, state)
        self.assertEqual(description['door'][0]['x'], 123)
        image = api.pixels(rom, description)
        self.assertEqual(image[43 * 160 + 123], 0); self.assertEqual(image[43 * 160 + 124], 6)

    def test_extra_coarse_bear_scanline_has_no_hmove_blank_and_keeps_wrapped_player_pixels(self):
        api = self.api(); rom = bytearray(self.player_rom()); rom[0xC11] = 0x3C; rom = bytes(rom)
        image = api.pixels(rom, api.describe(rom, {'ram': self.state(e4=27, e6=158, e8=150)}))
        self.assertEqual(image[56 * 160:56 * 160 + 8], bytes(8))
        self.assertEqual(image[57 * 160:57 * 160 + 8], bytes([36] * 4 + [10] * 4))

    def test_pre_wsync_source_color_fetch_changes_only_the_previous_line_tail(self):
        api = self.api(); rom = self.player_rom()
        for y, player_y, cutoff in ((77, 35, 91), (78, 40, 118), (89, 50, 118), (90, 50, 109), (103, 60, 130)):
            source_y = player_y + 46 - y; dx = source_y % 8
            for side in (-1, 1):
                x = cutoff + side
                image = api.pixels(rom, api.describe(rom, {'ram': self.state(e4=player_y, e6=x - dx)}))
                self.assertEqual(image[y * 160 + x], 2 + 2 * (source_y - int(side > 0)), (y, x))

    def test_post_wsync_color_update_keeps_old_color_before_source_x16(self):
        api = self.api(); rom = self.player_rom()
        for player_x, expected in ((8, 28), (12, 26)):
            image = api.pixels(rom, api.describe(rom, {'ram': self.state(e4=23, e6=player_x)}))
            self.assertEqual(image[57 * 160 + player_x + 4], expected)


if __name__ == '__main__': unittest.main()
