"""Passive entry/return CPU timers; no target-register or memory writes."""


def script(out,s,linked):
    entries={n:s[n] for n in ('presentation_prepare','presentation_world_prepare',
        'p_player_prepare','p_player_cache_lookup','p_player_emit_all','p_player_points',
        'p_player_count_band','p_player_nonempty','p_player_select',
        'p_bg_describe','p_dirty_describe','p_fast_release_dirty',
        'p_fast_background_rows','p_fast_upload_dirty','presentation_sprites_prepare',
        'p_fast_header_prepare','p_fast_igloo_prepare','p_fast_put',
        't_irq','presentation_hud_prepare','presentation_footer_prepare','nb_body',
        'ng_build','floe_acquire','hazard_lookup_common') if n in s}
    objects={'nf_stream':'floe-stream','co_lookup':'occupancy-lookup','ct_build':'enemy-buffer',
             'np0_build':'P0-pattern-gate','burst_body':'temperature-publisher','ad_main':'igloo-publisher',
             'he_query':'code/he_query','se_fast_query':'code/se_fast_query','cfe_contact':'code/cfe_contact'}
    entries.update({n:linked['objects'][obj]['address'] for n,obj in objects.items()})
    entries['grid-NAME-palette']=0x1C00
    tcl=f'''
set nfprof [open {{{out/'native-profile.tsv'}}} w]
set nfprof_id 0
set nfprof_returns [dict create]
set nfprof_irq 0
proc nfprof_leave {{id name started irq_before}} {{
 set elapsed [expr {{round(([machine_info time]-$started)*3579545)}}]
 if {{$name eq "t_irq"}} {{incr ::nfprof_irq $elapsed}}
 set exclusive [expr {{$elapsed-($::nfprof_irq-$irq_before)}}]
 puts $::nfprof "$name $elapsed $exclusive"
 debug remove_bp [dict get $::nfprof_returns $id]
 dict unset ::nfprof_returns $id
}}
proc nfprof_enter {{name}} {{
 set sp [reg SP]
 set ret [expr {{[debug read memory $sp]|([debug read memory [expr {{($sp+1)&65535}}]]<<8)}}]
 set id [incr ::nfprof_id]
 dict set ::nfprof_returns $id [debug set_bp $ret [format {{[reg SP]==%d}} [expr {{($sp+2)&65535}}]] [list nfprof_leave $id $name [machine_info time] $::nfprof_irq]]
}}
'''
    for name,address in entries.items():
        tcl+=f'debug set_bp {address} {{$::native_flat_ready}} {{nfprof_enter {{{name}}}}}\n'
    return tcl
