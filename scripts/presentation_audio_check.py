"""Actual game post-visible CPU and ordered PSG histories against frozen source.

Controlled intervals restore the independent original visible CPU/RAM and audio
latches. This is integration evidence, not natural pacing or listening proof.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from native_contract import compare
from presentation_audio import psg_step
from presentation_audio_source_check import registers,replay
from presentation_build import FILES,validate_rom
from presentation_records import parse_records
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_state import decode_state
from reference_traces import STATE_NAME,private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*FILES,*SOURCE_FILES,'scripts/presentation_audio_check.py',
    'scripts/presentation_audio_source_check.py','scripts/native_contract.py','scripts/reference_state.py',
    'scripts/render_build.py','scripts/smoke.py')))
INPUT_BYTES=133+6+21+16+4


def verify_streams(actual_events,expected_events,actual_writes,expected_writes):
    if actual_events!=expected_events:raise ValueError('native ordered source audio events differ or truncate')
    if actual_writes!=expected_writes:raise ValueError('physical PSG register history differs or truncates')


def workspace(source,state):
    psg=bytearray(state['psg'][:11]);psg[4:6]=bytes(2)
    owner=state['noise_owner']
    parts=bytes(9 if source[ch]in(0,11) else 1 if source[ch]==8 else 8 for ch in (0,1))
    return source+bytes(psg)+bytes((state['psg'][7]&192,255 if owner is None else owner))+parts


def check(build_dir,out,*,inject=False):
    if type(inject)is not bool:raise ValueError('explicit negative-control selection required')
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    producer={name:sha(ROOT/name) for name in HELPERS}
    build_dir=Path(build_dir).resolve();meta=json.loads((build_dir/'build.json').read_text())
    artifact=build_dir/meta['rom']['filename'];rom=artifact.read_bytes()
    if validate_rom(rom) or sha(artifact)!=meta['rom']['sha256'] or meta['profile'].get('ordered_psg')is not True:
        raise ValueError('exact audio-enabled presentation cartridge required')
    if any(sha(ROOT/name)!=value for name,value in meta['source_files'].items()):raise ValueError('audio build producers changed')
    domain=collect();inputs=bytearray();expected=[];events=[];writes=[];identities=[];excluded=[]
    base={'psg':bytes((1,0,1,0,0,0,1,191,0,0,0,0,0,0,0,0))}
    for audit in domain['audits']:
        root=ROOT/audit['root'];report=json.loads((root/'report.json').read_text())
        samples=json.loads((root/'fixtures.json').read_text()) if audit['family']=='fixtures' else report['points']
        initial=decode_state((root/'initial.state').read_bytes());before=initial
        for batch in sorted(root.glob('batch-*')):
            offset=int(batch.name.split('-')[1])
            for record in parse_records((batch/'records.bin').read_bytes()):
                if audit['family']=='fixtures':before=initial
                index=len(expected);visible=record['visible'];r=visible['registers'];source=registers(before)
                if visible['ram'][0x47]not in (0,1):
                    if audit['family']!='fixtures' or record['audio']:raise ValueError('natural/active audio interval outside player contract')
                    excluded.append({'id':f'{audit["root"]}/{batch.name}/{record["index"]}','reason':'synthetic graphics-only player selector outside original 0/1 gameplay contract','ordered_writes':0})
                    continue
                if any(cycle<=record['visible_cycles'] for cycle,_,_ in record['audio']):
                    raise ValueError('post-visible-only native integration requires independently observed phase')
                state=psg_step(source,base);sample=samples[offset+record['index']]['input']
                inputs.extend(bytes(visible['ram'])+bytes(r[key] for key in ('a','x','y','p','sp'))+source+workspace(source,state)+state['psg']
                    +bytes((sample['swcha'],sample['swchb'],int(sample['fire'][0]),int(sample['fire'][1]))))
                final,state,history=replay(source,record['audio'],state)
                events.extend((index,row['address'],row['raw']) for row in history)
                writes.extend((index,register,value) for row in history for register,value in row['psg_writes'])
                after=decode_state((batch/'plain/settings/state'/f'{STATE_NAME}.st{record["index"]}').read_bytes())
                if final!=registers(after):raise ValueError('source audio/capsule differs')
                expected.append(record['after']);identities.append(f'{audit["root"]}/{batch.name}/{record["index"]}');before=after
    count=len(expected)
    if len(inputs)!=count*INPUT_BYTES or count+len(excluded)!=2116:raise ValueError('whole original interval domain accounting required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs)
    syms=symbols(build_dir/'presentation.sym');emulator=Path(shutil.which('openmsx')).resolve()
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_GameAudio.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    hooks='\n'.join(f'debug set_bp {syms[f"p_audio_apply_{reg:02X}"]} {{$::active}} {{puts $::events "$::index {reg} [expr {{[reg AF]>>8}}] [debug read memory 0xC001] [machine_info time]"}}' for reg in range(21,27))
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set active 0
set selected -1
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb]
set events [open {{{out/'events.tsv'}}} w];set writes [open {{{out/'writes.tsv'}}} w]
proc fail_game_audio {{message}} {{puts stderr "GAME_AUDIO_FAIL $message index=$::index";exit 1;return -code error $message}}
{hooks}
debug set_watchpoint write_io {{160 161}} {{$::active}} {{
    if {{![info exists ::wp_last_address] || ![info exists ::wp_last_value]}} {{fail_game_audio io-payload}}
    set sampler [expr {{[reg PC]>={syms['sample_native_input']} && [reg PC]<={syms['sample_native_return']}}}]
    if {{($::wp_last_address&255)==160}} {{
        set ::selected $::wp_last_value
        if {{$sampler}} {{
            if {{$::selected ni {{14 15}}}} {{fail_game_audio sampler-selection}}
        }} elseif {{$::selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail_game_audio "unowned-selection reg=$::selected pc=[reg PC]"}}
    }} else {{
        if {{$sampler}} {{
            if {{$::selected!=15}} {{fail_game_audio sampler-write}}
        }} else {{
            if {{$::selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail_game_audio unowned-write}}
            if {{$::selected==7 && ($::wp_last_value&192)!=128}} {{fail_game_audio gpio-direction}}
            puts $::writes "$::index $::selected $::wp_last_value"
        }}
    }}
}}
proc dispatch_game_audio {{}} {{
    set ::active 0
    if {{$::index=={count}}} {{
        close $::actual;close $::events;close $::writes
        set f [open {{{out/'complete.json'}}} w];puts $f "\\{{\\\"complete\\\":true,\\\"cases\\\":$::index\\}}";close $f;exit;return
    }}
    set row [string range $::cases [expr {{$::index*{INPUT_BYTES}}}] [expr {{($::index+1)*{INPUT_BYTES}-1}}]]
    debug write_block memory 0xC000 [string range $row 0 127]
    set ::cpu [string range $row 128 132]
    debug write_block memory 0xC715 [string range $row 133 138]
    debug write_block memory 0xE000 [string range $row 139 159]
    for {{set r 0}} {{$r<16}} {{incr r}} {{binary scan [string index $row [expr {{160+$r}}]] cu value;debug write {{PSG regs}} $r $value}}
    set ::unowned "[debug read_block {{PSG regs}} 4 2][debug read_block {{PSG regs}} 11 5]"
    binary scan [string range $row 176 179] cu* input;lassign $input swcha swchb fire0 fire1
    set player [debug read memory 0xC047]
    if {{$player==0}} {{set keys $swcha;set fire $fire0}} elseif {{$player==1}} {{set keys [expr {{(($swcha&15)<<4)|15}}];set fire $fire1}} else {{fail_game_audio player}}
    set mask [expr {{(($keys&16) ? 0 : 32)|(($keys&32) ? 0 : 64)|(($keys&64) ? 0 : 16)|(($keys&128) ? 0 : 128)|($fire ? 1 : 0)}}]
    keymatrixup 8 255;keymatrixdown 8 $mask
    keymatrixup 6 96;keymatrixdown 6 [expr {{(($swchb&1) ? 0 : 32)|(($swchb&2) ? 0 : 64)}}]
    debug write memory 0xC6FD 0
    reg SP 0xF380;reg PC 0xC6D0;debug cont
}}
set boot [debug set_bp {syms['native_reset_done']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_game_audio target}}
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]
    debug write_block memory 0xC6D0 [binary format cu* {{205 {syms['sample_native_input']&255} {syms['sample_native_input']>>8} 205 {syms['native_call']&255} {syms['native_call']>>8} 195 217 198 24 254}}]
    debug set_bp 0xC6D3 {{}} {{
        binary scan $::cpu cu* r;lassign $r a x y p sp
        debug write memory 0xC600 [expr {{$p&64}}];debug write memory 0xC601 [expr {{$p&60}}];debug write memory 0xC602 $sp
        debug write memory 0xC60B [expr {{$sp&128}}]
        reg IX [expr {{0xC000|($sp&127)}}];reg IY [expr {{0xC000|$x}}]
        reg AF [expr {{$a*256|($p&128)|(($p&2) ? 64 : 0)}}];reg BC [expr {{$x*256+$y}}];reg DE [expr {{$p&1}}]
        set ::active 1
    }}
    debug set_bp 0xC6D9 {{}} {{debug break;after break {{
        set ::active 0
        if {{{int(inject)} && $::index==0}} {{puts $::events "0 21 255 0 0"}}
        binary scan [debug read_block memory 0xC6F0 5] cu* r;set flags [lindex $r 0]
        set p [expr {{($flags&128)|(($flags&64)>>5)|([lindex $r 4]&1)|[debug read memory 0xC600]|[debug read memory 0xC601]}}]
        puts -nonewline $::actual [binary format cu* [list [lindex $r 1] [lindex $r 3] [lindex $r 2] $p [debug read memory 0xC602]]][debug read_block memory 0xC000 128]
        if {{[debug read memory 0xC6FD]!=0 || [reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_game_audio native-abi}}
        if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40] || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_game_audio heap-or-vram}}
        if {{"[debug read_block {{PSG regs}} 4 2][debug read_block {{PSG regs}} 11 5]" ne $::unowned}} {{fail_game_audio unowned-psg}}
        incr ::index;dispatch_game_audio
    }}}}
    dispatch_game_audio
}}}}]
after time 600 {{fail_game_audio watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_GameAudio','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or 'GAME_AUDIO_FAIL' in log or not (out/'complete.json').is_file():raise ValueError('game audio capture failed: '+log[-1500:])
    complete=json.loads((out/'complete.json').read_text())
    if complete!={'complete':True,'cases':count}:raise ValueError('incomplete game audio receipt')
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*133:raise ValueError('incomplete whole CPU/RAM game audio capture')
    for index,wanted in enumerate(expected):
        row=actual[index*133:(index+1)*133]
        try:compare(wanted,{'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:])})
        except ValueError as error:raise ValueError(f'game audio CPU/RAM {index} {identities[index]}: {error}') from error
    raw_events=[line.split() for line in (out/'events.tsv').read_text().splitlines()]
    if any(len(row)!=5 for row in raw_events):raise ValueError('complete event timestamp and source epoch required')
    actual_events=[tuple(map(int,row[:3])) for row in raw_events]
    actual_writes=[tuple(map(int,line.split())) for line in (out/'writes.tsv').read_text().splitlines()]
    verify_streams(actual_events,events,actual_writes,writes)
    verify_files(domain['files'])
    if (any(sha(ROOT/name)!=value for name,value in producer.items()) or artifact.read_bytes()!=rom or (out/'cases.bin').read_bytes()!=inputs):
        raise ValueError('game audio producers/source/ROM/input changed')
    report={**complete,'excluded_graphics_only_fixtures':excluded,'ordered_source_writes':len(events),'physical_psg_writes':len(writes),'rom_sha256':meta['rom']['sha256'],
        'producer_files':producer,'input_files':domain['files'],'source_receipt_sha256':domain['source_receipt_sha256'],
        'artifacts':{p.name:sha(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,'manual_listening_accepted':False,
        'scope':'Actual integrated cartridge executes each original post-visible interval from independent visible CPU/all128RAM and actual source audio latches. Every ordered raw write, physical PSG write and after CPU/all128RAM matches; real keyboard/console sampling and hardware GPIO/unowned/heap/VRAM guards. Controlled phase injection; not natural cadence, oscillator phase, listening or physical hardware acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('complete','cases','ordered_source_writes','physical_psg_writes')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build-dir','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--inject',action='store_true');check(**vars(p.parse_args()))
