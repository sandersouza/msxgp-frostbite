"""Seal clean, complete issue11 evidence and the exact tested human ROM.

Only ROM/build/compact validation/SHA files are release assets. Full original
captures and the transitive private evidence manifest remain ignored/local.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from environment import ROOT
from floe_bench import validate_receipt,decode_scene
from floe_build import FILES,expected_pixels
from floe_paced import FRAME_BYTES
from floe_tables import verified_profiles
from native_contract import compare
from reference_provenance import audit_manifest,snapshot_paths
from reference_traces import private_output
from render_bench import PACED_MODES,validate_source_files
from stella_floe import digest
import render_model as model

COUNTS={'geometry':1368,'mechanics':86,'natural':2254,'cpu-generic':4497,'cpu-fast':1793}


def validate_positive(kind,report,rom_sha):
    complete=report.get('receipt',{}).get('complete') if kind.startswith('cpu-') else report.get('complete')
    if (complete is not True or report.get('exploratory',False) is not False
            or report.get('build_dirty',False) or report.get('harness_dirty',False)):
        raise ValueError('clean completed canonical evidence required')
    if kind.startswith('cpu-'):
        if report.get('cases')!=COUNTS[kind] or (kind=='cpu-fast' and report.get('carry_fusion') is not True):raise ValueError('complete native CPU case set required')
        return
    if report.get('rom',{}).get('sha256')!=rom_sha:raise ValueError('evidence uses another ROM')
    if kind in COUNTS and report.get('cases')!=COUNTS[kind]:raise ValueError('complete exact native case count required')
    if kind.startswith('paced-'):
        frames=2253 if kind=='paced-ntsc' else 1886
        if (report.get('source_steps')!=2254 or report.get('frames')!=frames or report.get('pixel_errors')!=0 or
                report.get('canonical_ram_injections')!=0 or not 0<report.get('max_busy_cycles',0)<report.get('frame_budget',0)
                or report.get('min_margin_cycles')!=report['frame_budget']-report['max_busy_cycles']):
            raise ValueError('complete safe injection-free paced natural evidence required')
    elif report.get('canonical_ram_injections')!=(0 if kind=='natural' else COUNTS[kind]):raise ValueError('declared fixture/natural ownership mismatch')


def audit_artifacts(directory,hashes):
    directory=Path(directory)
    if not hashes:raise ValueError('nonempty raw artifact manifest required')
    for name,sha in hashes.items():
        path=directory/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()) or digest(path)!=sha:
            raise ValueError(f'changed/unsafe raw artifact: {name}')


def cpu_rows(directory,private=False):
    directory=Path(directory);expected=json.loads((directory/'expected.json').read_text());actual=(directory/'actual.bin').read_bytes();size=233 if private else 137
    if not expected or len(actual)!=len(expected)*size:raise ValueError('complete expected/actual CPU rows required')
    for index,want in enumerate(expected):
        row=actual[index*size:(index+1)*size];compare(want,{'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])})
        if private:
            shadow=bytearray(96)
            for write in want['hardware_writes']:
                address=int(write['address'],16);slot=64+(address&31) if address&512 else address&63;shadow[slot]=int(write['value'],16)
            if row[133:229]!=shadow:raise ValueError('private CPU hardware-write shadow differs')


def tree(directory):
    directory=Path(directory)
    paths=[path for path in directory.rglob('*') if path.is_file()]
    if not paths or any(path.is_symlink() for path in paths):raise ValueError('complete regular evidence tree required')
    return {str(path.relative_to(directory)):digest(path) for path in sorted(paths)}


def seal(config_path,out):
    config=json.loads(Path(config_path).read_text());out=private_output(out)
    if out.exists():raise ValueError('immutable package path already exists')
    build_dir=ROOT/config['build'];build=json.loads((build_dir/'build.json').read_text());rom=build_dir/build['rom']['filename'];sha=digest(rom)
    if build['source_dirty'] or sha!=build['rom']['sha256']:raise ValueError('clean exact ROM build required')
    validate_source_files(build);audit_manifest({'tool_source_commit':build['source_commit'],'utility_fingerprints':build['source_files']},FILES)
    catalog=ROOT/config['catalog'];manifest,profiles=verified_profiles(catalog);del profiles
    if digest(catalog/'catalog.json')!=build['tables']['catalog_sha256']:raise ValueError('build/catalog identity differs')
    roots={'electrical_catalog':catalog,'original_route':ROOT/config['source_route'],'original_replay':ROOT/config['source_replay'],
           'observer':(ROOT/config['observer']).parent,'build_tables':build_dir/'tables'}
    summaries={};reports={}
    required=set(COUNTS)|{'paced-ntsc','paced-pal'}
    if set(config['checks'])!=required:raise ValueError('complete positive gate set required')
    for kind,relative in config['checks'].items():
        path=ROOT/relative;report=json.loads(path.read_text());validate_positive(kind,report,sha)
        audit_manifest(report,tuple(report['utility_fingerprints']))
        directory=path.parent/'native' if kind=='geometry' else path.parent
        if 'artifacts' in report:audit_artifacts(directory,report['artifacts'])
        if kind in ('geometry','mechanics','natural') or kind.startswith('cpu-'):cpu_rows(directory,kind.startswith('cpu-'))
        if kind.startswith('paced-') and (directory/'frames.bin').stat().st_size!=report['frames']*FRAME_BYTES:raise ValueError('partial natural frame stream')
        roots[kind]=path.parent;reports[kind]=report
        summaries[kind]={'report_sha256':digest(path),**{key:report[key] for key in ('cases','source_steps','frames','max_cycles','max_native_cycles','max_busy_cycles','frame_budget','min_margin_cycles','pixel_errors','assessment') if key in report}}
    route=json.loads((roots['original_route']/'route.json').read_text());replay=json.loads((roots['original_replay']/'replay.json').read_text())
    if replay.get('identical_full_cpu_ram_tia_riot_inputs') is not True or replay['original_route_sha256']!=digest(roots['original_route']/'route.json'):raise ValueError('strict original full-state replay required')
    if any(digest(roots['original_route']/name)!=value for name,value in route['files'].items()):raise ValueError('original route changed')
    suite_path=ROOT/config['suite'];suite=json.loads(suite_path.read_text());expected={name for name,*_ in PACED_MODES}|{'counts','ntsc_transitions_inverted','pal_transitions_inverted','negative_controls'}
    if set(suite)!=expected:raise ValueError('all dense/counts/toggle scenarios required')
    for name,report in suite.items():
        if name=='negative_controls':continue
        if report['rom_sha256']!=sha or report['build_dirty'] or report['harness_dirty']:raise ValueError('dirty/mixed stress evidence')
        validate_receipt(report,report['frame_budget'],report['layout'],report['width'],report['transitions'])
        directory=ROOT/report['directory'];audit_artifacts(directory,report['artifacts']);audit_manifest(report,tuple(report['utility_fingerprints']))
        if digest(directory/'user-data/machines/Frostbite_Movement.xml')!=report['profile_sha256']:raise ValueError('stress machine profile changed')
        roots['stress-'+name]=directory;summaries['stress-'+name]={'frames':240,'max_busy_cycles':report['max_busy_cycles'],'frame_budget':report['frame_budget'],'margin':report['frame_budget']-report['max_busy_cycles']}
    negatives=suite['negative_controls'];causes={'spacing':'fast-io-spacing','sprite':'fifth-sprite-slot','guard':'heap-guard','state':'RAM AA','pixel':'pixel mismatch','contact':'RAM B6','cache':'pixel mismatch'}
    if set(negatives)!=set(causes):raise ValueError('all seven integrated fault identities required')
    for name,needle in causes.items():
        report=negatives[name];directory=ROOT/report['directory'];log=(directory/'emulator.log').read_text()
        if not report['detected'] or report['harness_dirty'] or report['rom_sha256']!=sha or needle not in report['detail']:raise ValueError('wrong integrated fault identity')
        if name in ('spacing','sprite','guard') and f'FLOE_FAIL {needle}' not in log:raise ValueError('intended emulator fault absent')
        if name in ('state','contact'):
            normal=(ROOT/suite['ntsc']['directory']/'states.bin').read_bytes()[:404]
            fault=(directory/'states.bin').read_bytes()[:404]
            if len(normal)!=404 or len(fault)!=404:raise ValueError('complete negative source-step row required')
            prefix=266 if name=='state' else 133;offset=266 if name=='state' else 133;field=47 if name=='state' else 59
            if normal[:prefix]!=fault[:prefix] or [i for i,(a,b) in enumerate(zip(normal[offset:offset+133],fault[offset:offset+133])) if a!=b]!=[field]:
                raise ValueError('negative raw source state differs beyond intended field')
        if name in ('pixel','cache'):
            pixels=(directory/'presented.bin').read_bytes();regs=(directory/'presented_regs.bin').read_bytes();scenes=(directory/'scene_actual.bin').read_bytes()
            if not any(bytes(model.decode_pixels(pixels[i*16384:(i+1)*16384],list(regs[i*8:(i+1)*8])))!=bytes(expected_pixels(decode_scene(scenes[i*32:(i+1)*32]))) for i in range(len(pixels)//16384)):
                raise ValueError('pixel/cache corruption absent from raw data')
        roots['negative-'+name]=directory
    port2=ROOT/config['port2_negative'];expected=json.loads((port2/'expected.json').read_text());actual=(port2/'actual.bin').read_bytes();found=None
    if len(actual)!=len(expected)*137:raise ValueError('complete port2 negative rows required')
    for i,want in enumerate(expected):
        row=actual[i*137:(i+1)*137]
        try:compare(want,{'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])})
        except ValueError as error:found=str(error);break
    if found is None or 'RAM AF' not in found:raise ValueError('intended port2 input corruption absent')
    roots['negative-port2-fire']=port2
    evidence={name:{'directory':str(directory.relative_to(ROOT)),'files':tree(directory)} for name,directory in roots.items()}
    out.mkdir(parents=True,exist_ok=False);(out/'private-evidence.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    result={'schema_version':1,'version':build['version'],'diagnostic':True,'rom':build['rom'],'source_commit':build['source_commit'],
        'source':build['original'],'table_producer_commit':manifest['producer_commit'],'catalog_sha256':digest(catalog/'catalog.json'),
        'original_route_sha256':digest(roots['original_route']/'route.json'),'original_replay_sha256':digest(roots['original_replay']/'replay.json'),
        'checks':summaries,'negative_controls':[*causes,'port2_fire'],'private_evidence_manifest_sha256':digest(out/'private-evidence.json'),
        'manual_emulator':'Pending owner feedback','physical_hardware':'Pending owner feedback',
        'limitations':build['limitations'],'packager':snapshot_paths(('scripts/floe_delivery.py',))}
    shutil.copyfile(rom,out/rom.name);shutil.copyfile(build_dir/'build.json',out/'build.json')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');(out/'SHA256SUMS').write_text(f'{sha}  {rom.name}\n')
    if digest(out/rom.name)!=sha:raise ValueError('frozen ROM copy differs')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();r=seal(args.config,args.out);print(json.dumps({'version':r['version'],'rom':r['rom'],'negative_controls':r['negative_controls']}))
