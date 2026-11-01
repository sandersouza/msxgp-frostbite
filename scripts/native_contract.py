"""Independent original CPU versus actual openMSX Z80 differential proof."""
import argparse
import copy
import hashlib
import inspect
from importlib.metadata import version
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import sys
from py65.devices.mpu6502 import MPU

from mechanics_probe import execute_slice
from reference_inventory import ROOT,verified_input
from reference_cpu_check import arithmetic_vectors
from native_build import OUT,ROM,BUILD_FILES,build_contract
from native_codegen import observable_stops
from reference_provenance import snapshot_paths
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*BUILD_FILES,'scripts/native_contract.py','scripts/native_contract.tcl','scripts/mechanics_probe.py',
    'scripts/reference_cpu_check.py','scripts/reference_provenance.py','scripts/reference_state.py','scripts/source_timing.py',
    'scripts/reference_traces.py','scripts/trace_compare.py','scripts/render_build.py','scripts/render_model.py','scripts/smoke.py','scripts/rom.py')))


def reference(rom,case):
    case=copy.deepcopy(case);case['watch']=[f'{a:02X}' for a in range(128,256)]
    result=execute_slice(rom,case)
    result['ram']=[int(result['ram'][f'{a:02X}'],16) for a in range(128,256)]
    return result


def compare(expected,actual):
    if len(expected['ram'])!=128 or len(actual['ram'])!=128:raise ValueError('complete128byte RAM required')
    for key in ('a','x','y','p','sp'):
        if expected['registers'][key]!=actual['registers'][key]:
            raise ValueError(f'CPU {key}: expected{expected["registers"][key]:02X} actual{actual["registers"][key]:02X}')
    for index,(want,got) in enumerate(zip(expected['ram'],actual['ram'])):
        if want!=got:raise ValueError(f'RAM {index+128:02X}: expected{want:02X} actual{got:02X}')


def validate_entry(registers):
    sp=registers.get('sp',255)
    if type(sp) is not int or not 0x86<=sp<=255:
        raise ValueError('native source SP requires86..FF for proved3level RAM stack')


def validate_receipt(receipt,count):
    if (receipt.get('complete') is not True or receipt.get('cases')!=count or receipt.get('heap_guard') is not True
            or receipt.get('stack_min',0)<0xF340 or receipt.get('clock_hz')!=3579545 or receipt.get('ram_bytes')!=65536):
        raise ValueError('incomplete/unsafe native CPU receipt')


def contact_environment(ram):
    result=bytearray(ram);result[0x30:0x38]=bytes(8);result[0x38:0x3A]=b'\xff\xff';result[0x6D]=0
    # Explicit fixture environment, not collision geometry or native detection.
    if result[0x6A]==0 and result[0x64] in (53,79,105,131):
        row=3-(result[0x64]-53)//26;result[0x30+row*2]=128
    return bytes(result)


def chains(rom):
    result=[]
    for variation in range(4):
        initial={'id':f'chain-{variation}-init','start':'FB3B','stops':['FB94'],
                 'registers':{},'ram':{'80':f'{variation:02X}','82':'01','81':'FC','C5':'00'}}
        previous=reference(rom,initial);result.append(initial)
        for tick in range(192):
            ram=contact_environment(bytes(previous['ram']))
            directions=15 if tick<80 else 13 if tick<115 else 11 if tick<140 else 14 if tick<175 else 7
            fire=0 if tick in range(120,125) else 255
            case={'id':f'chain-{variation}-{tick}','start':'F476','stops':['F019'],'chain':True,
                  'ram':{f'{i+128:02X}':f'{v:02X}' for i,v in enumerate(ram)},'registers':previous['registers'],
                  'mmio':{'0280':f'{directions*17:02X}','0282':'3F','0284':'00','000C':f'{fire:02X}','000D':f'{fire:02X}'},'limit':10000}
            previous=reference(rom,case);result.append(case)
    return result


def cases(rom,syms):
    source=json.loads((ROOT/'references/mechanics-cases.json').read_text())['cases']+arithmetic_vectors(rom)
    for index in range(256):
        source.append({'id':f'clear-{index}','start':'F004','stops':['F00C'],
            'registers':{'a':165,'x':index,'y':90,'p':0x71},
            'ram':{f'{a:02X}':f'{(a*37+11)&255:02X}' for a in range(128,256)},'limit':2000})
    for sp in (0x86,0x87,0xBE,0xFE,0xFF):
        source.append({'id':f'stack-map-{sp}','start':'FB3B','stops':['FB94'],'registers':{'sp':sp},
                       'ram':{'80':'03','82':'01','C5':'00'},'limit':10000})
    for index,sample in ((127,127),(128,255)):
        source.append({'id':f'rmw-hardware-wrap-{index}','start':'FFE2','stops':['FFE4'],
            'registers':{'a':85,'x':index,'p':49},'ram':{},'mmio':{f'{(0x96+index)&15:04X}':f'{sample:02X}'},'limit':2})
    values=(0,1,9,10,15,16,25,73,80,121,128,153,160,240,250,255)
    for operation,start,stop,address in (('adc','FB9B','FB9D','CA'),('sbc','FCF5','FCF7','F9')):
        for left in values:
            for right in values:
                for carry in (0,1):
                    for decimal in (0,1):
                        source.append({'id':f'flags-{operation}-{left}-{right}-{carry}-{decimal}',
                            'start':start,'stops':[stop],'registers':{'a':left,'p':0x30|carry|(decimal<<3)},
                            'ram':{address:f'{right:02X}'},'limit':2})
    template=next(c for c in source if c['id']=='jump-up-start')['ram']
    for player in (0,1):
        for variation in range(4):
            for directions in range(16):
                for fire in (0,255):
                    for phase in (0,7,254,255):
                        ram={**template,'80':f'{variation:02X}','81':f'{phase:02X}','C7':f'{player:02X}',
                             'B8':'FF','B9':'FF','B6':'80','E4':'35','F1':'00','EA':'00','C6':'00'}
                        source.append({'id':f'phase-{player}-{variation}-{directions}-{fire}-{phase}',
                            'start':'F476','stops':['F019'],'ram':ram,'registers':{},
                            'mmio':{'0280':f'{directions*17:02X}','0282':'3F','0284':'00','000C':f'{fire:02X}','000D':f'{fire:02X}'},'limit':10000})
    source+=chains(rom)
    return [c for c in source if 'core_'+c['start'] in syms and all('core_'+s in syms for s in c['stops'])]


def run_contract(selected=None,profile=False,explore=False):
    build=build_contract();rom=(ROOT/'references/roms/frostbite.bin').read_bytes();syms=symbols(OUT/'native.sym')
    if build['source_dirty'] and not explore:raise ValueError('canonical native proof requires clean committed producers; use --explore for WIP')
    if version('py65')!='1.2.0' or sys.byteorder!='little':raise ValueError('reviewed py65/little-endian host required')
    cpu_path=Path(inspect.getfile(MPU));cpu_hash=hashlib.sha256(cpu_path.read_bytes()).hexdigest()
    producer=snapshot_paths(HELPERS) if not explore else {'tool_source_commit':build['source_commit'],
        'utility_fingerprints':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in HELPERS}}
    selected=cases(rom,syms) if selected is None else selected
    if any(int(stop,16) not in observable_stops() for case in selected for stop in case['stops']):
        raise ValueError('native CPU stop not pinned for observable flags')
    expected=[reference(rom,c) for c in selected]
    if not selected:raise ValueError('native source cases required')
    directory=Path(tempfile.mkdtemp(prefix='contract-',dir=OUT));packed=bytearray()
    for case,want in zip(selected,expected):
        registers={'a':0,'x':0,'y':0,'p':0x30,'sp':255,**case.get('registers',{})};p=registers['p']
        validate_entry(registers)
        af=registers['a']*256+(p&128)+(64 if p&2 else 0)
        packed+=struct.pack('<HHHHBBBBB',syms['core_'+case['start']],syms['core_'+want['stop_pc']],af,
            registers['x']*256+registers['y'],p&1,p&0x3C,p&64,registers['sp'],int(case.get('chain',False)))
        ram=bytearray(128)
        for a,v in case.get('ram',{}).items():ram[int(a,16)-128]=int(v,16)
        reads=bytearray(24)
        for a,v in case.get('mmio',{}).items():
            a=int(a,16);index=(16+(a&7)) if a&0x200 else a&15;reads[index]=int(v,16)
        packed+=ram+reads
    (directory/'cases.bin').write_bytes(packed);(directory/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    emulator=shutil.which('openmsx') or '/Applications/openMSX.app/Contents/MacOS/openmsx'
    emulator_hash=hashlib.sha256(Path(emulator).read_bytes()).hexdigest()
    profile_data=isolated_profile(find_machine_profile(emulator));validate_machine_profile(profile_data)
    user=directory/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Native.xml').write_bytes(profile_data)
    settings=directory/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    trace={address:int(name[5:],16) for name,address in syms.items() if re.fullmatch('core_[0-9A-F]{4}',name) and name[5:]!='F019'} if profile else {}
    launcher=directory/'launch.tcl';launcher.write_text(f'set native_dir {{{directory}}}\nset rpc_start {syms["rpc_start"]}\n'
        +'array set source_labels {'+' '.join(f'{pc} {source}' for pc,source in trace.items())+'}\n'
        +f'source {{{ROOT/"scripts/native_contract.tcl"}}}\n')
    environment={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
    result=subprocess.run([emulator,'-setting',str(settings),'-machine','Frostbite_Native','-cart',str(ROM),'-romtype','Normal','-script',str(launcher)],
                          cwd=ROOT,env=environment,capture_output=True,text=True,timeout=120)
    (directory/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (directory/'complete.json').is_file():raise ValueError(f'native capture incomplete: {directory}; '+(result.stdout+result.stderr)[-600:])
    validate_receipt(json.loads((directory/'complete.json').read_text()),len(selected))
    data=(directory/'actual.bin').read_bytes();record_size=233
    if len(data)!=len(selected)*record_size:raise ValueError('incomplete native result records')
    max_cycles=0
    for index,(case,want) in enumerate(zip(selected,expected)):
        row=data[index*record_size:(index+1)*record_size]
        actual={'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])}
        try:compare(want,actual)
        except ValueError as error:raise ValueError(f'{case["id"]}: {error}; {directory}') from error
        shadow=bytearray(96)
        for write in want['hardware_writes']:
            address=int(write['address'],16);slot=(64+(address&31)) if address&0x200 else address&63
            shadow[slot]=int(write['value'],16)
        if row[133:229]!=shadow:raise ValueError(f'{case["id"]}: hardware write shadow differs; {directory}')
        max_cycles=max(max_cycles,struct.unpack('<I',row[229:233])[0])
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=build['rom_sha256'] or verified_input(ROOT/'references/roms/frostbite.bin')!=build['source']:
        raise ValueError('source/native binary changed during capture')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in producer['utility_fingerprints'].items()):raise ValueError('capture helper changed')
    if not explore and snapshot_paths(HELPERS)!=producer:raise ValueError('capture producer changed')
    if hashlib.sha256(cpu_path.read_bytes()).hexdigest()!=cpu_hash or hashlib.sha256(Path(emulator).read_bytes()).hexdigest()!=emulator_hash:
        raise ValueError('independent CPU/emulator binary changed')
    report={'cases':len(selected),'max_cycles':max_cycles,'rom_sha256':build['rom_sha256'],'build_source_commit':build['source_commit'],
            'build_dirty':build['source_dirty'],'directory':str(directory.relative_to(ROOT)),
            **producer,'harness_dirty':build['source_dirty'],'backend':{'py65':'1.2.0','cpu_source_sha256':cpu_hash,'emulator_sha256':emulator_hash,
                'profile_sha256':hashlib.sha256(profile_data).hexdigest()},
            'input_sha256':hashlib.sha256(packed).hexdigest(),'actual_sha256':hashlib.sha256(data).hexdigest(),
            'expected_sha256':hashlib.sha256((directory/'expected.json').read_bytes()).hexdigest()}
    (directory/'verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--explore',action='store_true')
    args=parser.parse_args();run_contract(explore=args.explore)
