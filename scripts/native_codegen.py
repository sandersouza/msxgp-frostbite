"""Frostbite-specific audited static 6502→Z80 translation, never an interpreter.

Generic CFG/address/virtual-register patterns were audited from the supplied GPLv3
Seaquest infrastructure. No Seaquest address substitutions or optimizer survive.
Generated original-derived assembly/data remain local under outputs/native/.
"""
import hashlib
from py65.devices.mpu6502 import MPU

SOURCE_SHA256='cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834'
SIZES={'imp':1,'acc':1,'imm':2,'zpg':2,'zpx':2,'zpy':2,'rel':2,'abs':3,'abx':3,'aby':3,'ind':3,'inx':2,'iny':2}
BRANCHES={'BCC','BCS','BEQ','BNE','BMI','BPL','BVC','BVS'}
ROOTS=(0xF000,0xF476,0xFB3B,0xF6AB,0xFFD0,0xFCEA,0xFF5B,0xFE77,0xFE8B,0xFAEA,0xF0AF)
STOPS={0xF019,0xF0BD}
SUPPORTED={'LDA','LDX','LDY','STA','STX','STY','AND','ORA','EOR','CMP','CPX','CPY','ADC','SBC',
           'INC','DEC','INX','DEX','INY','DEY','TAX','TAY','TXA','TYA','TXS','TSX','ASL','LSR','ROL','ROR',
           'BIT','JMP','JSR','RTS','CLC','SEC','CLV','SED','CLD','SEI','CLI','NOP'}|BRANCHES


def decode(rom,pc):
    if len(rom)!=4096 or not 0xF000<=pc<=0xFFFF:raise ValueError('source PC/image outside4KiB')
    op,mode=MPU.disassemble[rom[pc-0xF000]];size=SIZES[mode]
    data=rom[pc-0xF000:pc-0xF000+size]
    if op not in SUPPORTED or mode in ('ind','inx','iny') or len(data)!=size:
        raise ValueError(f'unsupported source instruction {pc:04X}:{op}/{mode}')
    value=int.from_bytes(data[1:],'little')
    target=(pc+2+(value if value<128 else value-256))&65535 if mode=='rel' else value
    return {'address':pc,'mnemonic':op,'mode':mode,'size':size,'value':value,'target':target}


def reachable(rom,roots=ROOTS,stops=STOPS):
    pending=list(roots);result={}
    while pending:
        pc=pending.pop()
        if pc in result or pc in stops:continue
        item=decode(rom,pc);result[pc]=item;op=item['mnemonic']
        if op in BRANCHES|{'JMP','JSR'}:pending.append(item['target'])
        if op not in ('JMP','RTS'):pending.append(pc+item['size'])
    # Reject conflicting instruction boundaries rather than decoding data twice.
    occupied=set()
    for pc,item in sorted(result.items()):
        addresses=set(range(pc,pc+item['size']))
        if occupied&addresses:raise ValueError('overlapping source instruction boundaries')
        occupied|=addresses
    return result


def mapped(address,write=False):
    physical=address&0x1FFF
    if physical&0x1000:
        if write or physical<0x1C00:raise ValueError('unsupported source ROM/code data access')
        return f'original_data+${physical-0x1C00:03X}'
    if not physical&0x80:return f'${(0xC700 if write else 0xC300)+(physical&(63 if write else 15)):04X}'
    if not physical&0x200:return f'${0xC000+(physical&127):04X}'
    return f'${(0xC740 if write else 0xC340)+(physical&(31 if write else 7)):04X}'


def stack_depth(instructions,roots=ROOTS,stops=STOPS):
    pending=[(pc,()) for pc in roots];seen=set();maximum=0
    while pending:
        pc,returns=pending.pop()
        if pc in stops or (pc,returns) in seen:continue
        seen.add((pc,returns));item=instructions[pc];op=item['mnemonic'];following=pc+item['size']
        if op=='JSR':
            if len(returns)>=3:raise ValueError('source call depth exceeds proved3levels')
            maximum=max(maximum,len(returns)+1);pending.append((item['target'],returns+(following,)))
        elif op=='RTS':
            if returns:pending.append((returns[-1],returns[:-1]))
        elif op=='JMP':pending.append((item['target'],returns))
        else:
            if op=='TXS':
                previous=instructions.get(pc-2);increment=instructions.get(pc+1);loop=instructions.get(pc+2)
                if (returns or previous is None or previous['mnemonic']!='STA' or previous['mode']!='zpx' or previous['value']!=0
                        or increment is None or increment['mnemonic']!='INX' or loop is None or loop['mnemonic']!='BNE' or loop['target']!=pc-2):
                    raise ValueError('source TXS lacks proved bounded ascending zero-clear loop')
            pending.append((following,returns))
            if op in BRANCHES:pending.append((item['target'],returns))
    return maximum


def clear_patterns(instructions):
    result={}
    for pc,item in instructions.items():
        if item['mnemonic']!='LDA' or item['mode']!='imm' or item['value']!=0:continue
        store=instructions.get(pc+2,{});sp=instructions.get(pc+4,{});increment=instructions.get(pc+5,{});loop=instructions.get(pc+6,{})
        if (store.get('mnemonic')=='STA' and store.get('mode')=='zpx' and store.get('value')==0
                and sp.get('mnemonic')=='TXS' and increment.get('mnemonic')=='INX'
                and loop.get('mnemonic')=='BNE' and loop.get('target')==pc+2):result[pc]=pc+8
    return result


def pointer(item,write=False):
    mode=item['mode'];value=item['value'];index='b' if mode in ('zpx','abx') else 'c'
    if mode in ('zpg','abs'):return [f'ld hl,{mapped(value,write)}']
    if mode in ('zpx','zpy'):
        if value>=128:
            # In-place fast RAM path, still dispatch wrapped hardware accesses.
            return [f'ld hl,${0xC000+value-128:04X}','ld a,l',f'add a,{index}','ld l,a',
                    'bit 7,l','jr z,$+7','xor $80',f'call core_zp_{"write" if write else "read"}']
        return [f'ld a,${value:02X}',f'add a,{index}',f'call core_zp_{"write" if write else "read"}']
    if mode in ('abx','aby'):
        if not write and 0xFC00<=value<=0xFF00:
            return [f'ld hl,{mapped(value)}','ld a,l',f'add a,{index}','ld l,a','jr nc,$+3','inc h']
        return [f'ld hl,${value:04X}','ld a,l',f'add a,{index}','ld l,a','jr nc,$+3','inc h',
                f'call core_address_{"write" if write else "read"}']
    raise ValueError('unsupported source pointer')


def operand(item):
    if item['mode']=='imm':return [f'ld h,${item["value"]:02X}']
    return ['ld d,a']+pointer(item)+['ld h,(hl)','ld a,d']


def capture_c(invert=False):return ['ld e,0',f'jr {"c" if invert else "nc"},$+4','ld e,1']


def translate(item,n_live=True,z_live=True,v_live=True):
    op=item['mnemonic'];mode=item['mode'];value=item['value'];target=f'core_{item["target"]:04X}'
    if mode in ('zpg','abs') and op=='LDA':return [f'ld a,({mapped(value)})']+(['or a'] if n_live or z_live else [])
    if mode in ('zpg','abs') and op=='STA':return [f'ld ({mapped(value,True)}),a']
    if mode in ('zpg','abs') and op in ('STX','STY'):
        return [f'ld hl,{mapped(value,True)}',f'ld (hl),{"b" if op=="STX" else "c"}']
    if mode in ('zpg','abs') and op in ('INC','DEC') and mapped(value)==mapped(value,True):
        return [f'ld hl,{mapped(value)}',f'{op.lower()} (hl)']
    if mode in ('imm','zpg','abs') and op in ('AND','ORA','EOR','CMP'):
        code=[] if mode=='imm' else [f'ld hl,{mapped(value)}']
        argument=f'${value:02X}' if mode=='imm' else '(hl)'
        code+=[f'{dict(AND="and",ORA="or",EOR="xor",CMP="cp")[op]} {argument}']
        return code+(capture_c(True) if op=='CMP' else [])
    if op=='LDA':
        if mode=='imm':return [f'ld a,${value:02X}']+(['or a'] if n_live or z_live else [])
        return pointer(item)+['ld a,(hl)']+(['or a'] if n_live or z_live else [])
    if op in ('LDX','LDY'):
        return ['ld d,a']+([f'ld a,${value:02X}'] if mode=='imm' else pointer(item)+['ld a,(hl)'])+[
            f'ld {"b" if op=="LDX" else "c"},a','or a','ld a,d']
    if op in ('STA','STX','STY'):
        return ["ex af,af'"]+pointer(item,True)+["ex af,af'",f'ld (hl),{dict(STA="a",STX="b",STY="c")[op]}']
    if op in ('INC','DEC'):
        return ['ld d,a']+pointer(item)+['ld a,(hl)',f'{op.lower()} a','push af']+pointer(item,True)+['pop af','ld (hl),a','ld a,d']
    if op in ('AND','ORA','EOR','CMP','ADC','SBC'):
        code=operand(item)
        if op in ('ADC','SBC'):return code+[f'call core_{op.lower()}']
        if op=='CMP':return code+['cp h']+capture_c(True)
        return code+[dict(AND='and h',ORA='or h',EOR='xor h')[op]]
    if op in ('CPX','CPY'):
        return operand(item)+['ld d,a',f'ld a,{"b" if op=="CPX" else "c"}','cp h']+capture_c(True)+['ld a,d']
    if op in ('ASL','LSR','ROL','ROR'):
        code=[] if mode=='acc' else ['ld d,a']+pointer(item)+['ld a,(hl)']
        if op in ('ROL','ROR'):code+=['srl e']
        code+=[dict(ASL='add a,a',LSR='srl a',ROL='rl a',ROR='rr a')[op]]+capture_c()
        return code+([] if mode=='acc' else ['push af']+pointer(item,True)+['pop af','ld (hl),a','ld a,d'])
    if op=='BIT':
        if z_live:return operand(item)+['ld d,a','call core_bit']
        code=operand(item)+['ld d,a']
        if v_live:code+=['ld a,h','and $40','ld (core_v),a','ld a,d']
        if n_live:code+=['bit 7,h']
        return code
    if op=='JMP':return [f'jp {target}']
    if op=='JSR':return [f'ld (ix+0),${(item["address"]+2)>>8:02X}','dec ix',
                        f'ld (ix+0),${(item["address"]+2)&255:02X}','dec ix',f'call {target}']
    if op=='RTS':return ['jp core_return']
    if op in ('BEQ','BNE','BMI','BPL'):return [f'jp {dict(BEQ="z",BNE="nz",BMI="m",BPL="p")[op]},{target}']
    if op in ('BCC','BCS'):return ['ld d,a','ld a,e','rrca','ld a,d',f'jp {"c" if op=="BCS" else "nc"},{target}']
    if op in ('BVC','BVS'):return ['ld d,a','ld a,(core_v)','rlca','rlca','ld a,d',f'jp {"c" if op=="BVS" else "nc"},{target}']
    if op in ('CLC','SEC'):return [f'ld e,{int(op=="SEC")}']
    if op=='CLV':return ['push af','xor a','ld (core_v),a','pop af']
    if op in ('SED','CLD','SEI','CLI'):
        return ['ld hl,core_mode',f'{"set" if op in ("SED","SEI") else "res"} {3 if op in ("SED","CLD") else 2},(hl)']
    if op in ('INX','DEX','INY','DEY'):return [f'{"inc" if op.startswith("IN") else "dec"} {"b" if op.endswith("X") else "c"}']
    if op in ('TAX','TAY'):return [f'ld {"b" if op=="TAX" else "c"},a','or a']
    if op in ('TXA','TYA'):return [f'ld a,{"b" if op=="TXA" else "c"}','or a']
    if op=='TXS':return ['push af','ld a,b','and 128','ld (core_stack_high),a','ld a,b','and 127','ld l,a','ld h,$C0','push hl','pop ix','pop af']
    if op=='TSX':return ['ld d,a','push ix','pop hl','ld a,(core_stack_high)','or l','ld b,a','or a','ld a,d']
    if op=='NOP':return ['nop']
    raise ValueError('missing native translation')


def observable_stops():
    # Public logical CPU stop points are observable even when subsequent source
    # code would overwrite the flags. Calls/returns conservatively expose them.
    import json
    from reference_inventory import ROOT
    pins={int(s,16) for c in json.loads((ROOT/'references/mechanics-cases.json').read_text())['cases'] for s in c['stops']}
    return pins|{0xF00C,0xFB9D,0xFBC7,0xFCF7,0xFFE4,0xF019}


def generate(rom):
    if len(rom)!=4096 or hashlib.sha256(rom).hexdigest()!=SOURCE_SHA256:raise ValueError('original identity mismatch')
    instructions=reachable(rom);stack_depth(instructions);clears=clear_patterns(instructions);pins=observable_stops()
    def flag_liveness(defs,uses):
        incoming={pc:pc in pins for pc in instructions};outgoing=dict(incoming)
        changed=True
        while changed:
            changed=False
            for pc,item in reversed(sorted(instructions.items())):
                op=item['mnemonic'];following=pc+item['size']
                successors=[item['target']] if op=='JMP' else [following,item['target']] if op in BRANCHES else [following]
                out=op in ('JSR','RTS') or any(s in pins or incoming.get(s,True) for s in successors)
                live=pc in pins or op in uses or op in ('JSR','RTS') or (out and op not in defs)
                if live!=incoming[pc] or out!=outgoing[pc]:incoming[pc],outgoing[pc],changed=live,out,True
        return outgoing
    nz_defs={'LDA','LDX','LDY','AND','ORA','EOR','ADC','SBC','CMP','CPX','CPY','ASL','LSR','ROL','ROR','INC','DEC',
             'INX','DEX','INY','DEY','TAX','TAY','TXA','TYA','TSX','BIT'}
    ns=flag_liveness(nz_defs,{'BMI','BPL'});zs=flag_liveness(nz_defs,{'BEQ','BNE'});vs=flag_liveness({'BIT','ADC','SBC','CLV'},{'BVC','BVS'})
    lines=['; Local original-derived native code. Never commit this generated file.']
    for pc in sorted(STOPS):lines.extend([f'core_{pc:04X}:','    ret'])
    for pc,item in sorted(instructions.items()):
        lines.append(f'core_{pc:04X}:')
        if pc in clears and not any(pc<s<clears[pc] for s in pins):
            lines+=['    call core_clear',f'    jp core_{clears[pc]:04X}'];continue
        if pc in (0xF5AD,0xF630):
            lines+=['    IFDEF WITH_NATIVE_INPUT',f'    call sample_{"fire" if pc==0xF5AD else "directions"}','    ENDIF']
        lines.extend('    '+line for line in translate(item,ns[pc],zs[pc],vs[pc]))
        if pc+item['size'] in STOPS and item['mnemonic'] not in ('JMP','RTS'):
            lines.append(f'    jp core_{pc+item["size"]:04X}')
    return '\n'.join(lines)+'\n'
