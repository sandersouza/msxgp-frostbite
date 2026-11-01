"""Independent raw original observations for all source collision windows.

No compiled cartridge pointers or generated MSX masks are read by this oracle.
The ordinary single-copy basis requires a separately accepted alias proof.
"""
from functools import lru_cache
import json
from pathlib import Path

from environment import ROOT
from floe_query import RawContacts as RawFloes
from floe_truth import sample,view_index
from hazard_catalog import EDGE_XS
from hazard_tables import validate_layout
from reference_inventory import verified_input
from stella_hazard import digest


def row_y(y,row):
    value=y-(3-row)*26
    return value if 32<=value<=65 else 0


def shore_y(y):
    return y if 4<=y<=56 else 0


class Component:
    def __init__(self,root,rom):
        self.root=Path(root);self.plan=json.loads((self.root/'catalog.json').read_text())
        validate_layout(self.plan,rom)
        if self.plan['source']!=verified_input(ROOT/'references/roms/frostbite.bin'):
            raise ValueError('raw source component ROM differs')
        self.paths={};self.hashes={}
        for part in self.plan['partitions']:
            directory=self.root/f'worker-{part["start"]:03d}-{part["stop"]:03d}'
            for px in self.plan['player_x'][part['start']:part['stop']]:
                name=f'player-{px:03d}.truth';self.paths[px]=directory/name;self.hashes[px]=part['profiles'][name]
        self.modes={tuple(sorted(mode.items())):index for index,mode in enumerate(self.plan['modes'])}

    @lru_cache(maxsize=2)
    def profile(self,px):
        path=self.paths[px]
        if digest(path)!=self.hashes[px]:raise ValueError('raw source profile changed')
        data=path.read_bytes()
        if len(data)!=self.plan['cases_per_player']*58:raise ValueError('partial raw source profile')
        return data

    def record(self,px,y,mode,coordinate):
        data=self.profile(px);p=self.plan
        index=((p['ys'].index(y)*len(p['modes'])+self.modes[tuple(sorted(mode.items()))])*len(p['coordinates'])+p['coordinates'].index(coordinate))*58
        return data[index:index+58]


class RawContacts:
    def __init__(self,floes,edge,ordinary,shore):
        rom=(ROOT/'references/roms/frostbite.bin').read_bytes();self.floes=RawFloes(floes)
        self.edge=Component(edge,rom);self.ordinary=Component(ordinary,rom);self.shore=Component(shore,rom)

    def row_record(self,ram,row):
        px=ram[0x66];y=row_y(ram[0x64],row);shape=ram[0x23+row];reflection=bool(ram[0x11+row]&128);copies=ram[0x58+row];x=ram[0x54+row]
        if not 0<=px<160 or not 0<=x<160 or copies not in range(4):raise ValueError('original object coordinate outside complete domain')
        if px in EDGE_XS:
            return self.edge.record(px,y,{'shape':shape,'reflection':reflection,'nusiz':copies},x)
        result=bytearray(58)
        for copy in {0:(0,),1:(0,16),2:(0,32),3:(0,16,32)}[copies]:
            distance=(px-x-copy)%160
            if distance>152:distance-=160
            if distance not in range(-7,8):continue
            data=self.ordinary.record(px,y,{'shape':shape,'reflection':reflection,'nusiz':0},distance)
            for index in range(58):result[index]|=data[index]
        return bytes(result)

    def shore_record(self,ram):
        pose=ram[0x6F];px=ram[0x66];x=ram[0x68]
        if not 0<=pose<8 or not 0<=px<160 or not 0<=x<160:raise ValueError('original shore coordinate outside complete domain')
        aliases=self.shore.plan['bear_pose_aliases'];representatives=sorted({mode['bear_pose'] for mode in self.shore.plan['modes']})
        return self.shore.record(px,shore_y(ram[0x64]),{'bear_pose':representatives[aliases[pose]],'reflection':bool(ram[0x6C]&16)},x)

    def contacts(self,ram):
        if len(ram)!=128:raise ValueError('complete original RAM required')
        if ram[0x3F]&128:return {'rows':bytes([7])*8,'shore':7}
        view=view_index(ram[0x6E],ram[0x6B],bool(ram[0x6C]&8));rows=bytearray(self.floes.contacts(ram)['rows'])
        for row in range(4):rows[row*2+1]=sample(self.row_record(ram,row),view)
        return {'rows':bytes(rows),'shore':sample(self.shore_record(ram),view)}
