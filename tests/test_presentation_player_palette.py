import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PlayerPaletteTests(unittest.TestCase):
    def test_skin_hat_and_death_colors(self):
        from presentation_player_palette import player_color
        self.assertEqual([player_color(c,6) for c in (0x16,0x24,0x36)],[11,10,11])
        self.assertEqual(player_color(6,14),14)
        for code in (0x92,0x94,0x96,0x98):self.assertEqual(player_color(code,5),5)

    def test_header_identity_includes_level_threshold_and_colors(self):
        from presentation_player_palette import header_identity
        codes=bytes(range(12));colors=bytes((5,5,4))
        a=header_identity(codes,colors,19)
        self.assertNotEqual(a,header_identity(codes,colors,20))
        self.assertEqual(header_identity(codes,colors,20),header_identity(codes,colors,255))
        self.assertNotEqual(a,header_identity(codes,bytes((5,6,4)),19))
        self.assertEqual(len(a),16)

    def test_changed_glyphs_only_visit_intersecting_columns(self):
        from presentation_player_palette import changed_columns
        before=bytes(16)
        self.assertEqual(changed_columns(before,before),0)
        for glyph in range(12):
            after=bytearray(before);after[glyph]=8
            self.assertEqual(changed_columns(before,after),(3,14,24,112,192,896)[glyph%6])
        self.assertEqual(changed_columns(None,before),1023)
        after=bytearray(before);after[15]=1
        self.assertEqual(changed_columns(before,after),1023)

    def test_only_visible_player_pixels_are_recolored(self):
        from presentation_player_palette import adapt_tagged
        raw=bytes([0x24])*33600;tagged=bytearray(raw);tagged[100*160+40]|=1
        palette={0x24:(162,98,33)}
        from graphics_mapping import map_frame,map_x,map_y
        before=map_frame(raw,palette);after=adapt_tagged(raw,bytes(tagged),palette)
        expected=bytearray(before);start=map_y(100)*256+map_x(40)
        expected[start:start+map_x(41)-map_x(40)]=bytes([10])*(map_x(41)-map_x(40))
        self.assertEqual(after,bytes(expected))
        tagged[1]=0x37
        with self.assertRaises(ValueError):adapt_tagged(raw,bytes(tagged),palette)

    def test_terminal_animation_keeps_original_palette(self):
        from presentation_player_palette import adapted_frame
        from graphics_mapping import map_frame
        raw=bytes([0x24])*33600;palette={0x24:(162,98,33)}
        for offset in (0x6b,0x70):
            ram=bytearray(128);ram[offset]=1
            self.assertEqual(adapted_frame({'player_palette':True},b'',{},ram,raw,palette),map_frame(raw,palette))
