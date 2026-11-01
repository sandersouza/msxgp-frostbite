"""Controlled whole-ROM interaction cases with actual original-clock contacts.

Each declared initial state is a fixture. No contact/expected-state injection
occurs inside a native phase; input-only continuous routes are separate proof.
"""
import argparse
import json
from pathlib import Path

from environment import ROOT
from floe_model import visible_state
from floe_reference import visible_reference
from hazard_build import OUT
from hazard_check import run_target
from hazard_query import RawContacts
from native_contract import compare,reference
from reference_state import decode_state
from stella_floe import fixture,digest


def validate_effect(kind,before,after,contacts,row):
    if kind=='differential':return
    if kind in ('water','temperature'):
        valid=(after[0x71]&128 and before[0x64]>27 and before[0x6A]==0) if kind=='water' else (after[0x71]&16 and before[0x65]==1 and after[0x65]==0)
        if not valid:raise ValueError('distinct original water/temperature death cause required')
        return
    if kind in ('bear-push','bear-safe'):
        if not contacts['shore']&128:raise ValueError('actual fresh bear contact required')
        expected=before[0x66]-1 if kind=='bear-push' else before[0x66]
        if after[0x66]!=expected:raise ValueError('bear stage/airborne movement boundary differs')
        return
    if not contacts['rows'][row*2+1]&128:raise ValueError('actual odd-window contact required')
    if kind=='fish':
        old,new=before[0x5C+row],after[0x5C+row]
        if (after[0x77]!=before[0x77]+1 or new&~old or (old^new).bit_count()!=1
                or after[0x74]!=91 or after[0x67]!=16):raise ValueError('one fish segment and delayed-envelope entry required')
    elif kind=='airborne':
        if after[0x72]!=before[0x72] or after[0x77]!=before[0x77]:raise ValueError('airborne contact must not attach/collect')
    elif kind=='threat':
        if after[0x72]!=row or after[0x77]!=before[0x77]:raise ValueError('threat attachment must select the actual row')
    else:raise ValueError('known controlled contact effect required')


def original_step(rom,ram,registers,reader,keys=255):
    contacts=reader.contacts(ram);visible=visible_reference(rom,ram,registers,contacts)
    compare(visible,visible_state(rom,ram,registers,contacts))
    pins=keys if ram[0x47]==0 else (keys>>4)|240
    case={'id':'controlled-hazard','start':'F476','stops':['F019'],'registers':visible['registers'],
          'ram':{f'{i+128:02X}':f'{v:02X}' for i,v in enumerate(visible['ram'])},'limit':12000,
          'mmio':{'0280':f'{pins:02X}','0282':'3F','0284':'00','000C':'8C','000D':'8C'}}
    return reference(rom,case),contacts


def interaction_cases(base,rom,reader):
    """All rows/kinds, both controllers, three nonzero RNG seeds, six stages."""
    result=[]
    # First case is a grounded row3 fish; all four live mutation controls
    # have an effective, independently computed source comparison here.
    for player in (0,1):
        for seed in (1,0x5A,0xA5):
            for phase in (0,255):
                for row in (3,2,1,0):
                    for kind in (1,0,2,3):
                        for airborne in (0,1):
                            stage=(3,4,15,20,0,2)[(seed+row+kind+phase)%6]
                            r=bytearray(fixture(base['ram'],64,53+(3-row)*26,64,(0,128)))
                            patch={0x80:2+player,0x81:phase,0x82:seed,0xC5:0,0xC6:0,0xC7:player,
                                   0xCB:stage,0xCC:3,0xCD:15,0xE7:0,0xEA:airborne,0xE9:0,0xED:0,
                                   0xF1:0,0xF2:255,0xF4:0,0xF5:16,0xF6:0,0xF7:12 if phase else 0,0xAF:140,
                                   **{a:152 for a in range(0xAB,0xAF)}}
                            patch.update({0x91+row:kind|64|(128 if player else 0),
                                          0xA3+row:rom[0xD0A+kind*2],0xDC+row:1,0xD8+row:0})
                            for address,value in patch.items():r[address-128]=value
                            hit=None
                            for x in (64,63,65,62,66,61,67,60,68):
                                r[0x54+row]=x;r[0x60+row]=(x-32)%160
                                if reader.contacts(r)['rows'][row*2+1]&128:hit=bytes(r);break
                            if hit is None:raise ValueError('controlled source geometry has no real object hit')
                            effect='airborne' if airborne else 'fish' if kind==1 else 'threat'
                            result.append((f'{effect}-row{row}-kind{kind}-p{player}-seed{seed}-phase{phase}-stage{stage}',hit,effect,row))
    return result


def boundary_cases(base,rom,reader,template):
    result=[]
    for player in (0,1):
        for stage in (2,3):
            for airborne in (0,1):
                r=bytearray(template)
                for address,value in {0x80:2+player,0xC7:player,0xCB:stage,0xE4:27,0xEA:airborne,0xEF:0,0xEC:0}.items():r[address-128]=value
                for x in range(55,74):
                    r[0x68]=x
                    if reader.contacts(r)['shore']&128:break
                else:raise ValueError('bear boundary has no original shore hit')
                kind='bear-push' if stage==3 and airborne==0 else 'bear-safe'
                result.append((f'{kind}-stage{stage}-air{airborne}-p{player}',bytes(r),kind,3))
        for kind in ('water','temperature'):
            r=bytearray(template);r[0x47]=player;r[0]=2+player;r[1]=255;r[0x65]=1
            if kind=='water':
                r[0x64]=79
                for x in range(160):
                    r[0x1F:0x23]=bytes([x])*4
                    if not any(v&128 for v in reader.contacts(r)['rows'][::2]):break
                else:raise ValueError('water boundary must have no actual source floe contact')
                r[0x11:0x15]=bytes(4);r[0x23:0x27]=bytes(4);r[0x54:0x58]=bytes(4)
            result.append((f'{kind}-p{player}',bytes(r),kind,3))
    for seed in range(256):
        r=bytearray(template);r[2]=seed;r[1]=0
        result.append((f'full-phase-rng-seed{seed:02x}',bytes(r),'differential',3))
    return result


def check(out,build_dir,reader,initial_path,explore=False,inject='none'):
    base=decode_state(Path(initial_path).read_bytes());rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    records=bytearray();expected=[];summary=[]
    cases=interaction_cases(base,rom,reader)
    cases.extend(boundary_cases(base,rom,reader,cases[0][1]))
    for name,ram,effect,row in cases:
        want,contacts=original_step(rom,ram,base['cpu'],reader)
        try:validate_effect(effect,ram,want['ram'],contacts,row)
        except ValueError as error:
            raise ValueError(f'{name}: {error}; '+str({f'{a:02X}':(ram[a-128],want['ram'][a-128]) for a in (0xB8,0xB9,0xDC+row,0xEA,0xF1,0xF2,0xF4,0xF7)})) from error
        records.extend(ram);records.extend(base['cpu'][key] for key in ('a','x','y','p','sp'));records.extend((255,63,0))
        expected.append(want);summary.append({'id':name,'effect':effect,'row':row,'actual_contacts':list(contacts['rows']),
             'fields':{f'{a:02X}':want['ram'][a-128] for a in (0x82,0xB8,0xB9,0xE6,0xE7,0xEA,0xF1,0xF2,0xF4,0xF7)}})
    reader.verify_consumed()
    report,_=run_target(out,build_dir,bytes(records),expected,step_fixture=True,explore=explore,inject=inject,
                         additional_helpers=('scripts/hazard_mechanics.py','scripts/floe_reference.py','scripts/floe_model.py'))
    report.update(scenarios=summary,initial_sha256=digest(initial_path),
                  scope='Controlled declared initial RAM per case, actual native acquisition and physical keyboard sampling, complete original-instruction CPU/all128RAM equality. Both players, all rows/kinds, grounded/airborne, three seeds/six stages, bear2/3, water/temperature and all256 RNG phase seeds. Continuous reward/push/death routes and paced/manual/physical acceptance are separate.')
    (Path(out)/'mechanics.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--build-dir',type=Path,default=OUT)
    for name in ('floes','edge','ordinary','shore','initial'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--explore',action='store_true');p.add_argument('--inject',choices=('none','collision','rng','row_priority','sticky'),default='none');args=p.parse_args()
    r=check(args.out,args.build_dir,RawContacts(args.floes,args.edge,args.ordinary,args.shore),args.initial,args.explore,args.inject)
    print(json.dumps({'cases':r['cases'],'max_native_cycles':r['max_native_cycles']}))
