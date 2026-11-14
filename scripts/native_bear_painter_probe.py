"""Factorized native grid/palette proof with independent original-glyph pixels."""
import argparse
import json
from pathlib import Path

from compact_native_fixture import run, sha
from environment import ROOT
from native_bear_grid_probe import check as grid_check
from native_bear_keys import construct, make_key, masks
from reference_traces import private_output


BACKGROUNDS = (bytes([255])*8, bytes([17])*8,
               bytes([255])*6+bytes((17,68)), bytes([17])*7+bytes((68,)),
               bytes([255])*7+bytes((17,)))


def check(build, grid, out):
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    proof = json.loads((grid/'component-result.json').read_bytes())
    metadata = json.loads((build/'build.json').read_bytes())
    if not proof['complete'] or proof['input_rom_sha256'] != metadata['rom']['sha256'] or proof['renderer'] != 'rows':
        raise ValueError('exact512-case row grammar proof required')
    original = (ROOT/'references/roms/frostbite.bin').read_bytes()
    inputs, expected = bytearray(), bytearray()
    # All512 geometries already execute in the separate grid proof. Each
    # geometry here additionally paints each original row palette with every
    # foreground. Rotate the selected cell: all12 physical cells participate.
    host_cases = 0
    for group in range(16):
        for phase in range(16):
            for coarse in range(2):
                geometry = masks(original, group, phase, coarse)
                cell = (group*32+phase*2+coarse) % 12
                for background in BACKGROUNDS:
                    for foreground in range(1,16):
                        inputs.extend((group,phase,coarse,cell,foreground))
                        inputs.extend(background)
                        key = make_key(group,phase,coarse,cell//4,cell%4,128,foreground)
                        expected.extend(construct(original,int(cell//4==2),key,{128:bytes([255])*8+background}))
                        for mask in geometry:
                            tile = mask+bytes((foreground<<4)|(v&15) for v in background)
                            for y in range(8):
                                for x in range(8):
                                    actual = tile[8+y] >> (4 if tile[y] & (128>>x) else 0) & 15
                                    wanted = foreground if mask[y] & (128>>x) else background[y]&15
                                    if actual != wanted:
                                        raise ValueError('independent full-pixel projection differs')
                            host_cases += 1
    out.mkdir(parents=True)
    asm = [' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
           ' DS $4100-$,$FF','ng_entry:',' LD A,($C7B5)',' LD B,A',' LD A,($C7B6)',' LD C,A',' LD A,($C7B4)',
           ' CALL ng_build',' LD A,($C7B7)',' LD L,A',' LD H,0',' ADD HL,HL',' ADD HL,HL',' ADD HL,HL',
           ' LD DE,$C480',' ADD HL,DE',' LD DE,$C520',' LD BC,8',' LDIR',
           ' LD A,($C7B8)',' LD HL,$C7B9',' LD DE,$C528',' JP np_paint',
           ' INCLUDE "native_bear_grid_rows.asm"',' INCLUDE "native_bear_painter.asm"','np_fixture_end:',
           ' ASSERT $ <= $5000',' DS $5000-$,$FF','ng_info:',f' INCBIN "{grid/"info.bin"}"',
           'ng_rows:',f' INCBIN "{grid/"rows.bin"}"','ng_shifted:',f' INCBIN "{grid/"shifted.bin"}"',' DS $C000-$,$FF']
    result = run(out,'\n'.join(asm)+'\n',bytes(inputs),bytes(expected),input_address=0xC7B4,input_stride=13,
                 output_address=0xC520,output_stride=16,entry_name='ng_entry',end_name='np_fixture_end',
                 writes=((0xC480,0xC4DF),(0xC500,0xC50F),(0xC520,0xC52F)))
    result.update(host_complete_grid_palette_cases=host_cases,grid_proof_sha256=sha(grid/'component-result.json'),
                  original_sha256=sha(ROOT/'references/roms/frostbite.bin'),
                  input_rom_sha256=metadata['rom']['sha256'],background_vectors=5,foreground_colors=15,
                  scope='512 exact native geometries, every original solid-row palette and15 foregrounds; all12 cells and empty/equal-color cells, full independent host RGB. Component only; no whole-frame claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--grid',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build.resolve(),a.grid.resolve(),a.out)
