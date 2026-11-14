"""Source-linked scattered Z80 functions; no copying cartridge padding/code dumps."""
from pathlib import Path
import re
import subprocess
from environment import ROOT,verified_tool
from render_build import symbols


def assemble(out,name,text):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    source=out/(name+'.asm');binary=out/(name+'.bin');sym=out/(name+'.sym')
    source.write_text(text)
    r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={binary}',f'--sym={sym}',str(source)],capture_output=True,text=True)
    (out/(name+'.log')).write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError(f'{name} assembly failed: '+(r.stdout+r.stderr)[-2000:])
    return binary.read_bytes(),symbols(sym)


def split_functions(text,entries,end):
    """Explicit entries certify function boundaries, including required fallthroughs.

    Cross-object relative jumps become absolute jumps. Local branches and DJNZ
    stay relative; an unlisted global label remains with its enclosing object.
    """
    positions=[]
    for name in (*entries,end):
        matches=list(re.finditer(r'^'+re.escape(name)+r':',text,re.M))
        if len(matches)!=1:raise ValueError('unique source function boundary required: '+name)
        positions.append(matches[0].start())
    if positions!=sorted(positions):raise ValueError('source function boundaries must be ordered')
    header=text[:positions[0]];result={}
    for i,name in enumerate(entries):
        body=text[positions[i]:positions[i+1]]
        body=re.sub(r'^(\s*)JR(\s+(?:(?:NZ|Z|NC|C),\s*)?)([A-Za-z_]\w*)(\s*(?:;[^\n]*)?)$',r'\1JP\2\3\4',body,flags=re.M|re.I)
        result[name]=body
    return header,result


def link_functions(layout,out,functions,preamble):
    labels={n:0x8000 for body in functions.values() for n in re.findall(r'^([A-Za-z_]\w*):',body,re.M)}
    sizes={};offsets={}
    for n,body in functions.items():
        own=set(re.findall(r'^([A-Za-z_]\w*):',body,re.M))
        equ=''.join(f'{label} EQU ${address:04X}\n' for label,address in labels.items() if label not in own)
        data,q=assemble(out,n+'-size',' ORG $4000\n'+preamble+equ+body)
        sizes[n]=len(data);offsets[n]={label:q[label]-0x4000 for label in own}
    for n in sorted(functions,key=lambda n:(-sizes[n],n)):
        if 'code/'+n in layout.objects:
            row=layout.objects['code/'+n]
            if row['size']!=sizes[n]:raise ValueError('reserved source function size differs: '+n)
            a=row['address']
        else:a=layout.add('code/'+n,bytes(sizes[n]))
        labels.update({label:a+off for label,off in offsets[n].items()})
    for n,body in functions.items():
        own=set(offsets[n]);a=labels[n]
        equ=''.join(f'{label} EQU ${address:04X}\n' for label,address in labels.items() if label not in own)
        data,q=assemble(out,n,f' ORG ${a:04X}\n'+preamble+equ+body)
        if len(data)!=sizes[n] or any(q[label]!=labels[label] for label in own):raise ValueError('relocated source shape changed: '+n)
        layout.image[a:a+len(data)]=data
        from hashlib import sha256
        layout.objects['code/'+n]['sha256']=sha256(data).hexdigest()
    return labels
