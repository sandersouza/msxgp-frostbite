import copy
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PublicationTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('reference_report'),'compact publication gate missing')
        return importlib.import_module('reference_report')

    def fixture(self):
        base={'schema_version':1,'source':{'sha256':'a'*64},'tool_source_commit':'b'*40,'utility_sha256':'c'*64}
        backend={'name':'Stella','version':'7.0','source_contract':'d55b1aec0d067a4c901a6dcdf81cb8f579685659','binary_sha256':'e'*64}
        stella={**base,'backend':backend,'warmup_full_states_equal':True,'warmup_intervals':32,
            'policy':{'host_seed':1,'riot_timer_preset':127},'config_sha256':'f'*64,
            'poweron_sha256':'1'*64,'aligned_sha256':'2'*64,
            'scenarios':[{'variation':m,'steps':121+33*m,'mode_after_reset':m,'player_after_reset':0,
                'full_states_equal':True,'trace_sha256':'3'*64,'raw_state_chain_sha256':'4'*64,
                'negative_controls_detected':['coordinate','flag','collision','order','input','seed']} for m in range(4)],
            'controlled_player1_turns':[{'variation':m,'steps':11,'full_states_equal':True,
                'port1_direction_and_fire_observed':True,'trace_sha256':'5'*64} for m in (1,3)]}
        cpu={**base,'stella':backend,'py65':'1.2.0','py65_cpu_source_sha256':'6'*64,'cases_sha256':'7'*64,
            'matched':374,'total':374,'mechanics_cases_checked':86,'arithmetic_boundary_vectors':288,
            'excluded_constant_mmio_cases':15}
        ale={**base,'backend':{'name':'ALE','version':'0.12.1','source_commit':'8a8fafb1ac37796e3e8197a2e5727204fa1b926d','binary_sha256':'9'*64,'numpy':'2.0.0'},
            'modes':[{'mode':m,'steps':27,'policy':{'seed':1,'frame_skip':1,'repeat_action_probability':0},
                'full_serialized_states_equal':True,'ram_screen_inputs_equal':True,
                'initial_sha256':'1'*64,'trace_sha256':'2'*64} for m in (0,2)]}
        provenance={'preparation_summary_sha256':'3'*64,'preparation_trace_sha256':'3'*64,
                    'source_sha256':'a'*64,'preparation_tool_commit':'b'*40}
        refuge={**base,'provenance':provenance,'policy':{'config_sha256':'4'*64},'steps':1056,'independent_runs':2,
            'full_states_equal':True,'observation':{'refuge_x':9,'bear_min':15,'bear_max':133,
                'bear_direction_reversals':0,'bear_blocked_at_edge':True,'reserve':3,'grounded_shore':True,'effective_bear_hits':0},
            'trace_sha256':'5'*64}
        console={**base,'provenance':provenance,'steps':125,'full_states_equal':True,
            'observed_wrap_modes':[3,0,1,2],'mode_after_select_hold35':0,'mode_after_reset_select':0,'trace_sha256':'6'*64}
        return {'stella':stella,'cpu':cpu,'ale':ale,'refuge':refuge,'console':console}

    def test_incomplete_or_failed_evidence_cannot_be_published(self):
        parts=self.fixture();self.api().validate_reports('a'*64,parts)
        for kind in parts:
            broken=copy.deepcopy(parts)
            if kind=='stella':broken[kind]['scenarios'][2]['full_states_equal']=False
            elif kind=='cpu':broken[kind]['matched']=373
            elif kind=='ale':broken[kind]['modes'][0]['policy']['repeat_action_probability']=0.25
            elif kind=='refuge':broken[kind]['observation']['effective_bear_hits']=1
            else:broken[kind]['observed_wrap_modes']=[3,0,1,1]
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.api().validate_reports('a'*64,broken)

    def test_public_payload_uses_an_allowlist_including_nested_metadata(self):
        parts=self.fixture()
        parts['stella']['backend']['raw_original']='PRIVATE'
        parts['stella']['scenarios'][0]['ram']=[0]*128
        parts['cpu']['results']=[{'raw':'PRIVATE'}]
        public=self.api().compact_reports('a'*64,parts)
        self.assertNotIn('PRIVATE',str(public))
        self.assertNotIn('ram',public['stella']['scenarios'][0])
        self.assertNotIn('results',public['cpu'])

    def test_matching_unsupported_backend_metadata_is_still_refused(self):
        parts=self.fixture();parts['stella']['backend']['version']='unsupported'
        parts['cpu']['stella']=copy.deepcopy(parts['stella']['backend'])
        with self.assertRaises(ValueError):self.api().validate_reports('a'*64,parts)

    def test_reported_utility_hash_must_exist_at_claimed_producer_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir();p=root/'scripts/fixture.py';p.write_bytes(b'fixture\n')
            def git(*args):return subprocess.check_output(['git','-C',tmp,*args],stderr=subprocess.DEVNULL,text=True).strip()
            git('init','-q');git('add','scripts/fixture.py')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
            report={'tool_source_commit':git('rev-parse','HEAD'),'utility_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                    'utility_fingerprints':{'scripts/fixture.py':hashlib.sha256(p.read_bytes()).hexdigest()}}
            self.api().audit_producer(report,'scripts/fixture.py',root,('scripts/fixture.py',))
            report['utility_sha256']='0'*64
            with self.assertRaises(ValueError):self.api().audit_producer(report,'scripts/fixture.py',root,('scripts/fixture.py',))

    def test_helper_hash_must_match_producer_and_manifest_must_be_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir()
            for name in ('fixture.py','helper.py'):(root/'scripts'/name).write_bytes(name.encode())
            def git(*args):return subprocess.check_output(['git','-C',tmp,*args],stderr=subprocess.DEVNULL,text=True).strip()
            git('init','-q');git('add','scripts');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
            required=('scripts/fixture.py','scripts/helper.py')
            report={'tool_source_commit':git('rev-parse','HEAD'),
                    'utility_sha256':hashlib.sha256((root/required[0]).read_bytes()).hexdigest(),
                    'utility_fingerprints':{path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in required}}
            self.api().audit_producer(report,required[0],root,required)
            report['utility_fingerprints']['scripts/helper.py']='0'*64
            with self.assertRaises(ValueError):self.api().audit_producer(report,required[0],root,required)
            del report['utility_fingerprints']['scripts/helper.py']
            with self.assertRaises(ValueError):self.api().audit_producer(report,required[0],root,required)

    def test_capture_rejects_helper_modified_before_start(self):
        api=importlib.import_module('reference_provenance')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir()
            for name in ('fixture.py','helper.py'):(root/'scripts'/name).write_bytes(name.encode())
            def git(*args):return subprocess.check_output(['git','-C',tmp,*args],stderr=subprocess.DEVNULL,text=True).strip()
            git('init','-q');git('add','scripts');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
            paths=('scripts/fixture.py','scripts/helper.py')
            api.snapshot_paths(paths,root)
            (root/paths[1]).write_bytes(b'changed before start')
            with self.assertRaises(ValueError):api.snapshot_paths(paths,root)
