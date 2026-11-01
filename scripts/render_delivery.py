"""Audit compact renderer evidence and copy an immutable exact-byte release pack."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess
import tempfile

from render_build import ROOT,OUT,ROM,VERSION,validate_identity
from render_bench import validate_observations,validate_paced,validate_controls
from reference_provenance import audit_manifest,snapshot_paths

BUILD_FILES=('src/render_benchmark.asm','src/render.asm','scripts/render_build.py','scripts/render_model.py',
             'references/renderer-contract.json','references/tools-lock.json')
HARNESS_FILES=('scripts/render_bench.py','scripts/render_bench.tcl','scripts/render_controls.tcl',
               'scripts/render_model.py','scripts/render_build.py','scripts/smoke.py','scripts/rom.py',
               'scripts/environment.py','references/renderer-contract.json','references/tools-lock.json')
ROM_KEYS=('filename','size','used_bytes','padding_bytes','sha256','mapper')
FAULTS={'pixel','sprite','overflow','guard','spacing'}
REPORT=ROOT/'references/renderer-result.json'


def require(value,message):
    if not value:raise ValueError(message)


def digest(value,length=64):
    require(isinstance(value,str) and re.fullmatch(f'[0-9a-f]{{{length}}}',value),'invalid identity digest')


def validate_bundle(build,suite,rom=None):
    require(build['version']==VERSION and build['source_dirty'] is False,'clean identified renderer build required')
    digest(build['source_commit'],40)
    require(build['rom']['filename']==ROM.name and build['rom']['size']==32768
            and build['rom']['mapper']=='Normal/plain32KiB','unexpected renderer cartridge layout')
    require(type(build['rom']['used_bytes']) is int and 0<build['rom']['used_bytes']<=32768
            and build['rom']['padding_bytes']==32768-build['rom']['used_bytes'],'invalid used-ROM accounting')
    digest(build['rom']['sha256']);digest(build['assembler_sha256'])
    require(set(build['source_files'])==set(BUILD_FILES),'complete build dependencies required')
    for value in build['source_files'].values():digest(value)
    if rom is not None:validate_identity(rom,build)
    require(suite['schema_version']==1,'unsupported renderer suite')
    for name in ('rpc','ntsc','pal','controls'):
        part=suite[name]
        require(part['rom_sha256']==build['rom']['sha256'] and part['build_source_commit']==build['source_commit']
                and part['build_source_dirty'] is False and part['harness_source_dirty'] is False,'capture/build provenance differs or is dirty')
        digest(part['harness_source_commit'],40);digest(part['emulator_sha256']);digest(part['profile_sha256'])
        require(part['emulator']=='openMSX 21.0','reviewed openMSX21.0 evidence required')
        require(set(part['harness_hashes'])==set(HARNESS_FILES),'complete transitive capture helper manifest required')
        for path,value in part['harness_hashes'].items():
            digest(value)
            if path in build['source_files']:require(value==build['source_files'][path],'capture oracle/build dependency differs')
    validate_observations(suite['rpc'],643,build['rom']['sha256'])
    require(suite['rpc']['data_writes']==643*929,'incomplete RPC transfers')
    validate_paced(suite['ntsc'],59736);validate_paced(suite['pal'],71364);validate_controls(suite['controls'])
    require(set(suite['negative_controls'])==FAULTS and all(value is True for value in suite['negative_controls'].values()),'five actual fault detections required')


def selected(record,keys):return {key:record[key] for key in keys}


def compact_bundle(build,suite):
    validate_bundle(build,suite)
    timings={}
    for name in ('rpc','ntsc','pal'):
        part=suite[name];period=59736 if name!='pal' else 71364
        timings[name]={**selected(part,('cases','max_busy_cycles','min_spacing','max_sprites_per_line','data_writes')),
                       'frame_budget_cycles':period,'margin_cycles':period-part['max_busy_cycles']}
        if name!='rpc':
            timings[name].update({'max_commit_cycles':max(part['commit_cycles']),
                'period_min_cycles':min(part['period_cycles']),'period_max_cycles':max(part['period_cycles']),
                'source_reservations':part['step_counts'][-1],'consecutive_frames':True,'commit_inside_vblank':True})
    result={'schema_version':1,'version':VERSION,'scope':'Original-free synthetic renderer diagnostic; no native gameplay/original-graphics/hardware acceptance',
        'source_commit':build['source_commit'],'rom':selected(build['rom'],ROM_KEYS),
        'target':{'ram_kib':64,'vram_kib':16,'z80_hz':3579545,'extra_expansions':False},
        'allocation':{'vram_used_bytes':16000,'vram_free_bytes':384,'ram_state_extent_bytes':2816,
                      'guarded_stack_min':min(suite[name]['stack_min'] for name in ('rpc','ntsc','pal')),
                      'maximum_sprites_per_line':4,'surrogate_cycles_per_call':10018},
        'timings':timings,'controls':suite['controls']['control_checks'].copy(),
        'negative_controls':{name:True for name in sorted(FAULTS)},
        'provenance':{'build_source_files':{path:build['source_files'][path] for path in BUILD_FILES},
            'assembler_sha256':build['assembler_sha256'],
            'captures':{name:{'harness_source_commit':suite[name]['harness_source_commit'],
                'helper_sha256':{path:suite[name]['harness_hashes'][path] for path in HARNESS_FILES},
                'emulator_sha256':suite[name]['emulator_sha256'],'profile_sha256':suite[name]['profile_sha256']}
                for name in ('rpc','ntsc','pal','controls')}},
        'limits':['Synthetic masks/font, not original Frostbite assets or playable mechanics',
                  'Grid presentation rows; original coordinate/palette mapping remains issue9',
                  '10k-step surrogate is not measured native game/input/audio cost; integration must remeasure',
                  'Pixel oracle covers643 RPC scenes; paced frames check timing/slots/guards, not every paced pixel',
                  'VRAM reconstruction preview is not a framebuffer screenshot; RGB is approximate',
                  'Expanded cartridge slots, manual emulator review, audio and physical MSX acceptance remain pending']}
    if 'preview' in suite:
        digest(suite['preview']['sha256'])
        result['preview']={'sha256':suite['preview']['sha256'],
                           'method':'Actual emulated VRAM reconstruction; approximate RGB, not framebuffer capture'}
    return result


def audit_bundle(build,suite):
    audit_manifest({'tool_source_commit':build['source_commit'],'utility_fingerprints':build['source_files']},BUILD_FILES)
    for name in ('rpc','ntsc','pal','controls'):
        part=suite[name]
        audit_manifest({'tool_source_commit':part['harness_source_commit'],'utility_fingerprints':part['harness_hashes']},HARNESS_FILES)
        directory=(ROOT/part['directory']).resolve()
        require(directory.is_relative_to(OUT.resolve()),'private capture outside renderer outputs')
        require(json.loads((directory/'verified.json').read_text())==part,'suite differs from frozen verified capture')


def safe_build(build):
    return {'version':build['version'],'diagnostic':True,'source_commit':build['source_commit'],'source_dirty':False,
            'rom':selected(build['rom'],ROM_KEYS),'source_files':{path:build['source_files'][path] for path in BUILD_FILES},
            'assembler_sha256':build['assembler_sha256']}


def package_files(rom,build,report,notes,preview,destination):
    validate_identity(rom,build)
    require(build['source_dirty'] is False and report['source_commit']==build['source_commit']
            and report['rom']==selected(build['rom'],ROM_KEYS),'package differs from tested report/build')
    for value in (VERSION,build['source_commit'],build['rom']['sha256'],'Current state','Next','Human tests'):
        require(value in notes,'release notes lack exact identity or required human guidance')
    files={ROM.name:rom,'build.json':(json.dumps(safe_build(build),indent=2)+'\n').encode(),
           'renderer-result.json':(json.dumps(report,indent=2)+'\n').encode(),'release-notes.md':notes.encode()}
    if preview is not None:
        require(preview.startswith(b'\x89PNG\r\n\x1a\n') and hashlib.sha256(preview).hexdigest()==report['preview']['sha256'],'preview differs from verified reconstruction')
        files['preview-vram.png']=preview
    hashes={name:hashlib.sha256(value).hexdigest() for name,value in files.items()}
    files['SHA256SUMS']=''.join(f'{hashes[name]}  {name}\n' for name in sorted(hashes)).encode()
    destination=Path(destination)
    if destination.exists():
        require(not destination.is_symlink() and {path.name for path in destination.iterdir()}==set(files),'existing version directory differs')
        require(all(not (destination/name).is_symlink() and (destination/name).read_bytes()==value for name,value in files.items()),'never replace bytes in an existing version package')
    else:
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='renderer-package-',dir=destination.parent) as tmp:
            staged=Path(tmp)/'complete';staged.mkdir()
            for name,value in files.items():(staged/name).write_bytes(value)
            staged.rename(destination)
    return hashes


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('report','package'))
    parser.add_argument('--destination',type=Path,default=ROOT/f'outputs/releases/v{VERSION}')
    args=parser.parse_args()
    try:
        build_bytes=(OUT/'build.json').read_bytes();suite_bytes=(OUT/'suite.json').read_bytes()
        build=json.loads(build_bytes);suite=json.loads(suite_bytes);rom=ROM.read_bytes()
        validate_bundle(build,suite,rom);audit_bundle(build,suite)
        report=compact_bundle(build,suite)
        publication=snapshot_paths(('scripts/render_delivery.py','scripts/reference_provenance.py','scripts/reference_inventory.py',*HARNESS_FILES))
        report['publication']={**publication,'build_metadata_sha256':hashlib.sha256(build_bytes).hexdigest(),
                               'private_suite_sha256':hashlib.sha256(suite_bytes).hexdigest()}
        if args.command=='report':
            REPORT.write_text(json.dumps(report,indent=2)+'\n');print(f'Compact renderer report verified: {REPORT}')
        else:
            stored=json.loads(REPORT.read_text())
            # Publication metadata can have a later commit; measured identity stays frozen.
            require({k:v for k,v in stored.items() if k!='publication'}=={k:v for k,v in report.items() if k!='publication'},'tracked report differs from current tested evidence')
            for field in ('build_metadata_sha256','private_suite_sha256'):
                require(stored['publication'][field]==report['publication'][field],'tracked report receipt identity differs')
            notes=(ROOT/f'docs/releases/v{VERSION}.md').read_text()
            preview=(ROOT/suite['preview']['path']).read_bytes() if 'preview' in suite else None
            package_files(rom,build,stored,notes,preview,args.destination)
            print(f'Immutable exact-ROM renderer package: {args.destination}')
        return 0
    except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as error:
        print(f'Render delivery refused: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
