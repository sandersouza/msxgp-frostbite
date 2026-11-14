import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_native_disk import shared_payloads
from build_native_plain32 import overlap_slack
from build_native_flat_image import digest


class NativeLoaderContracts(unittest.TestCase):
    def test_only_proven_three_byte_backward_overlap_is_admitted(self):
        self.assertEqual(overlap_slack('File compressed (delta 3)'),3)
        for log in ('no delta','File compressed (delta 4)','(delta 30)'):
            with self.assertRaises(ValueError):overlap_slack(log)

    def test_disk_payloads_must_equal_the_exact_cartridge_not_just_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);r=bytearray(32768);r[:2]=b'AB';r[256:260]=b'low!';r[260:263]=b'gfx'
            (p/'FROSTBIT.ROM').write_bytes(r)
            (p/'cold-low.zx0').write_bytes(b'low!');(p/'cold-gfx-high.zx0').write_bytes(b'gfx')
            m=dict(rom_sha256=digest(r),compressed_low_bytes=4,compressed_gfx_high_bytes=3,
                   symbols=dict(main_data=0x4100,gfx_data=0x4104))
            self.assertEqual(shared_payloads(p,m),(b'low!',b'gfx'))
            (p/'cold-low.zx0').write_bytes(b'bad!')
            with self.assertRaises(ValueError):shared_payloads(p,m)

    def test_payload_cannot_point_outside_the_normal_cartridge(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);r=b'AB'+bytes(32766);(p/'FROSTBIT.ROM').write_bytes(r)
            (p/'cold-low.zx0').write_bytes(b'!');(p/'cold-gfx-high.zx0').write_bytes(b'?')
            m=dict(rom_sha256=digest(r),compressed_low_bytes=1,compressed_gfx_high_bytes=1,
                   symbols=dict(main_data=0xC000,gfx_data=0x4100))
            with self.assertRaises(ValueError):shared_payloads(p,m)
