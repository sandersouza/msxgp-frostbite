import copy
import hashlib
import importlib
import sys
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class RendererBenchTests(unittest.TestCase):
    def test_capture_refuses_helpers_changed_since_build(self):
        api=importlib.import_module('render_bench')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'model.py';path.write_bytes(b'original')
            metadata={'source_files':{'model.py':hashlib.sha256(path.read_bytes()).hexdigest()}}
            api.validate_source_files(metadata,root)
            path.write_bytes(b'modified')
            with self.assertRaises(ValueError):api.validate_source_files(metadata,root)
    def test_generated_directives_are_not_parsed_as_labels(self):
        api=importlib.import_module('render_build')
        with tempfile.TemporaryDirectory() as tmp,patch.object(api,'OUT',Path(tmp)):
            api.write_tables()
            for line in (Path(tmp)/'render_tables.inc').read_text().splitlines():
                self.assertTrue(line.startswith(' ') or ':' in line,line)

    def test_wrong_or_stale_rom_identity_is_rejected(self):
        api=importlib.import_module('render_build');data=bytearray(32768)
        self.assertTrue(api.validate_rom(data))
        data[:2]=b'AB';data[2:4]=(0x4010).to_bytes(2,'little');data[16:20]=b'FBR8'
        self.assertEqual(api.validate_rom(data),[])
        metadata={'rom':{'size':32768,'sha256':hashlib.sha256(data).hexdigest()},'version':'0.0.2-renderer'}
        api.validate_identity(data,metadata)
        data[-1]=1
        with self.assertRaises(ValueError):api.validate_identity(data,metadata)

    def test_decoder_uses_actual_name_page_bank_and_sprites(self):
        api=importlib.import_module('render_model');vram=bytearray(16384);regs=[2,0x42,6,255,3,0x36,7,4]
        vram[0x1B00]=208
        pixels=api.decode_pixels(vram,regs)
        self.assertEqual(set(pixels),{4})
        vram[0x1C00+16*32]=1;vram[4096+8]=128;vram[0x2000+4096+8]=0xF0
        regs[2]=7
        self.assertEqual(api.decode_pixels(vram,regs)[128*256],15)
        regs[2]=6
        self.assertEqual(api.decode_pixels(vram,regs)[128*256],4)

    def test_negative_pixel_occupancy_spacing_and_budget_controls_fail(self):
        api=importlib.import_module('render_bench')
        good={'cases':1,'complete':True,'min_spacing':29,'max_busy_cycles':50000,
              'pixel_errors':0,'max_sprites_per_line':4,'rom_sha256':'a'*64,'frame_budget':59736}
        api.validate_observations(good,expected_cases=1,rom_hash='a'*64)
        for field,value in (('complete',False),('cases',0),('min_spacing',28),('max_busy_cycles',59737),
                            ('pixel_errors',1),('max_sprites_per_line',5),('rom_sha256','b'*64)):
            changed={**good,field:value}
            with self.subTest(field=field),self.assertRaises(ValueError):api.validate_observations(changed,1,'a'*64)

    def test_unsafe_cache_aliases_and_incomplete_input_are_not_accepted(self):
        api=importlib.import_module('render_model')
        for layout in (0,1):
            for page in (0,1):
                used=set()
                for band in range(8):
                    entries=api.cache_segments(layout,page,band)
                    addresses={address+i for address,count,_ in entries for i in range(count)}
                    self.assertFalse(used&addresses);used|=addresses
                    self.assertEqual(len(addresses),32)

    def test_paced_gate_requires_consecutive_frames_real_busy_and_step_reservations(self):
        api=importlib.import_module('render_bench');from render_model import schedule
        for period in (59736,71364):
            total=0;steps=[]
            for count in schedule(240,period):total+=count;steps.append(total)
            good={'cases':240,'complete':True,'frames':list(range(100,340)),
                  'busy_cycles':[50000]*240,'max_busy_cycles':50000,'commit_cycles':[1200]*240,
                  'commit_start_y':[192]*240,'commit_y':[198]*240,'period_cycles':[period]*240,
                  'step_counts':steps,'surrogate_cycles':[10018]*total,'pal_flag':int(period==71364),
                  'max_sprites_per_line':4}
            api.validate_paced(good,period)
            for field,value in (('frames',list(range(100,339))+[340]),('busy_cycles',[period+1]*240),
                    ('commit_y',[0]*240),('period_cycles',[period*2]*240),('step_counts',[0]*240),
                    ('surrogate_cycles',[0]*total),('max_sprites_per_line',5)):
                with self.subTest(period=period,field=field),self.assertRaises(ValueError):api.validate_paced({**good,field:value},period)
