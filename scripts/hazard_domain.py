"""Source-addressed graphic/copy domains; no original bytes are embedded."""


def shapes(rom):
    if len(rom)!=4096:raise ValueError('complete4096-byte source required')
    result={0}  # Cold RAM clear precedes the first animated pointer update.
    for kind in range(4):
        for frame in range(256):
            index=kind*2
            if not frame&(16 if index==6 else 8):index+=1
            low=rom[0xD0A+index]
            if index>=2:
                phase=(frame>>3)&31
                if phase>=16:phase^=31
                low=(low+rom[0xDC2+phase])&255
            if low>248:raise ValueError('legal object graphic crosses an unmodeled page')
            result.add(low)
    return sorted(result)


def object_modes(rom):
    return [(shape,reflection,copies) for shape in shapes(rom)
            for reflection in (False,True) for copies in range(4)]


def bear_modes(rom):
    if len(rom)!=4096:raise ValueError('complete4096-byte source required')
    pointers={};representatives=[];aliases=[]
    for pose,pointer in enumerate(rom[0xEE7:0xEEF]):
        if pointer>237:raise ValueError('legal bear graphic crosses an unmodeled page')
        if pointer not in pointers:
            pointers[pointer]=len(representatives);representatives.append(pose)
        aliases.append(pointers[pointer])
    return representatives,aliases
