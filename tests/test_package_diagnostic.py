import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


class PackageTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('package_diagnostic'),'release identity gate missing')
        return importlib.import_module('package_diagnostic')

    def fixture(self):
        from rom import VERSION,ROM
        data=b'AB\x10\x40'+bytes(12)+b'FROSTBITE MSX1 DIAGNOSTIC'
        data+=bytes([255])*(16384-len(data))
        digest=hashlib.sha256(data).hexdigest()
        commit='a'*40
        build={'version':VERSION,'diagnostic':True,'source_commit':commit,'source_dirty':False,
               'rom':{'filename':ROM.name,'size':len(data),'sha256':digest}}
        smoke={'version':VERSION,'source_commit':commit,'source_dirty':False,'passed':True,
               'rom_sha256':digest,'ram_bytes':65536,'configured_vram_kib':16,'vdp':'TMS9918A',
               'z80_hz':3579545,'extra_extensions':0}
        return data,build,smoke,commit

    def test_matching_clean_source_and_bytes_are_accepted(self):
        api=self.api()
        api.validate_package(*self.fixture(),dirty=False)

    def test_stale_commit_or_smoke_hash_is_rejected(self):
        api=self.api()
        data,build,smoke,commit=self.fixture()
        with self.assertRaisesRegex(ValueError,'source commit'):
            api.validate_package(data,build,smoke,'b'*40,dirty=False)
        smoke['rom_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'ROM identity'):
            api.validate_package(data,build,smoke,commit,dirty=False)

    def test_dirty_or_failed_delivery_is_rejected(self):
        api=self.api()
        data,build,smoke,commit=self.fixture()
        with self.assertRaisesRegex(ValueError,'clean'):
            api.validate_package(data,build,smoke,commit,dirty=True)
        smoke['passed']=False
        with self.assertRaisesRegex(ValueError,'smoke'):
            api.validate_package(data,build,smoke,commit,dirty=False)


if __name__=='__main__':
    unittest.main()
