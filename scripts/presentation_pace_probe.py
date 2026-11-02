"""Continuous native-frame profiler, deliberately separate from acceptance.

Real keyboard inputs and the actual scheduler run without state injections.
Missed deadlines are retained as research results rather than suppressed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT
from graphics_mapping import map_frame
from presentation_build import FILES,validate_rom
from presentation_check import decode_target
from presentation_model import describe,pixels
from presentation_palette import audit_palette
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*FILES,'scripts/presentation_check.py','scripts/presentation_pace_probe.py')))
CAPTURE_BYTES=128+3*16392


def sha(data):return hashlib.sha256(data).hexdigest()


def verify_rows(text,count,family):
    period={'ntsc':59736,'pal':71364}[family]
    rows=[list(map(int,line.split())) for line in text.splitlines()]
    if len(rows)!=count or count<2:raise ValueError('complete multi-frame timing probe required')
    for index,row in enumerate(rows):
        if (len(row)!=10 or row[0]!=index or any(v<=0 for v in row[2:6]) or row[7]not in (1,2)
            or abs(sum(row[2:5])-row[5])>2 or (index and (row[1]<rows[index-1][1] or row[6]<=0))):
            raise ValueError('unordered/nonpositive/inconsistent continuous timing rows')
    skipped=sum(max(0,b[1]-a[1]-1) for a,b in zip(rows,rows[1:]))
    duplicate=sum(b[1]==a[1] for a,b in zip(rows,rows[1:]))
    overruns=sum(row[5]>=period for row in rows)
    bad_periods=sum(abs(row[6]-period)>40 for row in rows[1:])
    visible=sum(any(0<=y<192 for y in row[8:10]) for row in rows)
    return {'frames':count,'max_busy_cycles':max(row[5] for row in rows),'frame_budget':period,
        'over_budget_frames':overruns,'skipped_vdp_frames':skipped,'incorrect_periods':bad_periods,
        'visible_commits':visible,'duplicate_vdp_frames':duplicate,'deadline_met':not(overruns or skipped or duplicate or bad_periods or visible),'frame_deadline_accepted':False,
        'max_source_and_scheduler_cycles':max(row[2] for row in rows),'max_prepare_cycles':max(row[3] for row in rows)}


def probe(build_dir,out,*,family='ntsc',frames=120,play=False,last_world_budget=0):
    if family not in ('ntsc','pal') or type(frames)is not int or not 2<=frames<=600 or type(play)is not bool:
        raise ValueError('bounded continuous profile and explicit clock/input mode required')
    if type(last_world_budget)is not int or last_world_budget<0:raise ValueError('nonnegative last-world microbudget required')
    producer={name:sha((ROOT/name).read_bytes()) for name in HELPERS}
    build_dir=Path(build_dir).resolve();meta=json.loads((build_dir/'build.json').read_text())
    artifact=build_dir/meta['rom']['filename'];rom=artifact.read_bytes()
    if validate_rom(rom) or sha(rom)!=meta['rom']['sha256']:raise ValueError('continuous profile ROM identity mismatch')
    if any(sha((ROOT/name).read_bytes())!=value for name,value in meta['source_files'].items()):raise ValueError('continuous profile build producers changed')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    syms=symbols(build_dir/'presentation.sym');emulator=Path(shutil.which('openmsx')).resolve()
    stages=(('p_dirty_describe','description'),('p_fast_release_dirty','dirty-state'),('presentation_background_prepare','release'),
        ('presentation_world_prepare','background'),('presentation_hud_prepare','world'),('presentation_footer_prepare','header'),
        ('presentation_sprites_prepare','footer'),('p_fast_upload_dirty','sprites'))
    phase_setup='\n'.join(f'debug set_bp {syms[name]} {{}} {{mark_probe_phase {label}}}' for name,label in stages)
    counters=(('p_fast_resolve','resolve'),('presentation_typed_construct','construct'),('p_fast_ref_add','refadd'),
        ('p_fast_ref_drop','refdrop'),('p_fast_cell','cell'),('presentation_geometry_lookup','geometry'),
        ('presentation_geometry_pattern','pattern'),('p_fast_world_tile','worldtile'),('p_world_primitive','primitive'))
    counter_setup='\n'.join(f'debug set_bp {syms[name]} {{}} {{if {{$::inprepare}} {{incr ::calls({label})}}}}' for name,label in counters)
    counter_zero=';'.join(f'set ::calls({label}) 0' for _,label in counters)
    counter_row=' '.join(f'$::calls({label})' for _,label in counters)
    effective=ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    effective.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    profile=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(effective)
    validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_PaceProbe.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set steps 0
set tracking 0
set inprepare 0
set timing [open {{{out/'cycles.tsv'}}} w]
set phases [open {{{out/'phases.tsv'}}} w]
set counts [open {{{out/'counts.tsv'}}} w]
set captures [open {{{out/'captures.bin'}}} wb]
proc fail_probe {{message}} {{puts stderr "PACE_PROBE_FAIL $message frame=$::index";exit 1;return -code error $message}}
proc snapshot_probe {{}} {{return "[debug read_block VRAM 0 16384][debug read_block {{VDP regs}} 0 8]"}}
proc mark_probe_phase {{label}} {{
    if {{!$::inprepare}} {{return}}
    set now [machine_info time]
    puts $::phases "$::index $label [expr {{round(($now-$::previous_phase)*3579545)}}]"
    set ::previous_phase $now
}}
{phase_setup}
{counter_setup}
debug set_bp {syms['native_reset_done']} {{}} {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_probe target}}
    set ::slot [debug read ioports 168]
    debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]
    set VDP.too_fast_vram_access_callback {{fail_probe fast-vram}}
}}
debug set_bp {syms['native_step']} {{}} {{if {{$::tracking}} {{incr ::steps}}}}
debug set_bp {syms['paced_frame_start']} {{}} {{
    set now [machine_info time]
    if {{[info exists ::commit_started]}} {{
        set commit [expr {{round(($now-$::commit_started)*3579545)}}]
        set end_y [machine_info VDP_msx_y_pos]
        puts $::timing "$::index $::vdp_frame $::source_cycles $::prepare_cycles $commit [expr {{$::source_cycles+$::prepare_cycles+$commit}}] $::spacing $::steps $::commit_y $end_y"
        puts $::counts "$::index {counter_row}"
        puts -nonewline $::captures "$::ram$::before$::prepared[snapshot_probe]"
        incr ::index
        if {{$::index=={frames}}} {{close $::timing;close $::captures;close $::phases;close $::counts;exit;return}}
    }}
    if {{[debug read ioports 168]!=$::slot || ([reg IFF]&3)!=0 || [reg SP]!=0xF380}} {{fail_probe abi}}
    set ::tracking 1;set ::started $now;set ::steps 0
    if {{{int(play)} && $::index==4}} {{keymatrixdown 6 32}}
    if {{{int(play)} && $::index==6}} {{keymatrixup 6 32}}
    if {{{int(play)} && $::index==8}} {{keymatrixdown 8 64}}
    if {{{int(play)} && $::index==20}} {{keymatrixup 8 64}}
    if {{{int(play)} && $::index==24}} {{keymatrixdown 8 16}}
    if {{{int(play)} && $::index==48}} {{keymatrixup 8 16}}
    if {{{int(play)} && $::index==56}} {{keymatrixdown 8 128}}
    if {{{int(play)} && $::index==80}} {{keymatrixup 8 128}}
    if {{{int(play)} && $::index==88}} {{keymatrixdown 8 1}}
    if {{{int(play)} && $::index==90}} {{keymatrixup 8 1}}
}}
debug set_bp {syms['prepare']} {{}} {{
    if {{!$::tracking}} {{return}}
    set now [machine_info time];set ::source_cycles [expr {{round(($now-$::started)*3579545)}}]
    set ::prepare_started $now
    set ::inprepare 1;set ::previous_phase $now
    {counter_zero}
    set ::ram [debug read_block memory 0xC000 128];set ::abi [debug read_block memory 0xC600 256]
    set ::before [snapshot_probe]
}}
debug set_bp {syms['paced_wait']} {{}} {{
    mark_probe_phase prepared;set ::inprepare 0
    set ::prepare_cycles [expr {{round(([machine_info time]-$::prepare_started)*3579545)}}]
    if {{[debug read_block memory 0xC000 128] ne $::ram || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_probe renderer-mutated-source}}
    if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]}} {{fail_probe heap-redzone}}
    if {{[debug read memory 0xC231]!=0}} {{fail_probe compositor}}
    set ::prepared [snapshot_probe]
}}
debug set_bp {syms['paced_commit']} {{}} {{
    set now [machine_info time]
    set ::spacing [expr {{[info exists ::commit_started] ? round(($now-$::commit_started)*3579545) : 0}}]
    set ::commit_started $now;set ::vdp_frame [machine_info VDP_frame_count]
    set ::commit_y [machine_info VDP_msx_y_pos]
}}
after time {60+frames} {{fail_probe watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_PaceProbe','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'PACE_PROBE_FAIL' in log:raise ValueError('continuous profile failed: '+log[-1500:])
    report=verify_rows((out/'cycles.tsv').read_text(),frames,family);captured=(out/'captures.bin').read_bytes()
    timings=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    counts=[list(map(int,line.split())) for line in (out/'counts.tsv').read_text().splitlines()]
    if len(counts)!=frames or any(len(row)!=len(counters)+1 or row[0]!=i or any(v<0 for v in row[1:]) for i,row in enumerate(counts)):
        raise ValueError('incomplete/unordered continuous operation counts')
    phases=[line.split() for line in (out/'phases.tsv').read_text().splitlines()];labels=[label for _,label in stages]+['prepared']
    if len(phases)!=frames*len(labels):raise ValueError('incomplete continuous phase profiles')
    for index in range(frames):
        rows=phases[index*len(labels):(index+1)*len(labels)]
        if any(len(row)!=3 or row[0]!=str(index) or row[1]!=label or int(row[2])<=0 for row,label in zip(rows,labels)) or abs(sum(int(row[2]) for row in rows)-timings[index][3])>len(labels):
            raise ValueError('unordered continuous phases or sum differs from actual preparation')
    if len(captured)!=frames*CAPTURE_BYTES:raise ValueError('incomplete continuous frame captures')
    config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette=audit_palette(ROOT/config['palette'])
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if sha(original)!=meta['profile']['source_sha256']:raise ValueError('continuous profile original authority changed')
    for index in range(frames):
        row=captured[index*CAPTURE_BYTES:(index+1)*CAPTURE_BYTES];ram=row[:128]
        images=[];registers=[]
        for offset in (128,16520,32912):
            images.append(decode_target(row[offset:offset+16384],row[offset+16384:offset+16392]));registers.append(row[offset+16384:offset+16392])
        if images[0]!=images[1] or registers[0]!=registers[1]:raise ValueError(f'continuous preparation changed visible image at{index}')
        expected=map_frame(pixels(original,describe(original,{'ram':list(ram)})),palette)
        if images[2]!=expected:raise ValueError(f'continuous native pixels differ from proven source model at{index}')
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producer.items()) or artifact.read_bytes()!=rom or (ROOT/'references/roms/frostbite.bin').read_bytes()!=original:
        raise ValueError('continuous profile producers/ROM changed')
    report.update(rom_sha256=meta['rom']['sha256'],producer_files=producer,emulator_sha256=sha(emulator.read_bytes()),profile_sha256=sha(profile),
        family=family,play=play,canonical_ram_injections=0,source_equivalence_accepted=False,audio_accepted=False,
        scope='Private continuous clock/pixel-model profile with real scheduler and keyboard. Retains all missed deadlines; independent original-state/audio/full-route/human acceptance remains separate.',
        artifacts={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    report['last_world_cycles']=next(int(row[2]) for row in phases[-len(labels):] if row[1]=='world')
    report['last_world_microbudget']=last_world_budget or None
    report['operation_count_columns']=['index']+[label for _,label in counters];report['operation_counts']=counts
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    if last_world_budget and report['last_world_cycles']>last_world_budget:raise ValueError(f'last world component costs{report["last_world_cycles"]}>{last_world_budget}; no complete-frame acceptance implied')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--family',choices=('ntsc','pal'),default='ntsc');p.add_argument('--frames',type=int,default=120);p.add_argument('--play',action='store_true')
    p.add_argument('--last-world-budget',type=int,default=0)
    report=probe(**vars(p.parse_args()));print(json.dumps({k:report[k] for k in ('frames','max_busy_cycles','frame_budget','over_budget_frames','skipped_vdp_frames','max_source_and_scheduler_cycles','max_prepare_cycles')}))
