"""Interrupt-driven input-only source and coherent-picture diagnostic.

The source clock and committed-picture clock are deliberately separate metrics.
Original-derived traces and captures remain under ignored outputs/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT
from graphics_mapping import map_frame
from native_contract import compare
from presentation_check import decode_target
from presentation_direct_enemy import resident_geometry,decorate_actor_owners
from presentation_fixed_clock import ram_code
from presentation_fixed_ownership import audit_active,audit_row
from presentation_model import describe,pixels
from presentation_palette import audit_palette
from presentation_prepared_ownership import decorate_owners
from presentation_shared_ownership import constructor
from progression_play import input_records
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

CAPTURE_BYTES=128+3*16392
OWNER_BYTES=4214


def sha(data):return hashlib.sha256(data).hexdigest()


def active(ram):return all(ram[k]==0 for k in (0x46,0x67,0x71))


def clocks(irq,timings,points):
    """Use IRQ ENTRY times/frame counters, before variable PAL1/2-step work."""
    if not irq or any(len(r)!=7 or int(r[0])!=i+1 or int(r[4])not in (1,2) or int(r[6]) for i,r in enumerate(irq)):
        raise ValueError('missed/partial VBlank records')
    if any(int(b[1])-int(a[1])!=1 for a,b in zip(irq,irq[1:])):raise ValueError('missed hardware VBlank')
    if not timings or any(int(b[4])-int(a[4])<2 for a,b in zip(timings,timings[1:])):raise ValueError('picture cap differs')
    elapsed=float(irq[-1][2])-float(irq[0][2])
    if elapsed<=0:raise ValueError('positive measured source interval required')
    active_intervals=[]
    for a,b in zip(timings,timings[1:]):
        first,last=int(a[1]),int(b[1])
        if not first<last<len(points):raise ValueError('unordered picture source indices')
        # An interval crossing death/attract is not active gameplay, even if
        # its endpoints happen to be active again.
        if all(active(p['ram']) for p in points[first:last+1]):
            active_intervals.append(float(b[3])-float(a[3]))
    pictures_elapsed=float(timings[-1][3])-float(timings[0][3]) if len(timings)>1 else 0
    return dict(source_steps_per_second=sum(int(r[4]) for r in irq[1:])/elapsed,
        committed_pictures_per_second=(len(timings)-1)/pictures_elapsed if pictures_elapsed else None,
        active_picture_intervals=len(active_intervals),
        active_pictures_per_second=len(active_intervals)/sum(active_intervals) if active_intervals else None)


def probe(build,out,family,steps=2252,expanded=False):
    if family not in ('ntsc','pal') or type(steps)is not int or not 2<=steps<=2252:
        raise ValueError('bounded original route and explicit TV family required')
    producer=Path(__file__).read_bytes()
    meta=json.loads((build/'build.json').read_text());artifact=build/meta['rom']['filename'];rom=artifact.read_bytes()
    if sha(rom)!=meta['rom']['sha256']:raise ValueError('ROM identity differs')
    code=ram_code(meta,rom);s=symbols(build/'presentation.sym')
    for name,value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('build producer differs: '+name)
    source=ROOT/'outputs/progression/route-progression-v0-a'
    receipt=json.loads((source/'route.json').read_text())
    for name,value in receipt['files'].items():
        if sha((source/name).read_bytes())!=value:raise ValueError('original route differs: '+name)
    trace=json.loads((source/'trace.json').read_text())
    inputs=input_records(json.loads((source/'inputs.json').read_text()),trace['steps'])
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'producer.py').write_bytes(producer)
    (out/'route-inputs.bin').write_bytes(inputs)
    emulator=Path(shutil.which('openmsx')).resolve()
    profile=ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    profile.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    if expanded:
        primary=profile.find('.//primary[@slot="3"]')
        ram=primary.find('RAM');primary.remove(ram)
        ET.SubElement(primary,'secondary',{'slot':'2'}).append(ram)
    profile_raw=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(profile)
    validate_machine_profile(profile_raw)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_FixedClock.xml').write_bytes(profile_raw)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set route_index 0
set committed 0
set irq_active 0
set min_sp 62336
set booted 0
set f [open {{{out/'route-inputs.bin'}}} rb];set route_inputs [read $f];close $f
set cpu [open {{{out/'route-cpu.bin'}}} wb]
set captures [open {{{out/'captures.bin'}}} wb]
set owners [open {{{out/'owners.bin'}}} wb]
set irq [open {{{out/'irq.tsv'}}} w]
set timing [open {{{out/'pictures.tsv'}}} w]
proc fail {{message}} {{puts stderr "CLOCK_FAIL $message source=$::route_index pictures=$::committed PC=[reg PC]";exit 1;return -code error $message}}
proc snap {{}} {{return "[debug read_block VRAM 0 16384][debug read_block {{VDP regs}} 0 8]"}}
proc word {{a}} {{return [expr {{[debug read memory $a]|([debug read memory [expr {{$a+1}}]]<<8)}}]}}
proc guard {{}} {{
 if {{[debug read_block memory 0xE900 {len(code)}] ne [binary format H* {code.hex()}]}} {{fail ram-code}}
 if {{[debug read_block memory 0xF080 640] ne [string repeat [binary format c 165] 640]}} {{fail redzone}}
 if {{[word {s['t_late']}] || [word {s['t_spurious']}] || [debug read memory {s['t_fault']}]}} {{fail clock-fault}}
 if {{[debug read ioports 168] != [debug read memory {s['t_slot_primary']}]}} {{fail primary-slot}}
 if {{[debug read memory {s['t_slot_expanded']}] && ((255^[debug read memory 65535]) != [debug read memory {s['t_slot_secondary']}])}} {{fail secondary-slot}}
}}
proc capture_cpu {{cold}} {{
 if {{$cold}} {{
  binary scan [debug read_block memory 0xC6F0 5] cu* r;set flags [lindex $r 0]
  set a [lindex $r 1];set x [lindex $r 3];set y [lindex $r 2];set c [expr {{[lindex $r 4]&1}}];set sp [debug read memory 0xC602]
 }} else {{
  set flags [expr {{[reg AF]&255}}];set a [expr {{[reg AF]>>8}}];set x [expr {{[reg BC]>>8}}];set y [expr {{[reg BC]&255}}]
  set c [expr {{[reg DE]&1}}];set sp [expr {{[debug read memory 0xC60B]|([reg IX]&127)}}]
 }}
 set p [expr {{($flags&128)|(($flags&64)>>5)|$c|[debug read memory 0xC600]|[debug read memory 0xC601]}}]
 puts -nonewline $::cpu [binary format cu* [list $a $x $y $p $sp]][debug read_block memory 0xC000 128]
}}
debug set_bp {s['native_reset_done']} {{}} {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail target}}
 debug write_block memory 0xF080 [string repeat [binary format c 165] 640]
 debug write_block memory 0xF300 [string repeat [binary format c 90] 128]
 set ::booted 1
 capture_cpu 1
 set VDP.too_fast_vram_access_callback {{fail fast-vram}}
}}
debug set_bp {s['native_step']} {{}} {{
 incr ::route_index
 set at [expr {{$::route_index*4}}];set input [string range $::route_inputs $at [expr {{$at+3}}]]
 if {{[string length $input]!=4}} {{fail input-exhaustion}}
 binary scan $input cu* values;lassign $values swcha swchb fire0 fire1
 if {{[debug read memory 0xC047]!=0}} {{fail one-player-contract}}
 set mask [expr {{(($swcha&16)?0:32)|(($swcha&32)?0:64)|(($swcha&64)?0:16)|(($swcha&128)?0:128)|($fire0?1:0)}}]
 keymatrixup 8 255;keymatrixdown 8 $mask
 keymatrixup 6 96;keymatrixdown 6 [expr {{(($swchb&1)?0:32)|(($swchb&2)?0:64)}}]
}}
debug set_bp {s['native_return']} {{$::route_index>0}} {{capture_cpu 0}}
debug set_bp {s['t_main.frame']} {{}} {{
 if {{[debug read memory {s['t_ready']}]}} {{fail overwrite-pending}}
 set ::before [snap];set ::prepare_time [machine_info time]
}}
debug set_bp {s['presentation_prepare']+3} {{[debug read memory {s['t_enabled']}]==1}} {{
 set ::ram [debug read_block memory 0xF000 128];set ::snapshot_step [word {s['t_snapshot_step']}]
 if {{$::snapshot_step > $::route_index}} {{fail future-snapshot}}
}}
debug set_bp {s['t_prepare_gate']+19} {{[debug read memory {s['t_enabled']}]==1}} {{
 if {{([reg IFF]&3)!=0 || [debug read_block memory 0xF000 128] ne [debug read_block memory 0xC000 128]}} {{fail atomic-snapshot}}
}}
debug set_bp {s['t_main.prepared']} {{}} {{
 guard
 if {{[debug read memory 0xC231]}} {{fail compositor}}
 if {{[debug read_block memory 0xF000 128] ne $::ram}} {{fail snapshot-mutated}}
 set ::prepared [snap];set ::prepare_cycles [expr {{round(([machine_info time]-$::prepare_time)*3579545)}}]
 set ::owner "[debug read_block memory 0xC1D1 32][debug read_block memory 0xE5C0 32][debug read_block memory 0xC1F1 8][debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block memory 0xD000 2304][debug read_block memory 0xD900 264][debug read_block memory 0xCCA0 6][debug read_block memory 0xE800 32]"
}}
debug set_bp {s['t_irq']} {{}} {{
 if {{$::irq_active}} {{fail recursive-irq}}
 set ::irq_active 1;set ::irq_time [machine_info time];set ::irq_source $::route_index
 set ::irq_frame [machine_info VDP_frame_count]
}}
debug set_bp {s['t_irq.commit']} {{}} {{
 set ::commit_y [machine_info VDP_msx_y_pos]
 if {{$::commit_y>=0 && $::commit_y<192}} {{fail visible-commit}}
}}
debug set_bp {s['t_irq.committed']} {{}} {{
 set y [machine_info VDP_msx_y_pos]
 if {{$y>=0 && $y<192}} {{fail visible-commit-end}}
 puts -nonewline $::captures "$::ram$::before$::prepared[snap]"
 puts -nonewline $::owners $::owner
 puts $::timing "$::committed $::snapshot_step $::route_index [machine_info time] [machine_info VDP_frame_count] $::prepare_cycles $::commit_y $y"
 incr ::committed
}}
debug set_bp {s['t_irq.exit']} {{}} {{
 guard
 set cycles [expr {{round(([machine_info time]-$::irq_time)*3579545)}}]
 puts $::irq "[word {s['t_vblanks']}] $::irq_frame $::irq_time $cycles [expr {{$::route_index-$::irq_source}}] [word {s['t_commits']}] [word {s['t_late']}]"
 set ::irq_active 0
 if {{$::route_index>={steps}}} {{
  set done [open {{{out/'complete.tsv'}}} w];puts $done "$::route_index $::committed $::min_sp";close $done
  close $::cpu;close $::captures;close $::owners;close $::irq;close $::timing
  exit;return
 }}
}}
debug set_watchpoint write_mem {{0xF300 0xF37F}} {{$::booted && [reg SP]<$::min_sp}} {{
 set ::min_sp [reg SP]
 if {{$::min_sp<0xF300}} {{fail stack-overflow}}
}}
debug set_bp {s['wait_vblank']} {{[debug read memory {s['t_enabled']}]==1}} {{fail runtime-status-poll}}
debug set_bp {s['set_address']} {{[debug read memory {s['t_enabled']}]==1}} {{fail unprotected-address}}
after time {steps+60} {{fail watchdog}}
'''
    # No canonical source/CPU writes: only a redzone sentinel, real key pins,
    # and passive captures. The ROM installs its own vector and slot mapping.
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_FixedClock','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=360)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or 'CLOCK_FAIL' in log or not (out/'complete.tsv').exists():raise ValueError(f'clock probe failed (exit {run.returncode}): '+log[-2000:])
    actual=(out/'route-cpu.bin').read_bytes()
    if len(actual)%133:raise ValueError('partial native checkpoint')
    count=len(actual)//133
    done=list(map(int,(out/'complete.tsv').read_text().split()))
    if len(done)!=3 or not 0xF300<=done[2]<0xF380:raise ValueError('missing/bad observed stack watermark')
    if not steps+1<=count<=steps+2:raise ValueError('incomplete source route')
    for index in range(count):
        raw=actual[index*133:(index+1)*133];point=trace['steps'][index]
        try:compare({'ram':point['ram'],'registers':{k:point['cpu'][k] for k in ('a','x','y','p','sp')}},
            {'ram':list(raw[5:]),'registers':dict(zip(('a','x','y','p','sp'),raw[:5]))})
        except ValueError as e:raise ValueError(f'source step {index}: {e}') from e
    timings=[line.split() for line in (out/'pictures.tsv').read_text().splitlines()]
    irq=[line.split() for line in (out/'irq.tsv').read_text().splitlines()]
    if sum(int(r[4]) for r in irq)!=count-1:raise ValueError('source step counter differs')
    measured=clocks(irq,timings,trace['steps'])
    captures=(out/'captures.bin').read_bytes();owners=(out/'owners.bin').read_bytes()
    if len(captures)!=len(timings)*CAPTURE_BYTES or len(owners)!=len(timings)*OWNER_BYTES:raise ValueError('partial coherent-picture captures')
    config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette=audit_palette(ROOT/config['palette'])
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if sha(original)!=meta['profile']['source_sha256']:raise ValueError('original authority differs')
    tile=constructor(build);geometry=resident_geometry(rom,s)
    deltas=list(rom[s['p_template_deltas']-16384:s['p_template_deltas']-16384+10])
    for index in range(len(timings)):
        row=captures[index*CAPTURE_BYTES:(index+1)*CAPTURE_BYTES];ram=row[:128];regs=[];images=[]
        snapshot_index=int(timings[index][1])
        if ram!=bytes(trace['steps'][snapshot_index]['ram']):raise ValueError('picture snapshot differs from exact source step')
        for at in (128,16520,32912):
            r=row[at+16384:at+16392]
            if r[1]!=0xE2:raise ValueError('runtime IRQ/mode register differs')
            regs.append(r);images.append(decode_target(row[at:at+16384],r[:1]+bytes([0xC2])+r[2:]))
        audit_active(row[128:16512],row[16520:32904],regs[0])
        if regs[0]!=regs[1] or images[0]!=images[1]:raise ValueError(f'active picture changed during preparation {index}')
        if images[2]!=map_frame(pixels(original,describe(original,{'ram':list(ram)})),palette):raise ValueError(f'committed source pixels differ {index}')
        owner=owners[index*OWNER_BYTES:(index+1)*OWNER_BYTES]
        decorated=decorate_owners(owner[72:4182],owner[:32],owner[32:64],owner[64:72],rom,deltas)
        decorated=decorate_actor_owners(decorated,owner[4182:],rom,geometry)
        audit_row(decorated,row[32912:49296],tile,templates=True)
    if artifact.read_bytes()!=rom or Path(__file__).read_bytes()!=producer:
        raise ValueError('ROM/probe producer changed during capture; preserve but reject evidence')
    for name,value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('build producer changed during capture: '+name)
    report=dict(complete=True,family=family,expanded_ram_slot=expanded,stack_min_sp=done[2],stack_bytes=0xF380-done[2],rom_sha256=sha(rom),source_checkpoints=count,
        hardware_vblanks=len(irq),**measured,committed_pictures=len(timings),
        max_irq_cycles=max(int(r[3]) for r in irq),mean_irq_cycles=statistics.mean(int(r[3]) for r in irq),
        mean_prepare_elapsed_cycles=statistics.mean(int(r[5]) for r in timings),max_prepare_elapsed_cycles=max(int(r[5]) for r in timings),
        source_cpu_all_ram_equal=True,coherent_picture_pixels_equal=True,physical_owners_equal=True,
        active_page_protected=True,late_vblanks=0,canonical_source_writes=0,
        source_route_sha256=sha((source/'route.json').read_bytes()),emulator_sha256=sha(emulator.read_bytes()),profile_sha256=sha(profile_raw),
        producer_sha256=sha(producer),artifacts={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()},
        scope='Input-only emulator proof of the independent source and coherent-picture clocks. Original graphics per committed snapshot, not 60fps graphics. Manual/audio/physical acceptance remains separate.')
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--family',choices=('ntsc','pal'),required=True);parser.add_argument('--steps',type=int,default=2252)
    parser.add_argument('--expanded',action='store_true',help='same64KiB RAM in expanded primary3 secondary2')
    a=parser.parse_args();probe(a.build.resolve(),a.out.resolve(),a.family,a.steps,a.expanded)
