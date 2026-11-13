"""Optional exact precomposed bear cells from the immutable v20 cartridge."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_bear_native import prepared_packet,raw_pattern,row_strip
from presentation_direct_enemy import resident_geometry
from presentation_shared_ownership import constructor
from render_build import symbols

PARENT='c036c3d960da3be4331df6afbb168bc5037777d47be9f4892a16ff6f5d4e43ac'
CONTEXTS=((0,136,0,15),(1,129,0,15),(0,136,0,1),(1,129,0,1),(0,128,0,15),(1,131,0,15),(0,135,1,1),(1,132,0,1),(0,140,1,1))

def build(base,out,mode='native'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('original','native'):raise ValueError('new output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT);files=dict(m['source_files'])
    if len(files)!=170 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v20 source closure changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    s=symbols(base/'presentation.sym');g=resident_geometry(parent,s);tile=constructor(base)
    for name in('p_template_cover_normal','p_template_cover_coarse'):
        if parent[s[name]-0x4000+6:s[name]-0x4000+9]!=bytes([255])*3:raise ValueError('bulk bear rows must take the sealed full background fill')
    def physical(bank,address,size):
        if not 0x8000<=address<address+size<=0xc000:raise ValueError('cross-bank descriptor')
        at=bank*16384+address-0x8000;return parent[at:at+size]
    roots=physical(1,s['p_geo_bear_roots_data'],48);grids=[];ids=set()
    for group in range(16):
        lo,hi,bank=roots[group*3:group*3+3]
        for variant in range(32):
            code=int.from_bytes(physical(bank,lo+hi*256+variant*2,2),'little');c=g['classes'][code>>12];idx=code&4095
            if idx>=c['count']:raise ValueError('bear class index outside original domain')
            at=c['offset']+idx*c['stride'];logical=at//16384;data=physical(logical+3 if logical<11 else logical+242,0x8000+at%16384,c['stride'])
            row=tuple(int.from_bytes(data[i:i+2],'little')for i in range(0,len(data),2));ids.update(row);grids.append((c['columns'],c['rows'],row))
    if len(ids)!=470 or len(grids)!=512:raise ValueError('bear domain differs')
    patterns={n:raw_pattern(parent,m['template_assets']['physical_banks'],s['p_template_pattern_halves_offset'],n,s['p_template_pattern_count'])for n in ids}
    pool=[];pool_index={};indexes={}
    for n in sorted(ids):
        row=[]
        for bank,bg,clip,color in CONTEXTS:
            key=n.to_bytes(2,'little')+bytes((bg,clip,color,0));data=tile(bank,key)
            if len(data)!=16:raise ValueError('complete constructor tile required')
            if data not in pool_index:pool_index[data]=len(pool);pool.append(data)
            index=pool_index[data]
            if clip and not any(x&15 for x in patterns[n]):index|=0x8000
            row.append(index)
        indexes[n]=row
    if len(pool)!=2860:raise ValueError('deduplicated final tile pool differs')
    strips=[];strip_ids={};records=[];record_ids={};directory=bytearray()
    for columns,rows,identifiers in grids:
        strip_indexes=[]
        for theme in range(2):
            for row in range(3):
                bank=0 if row<2 else 1;bg=((136,129),(128,131))[theme][bank]
                row_ids=list(identifiers[row*columns:(row+1)*columns])+[0]*(4-columns)
                strip=row_strip([tile(bank,n.to_bytes(2,'little')+bytes((bg,0,15,0)))for n in row_ids])
                if strip not in strip_ids:strip_ids[strip]=len(strips);strips.append(strip)
                strip_indexes.append(strip_ids[strip])
        data=prepared_packet(columns,rows,identifiers,[indexes[n]for n in identifiers],strip_indexes)
        if data not in record_ids:record_ids[data]=len(records);records.append(data)
        directory.extend(record_ids[data].to_bytes(2,'little'))
    (out/'bear-strips.bin').write_bytes(b''.join(strips))
    if len(strips)>288:raise ValueError('bulk strip allocation exceeded')
    if len(records)>96:raise ValueError('record tail allocation exceeded')
    contexts=bytearray([255])*1024
    for i,(bank,bg,clip,color)in enumerate(CONTEXTS):contexts[(512 if color==15 else 0)+bank*256+(bg-128)*2+clip]=i
    (out/'bear-contexts.bin').write_bytes(contexts);(out/'bear-records.bin').write_bytes(b''.join(records));(out/'bear-directory.bin').write_bytes(directory);(out/'bear-tiles.bin').write_bytes(b''.join(pool))
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if '.'not in n)+'\n')
    source=ROOT/'src/presentation_bear_native.asm';run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"bear-native.bin"}',f'--sym={out/"bear-native.sym"}',f'--lst={out/"bear-native.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'bear-native-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'bear-native.sym');code=(out/'bear-native.bin').read_bytes();size=q['ai_ram_end']-q['ai_entry'];rom=bytearray(parent);patches=[]
    def ins(op,v):return bytes((op,v&255,v>>8))
    def patch(at,new,expected=None):
        old=bytes(rom[at:at+len(new)])
        if expected is not None and old!=expected:raise ValueError(f'guarded patch differs at{at}')
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlap')
        rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
    def tails(first,count,data):
        if len(data)>count*2048:raise ValueError('tail payload exceeded')
        data=data+bytes([255])*(count*2048-len(data))
        for index in range(count):patch((first+index)*16384+0x3800,data[index*2048:(index+1)*2048])
    tails(66,1,directory);tails(67,12,b''.join(records));tails(79,23,b''.join(pool));tails(102,1,code[size:size+2048]);tails(103,9,b''.join(strips));tails(112,1,code[size+2048:])
    if len(code)!=size+4096 or q['ai_entry']!=0xef33 or m['fixed_clock']['ram_code_bytes']!=1587:raise ValueError('kernel allocation differs')
    patch(115*16384+0x3800+1587,code[:size],bytes([255])*size)
    lo=s['t_initializer']-0x4000;hi=s['t_initializer_end']-0x4000;needle=ins(1,1587)
    if parent.count(needle,lo,hi)!=1:raise ValueError('kernel boot copy count differs')
    patch(parent.index(needle,lo,hi),ins(1,1587+size))
    lo=s['presentation_world_prepare']-0x4000;hi=s['p_world_primitive']-0x4000;needle=ins(0xcd,s['p_world_primitive'])+bytes((0xaf,))+ins(0x32,s['p_w_row'])
    if parent.count(needle,lo,hi)!=1:raise ValueError('single bear entry differs')
    patch(parent.index(needle,lo,hi),ins(0xcd,q['ai_entry']))
    for bank in range(66,113):
        start=bank*16384
        if rom[start:start+0x3800]!=parent[start:start+0x3800]:raise ValueError('live contact14 prefix changed')
    for bank in{p['offset']//16384 for p in patches}:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(data);(out/'template-assets'/name).write_bytes(data)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    m['fixed_clock']['ram_code_bytes']=1587+size;m['fixed_clock']['ram_code_sha256']=sha(rom[115*16384+0x3800:115*16384+0x3800+1587+size])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_bear_native.py',ROOT/'tests/test_presentation_bear_native.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='bear-native-ai-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Prepared native bear tiles only. Original mechanics/source/input/audio clock unchanged.'))
    m['bear_native']=dict(parent_rom_sha256=PARENT,patches=patches,descriptor_variants=512,records=len(records),logical_patterns=470,final_tiles=len(pool),bulk_strips=len(strips),contexts=CONTEXTS,directory_bank=66,record_banks=[67,78],tile_banks=[79,101],body_bank=102,reserved_ram_code_bytes_added=size,new_ram_allocation_bytes=0,new_vram_bytes=0,scope='Exact final16byte tiles for nine certified contexts, original per-cell fallback otherwise. Source state unchanged.')
    s.update({n:v for n,v in q.items()if n.startswith('ai_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-bear-native-ai.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),records=len(records),final_tiles=len(pool),reserved_ram_code_bytes_added=size,banked_code_bytes=q['ai_body_end']-q['ai_body']));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','native'),default='native');a=p.parse_args();build(a.base,a.out,a.mode)
