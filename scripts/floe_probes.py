"""Bounded original electrical-contact and visible-state differential probes."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import tempfile

from floe_capture import ROOT,OUT,HELPERS as RASTER_HELPERS,new_ale,load_catalog,sha
from floe_model import visible_state,floe_contacts
from floe_reference import visible_reference
from native_contract import reference,compare
from reference_inventory import verified_input
from reference_provenance import snapshot_paths
from reference_traces import poweron_capsule,run_debugger
from reference_state import decode_state

HELPERS=tuple(dict.fromkeys((*RASTER_HELPERS,'scripts/floe_probes.py','scripts/floe_reference.py',
    'scripts/native_contract.py','scripts/mechanics_probe.py','scripts/reference_traces.py',
    'scripts/reference_state.py','scripts/source_timing.py','scripts/trace_compare.py')))


def ram_commands(ram):
    if len(ram)!=128:raise ValueError('full128byte fixture required')
    return [f'ram #{i+128} #{v}' for i,v in enumerate(ram)]


def geometry_cases():
    for phase,x,px in itertools.product(range(16),range(160),range(160)):
        yield phase,x,px,53,0,0,0
    for row,pose,reflect,shift,dy,px,phase in itertools.product(range(4),range(6),range(2),(0,1,18),
            (-20,-19,-18,-1,0,1,6,7,8),(0,1,7,8,14,15,16,151,152,158,159),(0,3,8,15)):
        yield phase,(px+phase*7+dy*3)%160,px,131-row*26+dy,pose,reflect,shift


def electrical(directory,catalog_dir,producer):
    directory=Path(directory);directory.mkdir();rom=(ROOT/'references/roms/frostbite.bin').read_bytes();catalog=load_catalog(catalog_dir)
    runs=[];count=0
    for repeat in range(2):
        ale=new_ale();initial=ale.cloneSystemState();(directory/f'initial-{repeat}.state').write_bytes(initial.serialize())
        count=0
        with (directory/f'actual-{repeat}.bin').open('wb') as actual_file,(directory/f'state-hashes-{repeat}.bin').open('wb') as hashes:
            for phase,x,px,y,pose,reflect,shift in geometry_cases():
                ale.restoreSystemState(initial);shape=rom[0xDE0+phase]
                patch={0xC5:0,0xC6:0,0xE7:127,0xCB:0,0xE4:y,0xE6:px,0xEB:shift,0xEE:pose,0xEC:reflect*8,0xF0:0,
                    0x9E:phase,0x9C:shape<<4&255,0x9D:shape&240,**{0x9F+i:x for i in range(4)}}
                for a,v in patch.items():ale.setRAM(a&127,v)
                before=bytes(ale.getRAM());want=floe_contacts(rom,before,catalog)
                ale.act(0);actual=bytes(ale.getRAM());got=actual[0x30:0x38]
                if any(actual[a&127]!=v for a,v in patch.items() if a!=0xE7):raise ValueError(f'geometry changed atcase{count}:{phase,x,px,y,pose,reflect,shift}')
                if got[::2]!=want[::2]:raise ValueError(f'actual electrical contact differs atcase{count}:{phase,x,px,y,pose,reflect,shift}: {want.hex()} / {got.hex()}')
                actual_file.write(actual);hashes.write(hashlib.sha256(ale.cloneSystemState().serialize()).digest());count+=1
                if count%100000==0:print(f'Original electrical repeat{repeat+1}: {count}cases',flush=True)
        runs.append({'actual_sha256':sha((directory/f'actual-{repeat}.bin').read_bytes()),
            'state_hashes_sha256':sha((directory/f'state-hashes-{repeat}.bin').read_bytes())})
    if runs[0]!=runs[1]:raise ValueError('independent electrical/full-state executions differ')
    return {'cases':count,'independent_runs':2,'all_four_floe_bytes_equal':True,'runs':runs,
        'catalog_sha256':sha((Path(catalog_dir)/'catalog.json').read_bytes()),'catalog_directory':str(Path(catalog_dir).relative_to(ROOT)),**producer}


def phase_cases(rom):
    initial=reference(rom,{'id':'cold','start':'F000','stops':['F019'],'ram':{},'registers':{},'limit':10000})
    rng=random.Random(11)
    for i in range(1500):
        ram=bytearray(initial['ram']);regs={'a':rng.randrange(256),'x':rng.randrange(256),'y':rng.randrange(256),'p':0x30|rng.randrange(2)*4,'sp':255}
        for a in (0x81,0x82,0xC5,0xC6,0xCB,0xCD,0xEC):ram[a-128]=rng.randrange(256)
        ram[0x64]=rng.randrange(150);ram[0x66]=rng.randrange(160);ram[0x6E]=rng.randrange(6);ram[0x6B]=rng.randrange(19)
        contacts={'rows':bytes(7|rng.randrange(2)*128 for _ in range(8)),'shore':7|rng.randrange(2)*128}
        yield ram,regs,contacts


def phases(directory,producer):
    directory=Path(directory);directory.mkdir();rom=(ROOT/'references/roms/frostbite.bin').read_bytes();rows=[]
    for ram,regs,contacts in phase_cases(rom):
        want=visible_reference(rom,ram,regs,contacts);got=visible_state(rom,ram,regs,contacts);compare(want,got)
        rows.append({'before':list(ram),'registers':regs,'contacts':{**contacts,'rows':list(contacts['rows'])},
            'after':list(want['ram']),'after_registers':want['registers'],'instructions':want['instructions'],
            'write_set':sorted({offset+128 for _,offset,_ in want['ram_writes']})})
    (directory/'cases.json').write_text(json.dumps(rows)+'\n')
    return {'cases':len(rows),'all_cpu_and_128ram_equal':True,'cases_sha256':sha((directory/'cases.json').read_bytes()),**producer}


def stella_phases(directory,catalog_dir,producer):
    directory=Path(directory);directory.mkdir();rom_path=ROOT/'references/roms/frostbite.bin';rom=rom_path.read_bytes();catalog=load_catalog(catalog_dir)
    capsule,backend=poweron_capsule(rom_path,directory/'poweron')
    states,_=run_debugger(rom_path,'base dec\nloadState 0\nrunToPc $f019\nsaveState 0\nexitRom\n',directory/'cold',capsule)
    initial=states[0];base=decode_state(initial);cases=[]
    for phase,row,px in itertools.product(range(16),range(4),(0,7,15,64,151,159)):
        r=bytearray(base['ram']);shape=rom[0xDE0+phase];x=(px+phase*7+row*19)%160
        patch={0xC5:0,0xCB:phase%16,0xCD:(0,14,15,255)[phase%4],0xE4:131-row*26,
            0xE6:px,0xEE:phase%6,0xEC:(phase%2)*8,0xEB:phase%19,0xC6:phase*13&255,
            0x9E:phase,0x9C:shape<<4&255,0x9D:shape&240,**{0x9F+i:x for i in range(4)}}
        for a,v in patch.items():r[a-128]=v
        cases.append(bytes(r))
    records=[]
    for offset in range(0,len(cases),5):
        commands=['base dec']
        for i,ram in enumerate(cases[offset:offset+5]):
            commands+=['loadState 0']+ram_commands(ram)+[f'saveState {i*2}','runToPc $f476',f'saveState {i*2+1}']
        commands+=['exitRom',''];states,current_backend=run_debugger(rom_path,'\n'.join(commands),directory/f'batch-{offset:04d}',initial)
        if current_backend!=backend:raise ValueError('Stella backend changed')
        if set(states)!=set(range(len(cases[offset:offset+5])*2)):raise ValueError('missing visible phase checkpoints')
        for i,ram in enumerate(cases[offset:offset+5]):
            before=decode_state(states[i*2]);after=decode_state(states[i*2+1])
            if before['cpu']['pc']!=0xF019 or bytes(before['ram'])!=ram or after['cpu']['pc']!=0xF476:raise ValueError('Stella phase boundary/input differs')
            contacts={'rows':bytes(after['ram'][0x30:0x38]),'shore':after['ram'][0x6D] if after['ram'][0x6D]&128 else 7}
            expected={'ram':after['ram'],'registers':{k:after['cpu'][k] for k in ('a','x','y','p','sp')}}
            compare(expected,visible_state(rom,ram,before['cpu'],contacts))
            compare(expected,visible_reference(rom,ram,before['cpu'],contacts))
            if floe_contacts(rom,ram,catalog)[::2]!=contacts['rows'][::2]:raise ValueError(f'Stella floe contact differs case{offset+i}')
            records.append({'index':offset+i,'before_sha256':sha(states[i*2]),'after_sha256':sha(states[i*2+1]),'contacts':list(contacts['rows'])})
    (directory/'cases.json').write_text(json.dumps(records,indent=2)+'\n')
    return {'cases':len(records),'independent_backend':backend,'all_cpu_and_128ram_equal':True,
        'all_four_floe_bytes_equal':True,'cases_sha256':sha((directory/'cases.json').read_bytes()),**producer}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('phase','electrical','stella'));parser.add_argument('--catalog',type=Path)
    parser.add_argument('--explore',action='store_true');args=parser.parse_args();source=verified_input(ROOT/'references/roms/frostbite.bin')
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
    if dirty and not args.explore:raise ValueError('commit canonical probe producers first')
    producer=snapshot_paths(HELPERS) if not args.explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{p:sha((ROOT/p).read_bytes()) for p in HELPERS}}
    producer|={'source':source,'explore':args.explore,'source_dirty':dirty}
    OUT.mkdir(parents=True,exist_ok=True);directory=Path(tempfile.mkdtemp(prefix=args.command+'-',dir=OUT))/'raw'
    result=phases(directory,producer) if args.command=='phase' else (electrical if args.command=='electrical' else stella_phases)(directory,args.catalog,producer)
    (directory/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(f'Passed {result["cases"]} {args.command} cases: {directory}')
