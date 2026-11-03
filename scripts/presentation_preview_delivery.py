"""Seal a limited visual/audio diagnostic, explicitly rejecting game acceptance.

This does not implement the final presentation-delivery gate. Failed frame
measurements are mandatory public limitations, never promoted to acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from presentation_build import FILES,VERSION,validate_rom
from presentation_check import decode_target
from presentation_cpu_check import verify_capture
from presentation_matrix_check import verify_timing,CAPTURE_BYTES
from presentation_pace_probe import verify_rows
from progression_play import input_records,assess_receipt
from reference_traces import private_output


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preview_scope():
    return {'purpose':'presentation-audio-diagnostic','runtime_qualified':False,'frame_deadline_accepted':False,
        'manual_emulator_accepted':False,'physical_hardware_accepted':False}


def validate_scope(value):
    if value.get('purpose')!='presentation-audio-diagnostic' or any(value.get(key)is not False for key in preview_scope() if key!='purpose'):
        raise ValueError('explicit limited diagnostic scope and unaccepted timing/human/hardware evidence required')


def check_log(log):
    if any(marker in log for marker in ('MATRIX_FAIL','GAME_AUDIO_FAIL','FLOE_NATIVE_FAIL','PACE_PROBE_FAIL','Error executing')):
        raise ValueError('positive preview evidence contains fatal emulator error')


def audit_timing(report,raw,family):
    measured=verify_rows(raw,report['frames'],family)
    if any(report.get(key)!=value for key,value in measured.items()):raise ValueError('reported preview timing differs from raw rows')
    return measured


def checked_file(path,value,manifest):
    path=Path(path).resolve()
    if not path.is_file() or sha(path)!=value:raise ValueError(f'changed/missing evidence {path}')
    manifest[str(path)]=value


def receipt(path,rom_sha,manifest):
    path=Path(path).resolve();report=json.loads(path.read_text());manifest[str(path)]=sha(path)
    if report.get('rom_sha256')!=rom_sha:raise ValueError('mixed preview ROM evidence')
    producers=report.get('producer_files',report.get('producer',{}).get('utility_fingerprints',{}))
    if not producers:raise ValueError('complete checker producer closure required')
    for name,value in producers.items():checked_file(ROOT/name,value,manifest)
    artifacts=report.get('artifacts',{})
    if 'emulator.log'not in artifacts:raise ValueError('raw emulator log required')
    for name,value in artifacts.items():
        if Path(name).name!=name:raise ValueError('child evidence artifact required')
        checked_file(path.parent/name,value,manifest)
    check_log((path.parent/'emulator.log').read_text())
    for field in ('input_files','source_files'):
        for name,value in report.get(field,{}).items():checked_file(ROOT/name,value,manifest)
    return report


def seal(config,out):
    config=Path(config).resolve();selection=json.loads(config.read_text());manifest={str(config):sha(config)}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean committed preview producer required')
    build_dir=(ROOT/selection['build']).resolve();meta_path=build_dir/'build.json';meta=json.loads(meta_path.read_text())
    checked_file(meta_path,sha(meta_path),manifest)
    if (meta['source_commit']!=commit or meta['source_dirty']is not False or meta['exploratory']is not False
        or meta.get('private_contact_reuse') or meta['version']!=VERSION or meta['profile'].get('ordered_psg')is not True
        or meta['runtime_qualified']is not False or set(meta['source_files'])!=set(FILES)):
        raise ValueError('clean canonical audio preview build at exact current source required')
    for name,value in meta['source_files'].items():checked_file(ROOT/name,value,manifest)
    rom=build_dir/meta['rom']['filename'];rom_sha=meta['rom']['sha256'];checked_file(rom,rom_sha,manifest)
    if validate_rom(rom.read_bytes()):raise ValueError('valid exact4MiB ASCII16 preview ROM required')
    matrix_path=ROOT/selection['matrix'];matrix=receipt(matrix_path,rom_sha,manifest)
    if (matrix.get('complete')is not True or matrix.get('exploratory')is not False or matrix.get('cases')!=2115
        or matrix.get('different_frames')!=0 or matrix.get('component')!='full-scene' or matrix.get('domain')!='all-source'
        or any(matrix.get(key)is not True for key in ('full_source_pixels_accepted','fixed_role_ownership_accepted','physical_name_pages_accepted','integrated_dirty_states_accepted','dirty_row_list_accepted'))):
        raise ValueError('complete canonical source/physical-ownership matrix required')
    captures=(matrix_path.parent/'captures.bin').read_bytes();expected=(matrix_path.parent/'expected.tms').read_bytes()
    if len(captures)!=(1+2*2115)*CAPTURE_BYTES or len(expected)!=2115*49152:raise ValueError('complete whole-image raw captures required')
    def pixels(index):
        raw=captures[index*CAPTURE_BYTES:(index+1)*CAPTURE_BYTES]
        return decode_target(raw[:16384],raw[16384:]),raw[16384:]
    previous,registers=pixels(0)
    for index in range(2115):
        prepared,prep_regs=pixels(index*2+1);presented,registers_after=pixels(index*2+2)
        if prepared!=previous or prep_regs!=registers or presented!=expected[index*49152:(index+1)*49152]:raise ValueError('raw source pixels or visible preparation differ')
        previous,registers=presented,registers_after
    if verify_timing((matrix_path.parent/'timing.tsv').read_text(),2115)!=matrix['max_prepare_cycles_including_rpc']:raise ValueError('raw graphics maximum differs')
    audio_path=ROOT/selection['audio'];audio=receipt(audio_path,rom_sha,manifest)
    if (audio.get('complete')is not True or audio.get('cases')!=2115 or audio.get('ordered_source_writes')!=3499
        or audio.get('physical_psg_writes')!=2472 or len(audio.get('excluded_graphics_only_fixtures',[]))!=1
        or audio['excluded_graphics_only_fixtures'][0].get('ordered_writes')!=0 or audio.get('frame_deadline_accepted')is not False):
        raise ValueError('whole original ordered audio integration and explicit zero-write exclusion required')
    actual_audio=(audio_path.parent/'actual.bin').read_bytes()
    event_lines=(audio_path.parent/'events.tsv').read_text().splitlines();write_lines=(audio_path.parent/'writes.tsv').read_text().splitlines()
    if (len(actual_audio)!=2115*133 or len(event_lines)!=3499 or len(write_lines)!=2472
        or any(len(row.split())!=5 for row in event_lines) or any(len(row.split())!=3 for row in write_lines)):
        raise ValueError('complete raw CPU/audio event/PSG evidence required')
    routes=json.loads((ROOT/'references/progression-config.json').read_text())['routes']
    if set(selection['native'])!=set(routes):raise ValueError('all twelve native original input-only routes required')
    native_cases=0;native_max=0
    for name,row in routes.items():
        path=ROOT/selection['native'][name];report=receipt(path,rom_sha,manifest)
        source=ROOT/row['source'];route=json.loads((source/'route.json').read_text());trace=json.loads((source/'trace.json').read_text())
        if report.get('original_route_sha256')!=sha(source/'route.json'):raise ValueError('native source route binding differs')
        for filename,value in route['files'].items():checked_file(source/filename,value,manifest)
        points=trace['steps'];want=[{'ram':p['ram'],'registers':{k:p['cpu'][k] for k in ('a','x','y','p','sp')}} for p in points]
        inputs=input_records(json.loads((source/'inputs.json').read_text()),points)
        if (report.get('complete')is not True or report['cases']!=len(want) or report['canonical_ram_injections']!=0
            or report['clock_hz']!=3579545 or report['ram_bytes']!=65536 or report['stack_min']<0xF340
            or (path.parent/'cases.bin').read_bytes()!=inputs):raise ValueError('complete guarded zero-injection native replay required')
        actual,cycles=verify_capture((path.parent/'actual.bin').read_bytes(),want,(path.parent/'emulator.log').read_text())
        if cycles[0]!=0 or any(value<=0 for value in cycles[1:]) or max(cycles)!=report['max_native_cycles']:raise ValueError('raw native timing differs')
        if assess_receipt(actual,route)!=route['assessment'] or report['assessment']!=route['assessment']:raise ValueError('native/original completion milestones differ')
        native_cases+=len(want);native_max=max(native_max,max(cycles))
    if native_cases!=24820:raise ValueError('whole retained native checkpoint domain required')
    if set(selection['pace'])!={'ntsc','pal'}:raise ValueError('both measured TV families required')
    timing={}
    for family,filename in selection['pace'].items():
        path=ROOT/filename;report=receipt(path,rom_sha,manifest)
        if (report.get('family')!=family or report.get('play')is not True or report.get('canonical_ram_injections')!=0 or report.get('frames',0)<120):
            raise ValueError('bounded real-input continuous preview probe required')
        timing[family]=audit_timing(report,(path.parent/'cycles.tsv').read_text(),family)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);scope=preview_scope();validate_scope(scope)
    public_build={'version':VERSION,**scope,'source_commit':commit,'source_dirty':False,'rom':meta['rom'],
        'source_rom_sha256':meta['original']['sha256'],'hardware':{key:meta['profile'][key] for key in ('clock_hz','ram_bytes','vram_bytes','mapper','rom_bytes')},
        'source_files':meta['source_files'],'bank_usage':meta['banks']}
    validation={'version':VERSION,**scope,'source_commit':commit,'rom_sha256':rom_sha,
        'automated':{'source_backed_images':2115,'native_input_only_checkpoints':native_cases,'maximum_native_step_cycles':native_max,
            'ordered_source_audio_writes':3499,'physical_psg_writes':2472,'controlled_audio_intervals':2115,
            'excluded_graphics_only_zero_audio_fixtures':audio['excluded_graphics_only_fixtures'],'timing':timing},
        'evidence_receipts':{name:sha(ROOT/selection[name]) for name in ('matrix','audio')},
        'limitations':['Real-time frame budgets fail; slowdown, skipped/duplicated presentations and visible commits are measured.',
            'Preview tests cover appearance, sound presence/mapping and input regressions; do not judge original rhythm, difficulty or collision timing.',
            'Controlled source pixels/audio and unpaced native routes do not establish combined natural-play acceptance.',
            'Manual emulator/listening and physical-hardware evidence remain pending; all views and final game qualification remain issue14 work.']}
    package=out/'public';package.mkdir();shutil.copyfile(rom,package/rom.name)
    for filename,value in (('build.json',public_build),('validation.json',validation)):(package/filename).write_text(json.dumps(value,indent=2)+'\n')
    (package/'SHA256SUMS').write_text(''.join(f'{sha(package/name)}  {name}\n' for name in (rom.name,'build.json','validation.json')))
    for filename,value in manifest.items():checked_file(filename,value,{})
    (out/'private-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    seal={'complete':True,**scope,'source_commit':commit,'rom_sha256':rom_sha,'public_assets':{p.name:{'size':p.stat().st_size,'sha256':sha(p)} for p in package.iterdir()},
        'private_manifest_sha256':sha(out/'private-manifest.json')}
    (out/'seal.json').write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps(seal,indent=2));return seal


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','out'):p.add_argument('--'+name,type=Path,required=True)
    seal(**vars(p.parse_args()))
