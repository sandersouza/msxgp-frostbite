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

HELPERS=tuple(dict.fromkeys((*BUILD_FILES,'scripts/native_fast.py','scripts/native_analysis.py','scripts/native_contract.py','scripts/native_contract.tcl','scripts/mechanics_probe.py',
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
            case={'id':f'chain-{variation}-{tick}','start':'F476','stops':['F019'],'chain':tick>0,
                  'ram':{f'{i+128:02X}':f'{v:02X}' for i,v in enumerate(ram)},'registers':previous['registers'],
                  'mmio':{'0280':f'{directions*17:02X}','0282':'3F','0284':'00','000C':f'{fire:02X}','000D':f'{fire:02X}'},'limit':10000}
            previous=reference(rom,case);result.append(case)
    return result


def cases(rom,syms,phase_only=False):
    source=json.loads((ROOT/'references/mechanics-cases.json').read_text())['cases']+arithmetic_vectors(rom)
    source.append({'id':'cold-reset','start':'F000','stops':['F019'],'registers':{'a':165,'x':90,'y':75,'p':255},
                   'ram':{f'{a:02X}':f'{(a*37+11)&255:02X}' for a in range(128,256)},'limit':10000})
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
    if phase_only:source=[c for c in source if c['start'] in ('F000','F476')]
    missing=[c['id'] for c in source if 'core_'+c['start'] not in syms or any('core_'+s not in syms for s in c['stops'])]
    if missing:raise ValueError('native scope lost required source cases: '+','.join(missing))
    return source


def run_contract(selected=None,profile=False,explore=False,input_controls=None,corrupt_port2=False,fast_phase=False):
    build=build_contract(input_controls is not None,corrupt_port2,fast_phase);rom=(ROOT/'references/roms/frostbite.bin').read_bytes();syms=symbols(OUT/'native.sym')
    if build['source_dirty'] and not explore:raise ValueError('canonical native proof requires clean committed producers; use --explore for WIP')
    if version('py65')!='1.2.0' or sys.byteorder!='little':raise ValueError('reviewed py65/little-endian host required')
    cpu_path=Path(inspect.getfile(MPU));cpu_hash=hashlib.sha256(cpu_path.read_bytes()).hexdigest()
    helpers=HELPERS+('scripts/device_replay.py','scripts/native_input_check.py','src/native_input.asm') if input_controls is not None else HELPERS
    producer=snapshot_paths(helpers) if not explore else {'tool_source_commit':build['source_commit'],
        'utility_fingerprints':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in helpers}}
    default_cases=selected is None
    selected=cases(rom,syms,fast_phase) if default_cases else selected
    if fast_phase:
        filtered=[];reset_chain=True
        for case in selected:
            if case['start'] not in ('F000','F476'):
                if not default_cases:raise ValueError('fast phase only exposes F000/F476 entries')
                reset_chain=True;continue
            case=copy.deepcopy(case)
            if reset_chain:case['chain']=False
            reset_chain=False;filtered.append(case)
        selected=filtered
        from native_fast import validate_entries
        validate_entries(selected)
    if any(int(stop,16) not in observable_stops() for case in selected for stop in case['stops']):
        raise ValueError('native CPU stop not pinned for observable flags')
    expected=[reference(rom,c) for c in selected]
    if not selected:raise ValueError('native source cases required')
    directory=Path(tempfile.mkdtemp(prefix='contract-',dir=OUT));packed=bytearray()
    (directory/'native-contract.rom').write_bytes(ROM.read_bytes());(directory/'build.json').write_text(json.dumps(build,indent=2)+'\n')
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
    command=[emulator,'-setting',str(settings),'-machine','Frostbite_Native','-cart',str(ROM),'-romtype','Normal']
    environment={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
    device_setup=''
    if input_controls is not None:
        from device_replay import device_events,replay
        if len(input_controls)!=len(selected):raise ValueError('device event count mismatch')
        seed_script=directory/'seed.tcl';seed=directory/'seed.omr'
        seed_script.write_text(f'set renderer none\nset throttle off\nset power true\nplug joyporta msxjoystick1\nplug joyportb msxjoystick2\nreverse start\nafter time 1 {{reverse savereplay {{{seed}}};exit}}\n')
        seed_result=subprocess.run(command+['-script',str(seed_script)],cwd=ROOT,env=environment,capture_output=True,text=True,timeout=30)
        if seed_result.returncode or not seed.is_file():raise ValueError('device replay seed failed: '+seed_result.stderr)
        events=[]
        def event(time,tokens):events.append((time,'MSXCommandEvent',{'tokens':tokens}))
        def write(time,address,data):event(time,['debug','write_block','memory',str(address),data])
        write(5.001,0xD000,bytes([165])*0x2300);write(5.001,0xF300,bytes([165])*128)
        for i,(case,controls) in enumerate(zip(selected,input_controls)):
            time=6+i*.03;events+=device_events(time,controls);time+=.0002
            packet=packed[i*165:(i+1)*165];ram=packet[13:141]
            if case.get('chain'):
                write(time,0xC030,ram[48:58]);write(time,0xC06D,ram[109:110])
            else:
                write(time,0xC000,ram);write(time,0xC6F0,packet[4:9]);write(time,0xC600,bytes((packet[10],packet[9],packet[11])))
            write(time,0xC6FE,packet[:2]);write(time,0xC300,packet[141:157]);write(time,0xC340,packet[157:165]);write(time,0xC700,bytes(96))
            for address,byte in ((0xC340,packet[157]),(0xC342,packet[159]),(0xC30C,packet[153]),(0xC30D,packet[154])):write(time,address,bytes((255^byte,)))
            write(time,0xC6FD,b'\0');event(time,['debug','write','PSG regs','15',str((i*37)&255)])
            event(time,['debug','write_block','CPU regs','20',struct.pack('>H',syms['rpc_start'])])
        replay(seed,events,7+len(selected)*.03,directory/'devices.omr')
        device_setup=(f'set input_mode 1\nset input_entry {syms["sample_native_input"]}\nset input_return {syms["sample_native_return"]}\n'
            +f'set fire_return {syms["core_F5AD"]+3}\nset directions_return {syms["core_F630"]+3}\n'
            +f'reverse loadreplay -goto begin -viewonly {{{directory/"devices.omr"}}}\n')
    launcher=directory/'launch.tcl';launcher.write_text(f'set native_dir {{{directory}}}\nset rpc_start {syms["rpc_start"]}\nset idle {syms["idle"]}\nset input_mode 0\n'
        +device_setup
        +'array set source_labels {'+' '.join(f'{pc} {source}' for pc,source in trace.items())+'}\n'
        +f'source {{{ROOT/"scripts/native_contract.tcl"}}}\n')
    result=subprocess.run(command+['-script',str(launcher)],
                          cwd=ROOT,env=environment,capture_output=True,text=True,timeout=120)
    (directory/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (directory/'complete.json').is_file():raise ValueError(f'native capture incomplete: {directory}; '+(result.stdout+result.stderr)[-600:])
    receipt=json.loads((directory/'complete.json').read_text());validate_receipt(receipt,len(selected))
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
    if not explore and snapshot_paths(helpers)!=producer:raise ValueError('capture producer changed')
    if hashlib.sha256(cpu_path.read_bytes()).hexdigest()!=cpu_hash or hashlib.sha256(Path(emulator).read_bytes()).hexdigest()!=emulator_hash:
        raise ValueError('independent CPU/emulator binary changed')
    report={'cases':len(selected),'max_cycles':max_cycles,'rom_sha256':build['rom_sha256'],'build_source_commit':build['source_commit'],
            'fast_phase':fast_phase,'input_adapter':input_controls is not None,
            'build_dirty':build['source_dirty'],'directory':str(directory.relative_to(ROOT)),
            **producer,'harness_dirty':build['source_dirty'],'backend':{'py65':'1.2.0','cpu_source_sha256':cpu_hash,'emulator_sha256':emulator_hash,
                'profile_sha256':hashlib.sha256(profile_data).hexdigest()},
            'input_sha256':hashlib.sha256(packed).hexdigest(),'actual_sha256':hashlib.sha256(data).hexdigest(),
            'expected_sha256':hashlib.sha256((directory/'expected.json').read_bytes()).hexdigest(),'receipt':receipt}
    if input_controls is not None:
        from native_input_check import hardware
        mirrors=(directory/'mirrors.bin').read_bytes()
        if len(mirrors)!=4*len(selected) or receipt.get('input_samples',0)!=2*len(selected):raise ValueError('missing genuine input samples')
        for i,(case,controls) in enumerate(zip(selected,input_controls)):
            player=int(case['ram'].get('C7','00'),16)
            if tuple(mirrors[i*4:i*4+4])!=hardware(controls,player):raise ValueError(f'{case["id"]}: stale/incorrect hardware mirrors')
        report['device_replay_sha256']=hashlib.sha256((directory/'devices.omr').read_bytes()).hexdigest()
        report['mirrors_sha256']=hashlib.sha256(mirrors).hexdigest()
    (directory/'verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--explore',action='store_true')
    parser.add_argument('--fast-phase',action='store_true');args=parser.parse_args();run_contract(explore=args.explore,fast_phase=args.fast_phase)
