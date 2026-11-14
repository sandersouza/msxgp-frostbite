"""Complete maintained rare-contact functions, shared across all three IRQ paths."""
from pathlib import Path
from environment import ROOT
from native_flat_asm import split_functions


def sources():
    modules=(
        ('compact_floe_edge.asm',('ce_build_masks','ce_held','ce_low_mask','ce_align','ce_power','ce_active','ce_wrap'),'ce_end'),
        ('compact_floe_edge_row.asm',('ce_test_row','cer_glyph'),'cer_end'),
        ('compact_floe_edge_contact.asm',('cec_contact',),'cec_end'),
        ('compact_floe_edge_query.asm',('cfe_contact',),'cfe_end'),
        ('compact_hazard_context.asm',('cx_context','cx_find_distance','cx_test_distance'),'cx_end'),
        ('compact_hazard_program.asm',('hp_build','hp_shift','hp_align','hp_sample'),'hp_end'),
        ('compact_mask_program.asm',('mp_contact',),'mp_end'),
        ('compact_enemy_edge_query.asm',('he_query',),'he_end'),
        ('compact_shore_program.asm',('ws_build','ws_mask','ws_window','ws_align','ws_power','ws_wrap'),'ws_end'),
        ('compact_shore_exact_edge_query.asm',('se_fast_query',),'se_end'),
    )
    headers=[];functions={}
    for filename,entries,end in modules:
        text=(ROOT/'src'/filename).read_text()
        text=text.replace('    INCLUDE "compact_shore_cached_edge_query.asm"',(ROOT/'src/compact_shore_cached_edge_query.asm').read_text())
        header,body=split_functions(text,entries,end)
        headers.append(header);functions.update(body)
    defines={
        'CE_INPUT_ORIGIN':0x3300,'CE_SCRATCH_ORIGIN':0x0FC0,'CE_OUTPUT_ORIGIN':0x2940,
        'CE_ROW_INPUT_ORIGIN':0x2970,'CE_CONTACT_INPUT_ORIGIN':0x2990,'CE_CONTACT_SCRATCH_ORIGIN':0x2994,
        'CX_INPUT_ORIGIN':0x3300,'CX_OUTPUT_ORIGIN':0x2980,
        'HP_INPUT_ORIGIN':0x3300,'HP_OUTPUT_ORIGIN':0x2940,'HP_SCRATCH_ORIGIN':0x0FC0,'HP_QUERY_TAG':0x2990,
        'MP_INPUT_ORIGIN':0x2990,'MP_SCRATCH_ORIGIN':0x2997,
        'WS_INPUT_ORIGIN':0x3300,'WS_OUTPUT_ORIGIN':0x0E10,'WS_SCRATCH_ORIGIN':0x0FC0,'WS_QUERY_TAG':0x2990,
    }
    pre=''.join(f' DEFINE {n} ${v:04X}\n' for n,v in defines.items())+' DEFINE CE_CLIP_QUERY_Y\n'+''.join(headers)
    constants=dict(ce_glyphs=0x0100,ce_bases=0x0F00,cf_contact=0x3000,cf_control=0x3300,cf_y=0x3301,
                   cf_dx=0x3302,cf_pose=0x3303,hp_enemy=0x2700,hp_shapes=0x2900,hazard_y=0xC794,
                   hazard_x=0xC793,hazard_shape_index=0x7900,core_fault=0x8057,ce_edge_reverse=0xB800)
    return functions,pre,constants


def assets(read):
    reverse=read(49,0xBD00,256)
    if reverse!=read(2,0xB800,256):raise ValueError('complete core reverse-table alias differs')
    return dict(ce_edge_windows=read(49,0xBE00,320),ce_edge_bits=read(49,0xBF40,32),
                ce_edge_low_masks=read(49,0xBF60,32),ce_edge_control_clocks=read(49,0xBF80,20),
                ce_edge_motion_clocks=read(49,0xBF94,12),hp_samples=read(50,0xBD00,8),
                ws_glyphs=read(51,0xBD00,228),ws_samples=read(51,0xBE00,32),ws_selectors=read(51,0xBE20,30))
