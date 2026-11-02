"""Actual-Z80 exact constructor-key and live-name-refcount microproof."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from environment import ROOT,verified_tool
from native_shift_check import HELPERS as BASE_FILES
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_fast_cache_check.py','src/presentation_fast_cache.asm')))
ROW_BYTES=8456

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES:raise ValueError('whole constructor-cache state row required')
    if actual!=expected:
        at=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
        raise ValueError(f'actual constructor/refcount/pixel cache differs at{at}')

def fixtures():
    operations=[(3,0,0,bytes(5))]
    key=lambda group,n:hashlib.sha256(f'exact constructor {group}:{n}'.encode()).digest()[:5]
    for group in range(6):
        for n in range(64):operations.append((0,group,0,key(group,n)))
        for n in range(0,64,7):operations.append((0,group,0,key(group,n)))
        operations.append((0,group,0,key(group,500)))
    for group in (3,4,5,0,1,2):
        base=64 if group>=3 else 0
        for n in range(0,64,2):
            operations.append((2,group,base+n,bytes(5)))
            if n%7==0:operations.append((2,group,base+n,bytes(5)))
            operations.append((2,group,base+n,bytes(5))) #underflow must preserve all live state
        for n in range(32):operations.append((0,group,0,key(group,n+1000)))
    operations.append((3,0,0,bytes(5)))
    collisions=[bytes(3)+bytes((n,(-2*n)&255)) for n in range(32)]
    operations.extend((0,0,0,k) for k in collisions+list(reversed(collisions)))
    operations.extend((1,0,0,bytes(5)) for _ in range(254))
    operations.extend((op,group,slot,bytes(5)) for op,group,slot in ((0,6,0),(0,255,0),(1,0,64),(2,3,0),(2,5,128),(2,1,0)))
    tables=[[] for _ in range(6)];refs=bytearray(384);keys=bytearray([165])*1920;pixels=bytearray([165])*6144
    inputs=bytearray();expected=bytearray()
    for op,group,identifier,k in operations:
        image=hashlib.sha256(b'constructor pixels'+k).digest()[:16]
        inputs.extend(bytes((op,group,identifier))+k+image);result=miss=0
        if op==3:tables=[[] for _ in range(6)];refs=bytearray(384)
        elif group>=6:result=255;miss=2
        elif op==0:
            slot=next((i for i,old in enumerate(tables[group]) if old==k),None)
            if slot is None:
                slot=next((i for i in range(64) if refs[group*64+i]==0),None)
                if slot is None:result=255;miss=2
                else:
                    miss=1
                    if slot==len(tables[group]):tables[group].append(k)
                    else:tables[group][slot]=k
                    at=group*320+slot*5;keys[at:at+5]=k
                    at=(group*64+slot)*16;pixels[at:at+16]=image
            if slot is not None:
                at=group*64+slot
                if refs[at]==255:result=255;miss=2
                else:refs[at]+=1;result=slot+(64 if group>=3 else 0)
        elif identifier>=128 or bool(identifier&64)!=(group>=3):result=255;miss=2
        else:
            at=group*64+(identifier&63)
            if op==1:
                if refs[at]==255:result=255;miss=2
                else:refs[at]+=1
            elif refs[at]==0:result=255;miss=2
            else:refs[at]-=1
        expected.extend(bytes((result,miss))+bytes(map(len,tables))+refs+keys+pixels)
    return bytes(inputs),bytes(expected)

def audit_saved(out):
    inputs,expected=fixtures();count=len(inputs)//24
    if (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('constructor-cache fixture/oracle changed')
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected):raise ValueError('incomplete constructor-cache actual matrix')
    for at in range(0,len(actual),ROW_BYTES):verify_row(actual[at:at+ROW_BYTES],expected[at:at+ROW_BYTES])
    times=[list(map(int,row.split())) for row in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered constructor-cache timing')
    if 'FAST_CACHE_FAIL' in (out/'emulator.log').read_text():raise ValueError('constructor-cache guard failure')
    return count,max(row[1] for row in times)

def check(out,explore=False):
    producer={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:digest(ROOT/name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);inputs,expected=fixtures();count=len(inputs)//24
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
ready:
    JP ready
unit_run:
    XOR A
    LD (pf_miss),A
    LD A,($C2F0)
    CP 3
    JP Z,p_fast_init
    CP 1
    JR Z,.add
    CP 2
    JR Z,.drop
    LD A,($C2F1)
    CALL p_fast_resolve
    RET C
    LD ($C2F3),A
    LD A,(pf_miss)
    CP 1
    CALL Z,p_fast_store
    LD A,($C2F3)
    LD C,A
    LD A,($C2F1)
    CALL p_fast_ref_add
    RET C
    LD A,($C2F3)
    RET
.add:
    LD A,($C2F2)
    LD C,A
    LD A,($C2F1)
    JP p_fast_ref_add
.drop:
    LD A,($C2F2)
    LD C,A
    LD A,($C2F1)
    JP p_fast_ref_drop
    INCLUDE "presentation_fast_cache.asm"
    DS $C000-$,$FF
'''
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compile=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compile.stdout+compile.stderr)
    if compile.returncode:raise ValueError('constructor-cache assembler failed: '+compile.stderr[-1500:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Fast_Cache.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set count 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_fast_cache {{message}} {{puts stderr "FAST_CACHE_FAIL $message case=$::count";exit 1;return -code error $message}}
proc dispatch_fast_cache {{}} {{
 if {{$::count=={count}}} {{close $::result;close $::timing;exit;return}}
 set row [string range $::cases [expr {{$::count*24}}] [expr {{$::count*24+23}}]]
 debug write_block memory 0xC2F0 [string range $row 0 2]
 set ::key [string range $row 3 7];set ::image [string range $row 8 23]
 debug write_block memory 0xCC90 $::key;debug write_block memory 0xCC80 $::image
 debug write_block memory 0xC760 [binary format cu* {{205 {syms['unit_run']&255} {syms['unit_run']>>8} 195 102 199 24 254}}]
 reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_fast_cache target}}
 debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
 debug write_block memory 0xCCA0 [string repeat [binary format c 0] 96]
 set ::slot [debug read ioports 168]
 debug set_bp 0xC766 {{}} {{debug break;after break {{
  if {{[debug read_block memory 0xC000 128] ne [string repeat [binary format c 165] 128] || [debug read_block memory 0xC600 256] ne [string repeat [binary format c 165] 256]}} {{fail_fast_cache source}}
  if {{[debug read_block memory 0xF180 0x1C0] ne [string repeat [binary format c 165] 0x1C0] || [debug read_block memory 0xEF80 512] ne [string repeat [binary format c 165] 512]}} {{fail_fast_cache guard-sprite-shadow}}
  if {{[debug read_block memory 0xCC90 5] ne $::key || [debug read_block memory 0xCC80 16] ne $::image || [debug read_block memory 0xCC95 11] ne [string repeat [binary format c 165] 11]}} {{fail_fast_cache input}}
  if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_fast_cache abi}}
  set row [binary format cu* [list [reg A] [debug read memory 0xCCA6]]]
  append row [debug read_block memory 0xCCA0 6] [debug read_block memory 0xC080 384] [debug read_block memory 0xE800 1920] [debug read_block memory 0xD000 6144]
  puts -nonewline $::result $row;puts $::timing "$::count [expr {{round(([machine_info time]-$::started)*3579545)}}]"
  incr ::count;dispatch_fast_cache
 }}}}
 dispatch_fast_cache
}}}}]
after time 60 {{fail_fast_cache watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Fast_Cache','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=120)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or 'FAST_CACHE_FAIL' in log:raise ValueError('constructor-cache emulator failed: '+log[-1500:])
    n,maximum=audit_saved(out)
    if any(digest(ROOT/name)!=value for name,value in producer['utility_fingerprints'].items()):raise ValueError('constructor-cache producer changed')
    if not explore and snapshot_paths(HELPERS)!=producer:raise ValueError('constructor-cache revision changed')
    report={'producer':producer,'exploratory':explore,'complete':True,'cases':n,'max_cycles_including_rpc':maximum,'rom_sha256':digest(artifact),
            'emulator_sha256':digest(emulator),'profile_sha256':hashlib.sha256(profile).hexdigest(),'artifacts':{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()},
            'scope':'Exact five-byte keys, live generation refcounts and full16-byte cache values; instrumented unit only, no constructor-injectivity or full-frame acceptance'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--explore',action='store_true')
    r=check(**vars(p.parse_args()));print(json.dumps({k:r[k] for k in ('complete','cases','max_cycles_including_rpc')}))
