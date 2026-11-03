"""Finite static fragments preserve every glyph bit and footer background row."""
import importlib
import hashlib
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationStaticAssetsTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_static_assets'),'finite static asset constructor missing')
        return importlib.import_module('presentation_static_assets')
    def test_all_header_fragments_follow_the_original_glyph_row_and_pixel_phase(self):
        api=self.api();rom=bytes((i*37+i//7)&255 for i in range(4096));data=api.header_fragments(rom)
        self.assertEqual(len(data),1360)
        for glyph in range(34):
            address=0xF00+8*glyph if glyph<32 else 0xF53 if glyph==32 else 0xD6D
            for part,(shift,cell) in enumerate(((1,0),(1,1),(5,0),(5,1),(5,2))):
                for y in range(8):
                    value=rom[address+7-y];expected=0
                    for x in range(8):
                        if value&(128>>x):
                            for target in range(x*3//2,(x+1)*3//2):
                                local=target+shift-cell*8
                                if 0<=local<8:expected|=128>>local
                    self.assertEqual(data[glyph*40+part*8+y],expected)
    def test_igloo_masks_cover_all_pf1_bits_at_the_exact_six_pixel_block_width(self):
        api=self.api()
        for bits in range(256):
            actual=set()
            for column in range(6):
                mask=api.igloo_mask(bits,column)
                actual.update(column*8+x for x in range(8) if mask&(128>>x))
            expected={x for bit in range(8) if bits&(1<<bit) for x in range(bit*6,bit*6+6)}
            self.assertEqual(actual,expected)
    def test_footer_descriptors_decode_all_sixteen_states_and_retain_the_water_tail(self):
        api=self.api();rom=bytearray(4096)
        for i in range(0xF68,0xFC8):rom[i]=(i*17+37)&255
        palette={code:(0,0,0) for code in range(0,256,2)}
        palette.update({12:(200,200,200),144:(84,85,237)})
        package=api.footer_tiles(bytes(rom),palette)
        self.assertEqual(len(package['descriptors']),16*22)
        self.assertTrue(all(len(tile)==16 for tile in package['tiles']))
        for coarse in (0,1):
            for phase in range(8):
                decoded=api.decode_footer(package,phase,coarse)
                self.assertEqual(len(decoded),88*16)
                for y in range(2+coarse):self.assertEqual(decoded[y*88:(y+1)*88],bytes((4,))*88)
                self.assertEqual(decoded[-88:],bytes((1,))*88)
                expected=bytearray(bytes((1,))*(88*16))
                expected[:(2+coarse)*88]=bytes((4,))*((2+coarse)*88)
                def point(x,y,color):
                    for tx in range(8+x*3//2,8+(x+1)*3//2):expected[y*88+tx-32]=color
                for glyph in range(6):
                    for y in range(phase+1):
                        row=rom[0xF90+glyph*8+phase-y]
                        for x in range(8):
                            if row&(128>>x):point(22+glyph*8+x,3+coarse+y,15)
                for n in range(8-phase):
                    code=rom[0xFC7-n]&254;color=15 if code==12 else 4 if code==144 else 1
                    for x in list(range(20,36))+list(range(33-n,41-n)):point(x,5+phase+coarse+n,color)
                self.assertEqual(decoded,expected)

    def test_packed_static_tables_preserve_geometry_and_never_cross_mapper_windows(self):
        api=self.api();rom=bytes(4096);palette={code:(0,0,0) for code in range(0,256,2)}
        output_root=Path(__file__).resolve().parents[1]/'outputs';output_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_root) as temporary:
            root=Path(temporary);geometry=root/'geometry';geometry.mkdir()
            data=bytes((165,))*16284+bytes((255,))*100
            (geometry/'geometry-003.bin').write_bytes(data)
            meta={'used_bytes':16284,'physical_banks':[3],'files':{'geometry-003.bin':hashlib.sha256(data).hexdigest()},'source_sha256':hashlib.sha256(rom).hexdigest()}
            result=api.pack_static(rom,palette,geometry,meta,root/'static')
            self.assertEqual((geometry/'geometry-003.bin').read_bytes(),data)
            self.assertEqual((root/'static/assets-003.bin').read_bytes(),data)
            self.assertEqual(result['sections']['header']['pointer'],[0,128,4])
            self.assertEqual(result['header_glyphs'],34)
            for section in result['sections'].values():
                address=int.from_bytes(bytes(section['pointer'][:2]),'little')
                self.assertLessEqual(address+section['size'],0xC000)
            (geometry/'geometry-003.bin').write_bytes(bytes(16384))
            with self.assertRaises(ValueError):api.pack_static(rom,palette,geometry,meta,root/'bad')
