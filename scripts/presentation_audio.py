"""Ordered source writes and an explicit finite TIA-to-PSG adaptation.

Source CPU/RAM own every envelope and event. This projection changes no source
state and does not execute a TIA oscillator at runtime. Polynomial timbres,
analogue volume and target write timing remain documented adaptations.
"""

# Measured with the pinned, unmodified Stella AudioChannel at AUDF0. One phase
# pair averages114 color clocks; AUDF divides it by(value+1). These are general
# chip modes, not Frostbite event/route tables. DC and POLY9 have no square tone.
MODE_CYCLES=(1,15,465,465,2,2,31,31,511,31,31,1,6,6,93,93)
NO_TONE=frozenset((0,8,11))
OWNED_REGISTERS=(0,1,2,3,6,7,8,9,10)
MASKS=(15,15,31,31,15,15)


def byte(value):
    if type(value)is not int or not 0<=value<=255:raise ValueError('uint8 source value required')
    return value


def events(source_records):
    """Keep complete intervals, source timestamps and every raw ordered write."""
    if not isinstance(source_records,(list,tuple)) or not 1<=len(source_records)<=5000:
        raise ValueError('bounded nonempty source interval sequence required')
    result=[]
    for index,record in enumerate(source_records):
        if not isinstance(record,dict):raise ValueError('complete source record required')
        ordinal=record.get('index');duration=record.get('cycles');visible=record.get('visible_cycles');writes=record.get('audio')
        if (type(ordinal)is not int or ordinal!=index or type(duration)is not int or type(visible)is not int
                or not 0<visible<duration<=1<<19 or not isinstance(writes,(list,tuple)) or len(writes)>65535):
            raise ValueError('ordered bounded source interval and visible boundary required')
        ordered=[];prior=-1
        for write in writes:
            if not isinstance(write,(list,tuple)) or len(write)!=3:raise ValueError('complete source audio write required')
            cycle,address,value=write
            if (type(cycle)is not int or not 0<=cycle<=duration or cycle<prior or type(address)is not int or not 0x15<=address<=0x1A):
                raise ValueError('ordered in-interval TIA audio write required')
            ordered.append((cycle,address,byte(value)));prior=cycle
        result.append({'logical_step':index,'source_cycles':duration,'visible_cycles':visible,'writes':tuple(ordered)})
    return result


def tone_period(control,frequency):
    control=byte(control)&15;frequency=byte(frequency)&31
    if control in NO_TONE:return None
    # AY clock=color_clock/2; tone=AYclock/(16*period). Match the source mode
    # repetition frequency, then round half up and clamp the12-bit hardware.
    return max(1,min(4095,(114*MODE_CYCLES[control]*(frequency+1)+16)//32))


def noise_period(frequency):
    frequency=byte(frequency)&31
    return max(1,min(31,(114*(frequency+1)+16)//32))


def psg_step(source_registers,previous):
    """Project one source write's resulting latches; retain unowned PSG state.

    The caller invokes this after EVERY original write, including unchanged
    values, and records that event independently of the physical-write diff.
    Channel A/B follow source0/1. C stays silent. Active POLY9 source0 owns the
    shared noise clock before source1. Other polynomial modes use a square
    carrier at their measured repetition frequency; their timbre is approximate.
    """
    if not isinstance(source_registers,bytes) or len(source_registers)!=6:
        raise ValueError('six immutable source audio-register bytes required')
    old=previous.get('psg') if isinstance(previous,dict) else None
    if not isinstance(old,bytes) or len(old)!=16:raise ValueError('complete previous PSG register state required')
    source=bytes(value&mask for value,mask in zip(source_registers,MASKS));psg=bytearray(old)
    for channel in (0,1):
        period=tone_period(source[channel],source[channel+2])
        if period is not None:psg[channel*2:channel*2+2]=period.to_bytes(2,'little')
    owner=next((ch for ch in (0,1) if source[ch]==8 and source[ch+4]),None)
    if owner is not None:psg[6]=noise_period(source[owner+2])
    parts=tuple(9 if source[ch]in(0,11) else 1 if source[ch]==8 else 8 for ch in (0,1))
    psg[7]=(old[7]&192)|36|parts[0]|(parts[1]<<1)
    psg[8:11]=source[4:6]+bytes(1)
    writes=tuple((register,psg[register]) for register in OWNED_REGISTERS if psg[register]!=old[register])
    return {'source_registers':source,'psg':bytes(psg),'noise_owner':owner,'writes':writes}
