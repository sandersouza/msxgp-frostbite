import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeDeliveryTests(unittest.TestCase):
    def test_unverified_dirty_or_wrong_binary_cannot_be_packaged(self):
        api=importlib.import_module('floe_delivery');sha='a'*64
        good={'complete':True,'exploratory':False,'rom':{'sha256':sha},'cases':1368,'canonical_ram_injections':1368}
        api.validate_positive('geometry',good,sha)
        with self.assertRaises(ValueError):api.validate_positive('geometry',{key:value for key,value in good.items() if key!='complete'},sha)
        for change in ({'complete':False},{'exploratory':True},{'cases':1367},{'rom':{'sha256':'b'*64}}):
            with self.assertRaises(ValueError):api.validate_positive('geometry',{**good,**change},sha)
    def test_paced_gate_requires_real_cadence_pixels_and_no_injections(self):
        api=importlib.import_module('floe_delivery');sha='a'*64
        good={'complete':True,'exploratory':False,'rom':{'sha256':sha},'source_steps':2254,'frames':1886,'pixel_errors':0,
              'canonical_ram_injections':0,'max_busy_cycles':70000,'frame_budget':71364,'min_margin_cycles':1364}
        api.validate_positive('paced-pal',good,sha)
        for change in ({'frames':1885},{'canonical_ram_injections':1},{'pixel_errors':1},{'max_busy_cycles':71364},{'min_margin_cycles':0}):
            with self.assertRaises(ValueError):api.validate_positive('paced-pal',{**good,**change},sha)

    def test_observer_receipt_is_required_and_bound_to_catalog_and_raw_data(self):
        import copy
        import json
        import subprocess
        import tempfile
        api=importlib.import_module('floe_delivery')
        observer=importlib.import_module('floe_observer_check')
        stella=importlib.import_module('stella_floe')
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=api.ROOT,text=True).strip()
        helpers={name:api.digest(api.ROOT/name) for name in stella.HELPERS}
        checker={name:api.digest(api.ROOT/name) for name in observer.CHECK_HELPERS}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); initial=b'original-free synthetic capsule'
            catalog={'binary_sha256':'a'*64,'initial_sha256':api.hashlib.sha256(initial).hexdigest(),'helpers':helpers}
            report={'schema_version':1,'cases':4632,'actual_views':228,'invariant_links':3756,
                    'independent_unmodified_stella_phases':32,'cached_window_comparisons':768,
                    'checker_helpers':checker,'checker_sha256':checker[observer.CHECK_HELPERS[0]],
                    'binary_sha256':catalog['binary_sha256'],'source_commit':commit,'observations':[]}
            for name,count,roi in (('full',4632,False),('cache-full',768,False),('cache-roi',768,True)):
                directory=root/name;(directory/'raw').mkdir(parents=True)
                (directory/'initial.state').write_bytes(initial);(directory/'cases.bin').write_bytes(bytes(128*count))
                row=(bytes(58)+b'\x07'+bytes(19)) if roi else bytes(384)
                (directory/'results.bin').write_bytes(row*count)
                (directory/'raw/stella.log').write_text(f'FROSTBITE_PROBE_COMPLETE {count}\n')
                receipt={'schema_version':1,'mode':'top-floe ROI' if roi else 'complete visible phase','cases':count,
                         'backend':{'name':'Stella','version':'7.0','source_contract':stella.REVISION,'binary_sha256':catalog['binary_sha256']},
                         'upstream_revision':stella.REVISION,'helpers':helpers,
                         'files':{key:api.digest(directory/key) for key in ('initial.state','cases.bin','results.bin','raw/stella.log')}}
                (directory/'observation.json').write_text(json.dumps(receipt));report['observations'].append(receipt)
            path=root/'check.json';path.write_text(json.dumps(report))
            api.validate_observer(path,catalog)
            with self.assertRaises(FileNotFoundError):api.validate_observer(root/'missing-check.json',catalog)
            for change in ({'cases':4631},{'actual_views':227},{'invariant_links':3755},
                           {'independent_unmodified_stella_phases':31},{'cached_window_comparisons':767},
                           {'binary_sha256':'b'*64},{'checker_helpers':{}},{'checker_sha256':'0'*64}):
                with self.subTest(change=change):
                    path.write_text(json.dumps({**report,**change}))
                    with self.assertRaises(ValueError):api.validate_observer(path,catalog)
            stale=copy.deepcopy(report);stale['observations'][0]['backend']['binary_sha256']='b'*64
            path.write_text(json.dumps(stale))
            with self.assertRaises(ValueError):api.validate_observer(path,catalog)
            path.write_text(json.dumps(report));(root/'full/results.bin').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):api.validate_observer(path,catalog)

    def test_original_replay_rejects_changed_trace_and_final_state(self):
        import json
        import tempfile
        api=importlib.import_module('floe_delivery')
        routes=importlib.import_module('floe_routes')
        producer=api.snapshot_paths(routes.HELPERS)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);original=root/'original';replayed=root/'replayed';original.mkdir();replayed.mkdir()
            files={'trace.json':b'{"checkpoints": []}','inputs.json':b'[]','initial.state':b'synthetic initial','final.state':b'synthetic final'}
            for name,data in files.items():(original/name).write_bytes(data)
            for name in ('trace.json','final.state'):(replayed/name).write_bytes(files[name])
            route={**producer,'files':{name:api.digest(original/name) for name in files}}
            (original/'route.json').write_text(json.dumps(route))
            replay={**producer,'identical_full_cpu_ram_tia_riot_inputs':True,
                    'original_route_sha256':api.digest(original/'route.json'),'replay_trace_sha256':api.digest(replayed/'trace.json')}
            (replayed/'replay.json').write_text(json.dumps(replay))
            api.validate_original_replay(original,replayed)
            (replayed/'trace.json').write_bytes(files['trace.json']+b' ')
            with self.assertRaises(ValueError):api.validate_original_replay(original,replayed)
            replay['replay_trace_sha256']=api.digest(replayed/'trace.json');(replayed/'replay.json').write_text(json.dumps(replay))
            with self.assertRaises(ValueError):api.validate_original_replay(original,replayed)
            (replayed/'trace.json').write_bytes(files['trace.json']);replay['replay_trace_sha256']=api.digest(replayed/'trace.json')
            (replayed/'replay.json').write_text(json.dumps(replay));(replayed/'final.state').write_bytes(b'changed final')
            with self.assertRaises(ValueError):api.validate_original_replay(original,replayed)
