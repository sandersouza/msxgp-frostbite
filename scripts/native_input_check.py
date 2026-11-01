"""Real emulated keyboard/standard-joystick input versus independent source CPU."""
import argparse
import json

from native_contract import run_contract,reference,contact_environment
from reference_inventory import ROOT,verified_input


def hardware(controls,player):
    if player not in (0,1):raise ValueError('original C7 requires0/1')
    r6,r8,j1,j2=controls
    keys=15^(((r8>>5)&3)|((r8>>2)&4)|((r8>>4)&8))
    ports=((15^(j1&15))<<4)|(15^(j2&15))
    ports&=(keys|240) if player else ((keys<<4)|15)
    fire=[0 if j&16 else 128 for j in (j1,j2)]
    if r8&1:fire[player]=0
    return ports,63^((r6>>5)&3),*fire


def source_case(identity,ram,controls,registers=None,chain=False):
    ports,console,f1,f2=hardware(controls,int(ram.get('C7','00'),16))
    return {'id':identity,'start':'F476','stops':['F019'],'ram':ram,'registers':registers or {},'chain':chain,
            'mmio':{'0280':f'{ports:02X}','0282':f'{console:02X}','0284':'00','000C':f'{f1:02X}','000D':f'{f2:02X}'},'limit':10000}


def fixtures(rom):
    template=next(c for c in json.loads((ROOT/'references/mechanics-cases.json').read_text())['cases'] if c['id']=='jump-up-start')['ram']
    cases=[];devices=[]
    for player in (0,1):
        for bits in range(16):
            for fire in (0,1):
                keys=((bits&1)<<5)|((bits&2)<<5)|((bits&4)<<2)|((bits&8)<<4)|fire
                for kind in ('keyboard','joystick'):
                    controls=(0,keys,0,0) if kind=='keyboard' else (0,0,(bits|fire*16) if not player else 0,(bits|fire*16) if player else 0)
                    for phase in (0,7,254,255):
                        ram={**template,'81':f'{phase:02X}','C7':f'{player:02X}','B8':'FF','B9':'FF','B6':'80','E4':'35','EA':'00','C6':'00','F1':'00'}
                        cases.append(source_case(f'{kind}-{player}-{bits}-{fire}-{phase}',ram,controls));devices.append(controls)
        for port in range(32):
            controls=(0,17,port,31^port);ram={**template,'C7':f'{player:02X}','C6':'00','F1':'00'}
            cases.append(source_case(f'mixed-{player}-{port}',ram,controls));devices.append(controls)
        for console in (0,32,64,96,128):
            controls=(console,0,0,0);ram={**template,'C7':f'{player:02X}','C6':'00','F1':'00'}
            cases.append(source_case(f'console-{player}-{console}',ram,controls));devices.append(controls)
    for variation in range(4):
        initial={'id':'init','start':'FB3B','stops':['FB94'],'registers':{},'ram':{'80':f'{variation:02X}','82':'01','81':'FC','C5':'00'}}
        previous=reference(rom,initial)
        for tick in range(192):
            ram=contact_environment(bytes(previous['ram']));ram={f'{i+128:02X}':f'{v:02X}' for i,v in enumerate(ram)}
            # Down, left, up, right; held/released/repressed fire; console hold/release.
            keys=0 if tick<40 else 64 if tick<75 else 16 if tick<110 else 32 if tick<145 else 128
            keys|=int(80<=tick<87 or 96<=tick<100)
            controls=(64 if 150<=tick<156 else 32 if 170<=tick<174 else 0,keys,0,0)
            case=source_case(f'device-chain-{variation}-{tick}',ram,controls,previous['registers'],tick>0)
            previous=reference(rom,case);cases.append(case);devices.append(controls)
    return cases,devices


def run(explore=False,negative=False,fast_phase=False):
    verified_input(ROOT/'references/roms/frostbite.bin');rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    cases,controls=fixtures(rom)
    return run_contract(cases,explore=explore,input_controls=controls,corrupt_port2=negative,fast_phase=fast_phase)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--explore',action='store_true');parser.add_argument('--negative',action='store_true')
    parser.add_argument('--fast-phase',action='store_true');args=parser.parse_args();run(args.explore,args.negative,args.fast_phase)
