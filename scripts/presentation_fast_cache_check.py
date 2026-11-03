"""Actual-Z80 exact constructor-key and live-name-refcount microproof."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from environment import ROOT,verified_tool
from presentation_cache_hash import table,hash_key,collisions
from native_shift_check import HELPERS as BASE_FILES
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_fast_cache_check.py','src/presentation_fast_cache.asm','scripts/presentation_cache_hash.py')))
ROW_BYTES=5048
SEMANTIC_BYTES=2696

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=SEMANTIC_BYTES:raise ValueError('complete constructor state and semantic oracle required')
    if actual[:SEMANTIC_BYTES]!=expected:
        at=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
        raise ValueError(f'actual constructor/refcount cache differs at{at}')
    counts=expected[2:8];refs=expected[8:392];keys=expected[392:2696]
    heads=actual[2696:4232];links=actual[4232:4616];used=actual[4616:4664];hashes=actual[4664:5048]
    bitmap=bytes(sum(1<<bit for bit in range(8) if refs[group*64+part*8+bit]) for group in range(6) for part in range(8))
    if used!=bitmap:raise ValueError('live-name reference bitmap differs')
    for group,count in enumerate(counts):
        seen=set()
        for bucket in range(256):
            node=heads[group*256+bucket]
            while node!=255:
                if node>=count or node in seen:raise ValueError('invalid/duplicate/cyclic cache chain')
                seen.add(node);key=keys[group*384+node*6:group*384+node*6+6]
                if hash_key(key)!=bucket or hashes[group*64+node]!=bucket:raise ValueError('cache key in wrong bucket')
                node=links[group*64+node]
        if seen!=set(range(count)):raise ValueError('unreachable constructor key')

def fixtures():
    operations=[(3,0,0,bytes(6))]
    key=lambda group,n:hashlib.sha256(f'exact constructor {group}:{n}'.encode()).digest()[:6]
    for group in range(6):
        for n in range(64):operations.append((0,group,0,key(group,n)))
        for n in range(0,64,7):operations.append((0,group,0,key(group,n)))
        operations.append((0,group,0,key(group,500)))
    for group in (3,4,5,0,1,2):
        base=64 if group>=3 else 0
        for n in range(0,64,2):
            operations.append((2,group,base+n,bytes(6)))
            if n%7==0:operations.append((2,group,base+n,bytes(6)))
            operations.append((2,group,base+n,bytes(6))) #underflow must preserve all live state
        for n in range(32):operations.append((0,group,0,key(group,n+1000)))
    operations.append((3,0,0,bytes(6)))
    same_bucket=collisions(32)
    operations.extend((0,0,0,k) for k in same_bucket+list(reversed(same_bucket)))
    operations.extend((1,0,0,bytes(6)) for _ in range(254))
    operations.extend((op,group,slot,bytes(6)) for op,group,slot in ((0,6,0),(0,255,0),(1,0,64),(2,3,0),(2,5,128),(2,1,0)))
    tables=[[] for _ in range(6)];refs=bytearray(384);keys=bytearray([165])*2304
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
                    at=group*384+slot*6;keys[at:at+6]=k
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
        expected.extend(bytes((result,miss))+bytes(map(len,tables))+refs+keys)
    return bytes(inputs),bytes(expected)

def audit_saved(out):
    inputs,expected=fixtures();count=len(inputs)//25
    if (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('constructor-cache fixture/oracle changed')
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*ROW_BYTES:raise ValueError('incomplete constructor-cache actual matrix')
    for index in range(count):verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*SEMANTIC_BYTES:(index+1)*SEMANTIC_BYTES])
    times=[list(map(int,row.split())) for row in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered constructor-cache timing')
    if 'FAST_CACHE_FAIL' in (out/'emulator.log').read_text():raise ValueError('constructor-cache guard failure')
    maxima={str(op):max(row[1] for i,row in enumerate(times) if inputs[i*25]==op) for op in range(4)}
    return count,max(row[1] for row in times),maxima

def check(out,explore=False,owned=False):
    producer={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:digest(ROOT/name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);inputs,expected=fixtures();count=len(inputs)//25
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected);(out/'cache-crc.bin').write_bytes(table())
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
    if owned:
        # Establish the renderer-only entry's documented precondition using
        # an independent six-shift group-root calculation. Invalid caller
        # groups/generations retain the original fully checked entry.
        entry=entry.replace('CALL p_fast_ref_add\n','CALL unit_add_owned\n').replace('JP p_fast_ref_add\n','JP unit_add_owned\n').replace('JP p_fast_ref_drop\n','JP unit_drop_owned\n')
        wrapper='''unit_add_owned:
    CALL unit_owned_base
    JP C,p_fast_ref_add
    JP p_fast_ref_add_owned
unit_drop_owned:
    CALL unit_owned_base
    JP C,p_fast_ref_drop
    JP p_fast_ref_drop_owned
unit_owned_base:
    LD B,A
    CP 6
    JR NC,.invalid
    LD A,C
    CP 128
    JR NC,.invalid
    LD A,B
    CP 3
    LD A,C
    JR C,.first
    CP 64
    JR C,.invalid
    JR .valid
.first:
    CP 64
    JR NC,.invalid
.valid:
    LD L,B
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$C080
    ADD HL,DE
    LD (pf_owned_refs),HL
    LD A,B
    OR A
    RET
.invalid:
    LD A,B
    SCF
    RET
'''
        entry=entry.replace('    INCLUDE "presentation_fast_cache.asm"',wrapper+'    INCLUDE "presentation_fast_cache.asm"')
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compile=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={out}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
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
 set row [string range $::cases [expr {{$::count*25}}] [expr {{$::count*25+24}}]]
 debug write_block memory 0xC2F0 [string range $row 0 2]
 set ::key [string range $row 3 8];set ::image [string range $row 9 24]
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
  if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40] || [debug read_block memory 0xE100 1792] ne [string repeat [binary format c 165] 1792]}} {{fail_fast_cache guard-sprite-shadow}}
  if {{[debug read_block memory 0xCC90 6] ne $::key || [debug read_block memory 0xCC80 16] ne $::image || [debug read_block memory 0xCC96 10] ne [string repeat [binary format c 165] 10]}} {{fail_fast_cache input}}
  if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_fast_cache abi}}
  set row [binary format cu* [list [reg A] [debug read memory 0xCCA6]]]
  append row [debug read_block memory 0xCCA0 6] [debug read_block memory 0xC080 384] [debug read_block memory 0xD000 2304] [debug read_block memory 0xDB00 1536] [debug read_block memory 0xD900 384] [debug read_block memory 0xCCB0 48] [debug read_block memory 0xCB00 384]
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
    n,maximum,maxima=audit_saved(out)
    if any(digest(ROOT/name)!=value for name,value in producer['utility_fingerprints'].items()):raise ValueError('constructor-cache producer changed')
    if not explore and snapshot_paths(HELPERS)!=producer:raise ValueError('constructor-cache revision changed')
    report={'producer':producer,'exploratory':explore,'complete':True,'owned_reference_entries':owned,'cases':n,'max_cycles_including_rpc':maximum,'operation_maxima_including_rpc':maxima,'operation_codes':{'0':'resolve+acquire','1':'acquire','2':'release','3':'cold init'},'rom_sha256':digest(artifact),
            'emulator_sha256':digest(emulator),'profile_sha256':hashlib.sha256(profile).hexdigest(),'artifacts':{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()},
            'scope':'Exact six-byte keys, live refs/bitmap and independent bucket/link/hash structure validation. Metadata-only allocator, no pixel shadow; constructor injectivity and native full pixels/frame gates remain separate'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--explore',action='store_true');p.add_argument('--owned',action='store_true')
    r=check(**vars(p.parse_args()));print(json.dumps({k:r[k] for k in ('complete','cases','max_cycles_including_rpc')}))
