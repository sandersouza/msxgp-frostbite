"""Finite floe geometry programs and lossless half-pattern dictionaries.

These are source-mask/phase tables, never prerecorded game states or frames.
The existing original atlas IDs remain stable; new IDs are complete unions.
"""
from collections import defaultdict
import hashlib

from original_graphics import SOURCE_SHA256
from presentation_fixed import integer
from stella_floe import control_pairs


def pack_patterns(patterns):
    if not patterns or len(patterns)>16384 or any(not isinstance(p,bytes) or len(p)!=8 for p in patterns):raise ValueError('complete finite eight-byte patterns required')
    halves={};pairs=bytearray()
    for pattern in patterns:
        for at in (0,4):
            half=pattern[at:at+4]
            if half not in halves:halves[half]=len(halves)
            if halves[half]>=65536:raise ValueError('half-pattern dictionary exceeds uint16')
            pairs.extend(halves[half].to_bytes(2,'little'))
    return bytes(pairs),b''.join(halves)


def read_pattern(pairs,halves,index):
    if len(pairs)%4 or len(halves)%4:raise ValueError('complete half-pattern records required')
    integer(index,0,len(pairs)//4-1);result=bytearray()
    for at in (index*4,index*4+2):
        half=int.from_bytes(pairs[at:at+2],'little')*4
        if half+4>len(halves):raise ValueError('half index outside dictionary')
        result.extend(halves[half:half+4])
    return bytes(result)


def pack_program(program):
    if len(program)!=60 or any(type(v)is not int or not 0<=v<=14 for v in program):raise ValueError('two30-column rows and at most14 complete masks required')
    return bytes(program[i]|program[i+1]<<4 for i in range(0,60,2))


def cells(program,keys,root,y):
    integer(root,0,159);integer(y,0,185)
    if len(program)!=30 or not 1<=len(keys)<=14 or any(type(key)is not int or not 1<=key<16384 for key in keys):raise ValueError('complete packed program and finite mask IDs required')
    result={};shift=(root//16)*3
    for index in range(60):
        slot=(program[index//2]>>(index%2*4))&15
        if slot>len(keys):raise ValueError('program references an absent local mask')
        row,column=divmod(index,30);column=1+(column+shift)%30
        if slot and column>=2:result[y//8+row,column]=keys[slot-1]
    return result


def whole_masks(rom,root,delta,phase):
    """Direct source pixels, independently of the old geometry descriptor walk."""
    integer(root,0,15);integer(delta,0,19);integer(phase,0,7)
    signed=lambda v:(v>>4)-16 if v&128 else v>>4
    motion=[0]
    for line in range(1,7):motion.append(motion[-1]-signed(rom[0xDD2+7-line]))
    masks=defaultdict(lambda:bytearray(8))
    planes=((0,8+delta),) if delta<=8 else ((0,8),(delta,8))
    for copy in (0,32,64):
        for shift,width in planes:
            for line,dx in enumerate(motion):
                row,dy=divmod(phase+line,8)
                for bit in range(width):
                    x=(root+copy+shift+dx+bit)%160
                    for target in range(8+3*x//2,8+3*(x+1)//2):masks[row,target//8][dy]|=128>>(target%8)
    return {key:bytes(value) for key,value in masks.items()}


def compile_templates(tables):
    rom=tables['rom']
    if len(rom)!=4096 or hashlib.sha256(rom).hexdigest()!=SOURCE_SHA256:raise ValueError('original ROM authority required')
    signed=lambda v:(v>>4)-16 if v&128 else v>>4
    deltas=sorted({4+signed(a)-signed(b) for a,b in control_pairs(rom)})
    patterns=list(tables['patterns']);indices={pattern:index for index,pattern in enumerate(patterns)}
    if len(indices)!=len(patterns):raise ValueError('stable unique original atlas required')
    programs={};records=bytearray();directory=bytearray();maximum=0
    for phase in range(8):
        for delta in deltas:
            for root in range(16):
                masks=whole_masks(rom,root,delta,phase)
                ordered=list(dict.fromkeys(masks[cell] for cell in sorted(masks)));maximum=max(maximum,len(ordered))
                program=pack_program([0 if (row,col)not in masks else ordered.index(masks[row,col])+1 for row in range(2) for col in range(1,31)])
                if program not in programs:programs[program]=len(programs)
                if len(programs)>256:raise ValueError('program dictionary exceeds one-byte index')
                for mask in ordered:
                    if mask not in indices:indices[mask]=len(patterns);patterns.append(mask)
                if len(patterns)>16384 or len(records)>=65536:raise ValueError('finite template/pattern index exceeds its key field')
                directory.extend(len(records).to_bytes(2,'little'))
                records.extend(bytes((programs[program],len(ordered))))
                records.extend(b''.join(indices[mask].to_bytes(2,'little') for mask in ordered))
    pairs,halves=pack_patterns(patterns)
    for index,pattern in enumerate(patterns):
        if read_pattern(pairs,halves,index)!=pattern:raise ValueError('half dictionary changed a logical pattern')
    blobs={'template-index.bin':bytes(directory),'template-keys.bin':bytes(records),'template-names.bin':b''.join(programs),
        'pattern-pairs.bin':pairs,'pattern-halves.bin':halves,'logical-patterns.bin':b''.join(patterns)}
    return {'deltas':deltas,'template_count':len(directory)//2,'program_count':len(programs),'max_slots':maximum,
        'original_patterns':len(tables['patterns']),'patterns':len(patterns),'files':blobs}


def read_template(compiled,root,delta,y):
    integer(root,0,159);integer(y,0,185)
    if delta not in compiled['deltas']:raise ValueError('template delta is outside original control pairs')
    blobs=compiled['files'];index=(y%8*len(compiled['deltas'])+compiled['deltas'].index(delta))*16+root%16
    directory=blobs['template-index.bin'];records=blobs['template-keys.bin'];programs=blobs['template-names.bin']
    if len(directory)!=compiled['template_count']*2 or index*2+2>len(directory):raise ValueError('complete finite directory required')
    at=int.from_bytes(directory[index*2:index*2+2],'little')
    if at+2>len(records):raise ValueError('truncated template record')
    program,count=records[at:at+2]
    if not 1<=count<=14 or at+2+count*2>len(records) or program*30+30>len(programs):raise ValueError('truncated/invalid template keys or names')
    keys=[int.from_bytes(records[i:i+2],'little') for i in range(at+2,at+2+count*2,2)]
    if any(key>=compiled['patterns'] for key in keys):raise ValueError('template key outside logical atlas')
    return cells(programs[program*30:program*30+30],keys,root,y)
