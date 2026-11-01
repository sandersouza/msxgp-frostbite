"""Seal issue12 raw source, native, paced and intentional-failure evidence.

Only exact ROM/build/compact validation/SHA files are public release assets.
Original captures, all derived truth and complete private states stay ignored.
"""
import argparse
import json
from pathlib import Path
import shutil
import struct
import xml.etree.ElementTree as ET

from environment import ROOT
from floe_delivery import audit_artifacts,cpu_rows,tree
from floe_bench import validate_receipt,decode_scene
from floe_model import visible_state
from floe_tables import verified_profiles as verified_floes
from hazard_build import FILES,expected_pixels
from hazard_catalog import HELPERS as CATALOG_HELPERS
from hazard_check import HELPERS as TARGET_HELPERS,geometry_cases
from hazard_mechanics import original_step,interaction_cases,boundary_cases,validate_effect
from hazard_query import RawContacts
from hazard_observer_check import CHECK_HELPERS,cases_for,invariant_cases
from hazard_domain import shapes
from hazard_paced import validate_report,verify_saved
from hazard_play import input_records
from hazard_routes import HELPERS as ROUTE_HELPERS,validate_policy,assess
from hazard_tables import verified_profiles
from hazard_truth import FULL_BYTES,full_record,contacts,compare_roi,validate_invariants
from native_contract import compare
from native_shift_check import HELPERS as SHIFT_HELPERS,audit_saved as audit_shift_rows
from reference_inventory import verified_input
from reference_provenance import audit_manifest,snapshot_paths
from reference_state import decode_state
from reference_traces import private_output
from render_bench import PACED_MODES,validate_source_files
from smoke import validate_machine_profile
from stella_floe import control_pairs
from stella_hazard import digest,HELPERS as OBSERVER_HELPERS,validate_observation
from trace_compare import compare_traces,validate_trace
import render_model as model

COMPONENT_CASES={'edge':25132800,'ordinary':4954950,'shore':8294400,'aliases':3203200}
OBSERVER_COUNTS={'cases':9476,'actual_views':228,'object_shapes':33,'invariant_links':768,
                 'roi_comparisons':2560,'shore_roi_comparisons':2880,'old_floe_compatibility_cases':64}
STRESS_NAMES={name for name,*_ in PACED_MODES}|{'ntsc_transitions_inverted','pal_transitions_inverted','counts','mixed_ntsc','mixed_pal'}
STRESS_MODES={name:(family,layout,width,transitions) for name,family,layout,width,transitions in PACED_MODES}
STRESS_MODES.update(ntsc_transitions_inverted=('ntsc',1,1,True),pal_transitions_inverted=('pal',1,1,True),
                    counts=('ntsc',0,0,False),mixed_ntsc=('ntsc',0,0,False),mixed_pal=('pal',0,0,False))
NEGATIVE_CAUSES={'collision':'RAM B7','rng':'RAM 82','row_priority':'CPU y','sticky':'RAM ED',
                 'spacing':'fast-io-spacing','sprite':'fifth-sprite-slot','guard':'heap-guard',
                 'state':'RAM AA','pixel':'pixel mismatch','contact':'RAM B6','cache':'pixel mismatch'}
ROUTE_STEPS={'bear-chase':702,'bear-refuge':1235,'fish-envelope':812,'threat-push':603}
PACED_MODES={f'{family}-layout{layout}-width{width}':(family,layout,width) for family in ('ntsc','pal') for layout in (0,1) for width in (0,1)}
DELIVERY_HELPERS=tuple(dict.fromkeys((*TARGET_HELPERS,*ROUTE_HELPERS,*CHECK_HELPERS,'scripts/hazard_delivery.py',
    'scripts/hazard_mechanics.py','scripts/hazard_paced.py','scripts/hazard_play.py','scripts/hazard_bench.py',
    'scripts/floe_delivery.py','scripts/floe_bench.py','scripts/render_model.py')))
DELIVERY_HELPERS=tuple(dict.fromkeys((*DELIVERY_HELPERS,*SHIFT_HELPERS)))


def validate_target(kind,r,sha,count):
    if (r.get('complete') is not True or r.get('exploratory') is not False or r.get('rom',{}).get('sha256')!=sha
            or r.get('clock_hz')!=3579545 or r.get('ram_bytes')!=65536 or r.get('stack_min',0)<0xF340):
        raise ValueError('clean complete current-ROM target evidence required')
    if kind in ('geometry','mechanics'):
        if r.get('cases')!=count or r.get('canonical_ram_injections')!=count:raise ValueError('complete declared fixture set required')
        if kind=='geometry' and (r.get('full_original_phase_cases')!=count or r.get('declared_neutral_hazard_cases')!=[] or r.get('actual_literal_views')!=228):
            raise ValueError('all geometry phases must use actual original contacts')
    elif kind=='paced':
        validate_report(r,count,r['family']);period={'ntsc':59736,'pal':71364}[r['family']]
        if (r.get('pixel_errors')!=0 or r.get('frame_budget')!=period or not 0<r.get('max_busy_cycles',0)<period
                or r.get('min_margin_cycles')!=period-r['max_busy_cycles']):raise ValueError('complete safe paced-frame receipt required')
    else:raise ValueError('known target acceptance class required')


def validate_source_summary(r):
    if (r.get('cases')!=50289350 or any(r.get('components',{}).get(k,{}).get('cases')!=n for k,n in COMPONENT_CASES.items())
            or r.get('aliases',{}).get('complete_geometry') is not True or r['aliases'].get('cases')!=3203200
            or r['aliases'].get('literal_views')!=228 or r['aliases'].get('channels')!=2
            or r.get('physical_leaf_queries')!={'floe':881120,'edge':10987680,'ordinary':956160,'shore':3951520}):
        raise ValueError('complete source domains, both channels and physical decode proof required')


def validate_observer_summary(r):
    if (r.get('complete') is not True or r.get('producer_dirty') is not False
            or any(type(r.get(k)) is not int or r[k]!=v for k,v in OBSERVER_COUNTS.items())
            or r.get('nusiz_values')!=[0,1,2,3] or len(r.get('independent_unmodified_phases',[]))!=32):
        raise ValueError('complete clean original-clock observer coverage required')


def validate_suite_manifest(reports,sha):
    if set(reports)!=STRESS_NAMES:raise ValueError('all fifteen crowded/cache/mixed/toggle modes required')
    for name,r in reports.items():
        mode=tuple(r.get(k) for k in ('family','layout','width','transitions'))
        if (r.get('rom_sha256')!=sha or r.get('harness_dirty') is not False or r.get('build_dirty') is not False
                or mode!=STRESS_MODES[name] or r.get('catalog')!=('counts' if name=='counts' else 'dense')
                or r.get('canonical_seed')!=('mixed-counts' if name.startswith('mixed') else 'three-copies')
                or name.startswith('mixed') and r.get('canonical_nusiz_codes')!=[0,1,2,3]):
            raise ValueError('clean current-ROM stress and all real copy codes required')


def validate_route_binding(kind,route):
    if kind not in ROUTE_STEPS or route.get('kind')!=kind or route.get('steps')!=ROUTE_STEPS[kind]:
        raise ValueError('named natural gate must use its own complete original interaction')


def audit_binary(directory,report,build):
    directory=Path(directory);sha=build['rom']['sha256']
    if (digest(directory/build['rom']['filename'])!=sha or json.loads((directory/'build.json').read_text())!=build
            or report.get('build_source_commit')!=build['source_commit']
            or report.get('rom',{}).get('sha256',report.get('rom_sha256'))!=sha
            or 'rom' in report and report['rom']!=build['rom']):
        raise ValueError('copied tested ROM/build/header identity differs from sealed candidate')


def audit_profile(directory,report,name,family=None):
    path=Path(directory)/'user-data/machines'/name;data=path.read_bytes()
    if digest(path)!=report['profile_sha256']:raise ValueError('actual machine profile differs from tested receipt')
    validate_machine_profile(data)
    if family and ET.fromstring(data).findtext('.//VDP/version')!=('TMS9918A' if family=='ntsc' else 'TMS9929A'):
        raise ValueError('actual VDP family differs from named clock gate')


def validate_negative_manifest(reports,sha):
    if set(reports)!=set(NEGATIVE_CAUSES):raise ValueError('all eleven intentional faults required')
    for name,r in reports.items():
        if (r.get('detected') is not True or r.get('rom_sha256')!=sha or r.get('harness_dirty') is not False
                or NEGATIVE_CAUSES[name] not in r.get('detail','')):raise ValueError('wrong or stale negative-control identity')


def validate_shift_unit(r):
    if (r.get('complete') is not True or r.get('exploratory') is not False or r.get('cases')!=65536
            or r.get('variants')!=64 or r.get('all_values')!=256 or r.get('observed_nz_masks')!=[0,1,2,3]
            or r.get('carry_inputs')!=[0,1] or r.get('overflow_inputs')!=[0,64] or r.get('canonical_ram_guard') is not True):
        raise ValueError('complete clean actual-Z80 compact shift proof required')


def audit_observer(path,source):
    path=Path(path);r=json.loads(path.read_text());validate_observer_summary(r)
    audit_manifest({'tool_source_commit':r['producer_commit'],'utility_fingerprints':r['helpers']},CHECK_HELPERS)
    if r['source']!=source:raise ValueError('observer original differs')
    root=path.parent;all_records=[];base=None
    def raw(directory,embedded,full=True):
        nonlocal base
        receipt=json.loads((directory/'observation.json').read_text())
        if receipt!=embedded or receipt['backend']['binary_sha256']!=r['binary_sha256']:raise ValueError('observer raw backend/receipt changed')
        audit_manifest({'tool_source_commit':receipt['producer_commit'],'utility_fingerprints':receipt['helpers']},OBSERVER_HELPERS)
        audit_artifacts(directory,receipt['files'])
        if digest(directory/'initial.state')!=r['initial_sha256']:raise ValueError('observer initial capsule changed')
        if base is None:base=decode_state((directory/'initial.state').read_bytes())
        data=(directory/'results.bin').read_bytes();validate_observation(data,(directory/'raw/stella.log').read_text(),receipt['cases'],not full)
        return data
    for entry in r['observations']:
        directory=root/f'full-{entry["start"]:05d}';data=raw(directory,entry['receipt'])
        if entry['start']!=len(all_records):raise ValueError('source observer chunk continuity changed')
        all_records.extend(full_record(data[i:i+FULL_BYTES]) for i in range(0,len(data),FULL_BYTES))
        if entry['stop']!=len(all_records):raise ValueError('source observer chunk count changed')
    rom=(ROOT/'references/roms/frostbite.bin').read_bytes();domain=shapes(rom);cases=cases_for(base['ram'],domain)
    if len(all_records)!=9476:raise ValueError('observer full phase stream incomplete')
    for entry in r['observations']:
        if (root/f'full-{entry["start"]:05d}'/'cases.bin').read_bytes()!=b''.join(cases[entry['start']:entry['stop']]):
            raise ValueError('observer actual fixtures differ from complete source domain')
    for ram,record in zip(cases,all_records):compare(visible_state(rom,ram,base['cpu'],contacts(record,ram)),record)
    for key,prefix,window in (('roi_observations','roi',7),('shore_roi_observations','shore',8)):
        total=0
        for entry in r[key]:
            full=raw(root/f'{prefix}-full-{entry["start"]:05d}',entry['full'])
            roi=raw(root/f'{prefix}-cached-{entry["start"]:05d}',entry['roi'],False);total+=compare_roi(full,roi,window)
        if total!=r['roi_comparisons' if window==7 else 'shore_roi_comparisons']:raise ValueError('ROI comparisons incomplete')
    data=raw(root/'invariants',r['invariant_observation']);records=[full_record(data[i:i+FULL_BYTES]) for i in range(0,len(data),FULL_BYTES)]
    expected_cases,links=invariant_cases(base['ram'],domain,control_pairs(rom))
    if (root/'invariants/cases.bin').read_bytes()!=b''.join(expected_cases) or validate_invariants(records,links)!=768:
        raise ValueError('source invariance fixtures/links changed')
    for entry in r['independent_unmodified_phases']:
        directory=root/f'original-{entry["case"]:04d}'/'settings/state'
        for suffix,field in ((1,'before_sha256'),(2,'after_sha256')):
            if digest(directory/f'Frostbite (1983) (Activision).st{suffix}')!=entry[field]:raise ValueError('unmodified source phase capsule changed')
        state=decode_state((directory/'Frostbite (1983) (Activision).st2').read_bytes())
        compare(all_records[entry['case']],{'ram':state['ram'],'registers':{k:state['cpu'][k] for k in ('a','x','y','p','sp')}})
    old=root/'old-floe';receipt=json.loads((old/'observation.json').read_text());audit_artifacts(old,receipt['files'])
    data=(old/'results.bin').read_bytes()
    if len(data)!=64*384:raise ValueError('old source protocol compatibility stream incomplete')
    for i,record in enumerate(all_records[:64]):
        reduced=b''.join(record['truth'][row] for row in (0,2,4,6))+record['ram']+bytes(record['registers'].values())+record['glyph']
        if reduced!=data[i*384:(i+1)*384]:raise ValueError('old source protocol compatibility changed')
    return r


def audit_geometry(path,report):
    root=path.parent;native=root/'native';records=(native/'cases.bin').read_bytes()
    expected=json.loads((native/'expected.json').read_text());index=0;base=None;actual_cases=[]
    for entry in report['source_observations']:
        directory=root/f'original-{entry["start"]:05d}';receipt=json.loads((directory/'observation.json').read_text())
        if receipt!=entry['receipt'] or entry['start']!=index:raise ValueError('geometry source observation order/receipt changed')
        audit_artifacts(directory,receipt['files']);audit_manifest({'tool_source_commit':receipt['producer_commit'],'utility_fingerprints':receipt['helpers']},OBSERVER_HELPERS)
        if base is None:base=decode_state((directory/'initial.state').read_bytes())
        data=(directory/'results.bin').read_bytes();fixtures=(directory/'cases.bin').read_bytes()
        validate_observation(data,(directory/'raw/stella.log').read_text(),entry['cases'],False)
        for offset in range(entry['cases']):
            source=full_record(data[offset*FULL_BYTES:(offset+1)*FULL_BYTES]);ram=fixtures[offset*128:(offset+1)*128]
            wanted=ram+bytes(base['cpu'][k] for k in ('a','x','y','p','sp'))
            if records[index*133:(index+1)*133]!=wanted:raise ValueError('native geometry fixture differs from actual original case')
            compare(source,expected[index]);actual_cases.append(ram);index+=1
    if index!=14828 or actual_cases!=geometry_cases(base['ram'],(ROOT/'references/roms/frostbite.bin').read_bytes()):
        raise ValueError('native geometry lacks the actual complete source case set')


def audit_mechanics(path,reader,initial):
    directory=path.parent;base=decode_state(Path(initial).read_bytes());rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    expected=json.loads((directory/'expected.json').read_text());records=(directory/'cases.bin').read_bytes()
    cases=interaction_cases(base,rom,reader);cases.extend(boundary_cases(base,rom,reader,cases[0][1]))
    if len(expected)!=652 or len(records)!=652*136:raise ValueError('complete controlled native fixture stream required')
    for index,(_,ram,effect,row) in enumerate(cases):
        record=ram+bytes(base['cpu'][k] for k in ('a','x','y','p','sp'))+bytes((255,63,0))
        if records[index*136:(index+1)*136]!=record:raise ValueError('controlled native initial/input fixture changed')
        source,contact=original_step(rom,ram,base['cpu'],reader);validate_effect(effect,ram,source['ram'],contact,row);compare(source,expected[index])
    reader.verify_consumed()


def audit_route(original,replayed):
    original=Path(original);replayed=Path(replayed);r=json.loads((original/'route.json').read_text());rr=json.loads((replayed/'replay.json').read_text())
    audit_manifest(r,ROUTE_HELPERS);audit_manifest(rr,ROUTE_HELPERS);audit_artifacts(original,r['files'])
    if (r.get('clean_start') is not True or rr.get('complete') is not True or rr.get('identical_full_cpu_ram_tia_riot_inputs') is not True
            or rr['route_sha256']!=digest(original/'route.json') or rr['replay_trace_sha256']!=digest(replayed/'trace.json')
            or r['steps']!=ROUTE_STEPS[r['kind']] or rr['steps']!=r['steps']):raise ValueError('complete independent original route/replay required')
    trace=json.loads((original/'trace.json').read_text());actual=json.loads((replayed/'trace.json').read_text())
    validate_trace(trace);validate_trace(actual);validate_policy(trace['policy'])
    if compare_traces(trace,actual) or (original/'final.state').read_bytes()!=(replayed/'final.state').read_bytes():raise ValueError('full original replay/final capsule differs')
    inputs=json.loads((original/'inputs.json').read_text());input_records(inputs,trace['steps'])
    if assess(trace['steps'],r['kind'],r['preparation_intervals'],r['assessment'].get('approach_end'))!=r['assessment']:raise ValueError('source route predicate changed')
    return r


def audit_negative(name,r,positive,sealed_build):
    sha=sealed_build['rom']['sha256']
    directory=ROOT/r['directory'];audit_manifest(r,tuple(r['utility_fingerprints']));audit_artifacts(directory,r['artifacts'])
    build=json.loads((directory/'build.json').read_text())
    if build['source_dirty'] or build['rom']['sha256']!=sha or digest(directory/build['rom']['filename'])!=sha:raise ValueError('negative ROM/build identity changed')
    if build!=sealed_build:raise ValueError('negative copied build differs from sealed candidate')
    launch=(directory/'launch.tcl').read_text()
    if f'set inject {{{name}}}' not in launch and f'set inject_fault {name}\n' not in launch:raise ValueError('intended runtime mutation missing')
    if name in ('spacing','sprite','guard'):
        if f'FLOE_FAIL {NEGATIVE_CAUSES[name]}' not in (directory/'emulator.log').read_text():raise ValueError('intended raw emulator failure absent')
    elif name in ('collision','rng','row_priority','sticky'):
        expected=json.loads((directory/'expected.json').read_text());actual=(directory/'actual.bin').read_bytes()
        receipt=json.loads((directory/'complete.json').read_text())
        if len(expected)!=652 or len(actual)!=652*137 or receipt['cases']!=652:raise ValueError('incomplete native mutation witness')
        row=actual[:137];got={'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])}
        try:compare(expected[0],got)
        except ValueError as error:
            if NEGATIVE_CAUSES[name] not in str(error):raise ValueError('wrong native mutation witness') from error
        else:raise ValueError('native mutation escaped comparison')
        if name=='row_priority' and (got['ram'][0x31]!=135 or got['ram'][0x37]!=7):raise ValueError('row-priority latch swap not observed')
    elif name in ('state','contact'):
        normal=(ROOT/positive['ntsc']['directory']/'states.bin').read_bytes()[:404];fault=(directory/'states.bin').read_bytes()[:404]
        offset=266 if name=='state' else 133;field=47 if name=='state' else 59
        if len(fault)!=404 or normal[:offset]!=fault[:offset] or [i for i,(a,b) in enumerate(zip(normal[offset:offset+133],fault[offset:offset+133])) if a!=b]!=[field]:
            raise ValueError('intended raw state/contact mutation absent')
    else:
        pixels=(directory/'presented.bin').read_bytes();regs=(directory/'presented_regs.bin').read_bytes();scenes=(directory/'scene_actual.bin').read_bytes()
        if not any(bytes(model.decode_pixels(pixels[i*16384:(i+1)*16384],list(regs[i*8:(i+1)*8])))!=bytes(expected_pixels(decode_scene(scenes[i*32:(i+1)*32]))) for i in range(len(pixels)//16384)):
            raise ValueError('intended raw pixel/cache mutation absent')


def seal(config_path,out):
    config=json.loads(Path(config_path).read_text());out=private_output(out)
    if out.exists():raise ValueError('fresh immutable delivery path required')
    build_dir=ROOT/config['build'];build=json.loads((build_dir/'build.json').read_text());rom=build_dir/build['rom']['filename'];sha=digest(rom)
    if build['source_dirty'] or sha!=build['rom']['sha256'] or build['original']!=verified_input(ROOT/'references/roms/frostbite.bin'):raise ValueError('clean exact ROM/source build required')
    validate_source_files(build);audit_manifest({'tool_source_commit':build['source_commit'],'utility_fingerprints':build['source_files']},FILES)
    validate_source_summary(build['tables']);roots={'build':build_dir};summaries={}
    shift_path=ROOT/config['shift_unit'];shift=json.loads(shift_path.read_text());validate_shift_unit(shift)
    audit_manifest(shift,SHIFT_HELPERS);audit_artifacts(shift_path.parent,shift['artifacts'])
    if digest(shift_path.parent/'unit.rom')!=shift['rom_sha256'] or audit_shift_rows(shift_path.parent)!=shift['max_cycles_including_rpc']:
        raise ValueError('actual compact shift unit ROM/rows changed')
    roots['shift-unit']=shift_path.parent;summaries['shift-unit']={k:shift[k] for k in ('cases','variants','max_cycles_including_rpc')}
    for kind in COMPONENT_CASES:
        root=ROOT/config['catalogs'][kind];manifest,_,audit=verified_profiles(root)
        if audit!=build['tables']['components'][kind]:raise ValueError('source component changed since tested build')
        roots['catalog-'+kind]=root
    floes=ROOT/config['floe_catalog'];floe_manifest,_=verified_floes(floes)
    if floe_manifest['cases']!=8704000 or digest(floes/'catalog.json')!=build['tables']['floe_catalog_sha256']:raise ValueError('complete raw floe source changed')
    roots['catalog-floe']=floes
    reader=RawContacts(floes,roots['catalog-edge'],roots['catalog-ordinary'],roots['catalog-shore'])
    for name,hash_ in build['tables']['files'].items():
        if digest(build_dir/'tables'/name)!=hash_:raise ValueError('compiled source table changed')
    observer_path=ROOT/config['observer'];observer=audit_observer(observer_path,build['original']);roots['observer']=observer_path.parent
    if observer['binary_sha256']!=manifest['binary_sha256']:raise ValueError('observer acceptance/backend differs from catalogs')
    for kind,count in (('geometry',14828),('mechanics',652)):
        path=ROOT/config[kind];r=json.loads(path.read_text());validate_target(kind,r,sha,count);audit_manifest(r,tuple(r['utility_fingerprints']))
        directory=path.parent/'native' if kind=='geometry' else path.parent;audit_artifacts(directory,r['artifacts']);cpu_rows(directory)
        audit_binary(directory,r,build);audit_profile(directory,r,'Frostbite_Floes.xml')
        if kind=='geometry':audit_geometry(path,r)
        else:audit_mechanics(path,reader,floes/'initial.state')
        roots[kind]=path.parent;summaries[kind]={'cases':count,'report_sha256':digest(path),'max_native_cycles':r['max_native_cycles']}
    if set(config['routes'])!=set(ROUTE_STEPS):raise ValueError('all four complete natural interactions required')
    for kind,entry in config['routes'].items():
        source=ROOT/entry['source'];replay=ROOT/entry['replay'];route=audit_route(source,replay);validate_route_binding(kind,route)
        roots['source-'+kind]=source;roots['replay-'+kind]=replay
        if set(entry['paced'])!=set(PACED_MODES):raise ValueError('all eight natural clock/presentation combinations required')
        for mode,relative in entry['paced'].items():
            family,layout,width=PACED_MODES[mode]
            path=ROOT/relative;r=json.loads(path.read_text());validate_target('paced',r,sha,route['steps']);audit_manifest(r,tuple(r['utility_fingerprints']))
            if (r['family'],r['layout'],r['width'])!=(family,layout,width) or r['original_route_sha256']!=digest(source/'route.json'):raise ValueError('paced route/family/view identity changed')
            audit_artifacts(path.parent,r['artifacts']);audit_binary(path.parent,r,build);audit_profile(path.parent,r,'Frostbite_Paced.xml',family)
            period,busy,cycles=verify_saved(path.parent,source,family,r)
            if (r['max_busy_cycles'],r['max_native_cycles'])!=(max(busy),max(cycles)):raise ValueError('paced raw timing differs from receipt')
            roots[f'paced-{kind}-{mode}']=path.parent;summaries[f'paced-{kind}-{mode}']={k:r[k] for k in ('source_steps','frames','max_busy_cycles','frame_budget','min_margin_cycles','assessment','layout','width')}
    suite=json.loads((ROOT/config['suite']).read_text());validate_suite_manifest(suite,sha)
    for name,r in suite.items():
        validate_receipt(r,r['frame_budget'],r['layout'],r['width'],r['transitions']);audit_manifest(r,tuple(r['utility_fingerprints']))
        directory=ROOT/r['directory'];audit_artifacts(directory,r['artifacts']);audit_binary(directory,r,build);audit_profile(directory,r,'Frostbite_Movement.xml',r['family'])
        roots['stress-'+name]=directory;summaries['stress-'+name]={k:r[k] for k in ('max_busy_cycles','frame_budget','canonical_nusiz_codes')}
    negatives=json.loads((ROOT/config['negatives']).read_text());validate_negative_manifest(negatives,sha)
    for name,r in negatives.items():audit_negative(name,r,suite,build);roots['negative-'+name]=ROOT/r['directory']
    # Published old bytes remain independently reproducible through the shared
    # unchanged translator; the new compact core has separate unit/phase proof.
    old=ROOT/config['previous_build'];previous=json.loads((old/'build.json').read_text());validate_source_files(previous)
    if digest(old/previous['rom']['filename'])!='c298a0311eb263b4e2fdc5ce490d29880ac27ebbc92f53e492f17b7f5747d600':
        raise ValueError('old published ROM identity changed')
    evidence={name:{'directory':str(directory.relative_to(ROOT)),'files':tree(directory)} for name,directory in roots.items()}
    out.mkdir(parents=True,exist_ok=False);(out/'private-evidence.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    result={'schema_version':1,'version':build['version'],'diagnostic':True,'rom':build['rom'],'source_commit':build['source_commit'],
            'source':build['original'],'source_cells':build['tables']['cases'],'physical_leaf_queries':build['tables']['physical_leaf_queries'],
            'observer_acceptance':{k:observer[k] for k in OBSERVER_COUNTS},'checks':summaries,'negative_controls':list(NEGATIVE_CAUSES),
            'private_evidence_manifest_sha256':digest(out/'private-evidence.json'),'manual_emulator':'Pending owner feedback',
            'physical_hardware':'Pending owner feedback','limitations':build['limitations'],
            'packager':snapshot_paths(DELIVERY_HELPERS)}
    shutil.copyfile(rom,out/rom.name);shutil.copyfile(build_dir/'build.json',out/'build.json')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');(out/'SHA256SUMS').write_text(f'{sha}  {rom.name}\n')
    if digest(out/rom.name)!=sha:raise ValueError('frozen release copy differs')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    r=seal(args.config,args.out);print(json.dumps({'version':r['version'],'rom':r['rom'],'negative_controls':r['negative_controls']}))
