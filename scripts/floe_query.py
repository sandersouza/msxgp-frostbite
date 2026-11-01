"""Independent lookup of RAW original-clock observations, not MSX ROM tables."""
import json
from functools import lru_cache
from pathlib import Path

from floe_catalog import YS,validate_partitions
from floe_truth import sample,view_index
from stella_floe import digest


class RawContacts:
    def __init__(self,directory):
        self.directory=Path(directory);self.manifest=json.loads((self.directory/'catalog.json').read_text())
        if self.manifest.get('complete') is not True:raise ValueError('complete source contact catalog required')
        validate_partitions(self.manifest['partitions'],len(self.manifest['controls']))
        self.controls={tuple(pair):i for i,pair in enumerate(self.manifest['controls'])};self.paths={};self.hashes={}
        for part in self.manifest['partitions']:
            directory=self.directory/f'worker-{part["start"]:03d}-{part["stop"]:03d}'
            for px in range(part['start'],part['stop']):
                name=f'player-{px:03d}.truth';self.paths[px]=directory/name;self.hashes[px]=part['profiles'][name]

    @lru_cache(maxsize=8)
    def profile(self,px):
        path=self.paths[px]
        if digest(path)!=self.hashes[px]:raise ValueError('raw contact profile changed')
        return path.read_bytes()

    def contacts(self,ram):
        if len(ram)!=128:raise ValueError('complete source RAM required')
        result=bytearray([7]*8)
        if ram[0x3F]&128:return {'rows':bytes(result),'shore':7}
        control=self.controls[(ram[0x1C],ram[0x1D])];px=ram[0x66]
        if not 0<=px<160:raise ValueError('source P0 X outside0..159')
        profile=self.profile(px);view=view_index(ram[0x6E],ram[0x6B],bool(ram[0x6C]&8))
        for row,lower in enumerate((123,97,71,45)):
            y=ram[0x64]-lower;yi=y+1 if 0<=y<33 else 0;fx=ram[0x1F+row]
            if not 0<=fx<160:raise ValueError('source floe X outside0..159')
            offset=((yi*len(self.controls)+control)*160+fx)*58
            result[row*2]=sample(profile[offset:offset+58],view)
        return {'rows':bytes(result),'shore':7}
