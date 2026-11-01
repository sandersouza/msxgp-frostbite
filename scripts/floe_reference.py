"""Original visible instructions with explicit per-window electrical samples."""
from py65.devices.mpu6502 import MPU
from mechanics_probe import SliceBus


class VisibleBus(SliceBus):
    def __init__(self,rom,contacts):
        super().__init__(rom,{0x284:0,**{i:i for i in range(16)}})
        self.contacts=contacts;self.pc=0;self.ram_writes=[]

    def __getitem__(self,address):
        kind,offset=self.decode(address)
        if kind=='hardware' and offset==7:
            if self.pc==0xF244:return self.contacts['shore']
            if self.pc in (0xF331,0xF3BE):return self.contacts['rows'][self.ram[0x3A]]
        return super().__getitem__(address)

    def __setitem__(self,address,value):
        kind,offset=self.decode(address,True)
        if kind=='ram':self.ram_writes.append((self.pc,offset,value))
        super().__setitem__(address,value)


def visible_reference(rom,ram,registers,contacts):
    bus=VisibleBus(rom,contacts);bus.ram[:]=ram
    cpu=MPU(memory=bus,pc=0xF019)
    for key in ('a','x','y','p','sp'):setattr(cpu,key,registers.get(key,0x30 if key=='p' else 255 if key=='sp' else 0))
    count=0
    while cpu.pc!=0xF476:
        if count>=12000:raise ValueError('visible instruction watchdog')
        bus.pc=cpu.pc;cpu.step();count+=1
    return {'ram':bytes(bus.ram),'registers':{k:getattr(cpu,k) for k in ('a','x','y','p','sp')},
            'instructions':count,'ram_writes':bus.ram_writes}
