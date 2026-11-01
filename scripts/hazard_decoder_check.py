"""Original-free actual Z80 decoder/copy-distance check on a standard MSX1.

This private fixture cartridge is a unit-test harness, not a playable version.
It contains only synthetic data and never substitutes for whole-game gates.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from collision_compact import CompactRows
from environment import ROOT,verified_tool
from floe_truth import sample
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
from stella_hazard import digest
from reference_traces import private_output
from hazard_tables import compile_component,emit_component


def check(out):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    producer_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    producer_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    helpers={name:digest(ROOT/name) for name in ('src/hazard_contacts.asm','scripts/hazard_decoder_check.py','scripts/collision_compact.py',
                                               'scripts/hazard_tables.py','scripts/floe_tables.py','scripts/floe_truth.py','scripts/smoke.py','scripts/environment.py','scripts/render_build.py')}
    pool=CompactRows(row_format='nibble');roots=[];rows=[]
    for n in range(520):
        row=[bytes(58)]*160;raw=(n+1).to_bytes(2,'little')+bytes(27)
        shadow=bytes([255])*28+b'\x0f' if n%3==0 else bytes(29)
        row[(0,15,16,159)[n%4]]=raw+shadow;rows.append(row);roots.append(pool.intern_row(row))
    dense=[bytes(58)]*160
    for block in range(10):
        raw=((block+1)*37).to_bytes(2,'little')+bytes(27)
        shadow=bytes([255])*28+b'\x0f' if block%2 else bytes(29)
        dense[block*16]=dense[block*16+15]=raw+shadow
    rows.append(dense);roots.append(pool.intern_row(dense))
    plan={'kind':'edge','player_x':[0],'ys':[0,53],'modes':[{}]*264,'coordinates':list(range(160)),'cases_per_player':2*264*160}
    data=bytearray(plan['cases_per_player']*58)
    for mode in range(264):
        offset=((264+mode)*160+159)*58;data[offset:offset+2]=(mode+1).to_bytes(2,'little')
    compiled=compile_component(pool,plan,{0:bytes(data)})
    packed=pool.emit(14);directory=emit_component(packed,compiled);(out/'directory.bin').write_bytes(directory);cases=[]
    for n in (0,1,2,3,42,510,511,512,519):
        for x in (0,15,16,159):
            for view in (0,1,7,8,9,15,16,227):
                bank,address=packed.rows[roots[n]]
                cases.append({'entry':'contact_compact','bank':bank,'hl':address,'de':x,'bc':0x1357,'a':0,
                              'byte':view//8,'mask':1<<(view%8),'want':sample(rows[n][x],view)})
    for x in (0,15,16,31,47,63,79,95,111,127,143,159):
        for view in (0,1,7,8,9,15,16,227):
            bank,address=packed.rows[roots[520]]
            cases.append({'entry':'contact_compact','bank':bank,'hl':address,'de':x,'bc':0x1357,'a':0,
                          'byte':view//8,'mask':1<<(view%8),'want':sample(dense[x],view)})
    for mode in (0,255,256,263):
        for y in (0,1):
            for view in (0,8):
                raw=(mode+1).to_bytes(2,'little')+bytes(56) if y else bytes(58)
                cases.append({'entry':'hazard_lookup','bank':2,'hl':mode,'de':0,'bc':0x6200,'a':0,'x':159,'y':y,
                              'byte':view//8,'mask':1<<(view%8),'want':sample(raw,view)})
    for distance in range(160):
        cases.append({'entry':'hazard_copy_distance','bank':2,'hl':0x5333,'de':0x5A21,'bc':0x1303,'a':distance,
                      'byte':0,'mask':1,'distance':distance})
    banks=[]
    for number,data in enumerate(packed.banks,14):
        path=out/f'bank-{number}.bin';path.write_bytes(data+bytes([255])*(16384-len(data)))
        banks.extend(('    ORG $8000',f'    INCBIN "{path}"'))
    assembly='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
    CALL map_page2
ready:
    JP ready
map_page2:
    CALL $0138
    RRCA
    RRCA
    AND 3
    LD C,A
    LD E,A
    LD D,0
    LD HL,$FCC1
    ADD HL,DE
    BIT 7,(HL)
    JR Z,.slot
    LD HL,$FCC5
    ADD HL,DE
    LD A,(HL)
    AND $0C
    OR C
    OR $80
    JR .enable
.slot:
    LD A,C
.enable:
    LD H,$80
    JP $0024
core_fault:
    JP core_fault
floe_deref:
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD ($7000),A
    EX DE,HL
    RET
floe_viewbyte EQU $C785
floe_viewmask EQU $C786
hazard_row_min_y EQU 36
hazard_row_max_y EQU 61
hazard_shore_min_y EQU 4
hazard_shore_max_y EQU 56
hazard_shape_index EQU $6000
hazard_bear_index EQU $6100
hazard_edge_modes EQU $6200
hazard_ordinary_modes EQU $6500
hazard_shore_modes EQU $6600
'''
    assembly+=f'contact_record_bank EQU {packed.metadata["record_bank"]}\ncontact_block_bank EQU {packed.metadata["block_bank"]}\n'
    assembly+=f'    INCLUDE "hazard_contacts.asm"\n    ASSERT $ <= $6200\n    DS $6200-$,$FF\n    INCBIN "{out/"directory.bin"}"\n    ASSERT $ <= $8000\n    DS $8000-$,$FF\n'
    assembly+=''.join('    ORG $8000\n    DS $4000,$FF\n' for _ in range(13))+'\n'.join(banks)+'\n'
    total=14+len(packed.banks);capacity=1<<(total-1).bit_length()
    assembly+=''.join('    ORG $8000\n    DS $4000,$FF\n' for _ in range(capacity-total))
    (out/'fixture.asm').write_text(assembly);assembler=verified_tool('sjasmplus');rom=out/'fixture.rom'
    result=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={rom}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('decoder fixture assembler failed: '+(result.stdout+result.stderr)[-1500:])
    syms=symbols(out/'fixture.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Decoder.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    commands=[]
    for c in cases:
        commands.append('    {'+' '.join(str(v) for v in (syms[c['entry']],c['bank'],c['hl'],c['de'],c['bc'],c['a'],c['byte'],c['mask'],c.get('x',0),c.get('y',0)))+'}')
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set cases {{
{chr(10).join(commands)}
}}
set count 0
set result [open {{{out/'actual.tsv'}}} w]
proc fail_decoder {{message}} {{puts stderr "DECODER_FAIL $message";exit 1}}
proc dispatch_decoder {{}} {{
    if {{$::count==[llength $::cases]}} {{close $::result;exit}}
    lassign [lindex $::cases $::count] entry bank hl de bc a byte mask x y
    debug write memory 0x7000 $bank
    debug write memory 0xC785 $byte
    debug write memory 0xC786 $mask
    debug write memory 0xC793 $x
    debug write memory 0xC794 $y
    reg HL $hl;reg DE $de;reg BC $bc;reg A $a;reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
    debug write_block memory 0xC6D0 [binary format cu* [list 205 [expr {{$entry&255}}] [expr {{$entry>>8}}] 195 214 198 24 254]]
    reg PC 0xC6D0;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
    debug remove_bp $::boot
    debug break
    after break {{
        if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_decoder target}}
        debug set_bp 0xC6D6 {{}} {{debug break;after break {{
            puts $::result "$::count [reg A] [reg F] [reg HL] [reg BC] [reg DE] [reg IX] [reg IY] [reg SP] [reg IFF] [expr {{round(([machine_info time]-$::started)*3579545)}}]"
            incr ::count;dispatch_decoder
        }}}}
        dispatch_decoder
    }}
}}]
after time 30 {{fail_decoder watchdog}}
'''
    (out/'launch.tcl').write_text(tcl)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Decoder','-cart',str(rom),'-romtype','ASCII16','-script',str(out/'launch.tcl')],
                          cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=60)
    (out/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('decoder emulator failed: '+(result.stdout+result.stderr)[-1500:])
    actual=[[int(value) for value in line.split()] for line in (out/'actual.tsv').read_text().splitlines()]
    if len(actual)!=len(cases):raise ValueError('partial actual decoder fixture')
    for i,(c,r) in enumerate(zip(cases,actual)):
        index,a,flags,hl,bc,de,ix,iy,sp,iff,cycles=r
        if index!=i or ix!=0xDDDD or iy!=0xEEEE or sp!=0xF380 or iff&3:raise ValueError(f'unsafe decoder case{i}')
        if 'distance' in c:
            d=c['distance'];hit=d<8 or d>=153
            if bool(flags&1)!=hit or hit and a!=(d+7 if d<8 else d-153) or hl!=0x5333 or bc!=0x1303 or de!=0x5A21:
                raise ValueError(f'copy-distance differs at actual original-free Z80 case{i} distance{d} A{a} F{flags}')
        elif a!=c['want']:raise ValueError(f'physical native decoder differs at case{i}: {a} != {c["want"]}')
    if any(digest(ROOT/name)!=sha for name,sha in helpers.items()):raise ValueError('decoder fixture producer changed')
    report={'complete':True,'cases':len(cases),'decoder_cases':sum(c['entry']=='contact_compact' for c in cases),
            'all_ten_nibble_ranks':True,'profile_directory_cases':16,'all_160_copy_distances':True,'helpers':helpers,
            'producer_commit':producer_commit,'producer_dirty':producer_dirty,
            'max_cycles_including_rpc_call_return':{entry:max(r[-1] for c,r in zip(cases,actual) if c['entry']==entry) for entry in ('contact_compact','hazard_lookup','hazard_copy_distance')},
            'fixture_sha256':digest(rom),'emulator_sha256':digest(emulator),'profile_sha256':digest(user/'machines/Frostbite_Decoder.xml'),
            'scope':'Original-free synthetic unit cartridge only; actual standard MSX1 Z80. No gameplay, full-ROM timing, human or physical claim.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();print(json.dumps(check(args.out),indent=2))
