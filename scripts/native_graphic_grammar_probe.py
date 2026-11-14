"""Prove all native compact P0 patterns or complete source floe packets."""
import argparse
import json
from pathlib import Path

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from compact_floe_packet_probe import packet_data
from environment import ROOT
from native_graphic_grammar import p0,floes
from reference_traces import private_output


def check(build,out,kind):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if sha(build/m['rom']['filename'])!=m['rom']['sha256']:raise ValueError('bound input required')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final'
    cm=json.loads((control/'build.json').read_bytes());cr=(control/cm['rom']['filename']).read_bytes()
    if sha(control/cm['rom']['filename'])!=CONTROL_SHA:raise ValueError('immutable accepted literal oracle required')
    expansion=rom[2*16384+0x3300:2*16384+0x3700]
    header=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',' DS $4100-$,$FF']
    out.mkdir(parents=True)
    if kind=='p0':
        expected=cr[149*16384+0x3800:150*16384]+cr[148*16384+0x3A60:148*16384+0x3B20]
        if len(expected)!=2240 or expected!=(build/'player-band-patterns.bin').read_bytes():raise ValueError('all70 original P0 source patterns required')
        data=p0(expected,expansion)
        for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
        (out/'expansion.bin').write_bytes(expansion)
        asm=header+['np0_entry:',' LD A,($C7B4)',' INCLUDE "native_p0_pattern.asm"',' ASSERT $ <= $5000',
            ' DS $5000-$,$FF','np0_directory:',f' INCBIN "{out/"directory.bin"}"','np0_rows:',f' INCBIN "{out/"rows.bin"}"',
            ' DS $6000-$,$FF','np0_expansion:',f' INCBIN "{out/"expansion.bin"}"',' DS $C000-$,$FF']
        inputs=bytes(range(70));output=0xC500;stride=32;isize=1;end='np0_end';writes=((0xC500,0xC51F),)
    else:
        literal,expected=packet_data(cr);data=floes(literal['patterns'],literal['indices'])
        data.update(directory=literal['directory'],counts=literal['counts'])
        for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
        asm=header+['nf_entry:',' INCLUDE "native_floe_union.asm"',' ASSERT $ <= $5000',' DS $5000-$,$FF']
        for n in ('basis','indices','directory','counts'):
            asm += ['nf_'+n+':',f' INCBIN "{out/(n+".bin")}"']
        asm += [' DS $C000-$,$FF']
        inputs=b''.join(i.to_bytes(2,'little') for i in range(160));output=0xC480;stride=64;isize=2;end='nf_end';writes=((0xC480,0xC4BF),)
        if kind=='floe-stream':
            asm=header+['pk_pointer EQU $C1F9','pk_bank EQU $C1FB','pk_pending EQU $C1C1',
                'nf_entry:',' LD A,($C7B4)',' LD L,A',' LD H,0',' LD DE,nf_counts',' ADD HL,DE',
                ' LD A,(HL)',' LD (pk_pending+3),A',' LD A,($C7B4)',' AND 15',' RRCA',' LD H,A',
                ' AND 128',' LD L,A',' LD A,H',' AND 7',' ADD A,$B8',' LD H,A',' LD (pk_pointer),HL',
                ' LD A,($C7B4)',' DUP 4',' SRL A',' EDUP',' ADD A,35',' LD (pk_bank),A',
                ' XOR A',' OUT ($99),A',' LD A,$40',' OUT ($99),A',' LD A,$A5',' LD B,64',
                'nf_poison:',' OUT ($98),A',' NOP',' DJNZ nf_poison',' LD DE,$4000',' CALL nf_stream',
                ' XOR A',' OUT ($99),A',' OUT ($99),A',' LD DE,$C480',' LD B,64',' LD C,$98',
                'nf_read:',' IN A,(C)',' LD (DE),A',' INC DE',' DJNZ nf_read',' RET',
                't_restore_interrupts:',' RET',' INCLUDE "native_floe_union_stream.asm"','nf_end:',
                ' ASSERT $ <= $5000',' DS $5000-$,$FF']
            for n in ('basis','indices','directory','counts'):
                asm += ['nf_'+n+':',f' INCBIN "{out/(n+".bin")}"']
            asm+=[' DS $C000-$,$FF']
            writes+=((0xC1F9,0xC1FB),(0xC1C4,0xC1C4))
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=isize,
        output_address=output,output_stride=stride,entry_name='np0_entry' if kind=='p0' else 'nf_entry',end_name=end,writes=writes)
    result.update(kind=kind,input_rom_sha256=m['rom']['sha256'],oracle_rom_sha256=CONTROL_SHA,
                  grammar_bytes={n:len(b) for n,b in data.items()},
                  sources={n:sha(ROOT/n) for n in ('scripts/native_graphic_grammar_probe.py','scripts/native_graphic_grammar.py',
                           'src/'+('native_p0_pattern.asm' if kind=='p0' else 'native_floe_union_stream.asm' if kind=='floe-stream' else 'native_floe_union.asm'))},
                  scope='Every accepted P0 SGT or all160 complete source phase0 floe PGT prefixes, poison tail, ABI and bounded writes; no linked runtime/cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--kind',choices=('p0','floe','floe-stream'),required=True)
    a=p.parse_args();check(a.build,a.out,a.kind)
