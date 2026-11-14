"""Conservative native RAM allocation experiment, never a playable binary.

Every extent names its fixed owner or the source-level reason it is reusable.
Observed ROM coverage identifies consumers, not permission to omit other states.
Code reservations are explicit upper bounds pending source assembly/link tests.
"""
import argparse
import json
from pathlib import Path

from build_compact_packet_experiment import digest
from native_flat_layout import Layout
from native_graphic_grammar import floes,p0
from render_build import symbols
from reference_traces import private_output


def merged(rows):
    result=[]
    for a,b in sorted(rows):
        if result and a<=result[-1][1]:result[-1]=(result[-1][0],max(b,result[-1][1]))
        else:result.append((a,b))
    return result


def free_extents(m,*,native_lifetimes=False):
    from compact_enemy_ram_check import native_code_size
    enemy_end=0xE300+native_code_size(m)
    rows=[(r['address'],r['address']+r['size']) for r in m['compact_retired_resident']['ranges']]
    rows += [(r['address'],r['address']+r['size']) for r in m['compact_grid_palette']['reclaimed_ranges']]
    rows += [(0x0040,0x0100),(0x0940,0x0A00),(0x0E6A,0x0F00),(0x0F06,0x0F10),(0x0F9A,0x0FA0),
             (0x0FA4,0x0FC0),(0x0FE0,0x1000),(0x10A0,0x1100),(0x2921,0x2930),(0x293F,0x2940),
             (0x2968,0x2970),(0x2999,0x29A0),(0x29F5,0x2A00),(0x2F50,0x2F60),(0x2F6A,0x3000),
             (0x30BA,0x3100),(0x3221,0x3300),(0x3307,0x3400),(0x34C0,0x3500),(0x3551,0x3600),
             (0x3689,0x3690),(0x3FEB,0x4000)]
    # Core source ends BDFA; standing-shore module has one optional entry,
    # bypassed through the exact preserved native generator in this parent.
    rows += [(0xA34A,0xA400),(0xBA91,0xBBC7),(0xBDFA,0xC000)]
    # Fixed current copy extents/ABIs, not old names of RAM regions. These are
    # provisional until immutable-object/read-write guards run on the linked game.
    # C080..C17F is all eight32-byte P0 ways, including the area historically
    # named diagnostic_input. Preserve the complete current cache ABI.
    rows += [(0xC348,0xC380),(0xC580,0xC5A0),(0xC5E0,0xC600),(0xC60C,0xC620),
             (0xC623,0xC6F0),(0xC6F5,0xC6FD),(0xC7A0,0xC7B0),(0xC7B3,0xC7E0),(0xCB00,0xCC80),(0xDA09,0xDB00),
             (0xDFBE,0xE000),(0xE015,0xE100),(0xE100,0xE240),(0xE280,0xE2E0),(0xE2E4,0xE300),
             (enemy_end,0xE500),(0xEF3F,0xEFC1),(0xEFD1,0xEFE3),(0xF080,0xF300),(0xF380,0xF400),
             (0xFAC5,0xFC00),(0xFC18,0xFD00),(0xFD8B,0xFFF4)]
    # No runtime reader returns to the retired startup/preload routines. Their
    # cartridge source is retained during the takeover experiment.
    rows += [(0x4000,0x40B1),(0x4A7B,0x4AC9),(0x7C51,0x7D29),(0x7F20,0x7F46)]
    if native_lifetimes:
        from native_unused_keys import extents
        rows += list(extents())
        # Source-proved old table consumers / cold initializers. Their public
        # native gates are preserved; the linked image must guard every byte.
        # This is a candidate lifetime model until takeover read/write checks.
        rows += [(0x40B1,0x4123),(0x4AC9,0x4B02),(0x4B6E,0x4BBE),(0x6FD2,0x70DE),
                 (0x7273,0x7300),(0x7B63,0x7BE8),(0x7E5D,0x7EDB),
                 (0x7EEB,0x7F0C),(0x4BBF,0x4C00),(0x55FF,0x5616),
                 (0x561A,0x566B),(0x5042,0x506B)]
    return merged(rows)


def catalog(build,out,*,native_lifetimes=False,fast_P0=False,fast_bands=False):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if digest(rom)!=m['rom']['sha256'] or not m.get('native_name_palette_trial') or not m.get('native_p0_shore_trial'):
        raise ValueError('bound combined size experiment required')
    def read(bank,a,n):return rom[bank*16384+a-0x8000:bank*16384+a-0x8000+n]
    q=Layout(free_extents(m,native_lifetimes=native_lifetimes));total=sum(b-a for a,b in q.free);notes={}
    fixed={};scattered=[]
    def fixed_job(name,data,align=1,kind='immutable asset'):
        fixed[name]=(data,align);notes[name]=dict(kind=kind,bytes=len(data))
    def scatter_job(name,data,stride):
        scattered.append((name,data,stride))
        fixed_job(name+'-pointers',bytes(len(data)//stride*2))
        notes[name]=dict(kind='scatter records',bytes=len(data),stride=stride)
    from native_flat_edges import sources as edge_sources,assets as edge_assets
    from native_flat_asm import assemble
    import re
    functions,pre,constants=edge_sources()
    edge_data=edge_assets(read)
    labels={n:0x8000 for body in functions.values() for n in re.findall(r'^([A-Za-z_]\w*):',body,re.M)}
    constants.update({n:0x8000 for n in edge_data})
    for name,body in functions.items():
        own=set(re.findall(r'^([A-Za-z_]\w*):',body,re.M))
        eq={**{n:v for n,v in labels.items() if n not in own},**constants}
        data,_=assemble(out/'source-sizing',name,' ORG $4000\n'+pre+''.join(f'{n} EQU ${v:04X}\n' for n,v in eq.items())+body)
        fixed_job('code/'+name,bytes(len(data)),kind='measured source CODE RESERVATION')
    for name,data in edge_data.items():fixed_job(name,data)
    from native_grid_delta import pack
    grid=read(119,0xBE00,512)
    from presentation_grid24 import delta_table
    if grid!=delta_table():raise ValueError('complete original P0 grid translation differs')
    for i,data in enumerate(pack(grid)):fixed_job('P0-grid-rows'+str(i),data)
    fixed_job('P0-grid-lookup',bytes(28),kind='unassembled CODE RESERVATION')
    fixed_job('P0-grid-publisher',bytes(38),kind='unassembled CODE RESERVATION')
    fixed_job('credit-patterns',read(65,0xBD1A,112))
    fixed_job('credit-coarse-patterns',read(65,0xBE48,112))
    fixed_job('credit-commit',bytes(78),kind='unassembled CODE RESERVATION')
    fg=floes((build/'cp-patterns.bin').read_bytes(),(build/'cp-indices.bin').read_bytes())
    pg=p0((build/'player-band-patterns.bin').read_bytes(),read(2,0xB300,1024))
    fixed_job('floe-indices',fg['indices'])
    fixed_job('floe-plane-basis',fg['basis'],8)
    fixed_job('floe-directory',(build/'cp-directory.bin').read_bytes())
    fixed_job('occupancy-directory',(build/'co-directory.bin').read_bytes())
    fixed_job('white-NAME-programs',(build/'atlas-programs.bin').read_bytes())
    fixed_job('source-RNG',read(1,0xB700,256),256)
    # The complete original enemy group map already exists at7900. This is a
    # verified256-byte alias, not an observed-only pruning of unknown entries.
    if read(1,0xBC00,256)!=rom[0x3900:0x3A00]:raise ValueError('complete enemy map alias differs')
    tens=read(131,0xBD00,256)
    fixed_job('temperature-tens',b''.join(tens[i:i+9] for i in range(0,256,16)))
    scatter_job('temperature-units',read(131,0xBE00,512),32)
    directory=(build/'fv-directory.bin').read_bytes()
    values=[int.from_bytes(directory[i:i+2],'little') for i in range(0,len(directory),2)]
    runs=[]
    for i,address in enumerate(values):
        if runs and address==runs[-1][2]+(i-runs[-1][0])*8:runs[-1][1]+=1
        else:runs.append([i,1,address])
    if len(values)!=188 or len(runs)!=9:raise ValueError('complete frozen footer address family required')
    fixed_job('footer-address-runs',b''.join(bytes((first+count,))+((address-first*8)&65535).to_bytes(2,'little') for first,count,address in runs))
    fixed_job('background-rows',read(1,0xB800,288))
    fixed_job('background-PGT0',read(1,0xB940,216))
    fixed_job('background-CGT0',read(1,0xBA18,216))
    fixed_job('background-gradients',read(1,0xB920,32))
    fixed_job('background-PGT1',read(1,0xBAF0,40))
    fixed_job('background-CGT1',read(1,0xBB18,40))
    fixed_job('background-PGT2',read(1,0xBB40,48))
    fixed_job('background-CGT2',read(1,0xBB70,48))
    scatter_job('occupancy-rows',(build/'co-rows.bin').read_bytes(),16)
    from compact_byte_windows import pack_windows
    desc=read(146,0xB900,1152)
    dp=pack_windows([desc[i:i+16] for i in range(0,len(desc),16)])
    fixed_job('normal-P0-record-pointers',bytes(144))
    notes['normal-P0-records']=dict(kind='overlapping16-byte windows in scattered chunks',bytes=len(dp['pool']))
    notes['normal-P0-source-rows']=dict(kind='overlapping16-byte windows below8000',bytes=len(pg['rows']))
    fixed_job('normal-P0-pattern-directory',pg['directory'])
    scatter_job('bear-pictures',read(132,0xBC20,576),96)
    if read(132,0xBC00,32)!=read(2,0x9FF2,32):raise ValueError('complete native bear group alias differs')
    scatter_job('igloo-colors',read(119,0xB931,864),32)
    fixed_job('igloo-flags',read(119,0xB911,32))
    scatter_job('footer-NAMEs',read(13,0x8BC0,704),44)
    # Header key fields are opaque source ownership tags, not native pointers.
    tags=b''.join(read(35+i//16,0xB800+(i%16)*128+112,4) for i in range(160))
    scatter_job('floe-owner-tags',tags,64)
    for name,n in (('igloo-publisher',273),('temperature-publisher',369),('occupancy-lookup',41),
                   ('floe-stream',121),('floe-header',38),('white-publisher',132),('footer-reader',67),
                   ('enemy-buffer',184),('P0-pattern-gate',297 if fast_P0 else 67)):
        fixed_job(name,bytes(n),kind='unassembled CODE RESERVATION')
    # Reserve aligned pages before general byte objects, then place large
    # contiguous interfaces before scatter records. This is real packing of
    # exact extents; it does not certify their runtime lifetime yet.
    for name,(data,alignment) in sorted(fixed.items(),key=lambda item:(item[1][1]==1,-len(item[1][0]),item[0])):
        q.add(name,data,alignment)
    def publish(name,data):
        row=q.objects[name]
        if row['size']!=len(data):raise ValueError('reserved pointer extent differs')
        q.image[row['address']:row['address']+len(data)]=data
        row['sha256']=digest(data)
    parity=pg['directory']
    offs=b''.join((int.from_bytes(parity[i:i+2],'little')&32767).to_bytes(2,'little') for i in range(0,len(parity),2))
    pointers=q.windows('normal-P0-source-rows',pg['rows'],offs,16,96,address_limit=0x8000)
    publish('normal-P0-pattern-directory',b''.join((int.from_bytes(pointers[i:i+2],'little')|(int.from_bytes(parity[i:i+2],'little')&32768)).to_bytes(2,'little') for i in range(0,len(parity),2)))
    publish('normal-P0-record-pointers',q.windows('normal-P0-records',dp['pool'],dp['offsets'],16,128))
    for name,data,stride in sorted(scattered,key=lambda row:-row[2]):
        publish(name+'-pointers',q.records(name,data,stride))
    if fast_bands:q.add('bear-painter',bytes(19))
    out.mkdir(parents=True,exist_ok=True)
    (out/'native-allocations.bin').write_bytes(q.image)
    result=dict(complete=False,allocation_only=True,game_runtime_changed=False,mapperless_linked=False,
        closed_object_catalog=False,source_IRQ_edge_modules_pending=[],source_IRQ_edge_functions=len(functions),
        candidate_lifetime_reclamation=native_lifetimes,fast_P0=fast_P0,fast_bands=fast_bands,
        input_rom_sha256=m['rom']['sha256'],free_declared_bytes=total,allocated_bytes=sum(r['size'] for r in q.objects.values()),
        remaining_bytes=sum(b-a for a,b in q.free),objects=q.objects,free=q.free,notes=notes,
        limitations=['All three rare edge source families, P0 grid translation and runtime credit are allocated; linked execution/lifetimes remain unproved.',
                     'Upper/cold-only extents require linked read/write validation.',
                     'Code reservations must be replaced by actual maintained-source assembly.','No entry loader, complete executable, cadence or32KiB feasibility is proved.'])
    (out/'layout.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:result[k] for k in ('complete','free_declared_bytes','allocated_bytes','remaining_bytes')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--native-lifetimes',action='store_true')
    p.add_argument('--fast-P0',action='store_true')
    p.add_argument('--fast-bands',action='store_true')
    a=p.parse_args();catalog(a.build,a.out,native_lifetimes=a.native_lifetimes,fast_P0=a.fast_P0,fast_bands=a.fast_bands)
