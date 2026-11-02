"""Ordered real-Z80 controlled graphics matrix; never full-frame acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT
from graphics_mapping import map_frame
from presentation_build import FILES,validate_rom
from presentation_check import decode_target,crc_page
from presentation_cache_ownership import audit_row,ROW_BYTES as OWNERSHIP_BYTES
from presentation_dirty_audit import boot_histories,audit_scene,audit_list,audit_physical_names,ROW_BYTES as DIRTY_BYTES
from presentation_fragments import background_tables
from presentation_model import describe,pixels
from presentation_palette import audit_palette
from presentation_reference import HELPERS as SOURCE_FILES
from presentation_source_cases import FILES as CASE_FILES,collect as collect_source,verify_files
from reference_provenance import audit_manifest,snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*FILES,*SOURCE_FILES,*CASE_FILES,'scripts/presentation_check.py','scripts/presentation_matrix_check.py','scripts/presentation_cache_ownership.py','scripts/presentation_dirty.py','scripts/presentation_dirty_audit.py')))
CAPTURE_BYTES=16392

def sha(data):return hashlib.sha256(data).hexdigest()

def verify_timing(text,count):
    rows=[list(map(int,line.split())) for line in text.splitlines()]
    if len(rows)!=count or any(len(row)!=4 or row[0]!=i or row[1]<=0 or any(0<=y<192 for y in row[2:]) for i,row in enumerate(rows)):
        raise ValueError('incomplete/unordered/visible graphics trace or missing positive cycle measurement')
    return max(row[1] for row in rows)

def check(build_dir,out,*,component='full-scene',family='ntsc',limit=None,explore=False,all_source=False):
    maximum=2115 if all_source else 1690
    if limit is None:limit=maximum
    if component not in ('world','world-hud','without-player','full-scene') or family not in ('ntsc','pal') or type(limit)is not int or not 1<=limit<=maximum:
        raise ValueError('declared controlled domain, component and TV family required')
    producer={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:sha((ROOT/name).read_bytes()) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    build_dir=Path(build_dir).resolve();meta=json.loads((build_dir/'build.json').read_text());artifact=build_dir/meta['rom']['filename'];romdata=artifact.read_bytes()
    if validate_rom(romdata) or sha(romdata)!=meta['rom']['sha256']:raise ValueError('matrix ROM identity changed')
    crc=crc_page(meta,romdata)
    crc_guard=f'if {{[debug read_block memory 0xE100 256] ne [binary format H* {{{crc.hex()}}}]}} {{fail_matrix crc-shadow}}' if crc is not None else ''
    if any(sha((ROOT/name).read_bytes())!=value for name,value in meta['source_files'].items()):raise ValueError('matrix build producer changed')
    if not explore:
        if meta['source_dirty'] or meta['exploratory'] or meta.get('private_contact_reuse'):raise ValueError('canonical matrix requires canonical clean build')
        audit_manifest({'tool_source_commit':meta['source_commit'],'utility_fingerprints':meta['source_files']},FILES)
    bundle=None;source_hashes={}
    if all_source:
        bundle=collect_source();fixtures=bundle['cases'][:limit];authority_sha=bundle['source_receipt_sha256']
    else:
        config=json.loads((ROOT/'references/presentation-source-config.json').read_text());source=ROOT/config['fixtures'][0]
        summary=json.loads((ROOT/'references/presentation-source-result.json').read_text());report_raw=(source/'report.json').read_bytes()
        if sha(report_raw)!=summary['groups']['fixtures']['report_sha256']:raise ValueError('source fixture report changed')
        report=json.loads(report_raw);audit_manifest(report['producer'],SOURCE_FILES)
        fixtures_raw=(source/'fixtures.json').read_bytes()
        if sha(fixtures_raw)!=report['fixture_sha256']:raise ValueError('source fixtures changed')
        fixtures=json.loads(fixtures_raw)[:limit];authority_sha=sha(report_raw)
    palette_config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette=audit_palette(ROOT/palette_config['palette'])
    original=(ROOT/'references/roms/frostbite.bin').read_bytes();cases=bytearray();expected=bytearray()
    for index,sample in enumerate(fixtures):
        if bundle is not None:raw=sample['raster']
        else:
            point=report['points'][index];raw=(source/f'{index:04d}-{sample["name"]}.tia').read_bytes()
            if sha(raw)!=point['raster_sha256'] or sha(bytes(sample['ram']))!=point['before_ram_sha256']:raise ValueError('original fixture identity changed')
            source_hashes[f'{index:04d}-{sample["name"]}.tia']=sha(raw)
        if component!='full-scene':
            model=describe(original,sample)
            if component=='world':model['hud']['score']=[];model['hud']['status']=[];model['igloo']=[]
            if component!='without-player':model['door']=[]
            for row in model['player']['rows']:row['pattern']=row['prefix_pattern']=0
            if component!='without-player':
                for key in ('prefix','logo','playfield','ball'):model['footer'][key]=[]
            raw=pixels(original,model)
        cases.extend(bytes(sample['ram']));expected.extend(map_frame(raw,palette))
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(cases);(out/'expected.tms').write_bytes(expected)
    syms=symbols(build_dir/'presentation.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    profile.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    profile_raw=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(profile);validate_machine_profile(profile_raw)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Matrix.xml').write_bytes(profile_raw)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    entries=[syms[name] for name in ('presentation_prepare','wait_vblank','presentation_commit')]
    rpc=[205,entries[0]&255,entries[0]>>8,219,153]+[byte for entry in entries[1:] for byte in (205,entry&255,entry>>8)]+[195,110,199,24,254]
    sparse=meta['profile'].get('sparse_profile',False)
    dirty=sparse and 'p_dirty_describe' in syms
    listed=dirty and 'p_fast_collect_rows' in syms
    scene_bytes=DIRTY_BYTES+25 if listed else DIRTY_BYTES
    dirty_open=f'set scenes [open {{{out/"scenes.bin"}}} wb]' if dirty else ''
    dirty_close='close $::scenes;' if dirty else ''
    dirty_dump='puts -nonewline $::scenes "[debug read_block memory 0xE540 64][debug read_block memory 0xC2D8 3][debug read_block memory 0xC200 1][debug read_block memory 0xC2DE 2]"' if dirty else ''
    if listed:dirty_dump+=';puts -nonewline $::scenes "[debug read_block memory 0xC2CE 1][debug read_block memory 0xE580 24]"'
    boot_dump=f'set bootfile [open {{{out/"boot.bin"}}} wb];puts -nonewline $bootfile "[debug read_block memory 0xC000 128][debug read_block memory 0xC540 64][debug read_block memory 0xC5A0 64][debug read_block memory 0xC200 1][debug read_block memory 0xC2DE 2]";close $bootfile' if dirty else ''
    ownership_open=f'set owners [open {{{out/"ownership.bin"}}} wb]' if sparse else ''
    ownership_close='close $::owners;' if sparse else ''
    ownership_dump='puts -nonewline $::owners "[debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block memory 0xC080 384][debug read_block memory 0xCCA0 6]"' if sparse else ''
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set captures [open {{{out/'captures.bin'}}} wb]
set timing [open {{{out/'timing.tsv'}}} w]
{ownership_open}
{dirty_open}
proc fail_matrix {{message}} {{puts stderr "MATRIX_FAIL $message case=$::index";exit 1;return -code error $message}}
proc capture_matrix {{}} {{puts -nonewline $::captures [debug read_block VRAM 0 16384];puts -nonewline $::captures [debug read_block {{VDP regs}} 0 8]}}
proc guard_matrix {{}} {{
    {crc_guard}
    if {{[debug read_block memory 0xC000 128] ne $::ram || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_matrix source-state}}
    if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]}} {{fail_matrix heap-redzone}}
    if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_matrix abi}}
    if {{[debug read memory 0xC231]!=0}} {{fail_matrix "compositor miss=[debug read memory 0xCCA6] group=[debug read memory 0xCCA7] family=[debug read memory 0xC227] col=[debug read memory 0xC229] top=[debug read memory 0xC22A] counts=[debug read_block memory 0xCCA0 6]"}}
}}
proc dispatch_matrix {{}} {{
    if {{$::index=={limit}}} {{close $::captures;close $::timing;{ownership_close}{dirty_close}exit;return}}
    set ::ram [string range $::cases [expr {{$::index*128}}] [expr {{$::index*128+127}}]]
    debug write_block memory 0xC000 $::ram
    reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_matrix target}}
    {crc_guard}
    set ::slot [debug read ioports 168];set ::abi [debug read_block memory 0xC600 256]
    {boot_dump}
    debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]
    debug write_block memory 0xC760 [binary format cu* {{{' '.join(map(str,rpc))}}}]
    reg SP 0xF380
    capture_matrix
    set VDP.too_fast_vram_access_callback {{fail_matrix fast-vram}}
    debug set_bp 0xC763 {{}} {{debug break;after break {{
        set ::cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
        guard_matrix;capture_matrix;debug cont
    }}}}
    debug set_bp 0xC768 {{}} {{set ::commit_y [machine_info VDP_msx_y_pos];if {{$::commit_y>=0 && $::commit_y<192}} {{fail_matrix commit-visible}}}}
    debug set_bp 0xC76E {{}} {{debug break;after break {{
        guard_matrix
        set end_y [machine_info VDP_msx_y_pos];if {{$end_y>=0 && $end_y<192}} {{fail_matrix commit-end-visible}}
        capture_matrix
        {ownership_dump}
        {dirty_dump}
        puts $::timing "$::index $::cycles $::commit_y $end_y"
        incr ::index
        if {{$::index%100==0}} {{puts "MATRIX_CAPTURED $::index"}}
        dispatch_matrix
    }}}}
    dispatch_matrix
}}}}]
after time {60+limit*2} {{fail_matrix watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Matrix','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=300)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or 'MATRIX_FAIL' in log:raise ValueError('matrix emulator failed: '+log[-1800:])
    maximum=verify_timing((out/'timing.tsv').read_text(),limit);captured=(out/'captures.bin').read_bytes()
    if len(captured)!=(1+2*limit)*CAPTURE_BYTES:raise ValueError('incomplete native captures')
    if (out/'cases.bin').read_bytes()!=cases or (out/'expected.tms').read_bytes()!=expected:raise ValueError('matrix fixture artifacts changed')
    owners=(out/'ownership.bin').read_bytes() if sparse else b''
    if sparse and len(owners)!=limit*OWNERSHIP_BYTES:raise ValueError('incomplete live cache ownership matrix')
    ownership=[audit_row(owners[i*OWNERSHIP_BYTES:(i+1)*OWNERSHIP_BYTES]) for i in range(limit)] if sparse else []
    scenes=(out/'scenes.bin').read_bytes() if dirty else b''
    if dirty and len(scenes)!=limit*scene_bytes:raise ValueError('incomplete integrated dirty-scene matrix')
    rng=background_tables(original,palette)['rng_index'] if dirty else None
    histories=boot_histories((out/'boot.bin').read_bytes(),rng) if dirty else None
    boot_page=(out/'boot.bin').read_bytes()[256] if dirty else None
    def decode(index):
        row=captured[index*CAPTURE_BYTES:(index+1)*CAPTURE_BYTES]
        return decode_target(row[:16384],row[16384:]),row[16384:]
    previous,registers=decode(0);rows=[];failures=[]
    for index,sample in enumerate(fixtures):
        prepared,prep_regs=decode(index*2+1);presented,present_regs=decode(index*2+2)
        if prepared!=previous or prep_regs!=registers:raise ValueError(f'visible preparation changed at{index}')
        want=expected[index*49152:(index+1)*49152];different=sum(a!=b for a,b in zip(presented,want))
        row={'index':index,'name':sample['name'],'different_pixels':different,'actual_sha256':sha(presented),'expected_sha256':sha(want)}
        if sparse:
            vram=captured[(index*2+2)*CAPTURE_BYTES:(index*2+2)*CAPTURE_BYTES+16384]
            audit_physical_names(vram,owners[index*OWNERSHIP_BYTES:index*OWNERSHIP_BYTES+1536])
        if dirty:row['dirty_rows']=audit_scene(scenes[index*scene_bytes:index*scene_bytes+DIRTY_BYTES],sample['ram'],rng,histories,boot_page^((index+1)&1))
        if listed:audit_list(scenes[index*scene_bytes+DIRTY_BYTES:(index+1)*scene_bytes],scenes[index*scene_bytes+64:index*scene_bytes+67])
        rows.append(row)
        if different:failures.append(row)
        previous,registers=presented,present_regs
        if (index+1)%100==0:print(json.dumps({'checked':index+1,'failures':len(failures)}),flush=True)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producer['utility_fingerprints'].items()) or sha(artifact.read_bytes())!=meta['rom']['sha256']:raise ValueError('matrix producer/ROM changed')
    if bundle is not None:verify_files(bundle['files'])
    elif sha((source/'report.json').read_bytes())!=sha(report_raw) or sha((source/'fixtures.json').read_bytes())!=sha(fixtures_raw) or any(sha((source/name).read_bytes())!=value for name,value in source_hashes.items()):raise ValueError('source matrix changed')
    result={'producer':producer,'exploratory':explore,'component':component,'family':family,'cases':limit,'complete':not failures,'different_frames':len(failures),
            'rom_sha256':sha(romdata),'emulator_sha256':sha(emulator.read_bytes()),'profile_sha256':sha(profile_raw),'source_report_sha256':authority_sha,'domain':'all-source' if all_source else 'controlled-fixtures',
            'source_domain_families':bundle['families'] if bundle is not None else {'fixtures':1690},'unmapped_source_startup':bundle['unmapped_startup'] if bundle is not None else 0,
            'max_prepare_cycles_including_rpc':maximum,'frame_deadline_accepted':False,'full_source_pixels_accepted':component=='full-scene' and not failures,
            'live_cache_ownership_accepted':sparse,'physical_name_pages_accepted':sparse,'integrated_dirty_states_accepted':dirty,'dirty_row_list_accepted':listed,'ownership':ownership,
            'rows':rows,'artifacts':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()},
            'scope':'Ordered injected graphics fixtures, full source/ABI/RAM/slot/VRAM/visible-prepare/VBlank guards; not natural gameplay or whole-frame performance acceptance'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    if failures:raise ValueError(f'{len(failures)} native graphics frames differ; first{failures[0]}')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--component',choices=('world','world-hud','without-player','full-scene'),default='full-scene');p.add_argument('--family',choices=('ntsc','pal'),default='ntsc');p.add_argument('--limit',type=int);p.add_argument('--explore',action='store_true');p.add_argument('--all-source',action='store_true')
    r=check(**vars(p.parse_args()));print(json.dumps({k:r[k] for k in ('complete','cases','component','different_frames','max_prepare_cycles_including_rpc')}))
