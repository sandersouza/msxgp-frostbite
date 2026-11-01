"""Whole-phase shift lowering using the existing proved flag liveness.

Only source RAM80..FF and accumulator shifts use the compact path. Hardware
aliases and indexed modes retain the original translator. The shared generator
and prior diagnostic builds remain byte-identical when this adapter is absent.
Transfer/comparison operand and IY paths also retain their original code; only
flag outputs proved dead are removed from those paths.
"""
import native_fast
from native_codegen import capture_c,mapped


def compact_shift(item,facts):
    op=item['mnemonic'];mode=item['mode'];value=item['value'];live=facts['live_out']
    if op not in ('ASL','LSR','ROL','ROR'):return None
    if mode=='acc':code=[];target='a'
    elif mode in ('zpg','abs') and 128<=value<=255:code=[f'ld hl,{mapped(value)}'];target='(hl)'
    else:return None
    if op in ('ROL','ROR'):code+=['srl e']
    code+=['add a,a' if op=='ASL' and mode=='acc' else f'{dict(ASL="sla",LSR="srl",ROL="rl",ROR="rr")[op]} {target}']
    if live&8:code+=capture_c() if live&3 else ['ld e,0','rl e']
    return code


def compact_flags(item,facts,code):
    code=list(code);op=item['mnemonic'];live=facts['live_out']
    if op in ('TAX','TAY','TXA','TYA') and not live&3 and len(code)>1 and code[1]=='or a':
        del code[1]  # Keep the entire operand and IY-tracking path unchanged.
    if op in ('CPX','CPY') and not live&8:
        capture=capture_c(True)
        for i in range(len(code)-len(capture)+1):
            if code[i:i+len(capture)]==capture:
                del code[i:i+len(capture)];break
    return code


def generate(rom,carry_fusion=True):
    previous=native_fast.translate_fast
    def translate(item,facts,**options):
        code=compact_shift(item,facts)
        return compact_flags(item,facts,previous(item,facts,**options) if code is None else code)
    try:
        native_fast.translate_fast=translate
        return native_fast.generate_fast(rom,carry_fusion=carry_fusion)
    finally:native_fast.translate_fast=previous
