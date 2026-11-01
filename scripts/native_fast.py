"""Proved whole-phase specialization; no source-address behavior substitutions.

Only F000 cold reset and F476 with D clear are public entries. Internal flags
are live only when source control flow or the F019 exit observes them. IY tracks
C000+sourceX; direct indexed RAM accesses require a proved non-wrapping range.
"""
import hashlib
import re

from native_analysis import analyze
from native_codegen import SOURCE_SHA256,BRANCHES,reachable,stack_depth,clear_patterns,translate,operand,pointer,mapped,capture_c


def validate_entries(cases):
    for case in cases:
        if case['start'] not in ('F000','F476'):raise ValueError('fast phase only exposes F000/F476 entries')
        if case.get('stops',['F019'])!=['F019']:raise ValueError('fast phase only exposes the F019 CPU boundary')
        registers=case.get('registers',{})
        if case['start']=='F476' and (registers.get('p',0x30)&8 or registers.get('sp',255)!=255):
            raise ValueError('fast whole-phase ABI requires source D=0 and SP=FF')


def translate_fast(item,facts):
    op=item['mnemonic'];mode=item['mode'];value=item['value'];live=facts['live_out']
    n,z,v,c=(bool(live&bit) for bit in (1,2,4,8))
    indexed=mode=='zpx' and 128<=value<=255 and max(facts['x'])+value<256
    argument=f'(iy+{value-128})' if indexed else f'${value:02X}' if mode=='imm' else None
    if argument is None and mode in ('zpg','abs') and op in ('ADC','SBC','CMP','AND','ORA','EOR'):
        address=mapped(value)
        prefix=[f'ld hl,{address}'];argument='(hl)'
    else:prefix=[]
    code=None
    if op in ('CLC','SEC') and not c:code=[]
    elif op in ('CMP','CPX','CPY') and not live&11 and mode=='imm':code=[]
    elif op=='BIT' and mode in ('zpg','abs') and not z:
        code=[f'ld hl,{mapped(value)}']
        if v:code+=['ld d,a','ld a,(hl)','and $40','ld (core_v),a','ld a,d']
        if n:code+=['bit 7,(hl)']
    elif op=='BIT' and mode in ('zpg','abs') and z and not n:
        code=[f'ld hl,{mapped(value)}','ld d,a']
        if v:code+=['ld a,(hl)','and $40','ld (core_v),a','ld a,d']
        code+=['and (hl)','ld a,d']
    elif op in ('ADC','SBC') and facts['decimal']==frozenset({0}):
        if argument is None:prefix=operand(item);argument='h'
        known=facts['carry']
        if op=='ADC':
            prefix+=[] if known=={0} else ['scf'] if known=={1} else ['srl e']
            code=prefix+[f'{"add" if known=={0} else "adc"} a,{argument}']+(capture_c() if c else [])
        else:
            prefix+=[] if known=={1} else ['scf'] if known=={0} else ['srl e','ccf']
            code=prefix+[f'sub {argument}' if known=={1} else f'sbc a,{argument}']+(capture_c(True) if c else [])
        if v:code+=['push af','pop hl','ld d,h','ld h,core_v_table/256','ld a,(hl)','ld (core_v),a','ld a,d']
    elif op in ('ADC','SBC') and facts['decimal']==frozenset({1}):
        code=operand(item)+['ld d,a',f'call core_{op.lower()}_decimal']
    elif indexed and op=='LDA':code=[f'ld a,{argument}']+(['or a'] if n or z else [])
    elif indexed and op in ('STA','STX','STY'):code=[f'ld {argument},{dict(STA="a",STX="b",STY="c")[op]}']
    elif indexed and op in ('INC','DEC'):code=[f'{op.lower()} {argument}']
    elif op in ('CMP','AND','ORA','EOR') and argument is not None:
        code=prefix+[f'{dict(CMP="cp",AND="and",ORA="or",EOR="xor")[op]} {argument}']
        if op=='CMP' and c:code+=capture_c(True)
    elif op in ('LDX','LDY') and not n and not z:
        reg='b' if op=='LDX' else 'c'
        code=[f'ld {reg},${value:02X}'] if mode=='imm' else ['ld d,a']+pointer(item)+['ld a,(hl)',f'ld {reg},a','ld a,d']
    if code is None:code=translate(item,n,z,v)
    # IY tracking never modifies the virtual source flags or A.
    if not facts.get('iy_out',True):return code
    if op=='LDX' and mode=='imm':code+=[f'ld iy,${0xC000+value:04X}']
    elif op in ('LDX','TAX','TSX'):code+=['ld l,b','ld h,$C0','push hl','pop iy']
    elif op=='INX':
        code+=['inc iy']
        if 255 in facts['x']:code+=['jr nz,$+6','ld iy,$C000']
    elif op=='DEX':
        if 0 not in facts['x']:code+=['dec iy']
        elif max(facts['x'])<=128:code+=['dec iy','jp p,$+7','ld iy,$C0FF']
        else:code+=['ld l,b','ld h,$C0','push hl','pop iy']
    return code


def generate_fast(rom):
    if len(rom)!=4096 or hashlib.sha256(rom).hexdigest()!=SOURCE_SHA256:raise ValueError('original identity mismatch')
    instructions=reachable(rom);stack_depth(instructions);facts=analyze(instructions,contexts=True);clears=clear_patterns(instructions)
    if any(i['mnemonic']=='TSX' for i in instructions.values()):raise ValueError('fast phase cannot hide an observable source SP read')
    if any(returns for pc,returns in facts if pc==0xF019):raise ValueError('phase exit retains a source call context')
    def label(pc,returns):return f'core_{pc:04X}'+(''.join(f'_r{ret:04X}' for ret in returns))
    lines=['; Local whole-phase specialization. Entry F476 requires source D=0.','core_F019:','    ret']
    ordered=sorted((key for key in facts if key[0]!=0xF019),key=lambda key:(key[1],key[0]))
    for index,key in enumerate(ordered):
        pc,returns=key;item=instructions[pc];following=pc+item['size'];op=item['mnemonic']
        physical_next=ordered[index+1] if index+1<len(ordered) else None
        lines.append(label(pc,returns)+':')
        if pc in clears:lines+=['    call core_clear',f'    jp {label(clears[pc],returns)}'];continue
        if pc in (0xF5AD,0xF630):lines+=['    IFDEF WITH_NATIVE_INPUT',f'    call sample_{"fire" if pc==0xF5AD else "directions"}','    ENDIF']
        if op=='JSR':
            code=[f'ld hl,${pc+2:04X}',f'ld (${0xC07E-2*len(returns):04X}),hl',f'call core_{item["target"]:04X}']
        elif op=='RTS':code=['ret']
        elif op in BRANCHES and (item['target'],returns) not in facts[key]['successors']:code=[]
        elif op in BRANCHES and (following,returns) not in facts[key]['successors']:code=[f'jp core_{item["target"]:04X}']
        else:code=translate_fast(item,facts[key])
        context=returns+(following,) if op=='JSR' else returns
        code=[re.sub(r'core_([0-9A-F]{4})\b',lambda m:label(int(m[1],16),context),line) for line in code]
        if op not in ('JMP','RTS') and (following,returns) in facts and physical_next!=(following,returns):code+=[f'jp {label(following,returns)}']
        lines+=['    '+line for line in code]
    return '\n'.join(lines)+'\n'
