"""Force the source-IRQ status-read effect between the two VDP address bytes.

The injected callback runs IN99 only while IFF2 permits the source interrupt.
This is a deterministic latch-reset injection, not a claim of physical IRQ timing.
"""
import argparse
import json
from pathlib import Path

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def check(build,out,source):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if sha(build/m['rom']['filename'])!=m['rom']['sha256']:raise ValueError('bound original SGT input required')
    oracle=ROOT/'outputs/presentation/credit-reference-at/build-final';om=json.loads((oracle/'build.json').read_bytes());old=(oracle/om['rom']['filename']).read_bytes()
    if sha(oracle/om['rom']['filename'])!=CONTROL_SHA:raise ValueError('immutable source SGT oracle required')
    directory=(build/'sr-data.bin').read_bytes() if (build/'sr-data.bin').exists() else None
    if directory is None:raise ValueError('qualified RAM SGT input required')
    if len(directory)!=1214:raise ValueError('complete132-pattern literal-window grammar required')
    text=(ROOT/source).read_text();first=text.index('sw_upload:');before=text[:first];tail=text[first:]
    needle='    OUT ($99),A\n    LD A,D\n'
    if tail.count(needle)!=1:raise ValueError('unique VDP address latch boundary required')
    text=before+tail.replace(needle,'    OUT ($99),A\n    CALL ni_interrupt\n    LD A,D\n',1)
    out.mkdir(parents=True);(out/'sgt-data.bin').write_bytes(directory);(out/'injected-source.asm').write_text(text)
    # sw_directory has132 four-byte entries; literal pool follows528 bytes.
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380',
         ' LD A,$80',' OUT ($99),A',' LD A,$81',' OUT ($99),A','ready:',' JP ready',
         ' DS $4100-$,$FF','ni_entry:',' LD A,($C7B5)',' OR A',' JR Z,ni_di',' EI','ni_di:',
         ' LD A,($C7B4)',' LD DE,$4000',' CALL sw_upload',' LD A,I',' LD A,0',' JP PO,ni_flags',' INC A',
         'ni_flags:',' LD ($C520),A',' DI',' XOR A',' OUT ($99),A',' OUT ($99),A',' LD DE,$C500',' LD BC,$2098',
         'ni_read:',' IN A,(C)',' LD (DE),A',' INC DE',' DJNZ ni_read',' RET',
         'ni_interrupt:',' PUSH AF',' LD A,I',' JP PO,ni_return',' IN A,($99)','ni_return:',' POP AF',' RET',
         't_restore_interrupts:',' PUSH AF',' LD A,($C7B5)',' OR A',' JR Z,ni_restore_done',' EI',
         'ni_restore_done:',' POP AF',' RET','vdp_stream:',' OUTI',' JP NZ,vdp_stream',' RET',
         'sw_directory EQU $5000','sw_pool EQU $5210',f' INCLUDE "{out/"injected-source.asm"}"','ni_end:',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF',f' INCBIN "{out/"sgt-data.bin"}"',' DS $C000-$,$FF']
    inputs=bytes(v for mode in range(2) for index in range(132) for v in (index,mode))
    expected=b''.join(old[255*16384+0x1400+index*32:255*16384+0x1400+(index+1)*32]+bytes((mode,))
                       for mode in range(2) for index in range(132))
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=2,
               output_address=0xC500,output_stride=33,entry_name='ni_entry',end_name='ni_end',writes=((0xC500,0xC520),))
    result.update(source=source,input_rom_sha256=m['rom']['sha256'],sources={source:sha(ROOT/source)},
                  forced_latch_reset_only_when_IFF2=True,source_policy_restored=True,
                  scope='All132 actual SGTs with disabled/enabled source policy and a conditional status-read injection at the actual two-byte address-latch boundary; real natural PAL qualification remains separate.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--source',default='src/compact_enemy_windows.asm')
    a=p.parse_args();check(a.build,a.out,a.source)
