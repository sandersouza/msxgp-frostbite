"""Exact source-mask grammars for the final fixed-RAM link; no state pruning."""
from compact_byte_windows import pack_windows
from presentation_sprites import expand_pair


def floes(patterns,indices):
    if not patterns or len(patterns)%8 or not indices or len(indices)%2:
        raise ValueError('complete floe patterns and word indices required')
    values=[int.from_bytes(patterns[i:i+8],'little') for i in range(0,len(patterns),8)]
    if any(value>>56 for value in values):raise ValueError('phase0 floe bottom row must remain empty')
    basis=[]
    for value in sorted(set(values)):
        union=0
        for other in values:
            if other!=value and other&value==other:union|=other
        if union!=value:basis.append(value)
    # Literal full interior cells keep the old fast stream, including touched
    # blue ice. All other reducible cells retain exact two-mask union semantics.
    common=(1<<56)-1
    basis=sorted({0,*basis,*([common] if common in values else [])})
    if len(basis)>256:raise ValueError('floe union grammar exceeds byte selectors')
    pairs={}
    for i,a in enumerate(basis):
        for j,b in enumerate(basis):pairs.setdefault(a|b,(i,j))
    for i,a in enumerate(basis):pairs[a]=(i,0)
    if any(value not in pairs for value in values):raise ValueError('floe pattern needs more than two source planes')
    words=[]
    for i in range(0,len(indices),2):
        offset=int.from_bytes(indices[i:i+2],'little')
        if offset%8 or offset>=len(patterns):raise ValueError('floe index outside complete literal pattern domain')
        words.extend(pairs[values[offset//8]])
    return dict(basis=b''.join(value.to_bytes(8,'little') for value in basis),indices=bytes(words),
                selectors=bytes(v for value in values for v in pairs[value]))


def p0(patterns,expansion):
    if not patterns or len(patterns)%32 or len(expansion)!=1024:
        raise ValueError('whole P0 SGTs and both complete expansion phases required')
    expected=b''.join(bytes(expand_pair(x,phase)) for phase in range(2) for x in range(256))
    if expansion!=expected:raise ValueError('native source expansion differs from independent pixel projection')
    inverses=[{tuple(expand_pair(x,phase)):x for x in range(256)} for phase in range(2)]
    rows=[];phases=[]
    for at in range(0,len(patterns),32):
        pattern=patterns[at:at+32]
        for phase,inverse in enumerate(inverses):
            try:row=bytes(inverse[(pattern[y],pattern[y+16])] for y in range(16))
            except KeyError:continue
            rows.append(row);phases.append(phase);break
        else:raise ValueError('P0 pattern has pixels outside either original horizontal expansion')
    data=pack_windows(rows)
    if len(data['pool'])+16>32768:raise ValueError('native P0 literal offsets need15 bits')
    directory=b''.join((int.from_bytes(data['offsets'][i*2:i*2+2],'little')|(phase<<15)).to_bytes(2,'little')
                       for i,phase in enumerate(phases))
    return dict(rows=data['pool'],directory=directory)
