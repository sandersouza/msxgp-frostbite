"""Source-link the static RAM takeover image; not a cold/native product loader.

Every byte is maintained source or exact statically bound asset input. The
emulator may test the resulting overlays after genuine legacy cold init; no
captured RAM is an input to this builder. Unresolved interfaces fail explicitly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from native_flat_asm import assemble,link_functions
from native_flat_edges import sources as edge_sources,assets as edge_assets
from native_flat_layout import Layout
from render_build import symbols
from environment import ROOT


def digest(data):return hashlib.sha256(data).hexdigest()


def build(base,catalog,out,p0_proof=None,band_proofs=None,elide_mapper=False,p0_clear_proof=None,p0_sat_proof=None):
    base=base.resolve();catalog=catalog.resolve();out=out.resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());r=(base/m['rom']['filename']).read_bytes()
    if digest(r)!=m['rom']['sha256']:raise ValueError('bound native parent required')
    manifest=json.loads((catalog/'layout.json').read_bytes())
    if manifest['input_rom_sha256']!=digest(r) or not manifest['candidate_lifetime_reclamation']:
        raise ValueError('explicit complete-family candidate lifetime allocation required')
    q=Layout(manifest['free']);q.objects=manifest['objects'];q.image=bytearray((catalog/'native-allocations.bin').read_bytes())
    s=symbols(base/'presentation.sym');patches=[]
    def read(bank,a,n):return r[bank*16384+a-0x8000:bank*16384+a-0x8000+n]
    def address(name):return q.objects[name]['address']
    # Runtime code before allocation overlays. Lower query RAM and upper
    # initializer products are statically included for code relocation only;
    # runtime variables are preserved by the initial takeover experiment.
    image=bytearray(65536);image[0x4000:0x8000]=r[:16384];image[0x8000:0xC000]=read(2,0x8000,16384)
    immutable_ranges=[(0x4000,0xC000)]
    for row in m['coherent_x']['auxiliary_code']:
        a=row['ram_address'];data=read(row['bank'],row['rom_address'],row['size']);image[a:a+len(data)]=data
        immutable_ranges.append((a,a+len(data)))
    a=0xE900;image[a:a+m['fixed_clock']['ram_code_bytes']]=read(115,0xB800,m['fixed_clock']['ram_code_bytes'])
    immutable_ranges.append((a,a+m['fixed_clock']['ram_code_bytes']))
    for bank,a in ((46,0x3000),(47,0x3800)):
        image[a:a+0x800]=read(bank,0xB800,0x800)
    def patch(a,data,why):
        patches.append(dict(address=a,size=len(data),reason=why,before_sha256=digest(image[a:a+len(data)]),after_sha256=digest(data)))
        image[a:a+len(data)]=data
    def word(a,v,why):patch(a,v.to_bytes(2,'little'),why)
    def emit(name,text,extra=None):
        a=address(name);names={**s,**(extra or {})}
        own=set(re.findall(r'^([A-Za-z_]\w*):',text,re.M))
        pre=''.join(f'{n} EQU ${v:04X}\n' for n,v in names.items() if '.' not in n and n not in own)
        code,z=assemble(out/'assembly',name,f' ORG ${a:04X}\n'+pre+text)
        row=q.objects[name]
        if len(code)>row['size']:raise ValueError(f'{name}: linked{len(code)} > reserved{row["size"]}')
        data=code+bytes([255])*(row['size']-len(code));q.image[a:a+len(data)]=data;row['sha256']=digest(data)
        row['assembled_code_bytes']=len(code)
        return {n:z[n] for n in own}
    functions,pre,constants=edge_sources()
    constants.update({n:address(n) for n in edge_assets(read)})
    edge=link_functions(q,out/'assembly/edges',functions,pre+''.join(f'{n} EQU ${v:04X}\n' for n,v in constants.items()))
    # The production P0 mask directory now holds absolute pointers below8000,
    # with its high bit reserved for horizontal phase. All70 records survive.
    body=(ROOT/'src/native_p0_pattern.asm').read_text().replace('    LD HL,np0_rows\n    ADD HL,DE','    EX DE,HL')
    if manifest.get('fast_P0'):
        body=(ROOT/'src/native_p0_pattern_fast.asm').read_text()
        proof=p0_proof or ROOT/'outputs/compact/issue44-native-P0-fast-01/component-result.json'
        result=json.loads(proof.read_bytes())
        if not result['complete'] or result['cases']!=70 or any(digest((ROOT/n).read_bytes())!=h for n,h in result['sources'].items()):
            raise ValueError('every original native P0 pattern must pass before choosing the faster code')
    p0=emit('P0-pattern-gate',body,dict(np0_directory=address('normal-P0-pattern-directory'),np0_expansion=0xB300))
    floe=emit('floe-stream',(ROOT/'src/native_floe_union_stream.asm').read_text(),
              dict(nf_directory=address('floe-directory'),nf_indices=address('floe-indices'),nf_basis=address('floe-plane-basis')))
    # Exact source packet header tags remain opaque old ownership tags.
    header='''nh_copy:
 LD A,(pk_bank)
 SUB 35
 ADD A,A
 LD L,A
 LD H,0
 LD DE,nh_pointers
 ADD HL,DE
 LD E,(HL)
 INC HL
 LD D,(HL)
 LD HL,(pk_pointer)
 ADD HL,HL
 LD A,H
 AND 15
 ADD A,A
 ADD A,A
 LD L,A
 LD H,0
 ADD HL,DE
 LD DE,pk_pending
 LD BC,4
 LDIR
 RET
'''
    nh=emit('floe-header',header,dict(nh_pointers=address('floe-owner-tags-pointers')))
    source=(ROOT/'src/compact_enemy_occupancy.asm').read_text()
    source=source.replace('    DUP 4\n    ADD HL,HL\n    EDUP','''    ADD HL,HL
    LD DE,co_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL''',1).replace('    LD DE,co_rows\n    ADD HL,DE\n','')
    co=emit('occupancy-lookup',source,dict(co_directory=address('occupancy-directory'),co_pointers=address('occupancy-rows-pointers')))
    # Existing native enemy buffer arithmetic, expansion/reversal and original
    # source sprite sheet already reside in the retained core.
    enemy=emit('enemy-buffer',(ROOT/'src/compact_enemy_packet.asm').read_text(),
               dict(ct_original=0xA400,ct_shapes=0x2900,ct_expansion=0xB300,ct_reverse=0xB800))
    vp=(ROOT/'src/compact_footer_vram.asm').read_text();vp=vp[vp.index('vp_read:'):]
    vp+='\n'+(ROOT/'src/native_footer_address.asm').read_text()
    footer=emit('footer-reader',vp.replace('CALL vp_address','CALL nr_address'),dict(nr_runs=address('footer-address-runs')))
    # Keep the exact accepted credit bitmaps, including its coarse variant.
    source=(ROOT/'src/presentation_credit.asm').read_text();source=source[source.index('as_commit:'):source.index('as_coarse:')]
    credit=emit('credit-commit',source,dict(as_patterns=address('credit-patterns'),as_coarse=address('credit-coarse-patterns')))
    gd=emit('P0-grid-lookup',(ROOT/'src/native_grid_delta.asm').read_text(),
            dict(ngd_rows0=address('P0-grid-rows0'),ngd_rows1=address('P0-grid-rows1'),ngd_count0=15,ngd_count1=13))
    source=(ROOT/'src/presentation_grid_player.asm').read_text();source=source[source.index('ag_player:\n'):source.index('ag_player_end:')]
    first=source.index('    LD A,(p_w_coarse)');last=source.index('    OR A\n',first)
    source=source[:first]+'''    LD A,(p_w_coarse)
    LD C,A
    LD A,($F064)
    CALL ngd_lookup
'''+source[last:]
    grid=emit('P0-grid-publisher',source,dict(ngd_lookup=gd['ngd_lookup']))
    source=(ROOT/'src/presentation_ice_atlas.asm').read_text();source=source[source.index('ah_floe:'):source.index('ah_patterns:')]
    white=emit('white-publisher',source,dict(ah_programs=address('white-NAME-programs')))
    source=(ROOT/'src/presentation_igloo_colors.asm').read_text();source=source[source.index('ad_main:'):source.index('ad_code_end:')]
    source=source.replace('    DUP 5\n    ADD HL,HL\n    EDUP\n    LD DE,ad_colors\n    ADD HL,DE',
    '''    ADD HL,HL
    LD DE,ad_color_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL''')
    igloo=emit('igloo-publisher',source,dict(ad_flags=address('igloo-flags'),ad_color_pointers=address('igloo-colors-pointers')))
    source=(base/'ct-body.asm').read_text();source=source[source.index('burst_body:'):source.index('burst_body_end:')]
    source+='\n'+(ROOT/'src/native_temperature.asm').read_text()
    source=source.replace('CALL ct_build','CALL nt_build')
    temp=emit('temperature-publisher',source,dict(nt_tens=address('temperature-tens'),nt_units_directory=address('temperature-units-pointers')))
    # Native caller gates use direct addresses; the historical bank shadow has
    # no semantic role after this point. Retired mapper storage is reallocated.
    patch(s['t_mapper'],b'\xC9','all-RAM mapping gate')
    patch(0x5616,b'\x7D\xC3'+footer['vp_read'].to_bytes(2,'little'),'native frozen footer fetch')
    patch(0x7D29,b'\xC3'+edge['he_query'].to_bytes(2,'little'),'complete ordinary edge query')
    patch(0x7D76,b'\xC3'+edge['se_fast_query'].to_bytes(2,'little'),'complete shore edge query')
    cfi=symbols(base/'ce-acquire.sym');a=cfi['cfi_row.edge']
    old=image[a:a+8]
    if old[:2]!=bytes((0x3E,49)) or old[5:8]!=b'\xCD\x00\xBC':raise ValueError('bound floe edge gate differs')
    patch(a,b'\xCD'+edge['cfe_contact'].to_bytes(2,'little')+bytes(5),'complete floe edge query')
    # Emit tiny native gate replacements in their preserved ABI locations.
    def replace_gate(a,b,text):
        own=set(re.findall(r'^([A-Za-z_]\w*)(?::|\s+EQU\b)',text,re.M))
        code,z=assemble(out/'assembly',f'gate-{a:04X}',f' ORG ${a:04X}\n'+''.join(f'{n} EQU ${v:04X}\n' for n,v in s.items() if '.' not in n and n not in own)+text)
        if len(code)>b-a:raise ValueError('native gate exceeds interface')
        patch(a,code+bytes(b-a-len(code)),'native interface with unchanged calling convention')
        return z
    replace_gate(s['ag_player_entry'],s['ag_player_exit'],f' JP ${grid["ag_player"]:04X}\n')
    # Preserve mapper-save stack contracts on these two existing interfaces.
    replace_gate(s['ad_entry'],s['ad_hit'],f' LD A,(t_bank)\n PUSH AF\n JP ${igloo["ad_main"]:04X}\n')
    # White atlas bridge and packet PGT bridge are upper fixed public entries.
    patch(s['ah_runtime_bridge'],b'\xC3'+white['ah_floe'].to_bytes(2,'little'),'native white NAME publisher')
    # Locate the exact mapped native floe stream call in the shared publisher.
    needle=bytes((0x3E,54,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xC3,0,0xA8))
    matches=[a for a in range(0x4000,0xC000) if image[a:a+len(needle)]==needle]
    if len(matches)!=1:raise ValueError('unique native floe stream call required: '+str(matches))
    patch(matches[0],b'\xC3'+floe['nf_stream'].to_bytes(2,'little')+bytes(5),'native floe PGT stream')
    # Packet headers are gathered without dereferencing their opaque old key.
    needle=bytes((0x2A,s['pk_pointer']&255,s['pk_pointer']>>8,0x11,112,0,0x19,0x11,s['pk_pending']&255,s['pk_pending']>>8,0x01,4,0,0xED,0xB0))
    matches=[a for a in range(0xF400,0xF8D8) if image[a:a+len(needle)]==needle]
    if len(matches)!=1:raise ValueError('unique live floe header gather required: '+str(matches))
    patch(matches[0],b'\xCD'+nh['nh_copy'].to_bytes(2,'little')+bytes(len(needle)-3),'native opaque floe header gather')
    # Source RNG, NAME descriptors and world palette retain all finite values.
    a=s['p_bg_describe'];needle=bytes((0x26,0xB7));region=image[a:s['p_bg_roots']]
    if region.count(needle)!=1:raise ValueError('unique source RNG high-page load required')
    patch(a+region.index(needle)+1,bytes((address('source-RNG')>>8,)),'aligned full source RNG')
    patch(s['p_bg_roots'],b''.join((address('background-rows')+72*i).to_bytes(2,'little') for i in range(4)),'four complete background row programs')
    needle=b'\x11\x20\xB9';first=0xF900;region=image[first:0xFAC5]
    if region.count(needle)!=1:raise ValueError('unique background gradient input required')
    word(first+region.index(needle)+1,address('background-gradients'),'complete gradient table')
    # Two remaining resident world color table reads alias the already complete
    # original core palette at6100. Only instruction-bound source sites change.
    for a,b in ((s['p_template_background_covered'],s['p_template_cover_normal']),(s['p_world_color'],s['p_world_color']+18)):
        region=image[a:b];needle=b'\x21\xA0\xB5'
        if region.count(needle)!=1:raise ValueError('unique world color source at '+hex(a))
        word(a+region.index(needle)+1,0x6100,'complete world palette alias')
    patch(s['pt_background_roots'],b''.join(address('background-'+kind+str(bank)).to_bytes(2,'little') for bank in range(3) for kind in ('PGT','CGT')),'complete three-bank source backgrounds')
    first=s['presentation_hud_prepare'];needle=b'\x21\xF9\xB3';region=image[first:s['presentation_footer_prepare']]
    if region.count(needle)!=1:raise ValueError('unique live HUD selector palette required')
    if read(1,0xB3F9,7)!=read(2,0xA7F9,7):raise ValueError('complete HUD selector alias differs')
    word(first+region.index(needle)+1,0xA7F9,'all original HUD color selectors')
    needle=b'\x26\xBC';region=image[0xF400:0xF8D8]
    if region.count(needle)!=1:raise ValueError('unique native actor source group map required')
    word_address=0xF400+region.index(needle)+1
    patch(word_address,b'\x79','complete original enemy group map alias')
    # Public occupancy caller retains its original descriptor tail.
    a=s['v_geometry'];needle=bytes((0x3E,61,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0,0xB8))
    region=image[a:s['v_geometry_end']]
    if region.count(needle)!=1:raise ValueError('unique occupancy caller required')
    patch(a+region.index(needle),b'\xCD'+co['co_lookup'].to_bytes(2,'little')+bytes(5),'native complete occupancy lookup')
    # Keep i_generate argument gathering and i_done publication unchanged.
    a=s['i_generate'];b=s['i_done'];needle=bytes((0x3E,252,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0xE6,0x9C))
    region=image[a:b]
    if region.count(needle)!=1:raise ValueError('unique native enemy constructor gate required')
    patch(a+region.index(needle),b'\xCD'+enemy['ct_build'].to_bytes(2,'little')+bytes(5),'native enemy buffer')
    # Normal P0 recipe index is complete72; absolute pointers retain each whole
    #16-byte record even when the immutable pool is scattered across holes.
    a=s['x_try'];b=s['x_entry'];region=image[a:b]
    needle=b'\x6F\x26\x00'+b'\x29'*4+b'\x11\x00\xB9\x19'
    at=region.find(needle)
    if at<0:raise ValueError('complete normal P0 record index source required')
    end=region.find(b'\xED\xB0',at)+2
    if end<at:raise ValueError('complete normal P0 record copy required')
    text=f""" LD L,A
 LD H,0
 ADD HL,HL
 LD DE,${address('normal-P0-record-pointers'):04X}
 ADD HL,DE
 LD E,(HL)
 INC HL
 LD D,(HL)
 EX DE,HL
 LD DE,p_p_planes
 LD BC,16
 LDIR
"""
    replace_gate(a+at,a+end,text)
    a=s['x_entry'];b=s['x_entry.upload'];region=image[a:b]
    needle=bytes((0xCD,0xD1,0xEF))
    if region.count(needle)!=1:raise ValueError('unique P0 grammar constructor call required')
    word(a+region.index(needle)+1,p0['np0_build'],'native absolute-window P0 pattern')
    # Retroworks preserves the mapper-save stack consumed by its accepted body.
    a=s['as_bridge'];b=s['as_bridge_end'];region=image[a:b];needle=b'\xC3\xFA\xBD'
    if region.count(needle)!=1:raise ValueError('unique credit tail jump required')
    word(a+region.index(needle)+1,credit['as_commit'],'native exact credit update')
    # Temperature gate saves its source calling frame exactly as before.
    a=s['al_entry'] if 'al_entry' in s else s['al_gate']
    region=image[a:s['al_copy']]
    needle=b'\xC3\x00\xB8'
    if region.count(needle)!=1:raise ValueError('unique temperature body jump required')
    word(a+region.index(needle)+1,temp['burst_body'],'native temperature publisher')
    # Six complete96-byte bear sprite pictures use an absolute pointer table.
    text=f""" LD A,(p_w_group)
 ADD A,A
 LD L,A
 LD H,0
 LD DE,ng_info
 ADD HL,DE
 LD A,(HL)
 LD ($C496),A
 INC HL
 LD A,(HL)
 LD ($C497),A
 LD A,($C496)
 ADD A,A
 LD L,A
 LD H,0
 LD DE,${address('bear-pictures-pointers'):04X}
 ADD HL,DE
 LD E,(HL)
 INC HL
 LD D,(HL)
 LD ($C498),DE
 RET
"""
    replace_gate(s['ao_packet'],s['ao_thin_pattern'],text)
    # Native sprite upload no longer maps a foreign picture bank.
    replace_gate(s['an_upload'],s['an_native'],' JP vdp_write\n')
    # Exact footer record index now selects one whole44-byte sequence.
    a=s['p_template_footer_prepare'];b=s['p_template_footer_prepare.metadata'];region=image[a:b]
    needle=b'\x6F\x26\x00\x5D\x54'
    at=region.find(needle);end=region.find(b'\xE5\xDD\xE1',at)+3
    if at<0 or end<at:raise ValueError('unique footer NAME record setup required')
    text=f""" LD L,A
 LD H,0
 ADD HL,HL
 LD DE,${address('footer-NAMEs-pointers'):04X}
 ADD HL,DE
 LD E,(HL)
 INC HL
 LD D,(HL)
 PUSH DE
 POP IX
"""
    replace_gate(a+at,a+end,text)
    # Complete native query entry points make the historical table fallback
    # unreachable after takeover. Direct source clock contacts remain unchanged.
    patch(s['floe_acquire'],b'\xC3\x00\x31','native floe source query')
    patch(s['hazard_lookup_common'],b'\xC3\x00\x35','native ordinary source query')
    if manifest.get('fast_bands'):
        if not band_proofs:raise ValueError('both independent band proofs required')
        for key,cases in (('bear',512),('grid',1280)):
            result=json.loads((band_proofs[key]/'component-result.json').read_bytes())
            if not result['complete'] or result['cases']!=cases or any(digest((ROOT/n).read_bytes())!=h for n,h in result['sources'].items()):
                raise ValueError('current original-graphics band proof required: '+key)
        painter=emit('bear-painter',(ROOT/'src/native_bear_painter_small.asm').read_text())
        # The original158+62-byte helper block keeps its public ng_build entry;
        # only the moved painter CALL in the source-owned bear body changes.
        bear_grid=replace_gate(s['ng_build'],s['np_end'],(ROOT/'src/native_bear_grid_sparse.asm').read_text())
        if p0_clear_proof:
            proof=json.loads((p0_clear_proof/'component-result.json').read_bytes())
            if not proof['complete'] or not proof['IFF_disabled_and_enabled_preserved'] or any(digest((ROOT/n).read_bytes())!=h for n,h in proof['sources'].items()):
                raise ValueError('current exact P0 clear/IFF proof required')
            clear=replace_gate(bear_grid['ng_end'],s['np_end'],(ROOT/'src/native_p0_clear.asm').read_text())
            a=s['x_resume'];expected=bytes.fromhex('1181e70177003600edb0')
            if image[a:a+len(expected)]!=expected:raise ValueError('accepted five-plane P0 clear instruction extent required')
            patch(a,b'\xCD'+clear['np_clear'].to_bytes(2,'little')+bytes(7),'exact P0 zero clear with bounded IFF-preserving temporary stack')
        region=image[s['nb_body']:s['nb_error']];needle=b'\xCD'+s['np_paint'].to_bytes(2,'little')
        if region.count(needle)!=1:raise ValueError('one source-owned bear painter call required')
        word(s['nb_body']+region.index(needle)+1,painter['np_paint'],'relocated exact bear color painter')
        cg=dict(cg_directory=0x1000,cg_rows=0x1900,cg_palettes=0x1100)
        # Read final source symbols from the qualified initializer assembly.
        cg_source=symbols(base/'gp-code.sym')
        for n in cg:
            if n in cg_source:cg[n]=cg_source[n]
        code,_=assemble(out/'assembly','grid-palette-fast',' ORG $1C00\n'+''.join(f'{n} EQU ${v:04X}\n' for n,v in cg.items())+(ROOT/'src/native_grid_palette_fast.asm').read_text())
        if len(code)!=182:raise ValueError('same exact palette-code footprint required')
        patch(0x1C00,code,'aligned byte-index NAME palette constructor')
    for name,row in q.objects.items():
        a,n=row['address'],row['size'];image[a:a+n]=q.image[a:a+n]
    removed=[];superseded=[]
    if elide_mapper:
        # Instruction authority is the original fixed-clock patch list, never
        # an opcode-shaped byte scan through mixed assets and instructions.
        expected=b'\xCD'+s['t_mapper'].to_bytes(2,'little')
        for row in m['fixed_clock']['patches']:
            if row.get('before')!='320070' or row.get('after')!=expected.hex():continue
            bank,offset=divmod(row['offset'],16384)
            if bank not in (0,2):
                superseded.append(dict(offset=row['offset'],reason='foreign source bank'));continue
            a=(0x4000 if bank==0 else 0x8000)+offset
            if image[a:a+3]!=expected:
                superseded.append(dict(address=a,reason='explicit native replacement supersedes original site'));continue
            patch(a,bytes(3),'source-proved all-RAM no-op mapper CALL elision');removed.append(a)
    p0_cache=None
    if p0_sat_proof:
        proof=json.loads((p0_sat_proof/'component-result.json').read_bytes())
        if not proof['complete'] or proof['cases']!=1872 or not proof['full256byte_metadata_unchanged'] or not proof['final_IY_and_p_s_sat_equal'] or not proof['return_carry_clear']:
            raise ValueError('complete bounded P0 SAT byte/metadata/ABI proof required')
        if digest(image)!=proof['control_image_sha256'] or any(digest((ROOT/n).read_bytes())!=h for n,h in proof['sources'].items()):
            raise ValueError('P0 SAT experiment requires its exact source-bound control image')
        a=s['p_player_cache_lookup.entry']-5;b=s['p_player_cache_lookup.miss']
        if [a,b]!=proof['control_extent'] or digest(image[a:b])!=proof['control_code_sha256']:
            raise ValueError('actual selected P0 SAT instruction extent differs')
        sat=replace_gate(a,b,(ROOT/'src/native_p0_sat.asm').read_text())
        # The selected v31 already bypasses duplicate initialization. Verify
        # that compiled caller instead of claiming another saving from the
        # older maintained source. Public lookup remains unchanged/protected.
        source_name='src/presentation_player_cache.asm'
        if digest((ROOT/source_name).read_bytes())!=m['source_files'][source_name]:
            raise ValueError('certified original P0 key construction changed')
        first=s['p_player_cache_lookup']
        expected=b'\xCD'+s['p_player_init_masks'].to_bytes(2,'little')+b'\xCD'+s['p_player_variant_default'].to_bytes(2,'little')+b'\xDA'+s['p_world_fail'].to_bytes(2,'little')
        if image[first:first+len(expected)]!=expected:raise ValueError('checked initial cache default must remain')
        needle=b'\xCD'+s['p_player_variant_lookup.scan'].to_bytes(2,'little');region=image[first:a]
        if region.count(needle)!=1 or b'\xCD'+s['p_player_variant_lookup'].to_bytes(2,'little') in region:
            raise ValueError('selected v31 direct P0 scan caller required')
        site=first+region.index(needle)
        if s['p_player_variant_lookup.scan']!=s['p_player_variant_lookup']+4:
            raise ValueError('exact duplicate default/RET C prefix required')
        p0_cache=dict(experimental=True,component_proof_sha256=digest((p0_sat_proof/'component-result.json').read_bytes()),
                      control_image_sha256=proof['control_image_sha256'],SAT_extent=[a,b],writer_bytes=sat['ns_end']-sat['ns_sat'],
                      unchanged_scan_caller=site,duplicate_default_already_elided=True,allocation_bytes=0,whole_frame_acceptance=False)
    out.mkdir(parents=True,exist_ok=True)
    (out/'native-image.bin').write_bytes(image)
    manifest.update(source_linked_partial=True,complete=False,objects=q.objects,native_symbols={**edge,**p0,**floe,**nh,**co,**enemy,**footer,**credit,**gd,**grid,**white,**igloo,**temp},
                    patches=patches,image_sha256=digest(image),remaining_interfaces=[],
                    source_ROM_required_for_cold_init=True,mapperless_product=False,
                    elided_mapper_CALLs=removed,superseded_mapper_sites=superseded,native_P0_cache=p0_cache)
    (out/'native-link.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(dict(source_linked_partial=True,allocated_bytes=manifest['allocated_bytes'],remaining_bytes=manifest['remaining_bytes'],objects=len(q.objects)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','catalog','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--p0-proof',type=Path)
    p.add_argument('--bear-proof',type=Path);p.add_argument('--grid-proof',type=Path)
    p.add_argument('--elide-mapper',action='store_true')
    p.add_argument('--p0-clear-proof',type=Path)
    p.add_argument('--p0-sat-proof',type=Path)
    a=p.parse_args();build(a.base,a.catalog,a.out,a.p0_proof,dict(bear=a.bear_proof,grid=a.grid_proof) if a.bear_proof and a.grid_proof else None,a.elide_mapper,a.p0_clear_proof,a.p0_sat_proof)
