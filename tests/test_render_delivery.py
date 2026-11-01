import copy
import hashlib
import importlib
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class RendererDeliveryTests(unittest.TestCase):
    def api(self):return importlib.import_module('render_delivery')

    def fixture(self):
        api=self.api();from render_model import schedule
        data=bytearray(32768);data[:2]=b'AB';data[2:4]=(0x4014).to_bytes(2,'little');data[16:20]=b'FBR8'
        build={'version':'0.0.2-renderer','source_commit':'a'*40,'source_dirty':False,
               'rom':{'filename':'frostbite-0.0.2-renderer.rom','size':32768,'used_bytes':30674,
                      'padding_bytes':2094,'sha256':hashlib.sha256(data).hexdigest(),'mapper':'Normal/plain32KiB'},
               'source_files':{p:'b'*64 for p in api.BUILD_FILES},'assembler_sha256':'c'*64}
        base={'build_source_commit':'a'*40,'build_source_dirty':False,'harness_source_commit':'a'*40,
              'harness_source_dirty':False,'harness_hashes':{p:'b'*64 for p in api.HARNESS_FILES},
              'rom_sha256':build['rom']['sha256'],'complete':True,'min_spacing':29,
              'max_sprites_per_line':4,'emulator':'openMSX 21.0','emulator_sha256':'d'*64,'profile_sha256':'e'*64}
        rpc={**base,'cases':643,'max_busy_cycles':58409,'frame_budget':59736,'pixel_errors':0,
             'data_writes':643*929,'stack_min':62324}
        suite={'schema_version':1,'rpc':rpc,'negative_controls':{p:True for p in ('pixel','sprite','overflow','guard','spacing')}}
        for family,period,busy in (('ntsc',59736,55455),('pal',71364,65426)):
            total=0;steps=[]
            for n in schedule(240,period):total+=n;steps.append(total)
            suite[family]={**base,'cases':240,'max_busy_cycles':busy,'frame_budget':period,'stack_min':62324,
                'frames':list(range(240)),'busy_cycles':[busy]*240,'commit_cycles':[1205]*240,
                'commit_start_y':[192]*240,'commit_y':[197]*240,'period_cycles':[period]*240,
                'step_counts':steps,'surrogate_cycles':[10018]*total,'pal_flag':int(family=='pal'),'data_writes':223856}
        suite['controls']={**base,'cases':1,'control_checks':['right','left','space-edge','space-held','space-repress']}
        return bytes(data),build,suite

    def test_only_complete_clean_identity_bound_evidence_can_be_published(self):
        api=self.api();data,build,suite=self.fixture();api.validate_bundle(build,suite,data)
        for fault in ('dirty-build','dirty-harness','wrong-rom','wrong-producer','missing-helper','failed-control','failed-negative'):
            b=copy.deepcopy(build);s=copy.deepcopy(suite);rom=data
            if fault=='dirty-build':b['source_dirty']=True
            elif fault=='dirty-harness':s['ntsc']['harness_source_dirty']=True
            elif fault=='wrong-rom':rom=rom[:-1]+b'\x01'
            elif fault=='wrong-producer':s['rpc']['build_source_commit']='f'*40
            elif fault=='missing-helper':s['pal']['harness_hashes'].pop(next(iter(api.HARNESS_FILES)))
            elif fault=='failed-control':s['controls']['control_checks']=[]
            else:s['negative_controls']['spacing']=False
            with self.subTest(fault=fault),self.assertRaises(ValueError):api.validate_bundle(b,s,rom)

    def test_compact_report_excludes_unknown_raw_fields(self):
        api=self.api();data,build,suite=self.fixture()
        build['rom']['raw_original']='PRIVATE';suite['rpc']['ram']=[0]*128;suite['ntsc']['private']='PRIVATE'
        public=api.compact_bundle(build,suite)
        self.assertNotIn('PRIVATE',str(public));self.assertNotIn('ram',public['timings']['rpc'])
        self.assertEqual(public['timings']['rpc']['margin_cycles'],1327)

    def test_package_copies_exact_tested_bytes_and_never_replaces_a_version(self):
        api=self.api();data,build,suite=self.fixture();report=api.compact_bundle(build,suite)
        notes=f'0.0.2-renderer\n{build["source_commit"]}\n{build["rom"]["sha256"]}\nCurrent state\nNext\nHuman tests\n'
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/'release'
            hashes=api.package_files(data,build,report,notes,None,destination)
            self.assertEqual((destination/build['rom']['filename']).read_bytes(),data)
            self.assertEqual(hashes[build['rom']['filename']],hashlib.sha256(data).hexdigest())
            self.assertEqual(api.package_files(data,build,report,notes,None,destination),hashes)
            with self.assertRaises(ValueError):api.package_files(data,build,report,notes+'changed',None,destination)
            self.assertEqual((destination/'release-notes.md').read_text(),notes)
