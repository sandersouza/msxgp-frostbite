"""Actual-Z80 normalized visual-state/dirty-bit microproof; no frame verdict."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from presentation_build import FILES as BUILD_FILES
from presentation_dirty import scene,dirty_rows
from presentation_fragments import background_tables
from presentation_palette import audit_palette
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*BUILD_FILES,*SOURCE_FILES,'scripts/presentation_dirty.py','scripts/presentation_dirty_native_check.py')))
ROW_BYTES=67
INPUT_BYTES=133


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:
        raise ValueError('native whole normalized scene/dirty mask differs or is truncated')


def check(build_dir,out,explore=False,steady_budget=0):
    producer={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{name:digest(ROOT/name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    build_dir=Path(build_dir).resolve();meta=json.loads((build_dir/'build.json').read_text());artifact=build_dir/meta['rom']['filename']
    if not meta['profile'].get('sparse_profile') or digest(artifact)!=meta['rom']['sha256']:raise ValueError('exact sparse-profile ROM required')
    if any(digest(ROOT/name)!=value for name,value in meta['source_files'].items()):raise ValueError('dirty microproof build producer changed')
    domain=collect();config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette=audit_palette(ROOT/config['palette'])
    original=ROOT/'references/roms/frostbite.bin';original_sha=digest(original)
    if original_sha!=meta['profile']['source_sha256']:raise ValueError('dirty proof original ROM identity changed')
    rng=background_tables(original.read_bytes(),palette)['rng_index']
    inputs=bytearray();expected=bytearray();histories=[None,None]
    cases=[(case['ram'],0,0) for case in domain['cases']]
    cases += [(domain['cases'][0]['ram'],layout,width) for layout,width in ((0,0),(1,0),(0,1),(1,1))]
    # Pure key arithmetic boundaries, not additional original raster evidence.
    for nibble in range(16):
        for root in range(160):
            ram=bytearray(domain['cases'][0]['ram']);ram[0x1C]=nibble<<4;ram[0x1D]=((nibble+4)&15)<<4;ram[0x1F]=root
            cases.append((bytes(ram),0,0))
    for index,(ram,layout,width) in enumerate(cases):
        page=index&1;state=scene(ram,rng,layout=layout,width=width);dirty=dirty_rows(histories[page],state)
        inputs.extend(ram+bytes((state[1],int(ram[0x68]>=150),page,layout,width)))
        expected.extend(state+sum(1<<row for row in dirty).to_bytes(3,'little'));histories[page]=state
    count=len(cases);out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    syms=symbols(build_dir/'presentation.sym');entry=syms['p_dirty_describe'];emulator=Path(shutil.which('openmsx')).resolve()
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Dirty.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb]
set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_dirty {{message}} {{puts stderr "DIRTY_FAIL $message case=$::index";exit 1;return -code error $message}}
proc dispatch_dirty {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*{INPUT_BYTES}}}] [expr {{$::index*{INPUT_BYTES}+{INPUT_BYTES-1}}}]]
    set ::ram [string range $row 0 127]
    binary scan [string range $row 128 132] cu* params
    lassign $params profile coarse page layout width
    debug write_block memory 0xC000 $::ram
    debug write memory 0xC2E0 $profile;debug write memory 0xC223 $coarse;debug write memory 0xC200 $page
    debug write memory 0xC2DE $layout;debug write memory 0xC2DF $width
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_dirty target}}
    foreach {{address size}} {{0xC080 384 0xC300 256 0xC400 320 0xC600 352 0xC780 32 0xC800 7488 0xE580 3520}} {{
        debug write_block memory $address [string repeat [binary format c 165] $size]
    }}
    debug write_block memory 0xC540 [string repeat [binary format c 0] 64]
    debug write_block memory 0xC580 [string repeat [binary format c 165] 32]
    debug write_block memory 0xC5A0 [string repeat [binary format c 0] 64]
    debug write_block memory 0xC5E0 [string repeat [binary format c 165] 32]
    debug write_block memory 0xE540 [string repeat [binary format c 0] 64]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{62 2 50 0 112 205 {entry&255} {entry>>8} 195 107 199 24 254}}]
    debug set_bp 0xC768 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC080 384 0xC300 256 0xC400 320 0xC580 32 0xC5E0 32 0xC600 352 0xC780 32 0xC800 7488 0xE580 3520}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_dirty "guard $address"}}
        }}
        if {{[debug read_block memory 0xC000 128] ne $::ram || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_dirty source-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_dirty abi}}
        puts -nonewline $::actual "[debug read_block memory 0xE540 64][debug read_block memory 0xC2D8 3]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_dirty
    }}}}
    dispatch_dirty
}}}}]
after time 120 {{fail_dirty watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Dirty','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],
        cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or 'DIRTY_FAIL' in log:raise ValueError('actual dirty state capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected):raise ValueError('incomplete dirty-state actual matrix')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:
            (out/'failure.json').write_text(json.dumps({'index':index,'actual':list(actual[index*67:index*67+67]),'expected':list(expected[index*67:index*67+67])},indent=2)+'\n')
            raise ValueError(f'actual dirty scene/flags case{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete dirty-state timing')
    verify_files(domain['files'])
    if any(digest(ROOT/name)!=value for name,value in producer['utility_fingerprints'].items()) or digest(artifact)!=meta['rom']['sha256'] or digest(original)!=original_sha:
        raise ValueError('dirty-state producer/ROM changed during comparison')
    steady=max(row[1] for i,row in enumerate(times) if not any(expected[i*67+64:i*67+67]))
    result={'producer':producer,'cases':count,'original_observations':len(domain['cases']),'diagnostic_flag_cases':4,'arithmetic_boundary_cases':2560,
        'complete':True,'max_cycles_including_rpc':max(row[1] for row in times),'max_steady_cycles':steady,'declared_steady_microbudget':steady_budget or None,'rom_sha256':meta['rom']['sha256'],
        'actual_sha256':digest(out/'actual.bin'),'expected_sha256':digest(out/'expected.bin'),
        'source_receipt_sha256':domain['source_receipt_sha256'],'source_files':domain['files'],'frame_deadline_accepted':False,
        'scope':'Actual-Z80 scene/dirty-bit microproof with supplied calibrated BG profile/coarse parameters. No live dirty-renderer integration, frame, audio or human-ROM acceptance.'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    if steady_budget and steady>steady_budget:raise ValueError(f'unchanged visual state costs{steady}cycles above{steady_budget}microbudget; not a frame verdict')
    print(json.dumps({k:result[k] for k in ('cases','complete','max_cycles_including_rpc')}));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--explore',action='store_true');p.add_argument('--steady-budget',type=int,default=0)
    check(**vars(p.parse_args()))
