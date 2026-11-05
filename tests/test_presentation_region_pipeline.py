import unittest
from presentation_region_pipeline import changed_columns,igloo_records,record_address,declare_ram
from presentation_static_assets import decode_tile


class RegionPipelineTests(unittest.TestCase):
    def test_cold_color_and_single_column_transactions(self):
        columns=bytes(range(40));colors=bytes([6,0x76,0x70]);saved=columns+colors+bytes(5)
        self.assertEqual(changed_columns(columns,colors,saved),0)
        new=bytearray(columns);new[6*4+2]^=1
        self.assertEqual(changed_columns(new,colors,saved),1<<6)
        self.assertEqual(changed_columns(columns,bytes([5,0x75,0x70]),saved),1023)
        self.assertEqual(changed_columns(columns,colors,b'\xff'*48),1023)
        with self.assertRaises(ValueError):changed_columns(columns[:39],colors,saved)

    def test_all_igloo_bits_preserve_per_scanline_background_colors(self):
        background=bytes([255])*8+bytes([0x12,0x34,0x56,0x78,0x9a,0xbc,0xd1,0x23])
        records,mapping=igloo_records([background]);self.assertEqual(len(records),48*16)
        self.assertEqual(mapping,bytes([0]))
        first=(252,240,192)
        for cls in range(3):
            for pair in range(16):
                top=pair&3;bottom=pair>>2
                masks=[(first[cls] if p&1 else 0)|((first[cls]^255) if p&2 else 0) for p in (top,bottom)]
                tile=records[(cls*16+pair)*16:(cls*16+pair+1)*16]
                pixels=decode_tile(tile);original=decode_tile(background)
                for y in range(8):
                    for x in range(8):
                        expected=14 if masks[y//4]&(128>>x) else original[y*8+x]
                        self.assertEqual(pixels[y*8+x],expected)
        self.assertEqual(record_address(127),(116,0xbff0))
        self.assertEqual(record_address(128),(117,0xb800))
        self.assertEqual(record_address(1295),(126,0xb8f0))
        with self.assertRaises(ValueError):record_address(-1)
        edge=bytes([0x55])*8+bytes([0x12])*8
        records,mapping=igloo_records([edge,background])
        self.assertEqual(mapping,bytes([255,0]))
        self.assertEqual(len(records),48*16)

    def test_guard_checks_code_and_only_releases_declared_ram(self):
        text='if {[debug read_block memory 0xE880 0xAC0] ne [string repeat [binary format c 165] 0xAC0]} {fail_matrix heap-redzone}\ndebug write_block memory 0xE880 [string repeat [binary format c 165] 0xAC0]'
        new=declare_ram(text,b'\xc9','fail_matrix')
        self.assertIn('0xF000 0x340',new)
        self.assertIn('0xE900 1',new)
        self.assertIn('ram-code',new)
        with self.assertRaises(ValueError):declare_ram(new,b'\xc9','fail_matrix')
