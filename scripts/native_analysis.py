"""Conservative finite domains and flag liveness over bounded source call contexts.

Fast-phase entries require D=0. This analysis does not assume X is small: it
proves indexed RAM bounds, propagates every real call/return and splits tested
X/flag branches. Generic translation remains available for unrestricted slices.
"""
from collections import defaultdict,deque

ALL=frozenset(range(256))
NZ={'LDA','LDX','LDY','AND','ORA','EOR','ADC','SBC','CMP','CPX','CPY','ASL','LSR','ROL','ROR','INC','DEC',
    'INX','DEX','INY','DEY','TAX','TAY','TXA','TYA','TSX','BIT'}
CDEFS={'CLC','SEC','ADC','SBC','CMP','CPX','CPY','ASL','LSR','ROL','ROR'}


def analyze(instructions,roots=(0xF000,0xF476),stops=frozenset({0xF019}),contexts=False):
    initial=(ALL,frozenset({0}),frozenset({0,1}),None,None)
    domains={(pc,()):initial for pc in roots};pending=deque(domains);edges=defaultdict(set)
    def merge(key,value):
        if not value[0] or not value[1] or not value[2]:return
        old=domains.get(key)
        joined=value if old is None else tuple(old[i]|value[i] if i<3 else old[i] if old[i]==value[i] else None for i in range(5))
        if joined!=old:domains[key]=joined;pending.append(key)
    while pending:
        key=pending.popleft();pc,returns=key
        if pc in stops:continue
        item=instructions[pc];op=item['mnemonic'];following=pc+item['size'];x,d,c,nx,cx=domains[key]
        if op in ('LDX','TAX','TSX'):
            x=frozenset({item['value']}) if op=='LDX' and item['mode']=='imm' else ALL;nx=0;cx=None
        elif op in ('INX','DEX'):
            x=frozenset((v+(1 if op=='INX' else -1))&255 for v in x);nx=0;cx=None
        elif op=='TXA':nx=0
        elif op in NZ:nx=item['value'] if op=='CPX' and item['mode']=='imm' else None
        if op in CDEFS:
            c=frozenset({0 if op=='CLC' else 1}) if op in ('CLC','SEC') else frozenset({0,1})
            cx=item['value'] if op=='CPX' and item['mode']=='imm' else None
        if op in ('SED','CLD'):d=frozenset({int(op=='SED')})
        value=(x,d,c,nx,cx);targets=[]
        if op=='JSR':
            if len(returns)>=3:raise ValueError('analysis source call depth exceeds3')
            targets=[((item['target'],returns+(following,)),value)]
        elif op=='RTS':
            if returns:targets=[((returns[-1],returns[:-1]),value)]
        elif op=='JMP':targets=[((item['target'],returns),value)]
        elif op in ('BCC','BCS','BEQ','BNE','BMI','BPL','BVC','BVS'):
            for taken in (False,True):
                bx,bc=x,c
                if op in ('BCC','BCS'):
                    wanted=int(taken==(op=='BCS'));bc=c&{wanted}
                    if cx is not None:bx=frozenset(v for v in bx if int(v>=cx)==wanted)
                if nx is not None and op in ('BEQ','BNE','BMI','BPL'):
                    def predicate(v):
                        result=(v-nx)&255
                        return (result==0) if op=='BEQ' else (result!=0) if op=='BNE' else bool(result&128) if op=='BMI' else not result&128
                    bx=frozenset(v for v in bx if predicate(v)==taken)
                targets.append(((item['target'] if taken else following,returns),(bx,d,frozenset(bc),nx,cx)))
        else:targets=[((following,returns),value)]
        for successor,domain in targets:
            if not domain[0] or not domain[2]:continue
            edges[key].add(successor);merge(successor,domain)
    # N/Z/V/C bits1/2/4/8; a phase exit exposes all four source flags.
    live={key:15 if key[0] in stops else 0 for key in domains};out=dict(live);changed=True
    while changed:
        changed=False
        for key in reversed(domains):
            pc,_=key
            if pc in stops:continue
            op=instructions[pc]['mnemonic'];uses=0;defs=3 if op in NZ else 0
            if op in CDEFS:defs|=8
            if op in ('ADC','SBC','BIT','CLV'):defs|=4
            if op in ('ADC','SBC','ROL','ROR'):uses|=8
            conditional=len(edges[key])>1
            if op in ('BCC','BCS') and conditional:uses|=8
            if op in ('BMI','BPL') and conditional:uses|=1
            if op in ('BEQ','BNE') and conditional:uses|=2
            if op in ('BVC','BVS') and conditional:uses|=4
            after=0
            for successor in edges[key]:after|=live[successor]
            before=uses|(after&~defs)
            if before!=live[key] or after!=out[key]:live[key]=before;out[key]=after;changed=True
    iy_live={key:False for key in domains};iy_out=dict(iy_live);changed=True
    while changed:
        changed=False
        for key in reversed(domains):
            pc,_=key
            if pc in stops:continue
            i=instructions[pc];op=i['mnemonic'];x=domains[key][0]
            used=i['mode']=='zpx' and 128<=i['value']<=255 and max(x)+i['value']<256
            after=any(iy_live[s] for s in edges[key]);before=used or (after and op not in ('LDX','TAX','TSX'))
            if before!=iy_live[key] or after!=iy_out[key]:iy_live[key]=before;iy_out[key]=after;changed=True
    result={}
    for key,value in domains.items():
        pc,_=key;x,d,c,_,_=value
        if contexts:
            result[key]={'x':x,'decimal':d,'carry':c,'live_out':out[key],'iy_out':iy_out[key],'successors':frozenset(edges[key])};continue
        if pc not in result:result[pc]={'x':x,'decimal':d,'carry':c,'live_out':out[key]}
        else:
            r=result[pc];r['x']|=x;r['decimal']|=d;r['carry']|=c;r['live_out']|=out[key]
    return result
