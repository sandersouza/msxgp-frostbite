"""Cross-check original-clock sidecars, complete phase state and cached windows.

All controlled cases and independent unmodified-backend snapshots stay local.
This is electrical research evidence, not natural gameplay acceptance.
"""
import argparse
import json
from pathlib import Path
import random
import subprocess

from environment import ROOT
from floe_model import visible_state
from floe_truth import full_record,roi_record,sample,view_index
from native_contract import compare
from reference_state import decode_state
from reference_traces import run_debugger,private_output
from stella_floe import control_pairs,digest,fixture,observe

CHECK_HELPERS=('scripts/floe_observer_check.py','scripts/floe_model.py','scripts/native_contract.py')


def check(out,binary,initial_path):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    initial=Path(initial_path).read_bytes();base=decode_state(initial);rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    checker_helpers={name:digest(ROOT/name) for name in CHECK_HELPERS}
    rng=random.Random(111);cases=[];links=[];blanks=[];controls=control_pairs(rom)
    def add(px,y,fx,pair,extra=None):
        ram=bytearray(fixture(base['ram'],px,y,fx,pair))
        for address,value in (extra or {}).items():ram[address-128]=value
        cases.append(bytes(ram));return len(cases)-1
    # All228 actual pose/shift/reflection tuples, not merely their projections.
    for view in range(228):
        add((0,1,7,8,9,15,64,151,152,158,159)[view%11],rng.randrange(256),rng.randrange(160),controls[view%len(controls)],
            {0xEE:view//38,0xEB:view%38//2,0xEC:(view%2)*8})
    for group in range(120):
        px=(0,1,7,8,9,15,64,151,152,158,159)[group%11];pair=controls[group%len(controls)];fx=rng.randrange(160);dy=rng.randrange(-8,25)
        anchor=add(px,53+dy,fx,pair)
        for row in range(4):
            view=(group*4+row)%228
            extra={0xEE:view//38,0xEB:view%38//2,0xEC:(view%2)*8,0xF0:rng.randrange(4),0xE8:rng.randrange(256),0xEF:rng.randrange(256),0xC6:rng.randrange(256)}
            variant=add(px,131-row*26+dy,fx,pair,extra);links.append((anchor,variant,row,'view/row'))
        extra={**{0xD8+j:rng.randrange(8) for j in range(4)},**{0xD4+j:rng.randrange(160) for j in range(4)},
               **{0xA3+j:rng.randrange(256) for j in range(4)},**{0x91+j:rng.randrange(256) for j in range(4)}}
        links.append((anchor,add(px,53+dy,fx,pair,extra),3,'objects'))
        for c5,cb,cd in ((0,0,15),(0,4,15),(128,4,15),(0,2,255)):
            links.append((anchor,add(px,53+dy,fx,pair,{0xC5:c5,0xCB:cb,0xCD:cd}),3,'header'))
        blanks.append(add(px,53+dy,fx,pair,{0xBF:128}))
    for group,px in enumerate((0,1,7,8,9,64,151,152,158,159,14,143)):
        fx=rng.randrange(160);pair=controls[group%len(controls)];anchor=add(px,0,fx,pair)
        for y in range(256):
            variant=add(px,y,fx,pair)
            if not 45<=y<=77:links.append((anchor,variant,3,'outsideY'))
    data,receipt=observe(ROOT/'references/roms/frostbite.bin',binary,initial,cases,out/'full')
    records=[full_record(data[i*384:(i+1)*384]) for i in range(len(cases))]
    for a,b,row,kind in links:
        if records[a]['truth'][3]!=records[b]['truth'][row]:raise ValueError(f'{kind} invariant failed: {a},{b},{row}')
    for index in blanks:
        if any(any(row) for row in records[index]['truth']):raise ValueError('VBLANK source contact suppression failed')
    for ram,record in zip(cases,records):
        view=view_index(ram[0x6E],ram[0x6B],bool(ram[0x6C]&8))
        for row in range(4):
            if sample(record['truth'][row],view)!=record['ram'][0x30+row*2]:raise ValueError('literal actual-view latch mismatch')
        contacts={'rows':record['ram'][0x30:0x38],'shore':record['ram'][0x6D] if record['ram'][0x6D]&128 else 7}
        compare(record,visible_state(rom,ram,base['cpu'],contacts))
    # Independent original Stella: source ROM and unmodified backend only.
    for index in range(0,224,7):
        ram=cases[index];source=bytearray(initial);offset=base['_offsets']['ram'];source[offset:offset+128]=ram
        states,_=run_debugger(ROOT/'references/roms/frostbite.bin','loadState 0\nsaveState 1\nrunToPc $f476\nsaveState 2\nexitRom\n',out/f'original-{index:03d}',bytes(source))
        before=decode_state(states[1]);after=decode_state(states[2])
        if bytes(before['ram'])!=ram:raise ValueError('independent before-RAM identity mismatch')
        compare({'ram':after['ram'],'registers':{key:after['cpu'][key] for key in ('a','x','y','p','sp')}},records[index])
    roi_cases=[fixture(base['ram'],px,y,rng.randrange(160),controls[i%len(controls)])
               for px,y in ((0,53),(159,53),(64,50),(64,74),(8,65),(151,45)) for i in range(128)]
    full,full_receipt=observe(ROOT/'references/roms/frostbite.bin',binary,initial,roi_cases,out/'cache-full')
    roi,roi_receipt=observe(ROOT/'references/roms/frostbite.bin',binary,initial,roi_cases,out/'cache-roi',roi=True)
    for index in range(len(roi_cases)):
        a=full_record(full[index*384:(index+1)*384]);b=roi_record(roi[index*78:(index+1)*78])
        if a['truth'][3]!=b['truth'] or a['ram'][0x36]!=b['actual'] or a['glyph']!=b['glyph']:
            raise ValueError('cached original prefix/window differs from complete execution')
    if checker_helpers!={name:digest(ROOT/name) for name in CHECK_HELPERS}:raise ValueError('observer checker changed during verification')
    result={'schema_version':1,'cases':len(cases),'actual_views':228,'invariant_links':len(links),'checker_helpers':checker_helpers,
            'independent_unmodified_stella_phases':32,'cached_window_comparisons':len(roi_cases),
            'binary_sha256':digest(binary),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'checker_sha256':digest(__file__),'observations':[receipt,full_receipt,roi_receipt],
            'limitations':'Controlled geometry, not natural route or MSX acceptance; sound disabled'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--initial',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(check(args.out,args.binary,args.initial),indent=2))
