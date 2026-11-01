import copy
import importlib
import importlib.util
import sys
import tempfile
import hashlib
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class GraphicsReferenceTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('graphics_reference'),'original execution validator missing')
        return importlib.import_module('graphics_reference')

    def test_pixel_match_rejects_corruption_and_misplaced_table_view(self):
        api=self.api();frame=bytearray(160*210)
        frame[161]=22;frame[322]=36
        view={'width':2,'height':2,'pixels':[1,0,0,1]}
        self.assertEqual(api.match_view(bytes(frame),view,[22,36],[(1,1)]),(1,1))
        frame[161]=24
        with self.assertRaises(ValueError):api.match_view(bytes(frame),view,[22,36],[(1,1)])

    def test_omitted_rows_must_be_black(self):
        api=self.api();frame=bytearray(160*210);api.validate_crop(bytes(frame))
        for offset in (0,6*160,186*160,188*160,202*160,209*160):
            corrupted=frame.copy();corrupted[offset]=12
            with self.assertRaises(ValueError):api.validate_crop(bytes(corrupted))

    def test_logical_row_zero_is_bottom_raster_row(self):
        api=self.api();frame=bytearray(160*210)
        for y in range(160,168):frame[y*160+32]=142
        item={'width':8,'height':8,'pixels':[1,0,0,0,0,0,0,0]*8,'color':142}
        fixture={'asset':'row','family':'row'}
        self.assertEqual(api.source_check(bytes(frame),fixture,{'row':item},bytes(128)),(True,(32,160)))

    def test_repeats_require_pixels_states_actual_requested_modes_and_complete_frames(self):
        api=self.api();point={'name':'fixture','requested':{'e4':27},'actual':{'e4':27},
            'source_sha256':'a'*64,'state_sha256':'b'*64,'ram_sha256':'c'*64,'mapped_sha256':'d'*64,
            'vram_sha256':'e'*64,'decoded_sha256':'f'*64,'tiles_per_bank':[2,2,2],
            'changed_pixels':0,'overcolor_rows':0,'raw_match':True}
        api.validate_repeats([point],[copy.deepcopy(point)],['fixture'])
        for key,value in [('actual',{'e4':28}),('source_sha256','0'*64),('raw_match',False)]:
            other=copy.deepcopy(point);other[key]=value
            with self.assertRaises(ValueError):api.validate_repeats([point],[other],['fixture'])
        with self.assertRaises(ValueError):api.validate_repeats([],[],['fixture'])

    def test_compact_report_excludes_raw_original_payload(self):
        api=self.api();run={'source_sha256':'a'*64,'tool_source_commit':'b'*40,'utility_fingerprints':{},
            'backend':{'version':'0.12.1','binary_sha256':'c'*64,'raw_pixels':[7]},'facts':{'cases':1,'raw_pixels':[7]},
            'private_sha256':'d'*64,'assets':{'raw_bytes':[1]}}
        report=api.compact_report(run)
        self.assertNotIn('assets',report);self.assertNotIn('raw_pixels',report['facts'])
        self.assertNotIn('raw_pixels',report['backend'])

    def test_local_readback_rejects_missing_or_changed_original_pixels(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);suffixes=('tia','before-ram','ram','state','mapped','vram','target')
            point={'name':'fixture','file_sha256':{s:hashlib.sha256(b'fixture').hexdigest() for s in suffixes}}
            for suffix in suffixes:(root/f'0000-fixture.{suffix}').write_bytes(b'fixture')
            api.validate_files(root,[point])
            (root/'0000-fixture.tia').write_bytes(b'changed')
            with self.assertRaises(ValueError):api.validate_files(root,[point])

    def test_floe_cases_cover_original_white_activated_and_reflected_terminal_views(self):
        api=self.api();rom=bytearray(4096)
        cases=api.fixtures(bytes(rom))
        floes=[case for case in cases if case['family']=='palette-floe']
        self.assertEqual({case['patch'][0xAB] for case in floes},{12,152})
        fades=[case for case in cases if case['name'].startswith('fade-')]
        self.assertEqual(len(fades),68)
        self.assertEqual({case['patch'][0xF0] for case in fades},set(range(1,18)))

    def test_independent_decoder_rejects_pattern_damage_and_fifth_sprite_rectangle(self):
        api=self.api();mapping=importlib.import_module('graphics_mapping');pixels=bytes([1])*(256*192)
        vram=bytearray(mapping.compile_screen(pixels)['vram']);api.validate_target(bytes(vram),pixels)
        vram[0x2000]=0xF1
        with self.assertRaises(ValueError):api.validate_target(bytes(vram),pixels)
        vram=bytearray(mapping.compile_screen(pixels)['vram'])
        for i in range(5):vram[0x1B00+4*i:0x1B04+4*i]=bytes([255,i*16,0,1])
        vram[0x1B14]=208
        with self.assertRaisesRegex(ValueError,'sprite'):api.validate_target(bytes(vram),pixels)
