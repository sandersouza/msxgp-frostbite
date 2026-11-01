"""Local raster acquisition from the supplied original, with no public pixels."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from reference_inventory import ROOT,verified_input
from reference_provenance import snapshot_paths
from floe_model import player_rows,recover_masks

HELPERS=('scripts/floe_capture.py','scripts/floe_model.py','scripts/reference_inventory.py',
         'scripts/reference_provenance.py','references/manifest.json')
OUT=ROOT/'outputs/floes'


def sha(data):return hashlib.sha256(data).hexdigest()


def new_ale():
    import ale_py
    if ale_py.__version__!='0.12.1':raise ValueError('reviewed ALE0.12.1 required')
    ale=ale_py.ALEInterface();ale.setInt('random_seed',1);ale.setInt('frame_skip',1);ale.setFloat('repeat_action_probability',0)
    ale.loadROM(str(ROOT/'references/roms/frostbite.bin'))
    for _ in range(20):ale.act(0)
    return ale


def mask_rows(frame,top):
    rows=[]
    for y in range(top,top+7):
        row=bytearray(20)
        for x in range(160):
            if frame[y*160+x]==12:row[x//8]|=128>>(x%8)
        rows.append(bytes(row))
    return rows


def capture_catalog(destination,explore=False):
    import ale_py._ale_py as binary
    source=verified_input(ROOT/'references/roms/frostbite.bin');rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
    if dirty and not explore:raise ValueError('commit canonical raster producers first')
    producer=snapshot_paths(HELPERS) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{p:sha((ROOT/p).read_bytes()) for p in HELPERS}}
    destination=Path(destination).resolve()
    if destination.exists() or not destination.is_relative_to(OUT.resolve()):raise ValueError('fresh owned raster directory required')
    destination.mkdir(parents=True);runs=[]
    for repeat in range(2):
        ale=new_ale();initial=ale.cloneSystemState();directory=destination/f'run-{repeat}';directory.mkdir()
        (directory/'initial.state').write_bytes(initial.serialize())
        masks=bytearray();actual=bytearray();states=bytearray();screens=bytearray()
        for phase in range(16):
            shape=rom[0xDE0+phase]
            for x in range(160):
                ale.restoreSystemState(initial)
                patch={0xC5:0,0xC6:0,0xE7:127,0xCB:0,0xCD:0,0xE4:0,0xEB:0,0xEE:0,0xEC:0,0xF0:0,
                    0x9E:phase,0x9C:(shape<<4)&255,0x9D:shape&240,
                    **{0x9F+r:x for r in range(4)},**{0xAB+r:12 for r in range(4)},**{0xD8+r:0 for r in range(4)}}
                for a,v in patch.items():ale.setRAM(a&127,v)
                ale.act(0);frame=ale.getScreen().tobytes();ram=bytes(ale.getRAM())
                if any(ram[a&127]!=v for a,v in patch.items() if a not in (0xE7,0xCD)):
                    raise ValueError('raster selector changed during fixture')
                rows=mask_rows(frame,96)
                if any(mask_rows(frame,top)!=rows for top in (122,148,174)):raise ValueError('floe row windows have different geometry')
                masks+=b''.join(rows);actual+=ram;states+=ale.cloneSystemState().serialize();screens+=frame
        blobs={'masks.bin':masks,'actual.bin':actual,'states.bin':states,'screens.bin':screens}
        for name,data in blobs.items():(directory/name).write_bytes(data)
        runs.append({name:sha(data) for name,data in blobs.items()})
        print(f'Original floe raster repeat{repeat+1}:2560positions/phases, four windows each',flush=True)
    if runs[0]!=runs[1]:raise ValueError('independent full raster/state executions differ')
    # Deduplicate exact 160-bit rows, never coarsen or use a bounding rectangle.
    observed=load_catalog_raw(destination,[[rom[0xDE0+p]<<4&255,rom[0xDE0+p]&240] for p in range(16)])
    recovered=recover_masks(observed)
    raw=b''.join(row for p in range(16) for x in range(160)
        for row in recovered[(rom[0xDE0+p]<<4&255,rom[0xDE0+p]&240,x)])
    (destination/'collision-masks.bin').write_bytes(raw)
    unique={};pool=bytearray();indices=bytearray()
    for i in range(0,len(raw),20):
        row=raw[i:i+20]
        if row not in unique:unique[row]=len(unique);pool+=row
        indices+=unique[row].to_bytes(2,'little')
    (destination/'row-pool.bin').write_bytes(pool);(destination/'row-index.bin').write_bytes(indices)
    report={'schema':1,'source':source,**producer,'explore':explore,'source_dirty':dirty,
        'backend':{'name':'ALE','version':'0.12.1','binary_sha256':sha(Path(binary.__file__).read_bytes()),'seed':1,'frame_skip':1,'repeat_action_probability':0},
        'cases':2560,'source_windows':10240,'independent_runs':2,'unique_rows':len(unique),'pool_bytes':len(pool),'index_bytes':len(indices),
        'controls':[[rom[0xDE0+p]<<4&255,rom[0xDE0+p]&240] for p in range(16)],'runs':runs,
        'collision_masks_sha256':sha(raw),'row_pool_sha256':sha(pool),'row_index_sha256':sha(indices)}
    (destination/'catalog.json').write_text(json.dumps(report,indent=2)+'\n');return report


def load_catalog_raw(directory,controls,filename='run-0/masks.bin'):
    raw=(Path(directory)/filename).read_bytes()
    if len(raw)!=16*160*7*20 or len(controls)!=16:raise ValueError('complete phase/position raster required')
    result={}
    for phase,control in enumerate(controls):
        for x in range(160):
            start=(phase*160+x)*140;rows=tuple(raw[start+y*20:start+(y+1)*20] for y in range(7));key=(*control,x)
            if key in result and result[key]!=rows:raise ValueError('identical controls produced different rows')
            result[key]=rows
    return result


def load_catalog(directory):
    directory=Path(directory);report=json.loads((directory/'catalog.json').read_text());raw=(directory/'collision-masks.bin').read_bytes()
    if sha(raw)!=report['collision_masks_sha256']:raise ValueError('changed collision raster catalog')
    return load_catalog_raw(directory,report['controls'],'collision-masks.bin')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--explore',action='store_true');parser.add_argument('--out',type=Path)
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    destination=args.out or Path(tempfile.mkdtemp(prefix='catalog-',dir=OUT))/'raw'
    result=capture_catalog(destination,args.explore)
    print(json.dumps({k:result[k] for k in ('cases','unique_rows','pool_bytes','index_bytes')}));print(destination)
