#!/usr/bin/env python3
"""Local original-ROM graphics evidence and offline SCREEN2 asset-fit checks."""
import argparse
import hashlib
import json
import copy
import re
from pathlib import Path
import signal
import subprocess
import sys
import uuid

from reference_inventory import ROOT,verified_input
from reference_provenance import snapshot_paths
from original_graphics import catalog,view,SOURCE_SHA256
from graphics_mapping import map_x,map_y,map_frame,compile_screen,decode_screen,TMS_RGB
from render_model import decode_pixels,occupancy

HELPERS=('scripts/graphics_reference.py','scripts/original_graphics.py','scripts/graphics_mapping.py',
         'scripts/reference_inventory.py','scripts/reference_provenance.py','references/manifest.json',
         'references/graphics-contract.json','scripts/render_model.py')
FACTS=('cases','table_views','raw_matches','blank_views','repeat_equal','max_tiles_per_bank',
       'max_changed_pixels','total_changed_pixels','overcolor_rows','crop_checked',
       'source_state_unchanged_by_mapping','families','palette_codes','target_vram_bytes',
       'runtime_changed','negative_controls','max_sprites_per_line','max_sprite_patterns_bytes','total_patched_pixels',
       'igloo_distinct_states','daynight_source_probe_verified')


def digest(data):return hashlib.sha256(data).hexdigest()


def validate_crop(frame):
    if len(frame)!=160*210 or any(frame[y*160:(y+1)*160] != bytes(160) for y in range(210) if map_y(y) is None):
        raise ValueError('nonblack content in omitted source rows or invalid frame')


def match_view(frame,item,colors,candidates):
    width=item['width'];height=item['height'];bits=item['pixels']
    if len(frame)!=160*210 or len(bits)!=width*height or len(colors)!=height or not any(bits):
        raise ValueError('invalid/nonvisible table view')
    color_set={c&254 for c in colors}
    for x,y in candidates:
        if x<0 or y<0 or x+width>160 or y+height>210:continue
        good=True
        for row in range(height):
            for column in range(width):
                pixel=frame[(y+row)*160+x+column];bit=bits[row*width+column]
                if (bit and pixel!=(colors[row]&254)) or (not bit and pixel in color_set):
                    good=False;break
            if not good:break
        if good:return x,y
    raise ValueError('original raster differs from decoded table view')


def validate_repeats(first,second,expected):
    if not first or [p['name'] for p in first]!=expected or first!=second:
        raise ValueError('incomplete or differing independent original captures')
    for point in first:
        if point['requested']!=point['actual'] or not point['raw_match']:
            raise ValueError('requested presentation state was not observed/validated')
        if len(point['tiles_per_bank'])!=3 or max(point['tiles_per_bank'])>192:
            raise ValueError('SCREEN2 tile allocation exceeded')
        for key in ('source_sha256','state_sha256','ram_sha256','mapped_sha256','vram_sha256','decoded_sha256'):
            if len(point[key])!=64 or any(c not in '0123456789abcdef' for c in point[key]):
                raise ValueError('exact frame/state/artifact digest required')


def compact_report(run):
    return {key:run[key] for key in ('source_sha256','tool_source_commit','private_sha256')}|{
        'utility_fingerprints':{k:v for k,v in run['utility_fingerprints'].items() if k in HELPERS},
        'backend':{k:v for k,v in run['backend'].items() if k in ('name','version','binary_sha256','numpy','seed','frame_skip','repeat_action_probability')},
        'schema_version':1,'facts':{key:run['facts'][key] for key in FACTS if key in run['facts']},
        'limits':['Controlled presentation fixtures, not natural reachability or full-game proof',
                  'Offline background/sprite repair VRAM fit; native adapter/cache timing and ROM integration remain unimplemented',
                  'Measured emulator RGB nearest nominal TMS palette is approximate; physical colors/manual/hardware pending',
                  'Every dynamic renderer/ROM change must remeasure all layouts/widths/transitions/NTSC/PAL']}


def validate_files(directory,points):
    suffixes={'tia','before-ram','ram','state','mapped','vram','target'}
    initial=Path(directory)/'initial.state'
    if not initial.is_file() or initial.is_symlink() or not points:
        raise ValueError('initial original state missing or changed')
    initial_hash=digest(initial.read_bytes())
    if any(initial_hash!=p['initial_sha256'] for p in points):raise ValueError('initial original state changed')
    for index,point in enumerate(points):
        if not re.fullmatch('[a-z0-9-]{1,80}',point['name']) or set(point['file_sha256'])!=suffixes:
            raise ValueError('bounded complete raw artifact list required')
        for suffix,expected in point['file_sha256'].items():
            path=Path(directory)/f'{index:04d}-{point["name"]}.{suffix}'
            if not path.is_file() or path.is_symlink() or digest(path.read_bytes())!=expected:
                raise ValueError('saved original/target artifact missing or changed')


def validate_target(vram,expected):
    peak=max(occupancy(vram[0x1B00:0x1B80]))
    if peak>4:raise ValueError('actual SAT exceeds4 sprite rectangles per line')
    if decode_screen(vram)!=expected or bytes(decode_pixels(vram,bytes([2,0xC2,6,255,3,54,7,1])))!=expected:
        raise ValueError('independently decoded actual VRAM differs from mapped source')


def validate_variation(points):
    indexed={point['name']:point for point in points}
    stages={indexed[f'igloo-{i}']['source_sha256'] for i in range(16)}
    if len(stages)!=16:raise ValueError('igloo requested stages did not produce16 distinct source rasters')
    if indexed['palette-0-floe-0']['source_sha256']==indexed['palette-7-floe-0']['source_sha256']:
        raise ValueError('day/night source rasters did not change')
    if (indexed['palette-0-floe-0']['source_probe']!=[132,10]
            or indexed['palette-7-floe-0']['source_probe']!=[128,2]):
        raise ValueError('actual source day/night sky/shore colors do not match original palette paths')


def fixtures(rom):
    result=[]
    def add(name,family,patch,asset=None):result.append({'name':name,'family':family,'patch':patch,'asset':asset})
    # Keep the player in open water for table checks, far from shore/other actors.
    for pose in range(6):
        for reflection in range(2):
            for shift in range(19):
                add(f'player-{pose}-{reflection}-{shift}','player',
                    {0xEE:pose,0xEC:reflection*8,0xEB:shift,0xF0:0,0xE4:60,0xE6:64},
                    f'player-{pose}-{reflection}-{shift}')
    for frame in range(8):
        for reflection in range(2):
            add(f'bear-{frame}-{reflection}','bear',{0xEF:frame,0xEC:reflection*16,0xE8:100,0xCB:3},f'bear-{frame}-{reflection}')
    for pose in (4,5):
        for reflection in range(2):
            for fade in range(1,18):
                add(f'fade-{pose}-{reflection}-{fade}','player',
                    {0xEE:pose,0xEC:reflection*8,0xEB:0,0xF0:fade,0xE4:60,0xE6:64},
                    f'fade-{pose}-{reflection}-{fade}')
    for kind in range(4):
        for phase in range(2):
            for sway in range(1 if kind==0 else 5):
                for reflection in range(2):
                    pointer=rom[0xD0A+kind*2+phase]+sway;color=rom[0xD00+kind]&254
                    add(f'row-{kind}-{phase}-{sway}-{reflection}','row',
                        {0xA3:pointer,0xA7:color,0x91:reflection*128+kind,0xD4:32,0xD8:1},
                        f'row-{kind}-{phase}-{sway}-{reflection}')
    for digit in range(10):
        add(f'digit-{digit}','hud',{0xC8:digit*17,0xC9:digit*17,0xCA:digit*17,0xE5:digit*17,0xCC:digit},f'digit-{digit}')
    for stage in range(16):add(f'igloo-{stage}','igloo',{0xCD:stage})
    for rng in (1,9):
        for level in (3,7):add(f'door-{level}-{rng}','igloo',{0xCD:15,0x82:rng,0xCB:level})
    for player in (0,2):add(f'hud-player-{player}-level20','hud-scene',{0xC7:player,0xCB:20,0xC8:0x12,0xC9:0x34,0xCA:0x56})
    for level in (0,3,7,8,11,15):
        for phase in range(16):
            add(f'palette-{level}-floe-{phase}','palette-floe',{0xCB:level,0x9E:phase,
                0x9C:(rom[0xDE0+phase]<<4)&255,0x9D:rom[0xDE0+phase]&240,
                0xAB:12 if phase%2 else 152,0xAC:152 if phase%2 else 12})
    for x in (0,1,7,8,148,151,158,159):
        add(f'edge-{x}','edge',{0xE6:x,0xE8:x,0xCB:3})
        for copies in range(4):
            add(f'wrap-{x}-{copies}','row-wrap',{0xA3:rom[0xD0A],0xA7:142,0xD4:x,0xD8:copies,
                0x9F:x,0xA0:x,0xA1:x,0xA2:x})
    return result


def source_check(frame,fixture,assets,ram):
    name=fixture['asset']
    if name is None:return True,None
    item=assets[name]
    if not any(item['pixels']):return True,'blank'
    family=fixture['family']
    if family=='player':
        colors=item['colors'];candidates=[(x,y) for y in range(85,91) for x in range(62,67)]
    elif family=='bear':
        colors=[int(ram[0xBD-128])]*19;candidates=[(x,y) for y in range(48,65) for x in range(98,103)]
    elif family=='row':
        colors=[item['color']]*8;candidates=[(x,y) for y in range(158,164) for x in range(30,35)]
    else:
        colors=[142]*8;candidates=[(x,y) for y in (10,22) for x in range(8,145)]
    return True,match_view(frame,item,colors,candidates)


def png(path,pixels,width,height,palette):
    import struct,zlib
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    raw=b''.join(b'\0'+b''.join(bytes(palette[c]) for c in pixels[y*width:(y+1)*width]) for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def capture(rom_path,destination,explore=False):
    import ale_py
    import ale_py._ale_py as binary
    import numpy
    source=verified_input(Path(rom_path));rom=Path(rom_path).read_bytes();assets=catalog(rom)
    if ale_py.__version__!='0.12.1':raise ValueError('reviewed ALE0.12.1 required')
    destination=Path(destination).resolve()
    if not destination.is_relative_to(ROOT/'outputs') or destination==ROOT/'outputs':raise ValueError('fresh local outputs/ destination required')
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
    if dirty and not explore:raise ValueError('canonical graphics capture requires clean committed producers')
    producer=snapshot_paths(HELPERS) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{p:digest((ROOT/p).read_bytes()) for p in HELPERS}}
    binary_hash=digest(Path(binary.__file__).read_bytes());destination.mkdir(parents=True,exist_ok=False)
    (destination/'catalog.json').write_text(json.dumps(assets)+'\n')
    cases=fixtures(rom);runs=[];palette={};max_tiles=[0,0,0];max_changed=total_changed=crowded=raw_matches=blank=0
    max_sprites=max_patterns=patched=0
    for repeat in range(2):
        ale=ale_py.ALEInterface();ale.setInt('random_seed',1);ale.setInt('frame_skip',1);ale.setFloat('repeat_action_probability',0)
        ale.loadROM(str(rom_path))
        for _ in range(20):ale.act(0)
        baseline=ale.cloneSystemState();initial=digest(baseline.serialize());directory=destination/f'run-{repeat}';directory.mkdir();points=[]
        (directory/'initial.state').write_bytes(baseline.serialize())
        for index,fixture in enumerate(cases):
            ale.restoreSystemState(baseline)
            for address,value in fixture['patch'].items():ale.setRAM(address&127,value)
            if fixture['family']=='igloo':
                # C0..C4 are prepared in the prior frame's overscan from CD.
                # A RAM selector change alone is not evidence of a drawn stage.
                ale.act(0)
                for address,value in fixture['patch'].items():ale.setRAM(address&127,value)
            before=bytes(ale.getRAM());ale.act(0);ram=bytes(ale.getRAM());frame=ale.getScreen().tobytes();rgb=ale.getScreenRGB().reshape(-1,3)
            for code in set(frame):
                offset=frame.index(code);color=tuple(int(c) for c in rgb[offset])
                if code in palette and palette[code]!=color:raise ValueError('inconsistent original palette RGB')
                palette[code]=color
            validate_crop(frame)
            try:matched,location=source_check(frame,fixture,assets['assets'],ram)
            except ValueError as error:raise ValueError(f'{fixture["name"]}: {error}') from error
            state=ale.cloneSystemState().serialize();mapped=map_frame(frame,palette);compiled=compile_screen(mapped,restore=True);decoded=decode_screen(compiled['vram'])
            validate_target(compiled['vram'],mapped)
            if digest(ale.cloneSystemState().serialize())!=digest(state) or bytes(ale.getRAM())!=ram:
                raise ValueError('offline mapping changed original state')
            actual={f'{a:02x}':ram[a&127] for a in fixture['patch']};requested={f'{a:02x}':v for a,v in fixture['patch'].items()}
            point={'name':fixture['name'],'family':fixture['family'],'requested':requested,'actual':actual,
                'source_sha256':digest(frame),'state_sha256':digest(state),'ram_sha256':digest(ram),
                'mapped_sha256':digest(mapped),'vram_sha256':digest(compiled['vram']),'decoded_sha256':digest(decoded),
                'tiles_per_bank':compiled['tiles_per_bank'],'changed_pixels':compiled['changed_pixels'],
                'overcolor_rows':compiled['overcolor_rows'],'raw_match':matched,'match_location':location,'initial_sha256':initial,
                'source_probe':[frame[10*160+10],frame[45*160+10]]}
            if sum(a!=b for a,b in zip(mapped,decoded))!=compiled['changed_pixels']:raise ValueError('independent VRAM decode loss count differs')
            stem=directory/f'{index:04d}-{fixture["name"]}'
            blobs={'tia':frame,'before-ram':before,'ram':ram,'state':state,'mapped':mapped,'vram':compiled['vram'],'target':decoded}
            point['file_sha256']={suffix:digest(data) for suffix,data in blobs.items()}
            for suffix,data in blobs.items():
                stem.with_suffix('.'+suffix).write_bytes(data)
            if index==0 or fixture['family']=='igloo' or fixture['name'] in ('palette-8-floe-0','palette-3-floe-0'):
                png(stem.with_suffix('.source.png'),frame,160,210,palette)
                png(stem.with_suffix('.target.png'),decoded,256,192,TMS_RGB)
            points.append(point)
            if repeat==0:
                max_tiles=[max(a,b) for a,b in zip(max_tiles,compiled['tiles_per_bank'])]
                max_changed=max(max_changed,compiled['changed_pixels']);total_changed+=compiled['changed_pixels'];crowded+=compiled['overcolor_rows']
                max_sprites=max(max_sprites,compiled['sprites_per_line']);max_patterns=max(max_patterns,compiled['sprite_patterns_bytes']);patched+=compiled['patched_pixels']
                if fixture['asset'] is not None:
                    if location=='blank':blank+=1
                    else:raw_matches+=1
        validate_files(directory,points)
        (directory/'points.json').write_text(json.dumps(points,indent=2)+'\n');runs.append(points)
        print(f'Original graphics repeat{repeat+1}: {len(points)} frames',flush=True)
    validate_repeats(*runs,[case['name'] for case in cases]);validate_variation(runs[0]);validate_variation(runs[1])
    negatives=[]
    for key,value in [('source_sha256','0'*64),('actual',{})]:
        wrong=copy.deepcopy(runs[1]);wrong[0][key]=value
        try:validate_repeats(runs[0],wrong,[case['name'] for case in cases])
        except ValueError:negatives.append(key)
        else:raise ValueError('corrupted evidence escaped rejection')
    first=destination/'run-0/0000-player-0-0-0.tia';original=first.read_bytes()
    first.write_bytes(bytes([original[0]^1])+original[1:])
    try:validate_files(destination/'run-0',runs[0])
    except ValueError:negatives.append('saved_pixels')
    else:raise ValueError('changed saved pixels escaped rejection')
    finally:first.write_bytes(original)
    item=assets['assets']['player-0-0-0'];x,y=runs[0][0]['match_location'];bad=bytearray(original)
    bit=item['pixels'].index(1);bad[(y+bit//8)*160+x+bit%8]^=2
    try:match_view(bytes(bad),item,item['colors'],[(x,y)])
    except ValueError:negatives.append('table_pixels')
    else:raise ValueError('corrupted table pixel escaped rejection')
    target=(destination/'run-0/0000-player-0-0-0.mapped').read_bytes()
    original_vram=(destination/'run-0/0000-player-0-0-0.vram').read_bytes()
    corrupt=bytearray(original_vram);tile=corrupt[0x1800];corrupt[tile*8]=255;corrupt[0x2000+tile*8]=0xF1
    try:validate_target(bytes(corrupt),target)
    except ValueError:negatives.append('target_pixels')
    else:raise ValueError('changed target pixels escaped rejection')
    corrupt=bytearray(original_vram)
    for index in range(5):corrupt[0x1B00+4*index:0x1B04+4*index]=bytes([255,index*16,0,1])
    corrupt[0x1B14]=208
    try:validate_target(bytes(corrupt),target)
    except ValueError as error:
        if 'sprite' not in str(error):raise
        negatives.append('fifth_sprite')
    else:raise ValueError('fifth sprite rectangle escaped rejection')
    validate_files(destination/'run-0',runs[0])
    if not explore:
        if snapshot_paths(HELPERS)!=producer:raise ValueError('producer changed during capture')
    if digest(Path(binary.__file__).read_bytes())!=binary_hash or verified_input(Path(rom_path))!=source:
        raise ValueError('ROM/backend changed during capture')
    private={'runs':runs,'palette':palette,'catalog_sha256':digest((destination/'catalog.json').read_bytes())}
    (destination/'evidence.json').write_text(json.dumps(private,indent=2)+'\n')
    result={'source_sha256':SOURCE_SHA256,**producer,'backend':{'name':'ALE','version':ale_py.__version__,'binary_sha256':binary_hash,'numpy':numpy.__version__,
        'seed':1,'frame_skip':1,'repeat_action_probability':0},'private_sha256':digest((destination/'evidence.json').read_bytes()),
        'facts':{'cases':len(cases),'table_views':len(assets['assets']),'raw_matches':raw_matches,'blank_views':blank,'repeat_equal':True,
            'max_tiles_per_bank':max_tiles,'max_changed_pixels':max_changed,'total_changed_pixels':total_changed,'overcolor_rows':crowded,
            'crop_checked':True,'source_state_unchanged_by_mapping':True,'families':sorted({c['family'] for c in cases}),
            'palette_codes':len(palette),'target_vram_bytes':16384,'runtime_changed':False,'negative_controls':negatives,
            'max_sprites_per_line':max_sprites,'max_sprite_patterns_bytes':max_patterns,'total_patched_pixels':patched}}
    result['facts'].update({'igloo_distinct_states':16,'daynight_source_probe_verified':True})
    (destination/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if not explore:(ROOT/'references/graphics-result.json').write_text(json.dumps(compact_report(result),indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'outputs/graphics'/uuid.uuid4().hex);parser.add_argument('--explore',action='store_true')
    args=parser.parse_args();signal.alarm(300)
    try:
        result=capture(ROOT/'references/roms/frostbite.bin',args.out,args.explore)
        print(json.dumps(result['facts'],indent=2));print(f'Local derived artifacts: {args.out}');return 0
    except (ValueError,OSError,KeyError) as error:
        print(f'Graphics evidence refused: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
