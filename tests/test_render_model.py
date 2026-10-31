import copy
import importlib
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class RendererModelTests(unittest.TestCase):
    def api(self):return importlib.import_module('render_model')

    def test_all_x_positions_clip_repeat_and_preserve_input(self):
        api=self.api()
        for x in range(160):
            scene=api.scene(x);before=copy.deepcopy(scene)
            data=api.encode_scene(scene)
            self.assertEqual(len(data),32)
            pixels=api.background_pixels(scene)
            self.assertEqual(len(pixels),256*192)
            self.assertTrue(all(pixels[y*256+column] in (1,4) for y in range(64,192) for column in tuple(range(8))+tuple(range(248,256))))
            self.assertEqual(scene,before)
            self.assertEqual(api.display_x(x),8+(3*x)//2)
        with self.assertRaises(ValueError):api.encode_scene({**api.scene(0),'player_x':160})

    def test_phase_tables_have_full_bank_crossing_padding_and_exact_colors(self):
        api=self.api();tables=api.phase_tables()
        self.assertEqual(len(tables),5*16*4*64)
        for kind in range(5):
            for phase in range(16):
                for shift in (0,2,4,6):
                    block=tables[((kind*16+phase)*4+shift//2)*64:((kind*16+phase)*4+shift//2+1)*64]
                    self.assertEqual(len(block),64)
                    self.assertEqual(sum(byte.bit_count() for byte in block),sum(byte.bit_count() for byte in tables[((kind*16+phase)*4)*64:((kind*16+phase)*4+1)*64]))
        self.assertIn(124,api.BAND_Y[1])

    def test_hybrid_sprite_rectangles_never_exceed_four_and_all_sprite_option_fails(self):
        api=self.api()
        for x in range(160):
            for y in (0,48,79,95,119,127,175,191):
                s=api.scene(x);s.update(player_y=y,bear_y=y,bear_x=min(x,151))
                sat=api.sprite_attributes(s)
                self.assertEqual(len(sat),33)
                self.assertEqual(max(api.occupancy(sat)),4)
        self.assertGreater(api.all_sprite_peak(),4)
        self.assertEqual(len(api.sprite_patterns()),2048)

    def test_vram_regions_do_not_overlap_or_exceed_real_16k(self):
        regions=self.api().vram_regions();used=set()
        for start,size in regions.values():
            region=set(range(start,start+size));self.assertFalse(used&region);used|=region
        self.assertLessEqual(max(used),16383)
        self.assertEqual(sum(size for _,size in regions.values()),16000)

    def test_rational_schedule_preserves_every_required_step(self):
        api=self.api()
        for period in (59736,71364):
            steps=api.schedule(1000,period)
            self.assertEqual(sum(steps),(1000*period)//59736)
            self.assertTrue(set(steps)<={1,2})
        self.assertEqual(api.schedule(240,59736),[1]*240)
        self.assertIn(2,api.schedule(240,71364))
        with self.assertRaises(ValueError):api.schedule(1,1)
