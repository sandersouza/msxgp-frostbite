"""Original-free actual-Z80 shift/flag/RAM microproof, not a human ROM."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from native_shifts import compact_shift
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
from stella_hazard import digest

HELPERS=('scripts/native_shifts.py','scripts/native_shift_check.py','scripts/native_fast.py','scripts/native_codegen.py',
         'scripts/native_analysis.py','scripts/environment.py','scripts/smoke.py','scripts/render_build.py',
         'scripts/reference_provenance.py','scripts/reference_traces.py','scripts/reference_inventory.py',
         'scripts/reference_state.py','scripts/source_timing.py','scripts/trace_compare.py','scripts/stella_hazard.py',
         'scripts/stella_floe.py','references/manifest.json','references/tools-lock.json')


def verify_rows(cases,actual):
    if len(actual)!=len(cases):raise ValueError('partial actual shift matrix')
    for index,(case,row) in enumerate(zip(cases,actual)):
        name,mode,nz,clive,value,carry,overflow=case;op=name.split('_')[1]
        wanted={'ASL':(value*2)&255,'LSR':value>>1,'ROL':((value*2)|carry)&255,'ROR':(value>>1)|(carry<<7)}[op]
        wanted_c=value>>7 if op in ('ASL','ROL') else value&1
        i,a,flags,e,ram,v,bc,ix,iy,sp,iff,cycles=row
        if (i!=index or bc!=4951 or ix!=56797 or iy!=61166 or sp!=0xF380 or iff&3 or v!=overflow
                or a!=(wanted if mode=='acc' else 165) or ram!=(wanted if mode=='zpg' else value)
                or nz&1 and bool(flags&128)!=bool(wanted&128) or nz&2 and bool(flags&64)!=(wanted==0)
                or clive and e!=wanted_c):raise ValueError(f'actual shift differs case{index} {case}: {row}')


def audit_saved(out):
    cases=[(f"shift_{op}_{mode}_{nz}_{clive}",mode,nz,clive,value,carry,overflow)
           for op in ("ASL","LSR","ROL","ROR") for mode in ("acc","zpg") for nz in range(4)
           for clive in (0,8) for value in range(256) for carry in (0,1) for overflow in (0,64)]
    actual=[[int(v) for v in line.split()] for line in (Path(out)/"actual.tsv").read_text().splitlines()]
    verify_rows(cases,actual)
    return max(row[-1] for row in actual)


def check(out,explore=False):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if dirty and not explore:raise ValueError('clean committed shift unit producer required')
    producer={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:digest(ROOT/name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    assembly=['    ORG $4000','    DB "AB"','    DW start','    DS 12,0','start:','    DI','    LD SP,$F380','ready:','    JP ready']
    cases=[];labels=[]
    for op in ('ASL','LSR','ROL','ROR'):
        for mode in ('acc','zpg'):
            for nz in range(4):
                for c_live in (0,8):
                    name=f'shift_{op}_{mode}_{nz}_{c_live}';labels.append(name);assembly.append(name+':')
                    assembly.extend('    '+line for line in compact_shift({'mnemonic':op,'mode':mode,'value':0x82},{'live_out':nz|c_live}))
                    assembly.append('    RET')
                    for value in range(256):
                        for carry in (0,1):
                            for overflow in (0,64):cases.append((name,mode,nz,c_live,value,carry,overflow))
    assembly+=['    DS $C000-$,$FF'];(out/'unit.asm').write_text('\n'.join(assembly)+'\n')
    assembler=verified_tool('sjasmplus');rom=out/'unit.rom'
    result=subprocess.run([str(assembler),'--nologo',f'--raw={rom}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('shift unit assembler failed: '+result.stderr[-1000:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Shifts.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    commands=['{'+' '.join(str(x) for x in (syms[name],int(mode=='zpg'),nz,c_live,value,carry,overflow))+'}' for name,mode,nz,c_live,value,carry,overflow in cases]
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set count 0
set cases {{{chr(10).join(commands)}}}
set result [open {{{out/'actual.tsv'}}} w]
set blank [string repeat [binary format c 165] 128]
proc fail_shift {{message}} {{puts stderr "SHIFT_FAIL $message case=$::count";exit 1}}
proc dispatch_shift {{}} {{
    if {{$::count==[llength $::cases]}} {{close $::result;exit}}
    lassign [lindex $::cases $::count] entry mem nz clive value carry overflow
    debug write_block memory 0xC000 $::blank
    debug write memory 0xC002 $value
    debug write memory 0xC600 $overflow
    reg AF [expr {{256*($mem ? 165 : $value)+197}}]
    reg BC 4951;reg DE [expr {{21760+$carry}}];reg HL 43981;reg IX 56797;reg IY 61166;reg SP 0xF380
    debug write_block memory 0xC6D0 [binary format cu* [list 205 [expr {{$entry&255}}] [expr {{$entry>>8}}] 195 214 198 24 254]]
    reg PC 0xC6D0;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
    debug remove_bp $::boot;debug break
    after break {{
        if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_shift target}}
        debug set_bp 0xC6D6 {{}} {{debug break;after break {{
            set ram [debug read_block memory 0xC000 128]
            if {{[string replace $ram 2 2 [binary format c 165]] ne $::blank}} {{fail_shift canonical-ram}}
            puts $::result "$::count [reg A] [reg F] [reg E] [debug read memory 0xC002] [debug read memory 0xC600] [reg BC] [reg IX] [reg IY] [reg SP] [reg IFF] [expr {{round(([machine_info time]-$::started)*3579545)}}]"
            incr ::count;dispatch_shift
        }}}}
        dispatch_shift
    }}
}}]
after time 120 {{fail_shift watchdog}}
'''
    (out/'launch.tcl').write_text(tcl)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Shifts','-cart',str(rom),'-romtype','ASCII16','-script',str(out/'launch.tcl')],
        cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    (out/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('actual shift unit failed: '+(result.stdout+result.stderr)[-1000:])
    actual=[[int(v) for v in line.split()] for line in (out/'actual.tsv').read_text().splitlines()]
    verify_rows(cases,actual)
    if any(digest(ROOT/name)!=hash_ for name,hash_ in producer['utility_fingerprints'].items()):raise ValueError('shift unit producer changed')
    if not explore and snapshot_paths(HELPERS)!=producer:raise ValueError('shift unit revision changed')
    report={**producer,'complete':True,'exploratory':explore,'cases':len(cases),'variants':len(labels),'all_values':256,
            'observed_nz_masks':[0,1,2,3],'carry_inputs':[0,1],'overflow_inputs':[0,64],
            'max_cycles_including_rpc':max(r[-1] for r in actual),'rom_sha256':digest(rom),'emulator_sha256':digest(emulator),
            'profile_sha256':digest(user/'machines/Frostbite_Shifts.xml'),'canonical_ram_guard':True,
            'artifacts':{str(path.relative_to(out)):digest(path) for path in out.rglob('*') if path.is_file()},
            'scope':'Original-free synthetic microcartridge; actual standard MSX1 Z80, all shifted values/flags, preserved A/BC/IX/IY/SP/DI/V and untouched canonical RAM. Whole-original-CPU and paced-game acceptance remain separate.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--explore',action='store_true');args=p.parse_args()
    print(json.dumps(check(args.out,args.explore),indent=2))
