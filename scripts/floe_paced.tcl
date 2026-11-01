set save_settings_on_exit false
set renderer none
set throttle off
set speed 999
set source_count 0
set frame_count 0
set tracking 0
set last_commit -1
set last_data -1
set min_spacing 999999
set max_slots 0
set inputs [open $paced_dir/inputs.bin rb]
fconfigure $inputs -translation binary
set states [open $paced_dir/states.bin wb]
fconfigure $states -translation binary
set frames [open $paced_dir/frames.bin wb]
fconfigure $frames -translation binary
proc fail_paced {message} {
    set f [open $::paced_dir/failure-sat.bin wb];fconfigure $f -translation binary;puts -nonewline $f [debug read_block VRAM 0x1B00 128];close $f
    puts stderr "FLOE_PACED_FAIL $message source=$::source_count frame=$::frame_count pc=[reg PC]";exit 1
}
proc saved_paced_cpu {} {
    binary scan [debug read_block memory 0xC6F0 5] cu* r
    set flags [lindex $r 0]
    set p [expr {($flags&128)|(($flags&64)>>5)|([lindex $r 4]&1)|[debug read memory 0xC600]|[debug read memory 0xC601]}]
    return [binary format cu* [list [lindex $r 1] [lindex $r 3] [lindex $r 2] $p [debug read memory 0xC602]]]
}
proc actual_paced_cpu {} {
    set af [reg AF];set bc [reg BC]
    set p [expr {($af&128)|(($af&64)>>5)|([reg DE]&1)|[debug read memory 0xC600]|[debug read memory 0xC601]}]
    return [binary format cu* [list [expr {$af>>8}] [expr {$bc>>8}] [expr {$bc&255}] $p [expr {([reg IX]&127)|[debug read memory 0xC60B]}]]]
}
proc devices_paced {input} {
    binary scan $input cu* v
    lassign $v swcha swchb fire
    set mask [expr {(($swcha&16) ? 0 : 32)|(($swcha&32) ? 0 : 64)|(($swcha&64) ? 0 : 16)|(($swcha&128) ? 0 : 128)|($fire ? 1 : 0)}]
    keymatrixup 8 255;keymatrixdown 8 $mask
    set console [expr {(($swchb&1) ? 0 : 32)|(($swchb&2) ? 0 : 64)}]
    keymatrixup 6 96;keymatrixdown 6 $console
}
proc slots_paced {} {
    binary scan [debug read_block VRAM 0x1B00 128] cu* sat
    array set lines {}
    for {set i 0} {$i<128} {incr i 4} {
        set y [lindex $sat $i]
        if {$y==208} {break}
        set top [expr {($y+1)&255}]
        for {set row $top} {$row<$top+16 && $row<192} {incr row} {
            if {![info exists lines($row)]} {set lines($row) 0}
            incr lines($row)
            set ::max_slots [expr {max($::max_slots,$lines($row))}]
        }
    }
    if {$::max_slots>4} {fail_paced fifth-sprite-slot}
}
proc finish_paced {} {
    close $::inputs;close $::states;close $::frames
    if {[debug read_block memory 0xD000 0x2300] ne [string repeat [binary format c 165] 0x2300]} {fail_paced heap-guard}
    set stack_min 0xF380
    binary scan [debug read_block memory 0xF300 128] cu* stack
    for {set i 0} {$i<128} {incr i} {if {[lindex $stack $i]!=165} {set stack_min [expr {0xF300+$i}];break}}
    if {$stack_min<0xF340} {fail_paced stack-reserve}
    set f [open $::paced_dir/complete.json w]
    puts $f "\{\"complete\":true,\"source_steps\":$::source_count,\"frames\":$::frame_count,\"canonical_ram_injections\":0,\"clock_hz\":[machine_info z80_freq],\"ram_bytes\":[debug size {Main RAM}],\"min_spacing\":$::min_spacing,\"max_sprites_per_line\":$::max_slots,\"stack_min\":$stack_min,\"pal_flag\":[debug read memory 0xC21B]\}"
    close $f;exit
}
set boot_bp [debug set_bp $symbols(native_reset_done) {} {
    debug remove_bp $::boot_bp
    if {[machine_info z80_freq]!=3579545 || [debug size {Main RAM}]!=65536} {fail_paced clock-or-ram}
    if {[dict get [machine_info device VDP] version] ni {TMS9918A TMS9929A} || [llength [machine_info extension]]!=1} {fail_paced vdp-or-expansion}
    set ::slot [debug read ioports 168]
    debug write_block memory 0xD000 [string repeat [binary format c 165] 0x2300]
    debug write_block memory 0xF300 [string repeat [binary format c 165] 128]
    set input [read $::inputs 3]
    if {$input ne [binary format ccc 255 63 0]} {fail_paced first-cold-input}
    puts -nonewline $::states [saved_paced_cpu][debug read_block memory 0xC000 128][binary format i 0]
    incr ::source_count
    set VDP.too_fast_vram_access_callback {fail_paced fast-vram}
    debug set_watchpoint write_io 0x98 {} {
        set now [machine_info time]
        if {$::last_data>=0} {
            set cycles [expr {round(($now-$::last_data)*3579545)}]
            set ::min_spacing [expr {min($::min_spacing,$cycles)}]
            if {$cycles<29} {fail_paced fast-io-spacing}
        }
        set ::last_data $now
    }
    debug set_bp $::symbols(status_sample) {} {if {[reg A]&64} {fail_paced fifth-sprite-status}}
    debug set_bp $::symbols(paced_frame_start) {} {set ::tracking 1}
    debug set_bp $::symbols(native_step) {} {
        set input [read $::inputs 3]
        if {[string length $input]==0} {finish_paced;return}
        if {[string length $input]!=3} {fail_paced truncated-input}
        devices_paced $input
        set ::source_started [machine_info time]
    }
    debug set_bp $::symbols(native_return) {} {
        puts -nonewline $::states [actual_paced_cpu][debug read_block memory 0xC000 128][binary format i [expr {round(([machine_info time]-$::source_started)*3579545)}]]
        incr ::source_count
    }
    debug set_bp $::symbols(prepare) {} {
        if {!$::tracking} {return}
        set ::frozen_ram [debug read_block memory 0xC000 128]
        set ::frozen_scene [debug read_block memory 0xC100 32]
        set ::before [debug read_block VRAM 0 16384][debug read_block {VDP regs} 0 8]
    }
    debug set_bp $::symbols(paced_wait) {} {
        if {$::frozen_ram ne [debug read_block memory 0xC000 128] || $::frozen_scene ne [debug read_block memory 0xC100 32]} {fail_paced renderer-changed-logical-state}
        set ::prepared [debug read_block VRAM 0 16384][debug read_block {VDP regs} 0 8]
        set ::pending_busy [expr {$::last_commit<0 ? 0 : round(([machine_info time]-$::last_commit)*3579545)}]
    }
    debug set_bp $::symbols(paced_commit) {} {
        set now [machine_info time]
        set ::pending_period [expr {$::last_commit<0 ? 0 : round(($now-$::last_commit)*3579545)}]
        set ::last_commit $now
        set ::pending_frame [machine_info VDP_frame_count]
        set ::pending_y [machine_info VDP_msx_y_pos]
    }
    debug set_bp $::symbols(commit_end) {} {
        if {$::last_commit<0} {return}
        if {[debug read ioports 168]!=$::slot || [reg IFF]&3} {fail_paced slots-or-interrupts}
        slots_paced
        set header [binary format i* [list $::pending_frame $::source_count $::pending_busy $::pending_period [expr {round(([machine_info time]-$::last_commit)*3579545)}] $::pending_y [machine_info VDP_msx_y_pos]]]
        puts -nonewline $::frames $header$::frozen_ram$::frozen_scene$::before$::prepared[debug read_block VRAM 0 16384][debug read_block {VDP regs} 0 8]
        incr ::frame_count
    }
}]
after time 120 {fail_paced watchdog}
