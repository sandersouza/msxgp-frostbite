"""Controlled whole-ROM floe/entry/temperature cases using actual MSX keys.

Initial states are declared fixtures. Floe contacts come from original-clock
observations; odd/shore inputs are explicitly neutral while issue12 is pending.
These boundary cases are separate from the uninterrupted natural route.
"""
import argparse
import json
from pathlib import Path

from environment import ROOT
from floe_build import OUT
from floe_check import run_target
from floe_query import RawContacts
from floe_reference import visible_reference
from native_contract import reference
from reference_state import decode_state
from stella_floe import fixture,digest


def scenarios():
    return [
        ('first-white',{0xCD:255,0xF6:255},False,255,{'CD':0}),
        ('last-white',{0xCD:14,0xF6:255},False,255,{'CD':15}),
        ('build-before-fire',{0xCD:14,0xF6:255},True,255,{'CD':15,'direction_toggle':False}),
        ('blue-no-duplicate',{0xCD:0,0xAE:152,0xF6:255},False,255,{'CD':0}),
        ('reverse-cost',{0xCD:8,0xAE:152},True,255,{'CD':7,'direction_toggle':True}),
        ('reverse-completed-free',{0xCD:15,0xAE:152},True,255,{'CD':15,'direction_toggle':True}),
        ('held-fire',{0xCD:8,0xAE:152,0xAF:12},True,255,{'CD':8,'direction_toggle':False}),
        ('released-fire',{0xCD:8,0xAE:152,0xAF:12},False,255,{'CD':8,'direction_toggle':False}),
        ('no-block-fire',{0xCD:255,0xAE:152},True,255,{'CD':255,'direction_toggle':False}),
        ('air-fire',{0xCD:8,0xAE:152,0xEA:1},True,255,{'CD':8,'direction_toggle':False}),
        ('shore-fire',{0xCD:8,0xE4:27},True,255,{'CD':8}),
        ('rearm-boundary',{0xCD:8,**{a:152 for a in range(0xAB,0xAF)},0xF5:1},False,255,{'CD':8,'rows':12}),
        ('cooldown-remains',{0xCD:8,**{a:152 for a in range(0xAB,0xAF)},0xF5:2},False,255,{'CD':8,'rows':152}),
        ('completed-no-rearm',{0xCD:15,**{a:152 for a in range(0xAB,0xAF)},0xF5:0},False,255,{'CD':15,'rows':152}),
        ('landing-timeout-priority',{0xCD:255,0xF6:255,0xE5:1,0x81:255},False,255,{'CD':0,'E5':0,'F1':16}),
        *[(f'door-{x:02x}',{0xCD:15,0xE4:27,0xE6:x},False,239,{'entry':120<=x<=127}) for x in (119,120,127,128)],
        ('incomplete-door',{0xCD:14,0xE4:27,0xE6:123},False,239,{'entry':False}),
        *[(f'wrap-{x}-{direction}',{0xCD:0,0xCB:15,0xE4:27,**{a:x for a in range(0x9F,0xA3)},
                  **{a:16|direction for a in range(0x91,0x95)},**{a:15 for a in range(0x99,0x9C)}},False,255,{'wrap':(x,direction)})
          for x,direction in ((159,0),(0,64))]
    ]


def check(out,build_dir,catalog,initial_path,explore=False,inject='none'):
    out=Path(out);initial=decode_state(Path(initial_path).read_bytes());rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    reader=RawContacts(catalog);records=bytearray();expected=[];summary=[]
    for player in (0,1):
        for phase in (0,255):
            for name,patch,fire,keys,assertions in scenarios():
                if 0x81 in patch and patch[0x81]!=phase:continue
                ram=bytearray(fixture(initial['ram'],64,53,64,(0,128)))
                defaults={0x80:2+player,0x81:phase,0xC5:0,0xC6:0,0xC7:player,0xCB:0,0xCC:3,0xCD:0,
                          0xE7:0,0xEA:0,0xE9:0,0xED:0,0xF1:0,0xF2:255,0xF5:16,0xF6:0,0xAF:140,
                          **{a:12 for a in range(0xAB,0xAF)}}
                for address,value in {**defaults,**patch}.items():ram[address-128]=value
                contacts=reader.contacts(ram)
                if ram[0x64]==53 and not contacts['rows'][6]&128:raise ValueError('controlled floe landing lacks actual source overlap')
                visible=visible_reference(rom,ram,initial['cpu'],contacts)
                pins=keys if player==0 else ((keys>>4)|240)
                fires=[140,140];fires[player]=12 if fire else 140
                case={'id':f'{name}-p{player}-phase{phase}','start':'F476','stops':['F019'],'registers':visible['registers'],
                      'ram':{f'{i+128:02X}':f'{value:02X}' for i,value in enumerate(visible['ram'])},'limit':12000,
                      'mmio':{'0280':f'{pins:02X}','0282':'3F','0284':'00','000C':f'{fires[0]:02X}','000D':f'{fires[1]:02X}'}}
                want=reference(rom,case);after=want['ram']
                for field,value in assertions.items():
                    if field=='direction_toggle':valid=bool((ram[0x14]^after[0x14])&64)==value
                    elif field=='rows':valid=after[0x2B:0x2F]==[value]*4
                    elif field=='entry':valid=bool(after[0x69]&128)==value
                    elif field=='wrap':valid=after[0x1F]<8 if value==(159,0) else after[0x1F]>=152
                    else:valid=after[int(field,16)-128]==value
                    if not valid:raise ValueError(f'original semantic expectation failed: {case["id"]}/{field}: '+str({f'{a:02X}':after[a-128] for a in (0x91,0x94,0x9F,0xCD,0xE5,0xE9,0xEA,0xF1,0xF5)}))
                records.extend(ram);records.extend(initial['cpu'][key] for key in ('a','x','y','p','sp'));records.extend((keys,63,int(fire)))
                expected.append(want);summary.append({'id':case['id'],'assertions':assertions,'after':{f'{a:02X}':after[a-128] for a in (0x94,0x9F,0xCD,0xE5,0xE9,0xF1,0xF5)}})
    report,_=run_target(out,build_dir,bytes(records),expected,explore=explore,step_fixture=True,inject=inject,extra_helpers=('scripts/floe_mechanics.py',))
    report.update(scenarios=summary,source_catalog_sha256=digest(Path(catalog)/'catalog.json'),
                  scope='Controlled initial states, actual MSX keyboard/button input, original-clock floes and complete original-instruction CPU/RAM comparison. Explicit neutral odd/shore channels; natural route is separate.')
    (out/'mechanics.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--build-dir',type=Path,default=OUT)
    parser.add_argument('--catalog',type=Path,required=True);parser.add_argument('--initial',type=Path,required=True);parser.add_argument('--explore',action='store_true')
    parser.add_argument('--inject',choices=('none','port2_fire'),default='none')
    args=parser.parse_args();r=check(args.out,args.build_dir,args.catalog,args.initial,args.explore,args.inject);print(json.dumps({'cases':r['cases'],'max_native_cycles':r['max_native_cycles']}))
