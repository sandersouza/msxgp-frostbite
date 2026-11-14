"""Compare the native P0 cache SAT writer against sealed control and byte oracle."""
import argparse
import json
from pathlib import Path
from compact_native_fixture import run,sha
from native_flat_asm import assemble
from environment import ROOT
from render_build import symbols


def check(base,delivery,out):
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((delivery/'native-delivery-build.json').read_bytes())
    cartridge=delivery/'cartridge/FROSTBIT.ROM'
    if sha(cartridge)!=m['files']['cartridge/FROSTBIT.ROM']['sha256'] or cartridge.stat().st_size!=32768:
        raise ValueError('exact selected native cartridge required')
    linked=json.loads((delivery/'linked/native-link.json').read_bytes());image=(delivery/'linked/native-image.bin').read_bytes()
    if sha(delivery/'linked/native-image.bin')!=linked['image_sha256']:raise ValueError('bound native code required')
    s=symbols(base/'presentation.sym');old=(ROOT/'src/presentation_player_bands.asm').read_text()
    body=old[old.index('ao_cache_entry:'):old.index('    ASSERT $ <= AO_CACHE_MISS')]
    defs='p_pc_cut EQU $C296\np_s_sat EQU $C251\nSAT EQU $C400\n'
    control='ns_sat:\n LD D,A\n LD IY,SAT\n'+body+'ns_end:\n'
    out.mkdir(parents=True)
    start=s['p_player_cache_lookup.entry']-5;end=s['p_player_cache_lookup.miss']
    code,_=assemble(out/'control-production','P0-cache-SAT',f' ORG ${start:04X}\n'+defs+control+f' DS ${end:04X}-$,0\n')
    if len(code)!=end-start or image[start:end]!=code:raise ValueError('maintained control does not equal selected native game extent')
    inputs=bytearray();expected=bytearray()
    vectors=(0,1,7,15,16,23,31,63,127,128,192,254,255)
    for page in range(2):
      for way in range(3):
       pointer=0xC080+page*128+way*32+10;pattern=page*96+way*24
       for count in range(1,7):
        for v,offset in enumerate(vectors):
         cut=vectors[(v+4)%len(vectors)]
         records=bytes(n for i in range(6) for n in ((offset+i*17)&255,(v+i*3)&15))
         for x in (0,8,127,255):
          inputs.extend(pointer.to_bytes(2,'little')+bytes((pattern,count,x,cut))+records)
          output=bytearray([165])*128
          for i in range(count):output[i*4:i*4+4]=bytes(((cut+records[i*2]-1)&255,x,pattern+i*4,records[i*2+1]))
          end_pointer=(0xC400+count*4).to_bytes(2,'little')
          metadata=bytearray([165])*256;metadata[pointer-0xC080:pointer-0xC080+12]=records
          expected.extend(output+end_pointer+end_pointer+bytes(1)+metadata)
    results={}
    for name in ('control','candidate'):
        dest=out/name;dest.mkdir()
        wrapper=''' ORG $4000
 DB "AB"
 DW start
 DS 12,0
start:
 DI
 LD SP,$F380
ready:
 JP ready
 DS $4100-$,$FF
ns_entry:
 PUSH IY
 LD HL,$C080
 LD DE,$C081
 LD BC,255
 LD (HL),165
 LDIR
 LD A,($C7B9)
 LD (p_pc_cut),A
 LD DE,($C7B4)
 LD HL,$C7BA
 LD BC,12
 LDIR
 LD HL,($C7B4)
 LD A,($C7B7)
 LD B,A
 LD A,($C7B8)
 LD C,A
 LD A,($C7B6)
 CALL ns_sat
 LD A,0
 ADC A,0
 LD ($C484),A
 PUSH IY
 POP DE
 LD ($C480),DE
 LD DE,(p_s_sat)
 LD ($C482),DE
 LD HL,$C080
 LD DE,$C485
 LD BC,256
 LDIR
 POP IY
 RET
'''
        implementation=control if name=='control' else ' INCLUDE "native_p0_sat.asm"\n'
        result=run(dest,defs+wrapper+implementation+'fixture_end:\n DS $C000-$,$FF\n',bytes(inputs),bytes(expected),
            input_address=0xC7B4,input_stride=18,output_address=0xC400,output_stride=389,
            entry_name='ns_entry',end_name='fixture_end',writes=((0xC400,0xC584),(0xC080,0xC17F),(0xC251,0xC252),(0xC296,0xC296)))
        results[name]=result
    if results['candidate']['cycles_including_call_and_jump']['mean']>=results['control']['cycles_including_call_and_jump']['mean']:
        raise ValueError('no component speed gain')
    result=dict(complete=True,component_only=True,cases=len(inputs)//18,control_image_sha256=linked['image_sha256'],
        control_ROM_sha256=sha(cartridge),control_extent=[start,end],control_code_sha256=sha(out/'control-production/P0-cache-SAT.bin'),
        generations=2,ways_per_generation=3,entries=[1,6],signed_offset_vectors=len(vectors),horizontal_values=[0,8,127,255],
        full256byte_metadata_unchanged=True,final_IY_and_p_s_sat_equal=True,return_carry_clear=True,
        native_results=results,sources={n:sha(ROOT/n) for n in ('scripts/native_p0_sat_probe.py','src/native_p0_sat.asm','src/presentation_player_bands.asm')})
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','delivery','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();check(a.base.resolve(),a.delivery.resolve(),a.out.resolve())
