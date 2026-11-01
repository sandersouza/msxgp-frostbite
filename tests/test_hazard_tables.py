import copy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardTableTests(unittest.TestCase):
    def test_resident_common_profiles_require_byte_exact_source_equivalence(self):
        api=importlib.import_module('hazard_tables');codec=importlib.import_module('collision_compact')
        plan={'kind':'ordinary','player_x':[25,26],'ys':[0,53],'modes':[{}],'coordinates':list(range(-7,8)),'cases_per_player':30}
        raw=bytes(15*58)+b'\x01'+bytes(15*58-1);pool=codec.CompactRows()
        compiled=api.compile_component(pool,plan,{25:raw,26:raw});packed=pool.emit()
        directory=api.ordinary_common(packed,compiled,25,26);self.assertEqual(len(directory),3)
        compiled['profiles'][26][0][1]=compiled['profiles'][26][0][0]
        with self.assertRaisesRegex(ValueError,'ordinary profiles differ'):api.ordinary_common(packed,compiled,25,26)

    def test_compiler_keeps_the_264th_mode_and_last_source_coordinate(self):
        api=importlib.import_module('hazard_tables');codec=importlib.import_module('collision_compact')
        plan={'kind':'edge','player_x':[159],'ys':[0,53],'modes':[{}]*264,'coordinates':list(range(160)),'cases_per_player':2*264*160}
        profile=bytearray(plan['cases_per_player']*58)
        for mode in range(264):
            offset=((264+mode)*160+159)*58;profile[offset:offset+2]=(mode+1).to_bytes(2,'little')
        pool=codec.CompactRows();compiled=api.compile_component(pool,plan,{159:bytes(profile)})
        packed=pool.emit();directory=api.emit_component(packed,compiled)
        self.assertEqual(len(directory),264*3)
        bank=directory[791];address=int.from_bytes(directory[789:791],'little')
        pointer=api.read_bytes(packed.banks,14,(bank,address),3)
        pointer=api.read_bytes(packed.banks,14,(pointer[2],int.from_bytes(pointer[:2],'little')),6)[3:6]
        row=codec.read_row(packed.banks,packed.metadata,(pointer[2],int.from_bytes(pointer[:2],'little')),159)
        self.assertEqual(row[:2],(264).to_bytes(2,'little'))

    def test_complete_layout_rejects_exploration_and_missing_cold_mode(self):
        api=importlib.import_module('hazard_tables');domain=importlib.import_module('hazard_catalog')
        rom=bytearray(4096);rom[0xD0A:0xD12]=bytes([80,88,120,128,160,168,200,208]);rom[0xDC2:0xDD2]=bytes(range(16))
        plan=domain.capture_plan('edge',rom);plan.update(complete=True,cases=plan['expected_cases'],exploratory=False,producer_dirty_at_start=False)
        parts=[{'start':0,'stop':17,'cases':plan['expected_cases']}];plan['partitions']=parts
        self.assertEqual(api.validate_layout(plan,rom),plan['expected_cases'])
        for key,value in [('exploratory',True),('complete',False),('producer_dirty_at_start',True),('cases',1),('modes',plan['modes'][1:]),('player_x',plan['player_x'][1:])]:
            bad=copy.deepcopy(plan);bad[key]=value
            with self.assertRaises(ValueError,msg=key):api.validate_layout(bad,rom)

    def test_copy_union_retains_both_channels_and_the_160_clock_wrap(self):
        api=importlib.import_module('hazard_tables')
        records={}
        def lookup(px,y,shape,reflection,dx):
            records[dx]=records.get(dx,0)+1
            value=bytearray(58);value[0]=1<<(dx+2);value[29]=4 if dx==0 else 0
            return bytes(value)
        value=api.copy_union(64,42,100,False,3,64,lookup)
        self.assertEqual(records,{0:1})
        self.assertEqual(value[0],4);self.assertEqual(value[29],4)
        records.clear();value=api.copy_union(64,42,100,False,1,48,lookup)
        self.assertEqual(records,{0:1})
        records.clear();value=api.copy_union(10,42,100,False,1,154,lookup)
        self.assertEqual(records,{0:1})
        self.assertEqual(value[0],4);self.assertEqual(value[29],4)

    def test_record_addressing_is_exact_and_rejects_outside_domains(self):
        api=importlib.import_module('hazard_tables');domain=importlib.import_module('hazard_catalog')
        rom=bytearray(4096);rom[0xD0A:0xD12]=bytes([80,88,120,128,160,168,200,208]);rom[0xDC2:0xDD2]=bytes(range(16))
        plan=domain.capture_plan('ordinary',rom,players=[64]);data=bytearray(plan['cases_per_player']*58)
        offset=((1*len(plan['modes'])+3)*15+14)*58;data[offset]=5
        self.assertEqual(api.profile_record(plan,bytes(data),32,3,7),bytes([5])+bytes(57))
        for args in [(31,3,7),(32,999,7),(32,3,8)]:
            with self.assertRaises(ValueError):api.profile_record(plan,bytes(data),*args)
        with self.assertRaises(ValueError):api.profile_record(plan,bytes(data[:-1]),32,3,7)

    def test_rehashed_profile_or_fixture_cannot_replace_raw_source_proof(self):
        api=importlib.import_module('hazard_tables')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'references/roms').mkdir(parents=True);(root/'references/roms/frostbite.bin').write_bytes(bytes(4096))
            (root/'initial.state').write_bytes(b'capsule');(root/'stella').write_bytes(b'backend');(root/'frostbite-hazard-observer.json').write_text('{}')
            directory=root/'worker-000-001';batch=directory/'px-064-y-00-batch-00000';(batch/'raw').mkdir(parents=True)
            profile=directory/'player-064.truth';profile.write_bytes(bytes(58))
            (batch/'initial.state').write_bytes(b'capsule');(batch/'cases.bin').write_bytes(bytes(128))
            (batch/'results.bin').write_bytes(bytes(58)+b'\x07'+bytes(19));(batch/'raw/stella.log').write_text('FROSTBITE_HAZARDS_COMPLETE 1\n')
            helpers={key:'x'*64 for key in api.HELPERS};backend={'producer_commit':'build','producer_dirty':False,'helpers':{}}
            observed={'producer_commit':'capture','producer_dirty':True,'helpers':{key:helpers[key] for key in api.OBSERVER_HELPERS},
                      'cases':1,'mode':'top-object ROI','backend_build':backend,'backend_build_sha256':api.digest(root/'frostbite-hazard-observer.json'),
                      'backend':{'binary_sha256':api.digest(root/'stella')}}
            plan={'kind':'ordinary','player_x':[64],'ys':[0],'modes':[{}],'coordinates':[0],'cases_per_player':1,'expected_cases':1}
            manifest={**plan,'complete':True,'exploratory':True,'source':{'sha':'source'},'producer_commit':'capture','helpers':helpers,
                      'backend_build':backend,'binary_sha256':api.digest(root/'stella'),'backend_build_sha256':api.digest(root/'frostbite-hazard-observer.json'),
                      'initial_sha256':api.digest(root/'initial.state'),'preparation':{'capsule':'known'},'cases':1}
            part={'start':0,'stop':1,'cases':1}
            def reseal():
                observed['files']={name:api.digest(batch/name) for name in ('initial.state','cases.bin','results.bin','raw/stella.log')}
                (batch/'observation.json').write_text(json.dumps(observed))
                part['profiles']={profile.name:api.digest(profile)}
                part['receipts']=[{'path':str((batch/'observation.json').relative_to(root)),'sha256':api.digest(batch/'observation.json'),
                                   'player_x':64,'y_index':0,'offset':0,'cases':1}]
                (directory/'partition.json').write_text(json.dumps(part));manifest['partitions']=[part]
                (root/'catalog.json').write_text(json.dumps(manifest))
            with (patch.object(api,'ROOT',root),patch.object(api,'capture_plan',return_value=plan),
                  patch.object(api,'producer',return_value=helpers),patch.object(api,'verified_input',return_value={'sha':'source'}),
                  patch.object(api,'audit_manifest'),patch.object(api,'verified_backend',return_value=backend),
                  patch.object(api,'source_reset_checkpoint',create=True,return_value=(b'capsule',{'capsule':'known'})),
                  patch.object(api,'decode_state',return_value={'ram':bytes(128)}),patch.object(api,'make_case',return_value=bytes(128))):
                reseal();self.assertEqual(api.verified_profiles(root,exploratory=True)[2]['cases'],1)
                manifest['preparation']={'capsule':'different'};reseal()
                with self.assertRaisesRegex(ValueError,'preparation'):api.verified_profiles(root,exploratory=True)
                manifest['preparation']={'capsule':'known'}
                profile.write_bytes(b'\x01'+bytes(57));reseal()
                with self.assertRaisesRegex(ValueError,'profile differs'):api.verified_profiles(root,exploratory=True)
                profile.write_bytes(bytes(58));(batch/'cases.bin').write_bytes(b'\x01'+bytes(127));reseal()
                with self.assertRaisesRegex(ValueError,'declared component'):api.verified_profiles(root,exploratory=True)
