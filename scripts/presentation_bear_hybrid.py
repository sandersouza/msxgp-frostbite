"""Exact sprite-prefix/tile-suffix bear packets; original gameplay is untouched."""
BASE=13539

def cropped_mask(mask,cut):
    if len(mask)!=8 or type(cut)is not int or not 0<=cut<8:raise ValueError('whole source mask and bounded cut required')
    return bytes(v&(255>>cut)for v in mask)

def geometry_packet(ids,tiles,columns,cut,coarse):
    if len(ids)!=6 or len(tiles)!=4 or any(len(row)!=6 for row in tiles)or columns not in(3,4)or type(cut)is not int or not 0<=cut<8 or type(coarse)is not int or coarse not in(0,1):raise ValueError('complete bounded suffix record required')
    if any(type(n)is not int or not 0<=n<16384 for n in ids)or any(type(n)is not int or not 0<=n<512 for row in tiles for n in row):raise ValueError('logical/tile namespace exceeded')
    return b''.join(n.to_bytes(2,'little')for n in ids)+b''.join(n.to_bytes(2,'little')for row in tiles for n in row)+bytes((columns,cut,coarse,0))

def sprite_prefix(pixels):
    if len(pixels)!=320:raise ValueError('complete16x20 source bitmap required')
    result=bytearray(64)
    for y in range(20):
        for x in range(16):
            if pixels[y*16+x]:
                for tx in range(3*x//2,3*(x+1)//2):
                    if tx<16:
                        sy=y+8;result[(sy//16)*32+sy%16+(tx//8)*16]|=128>>(tx%8)
    return bytes(result)

def validate_synthetic_role(bank,slot,key,registry):
    if len(key)!=6:raise ValueError('whole physical key required')
    identifier=int.from_bytes(key[:2],'little')
    if key[5]!=0 or identifier<BASE:return False
    backgrounds={0:(136,128),1:(129,131,132,128)}
    if identifier not in registry or bank not in(0,1)or slot not in((2,6,66,70)if bank==0 else(2,66))or key[2]not in backgrounds[bank]or key[3]!=0 or key[4]not in(1,15):raise ValueError('synthetic bear mask outside registered boundary role')
    return True

def compile_assets(base):
    from pathlib import Path
    import json,hashlib
    from environment import ROOT
    from presentation_fast_model import prepare
    from presentation_palette import audit_palette
    from presentation_floe_templates import compile_templates
    from presentation_fragments import mask_tiles
    from original_graphics import view
    from presentation_constructors import construct
    from render_build import symbols
    base=Path(base);m=json.loads((base/'build.json').read_text());rom=(base/m['rom']['filename']).read_bytes();source=(ROOT/'references/roms/frostbite.bin').read_bytes();s=symbols(base/'presentation.sym')
    if hashlib.sha256(rom).hexdigest()!=m['rom']['sha256']:raise ValueError('parent ROM differs')
    cfg=json.loads((ROOT/'references/presentation-assets-config.json').read_text());tables=prepare(source,audit_palette(ROOT/cfg['palette']),base/'geometry')
    data=compile_templates(tables)['files']['logical-patterns.bin'];patterns=[data[i:i+8]for i in range(0,len(data),8)]
    if len(patterns)!=BASE or patterns[0]!=bytes(8):raise ValueError('original full mask namespace changed')
    canonical={p:i for i,p in reversed(list(enumerate(patterns)))};directory=rom[66*16384+0x3800:66*16384+0x3c00];records={};sprites=bytearray();registry_by_mask={};new=set();checks=0
    for group in range(16):
        image=view(source,0xfd00+source[0xee7+group//2],19,bool(group&1),2);bitmap=image['pixels']+image['pixels'][-16:];sprites.extend(sprite_prefix(bitmap))
        for phase in range(16):
            for coarse in range(2):
                at=group*64+phase*4+coarse*2;rid=int.from_bytes(directory[at:at+2],'little');p=(67+rid//8)*16384+0x3800+(rid%8)*256;old=rom[p:p+256];cols,rows,stride=old[240:243]
                geometry=mask_tiles(bitmap,16,20,phase,3+coarse);ids=[int.from_bytes(old[i*20:i*20+2],'little')for i in range(cols*3)]
                if (cols,rows)!=(geometry['columns'],geometry['rows'])or[patterns[i]for i in ids]!=geometry['patterns']:raise ValueError('source geometry differs')
                cut=(8+phase*3//2)&7;shapes=[]
                for row in range(3):
                    for cell in range(2):
                        col=cell+2;raw=patterns[ids[row*cols+col]]if col<cols else bytes(8);mask=cropped_mask(raw,cut if cell==0 else 0);shapes.append(mask)
                        if any(mask)and mask not in canonical:
                            new.add(mask);registry_by_mask.setdefault(mask,(ids[row*cols+col],cut))
                record=(cols,cut,coarse,tuple(shapes))
                if rid in records and records[rid]!=record:raise ValueError('record alias changes crop/coarse')
                records[rid]=record;checks+=1
    if set(records)!=set(range(96))or len(new)!=80:raise ValueError('bounded suffix domain changed')
    new_masks=sorted(new);registry=[dict(synthetic_ID=BASE+i,original_ID=registry_by_mask[p][0],cut=registry_by_mask[p][1])for i,p in enumerate(new_masks)];lookup={**canonical,**{p:BASE+i for i,p in enumerate(new_masks)}};extended=patterns+new_masks
    roots=rom[s['p_bg_roots']-0x4000:s['p_bg_roots']-0x4000+8];background_rows=bytearray()
    for theme in range(4):
        address=int.from_bytes(roots[theme*2:theme*2+2],'little')
        if not 0x8000<=address<=0xbfb8:raise ValueError('background root outside bank1')
        for row in range(6,9):
            at=16384+address-0x8000+row*3;background_rows.extend(rom[at:at+3])
    def background(bank,identifier):
        i=identifier-128;return tables['background']['patterns'][bank][i*8:i*8+8]+tables['background']['colors'][bank][i*8:i*8+8]
    pool=[];pool_ids={};packets=bytearray()
    for rid in range(96):
        cols,cut,coarse,shapes=records[rid];ids=[lookup[p]if any(p)else 0 for p in shapes];variants=[]
        for color in(15,1):
            for theme in range(2):
                indexes=[]
                for cell,n in enumerate(ids):
                    if not n:indexes.append(0);continue
                    row=cell//2;bank=int(row==2);bg=background_rows[(coarse*2+theme)*9+row*3+2]
                    tile=construct(n.to_bytes(2,'little')+bytes((bg,0,color,0)),patterns=extended,backgrounds={bg:background(bank,bg)},header=b'',footer=[])
                    if tile not in pool_ids:pool_ids[tile]=len(pool);pool.append(tile)
                    indexes.append(pool_ids[tile])
                variants.append(indexes)
        packets.extend(geometry_packet(ids,variants,cols,cut,coarse))
    if len(pool)!=461 or len(sprites)!=1024 or len(packets)!=6144:raise ValueError('hybrid table capacity differs')
    return dict(directory=directory,sprites=bytes(sprites),records=bytes(packets),tiles=b''.join(pool),background_rows=bytes(background_rows),registry=registry,new_masks=b''.join(new_masks),geometry_cases=checks,tile_count=len(pool),source_pattern_count=BASE)

def record_packet(programs,columns,cut,coarse):
    if len(programs)!=2 or any(len(row)!=3 for row in programs)or columns not in(3,4)or type(cut)is not int or not 0<=cut<8 or type(coarse)is not int or coarse not in(0,1):raise ValueError('both actual palette choices and complete dimensions required')
    if any(type(n)is not int or not 0<=n<368 for row in programs for n in row):raise ValueError('row program index exceeds eight safe tails')
    return b''.join((0xb800+(n%46)*44).to_bytes(2,'little')+bytes((134+n//46,))for row in programs for n in row)+bytes((columns,cut,coarse,0))

def row_program(tiles,keys):
    if len(tiles)!=2 or any(len(t)!=16 for t in tiles)or len(keys)!=2 or any(len(k)!=6 for k in keys):raise ValueError('two whole tiles and publication keys required')
    return b''.join(t[:8]for t in tiles)+b''.join(t[8:]for t in tiles)+b''.join(keys)

def pack_programs(programs):
    if not 1<=len(programs)<=368 or any(len(p)!=44 for p in programs):raise ValueError('bounded complete44-byte row programs required')
    data=bytearray([255])*16384
    for i,p in enumerate(programs):
        at=(i//46)*2048+(i%46)*44;data[at:at+44]=p
    return bytes(data)

def compile_transactions(base):
    assets=compile_assets(base);old=assets['records'];tiles=assets['tiles'];bg=assets['background_rows'];programs=[];indexes={};records=bytearray()
    for rid in range(96):
        rec=old[rid*64:(rid+1)*64];ids=[int.from_bytes(rec[i*2:i*2+2],'little')for i in range(6)];coarse=rec[62];variants=[]
        # These are exactly the two source palette choices at level>=3.
        for night,combo,color in((0,2,1),(1,1,15)):
            tile_ids=[int.from_bytes(rec[12+(combo*6+i)*2:14+(combo*6+i)*2],'little')for i in range(6)];row_ids=[]
            for row in range(3):
                cells=[tiles[tile_ids[row*2+j]*16:tile_ids[row*2+j]*16+16]if ids[row*2+j]else bytes(16)for j in range(2)]
                keys=[ids[row*2+j].to_bytes(2,'little')+bytes((bg[(coarse*2+night)*9+row*3+2],0,color,0))if ids[row*2+j]else bytes([255])*6 for j in range(2)]
                program=row_program(cells,keys)
                if program not in indexes:indexes[program]=len(programs);programs.append(program)
                row_ids.append(indexes[program])
            variants.append(row_ids)
        records.extend(record_packet(variants,rec[60],rec[61],coarse))
    if len(programs)!=352 or len(records)!=2112:raise ValueError('bounded transaction domain changed')
    return {**assets,'records':bytes(records[:2046]),'extra_records':bytes(records[2046:]),'programs':pack_programs(programs),'program_count':len(programs),'record_bytes':22}
