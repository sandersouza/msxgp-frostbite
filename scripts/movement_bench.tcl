set save_settings_on_exit false
set renderer none
set throttle off
set speed 999
set power true
set count 0
set busy {}
set frames {}
set commits {}
set last_commit -1
set min_spacing 999999
set last_data -1
set max_slots 0
set sources 0
set source_cycles {}
set work_frame 0
set prepare_cycles {}
set period_cycles {}
set commit_cycles {}
set commit_end_y {}
set step_counts {}
set mode_samples {}
set files {}
proc fail_movement {message} {puts stderr "MOVEMENT_FAIL $message pc=[reg PC] frame=$::count header=[debug read memory 0x4000],[debug read memory 0x4001] marker=[debug read memory 0xC2FE],[debug read memory 0xC2FF] slot=[debug read ioports 168]";exit 1}
proc require_movement {condition message} {if {![uplevel 1 [list expr $condition]]} {fail_movement $message;error $message}}
proc binary_file {path} {set f [open $path wb];fconfigure $f -translation binary;return $f}
proc cpu_state {} {
    set af [reg AF];set bc [reg BC]
    set p [expr {($af&128)|(($af&64)>>5)|([reg DE]&1)|[debug read memory 0xC600]|[debug read memory 0xC601]}]
    return [binary format cu* [list [expr {$af>>8}] [expr {$bc>>8}] [expr {$bc&255}] $p [expr {([reg IX]&127)|[debug read memory 0xC60B]}]]]
}
proc step_devices {} {
    set tick [expr {[debug read memory 0xC218]+256*[debug read memory 0xC219]}]
    set tick [expr {$tick%192}]
    set mask [expr {$tick<80 ? 0 : $tick<115 ? 64 : $tick<140 ? 16 : $tick<175 ? 32 : 128}]
    if {$tick>=120 && $tick<125} {set mask [expr {$mask|1}]}
    set ::key_mask $mask
    keymatrixup 8 255
    keymatrixdown 8 $mask
}
proc frame_devices {} {
    if {$::transitions} {
        if {$::work_frame%4==0} {keymatrixdown 6 128;keymatrixdown 7 1}
        if {$::work_frame%4==2} {keymatrixup 6 128;keymatrixup 7 1}
    }
    incr ::work_frame
}
proc slots_movement {} {
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
    require_movement {$::max_slots<=4} fifth-sprite-slot
}
proc finish_movement {} {
    require_movement {[debug read_block memory 0xD000 0x2300] eq [string repeat [binary format c 165] 0x2300]} heap-guard
    close $::state_file
    close $::scenes
    foreach channel $::files {close $channel}
    set stack_min 0xF380
    binary scan [debug read_block memory 0xF300 128] cu* stack_bytes
    for {set i 0} {$i<128} {incr i} {if {[lindex $stack_bytes $i]!=165} {set stack_min [expr {0xF300+$i}];break}}
    require_movement {$stack_min>=0xF340} stack-reserve
    set f [open $::bench_dir/complete.json w]
    puts $f "\{\"complete\":true,\"cases\":$::count,\"busy_cycles\":\[[join $::busy ,]\],\"frames\":\[[join $::frames ,]\],\"commit_y\":\[[join $::commits ,]\],\"min_spacing\":$::min_spacing,\"max_sprites_per_line\":$::max_slots,\"source_steps\":$::sources,\"source_cycles\":\[[join $::source_cycles ,]\],\"prepare_cycles\":\[[join $::prepare_cycles ,]\],\"period_cycles\":\[[join $::period_cycles ,]\],\"commit_cycles\":\[[join $::commit_cycles ,]\],\"commit_end_y\":\[[join $::commit_end_y ,]\],\"step_counts\":\[[join $::step_counts ,]\],\"mode_samples\":\[[join $::mode_samples ,]\],\"stack_min\":$stack_min,\"pal_flag\":[debug read memory 0xC21B]\}"
    close $f
    exit
}
after time 5 {
    require_movement {[debug read memory 0xC2FE]==82 && [debug read memory 0xC2FF]==56} not-ready
    require_movement {[machine_info z80_freq]==3579545 && [debug size {Main RAM}]==65536} clock-or-ram
    require_movement {[dict get [machine_info device VDP] version] in {TMS9918A TMS9929A} && [llength [machine_info extension]]==1} vdp-or-expansion
    set ::boot_bp [debug set_bp $::symbols(paced_frame_start) {} {
        debug remove_bp $::boot_bp
        debug break
        after break {
            set f [open $::bench_dir/initial.bin rb];set initial [read $f];close $f
            debug write_block memory 0xC000 [string range $initial 0 127]
            debug write_block memory 0xC6F0 [string range $initial 128 132]
            debug write_block memory 0xC600 [string range $initial 133 135]
            debug write_block memory 0xD000 [string repeat [binary format c 165] 0x2300]
            debug write_block memory 0xF300 [string repeat [binary format c 165] 128]
            foreach addr {0xC212 0xC213 0xC218 0xC219 0xC622} {debug write memory $addr 0}
            debug write memory 0xC11F $::initial_layout
            debug write memory 0xC11E $::initial_width
            set ::state_file [binary_file $::bench_dir/states.bin]
            foreach name {adapters scene_actual before_vram before_regs prepared prepared_regs presented presented_regs} {
                set ::$name [binary_file $::bench_dir/$name.bin]
                lappend ::files [set ::$name]
            }
            set ::slot_guard [debug read ioports 168]
            set ::scenes [open $::bench_dir/scenes.bin rb]
            set VDP.too_fast_vram_access_callback {fail_movement fast-vram}
            debug set_watchpoint write_io 0x98 {} {
                set now [machine_info time]
                if {$::last_data>=0} {
                    set spacing [expr {round(($now-$::last_data)*3579545)}]
                    set ::min_spacing [expr {min($::min_spacing,$spacing)}]
                    require_movement {$spacing>=29} fast-io-spacing
                }
                set ::last_data $now
            }
            debug set_bp $::symbols(status_sample) {} {if {[reg A]&64} {fail_movement fifth-sprite-status}}
            debug set_bp $::symbols(paced_frame_start) {} {frame_devices}
            debug set_bp $::symbols(native_step) {} {step_devices}
            debug set_bp $::symbols(native_call) {} {
                set ::source_started [machine_info time]
                set ::before [cpu_state]
                append ::before [debug read_block memory 0xC000 128]
            }
            debug set_bp $::symbols(native_return) {} {
                if {$::inject_fault eq "state"} {debug write memory 0xC02A [expr {1^[debug read memory 0xC02A]}]}
                set row $::before
                append row [cpu_state] [debug read_block memory 0xC000 128] [binary format c $::key_mask]
                foreach addr {0xC340 0xC342 0xC30C 0xC30D} {append row [binary format c [debug read memory $addr]]}
                puts -nonewline $::state_file $row
                lappend ::source_cycles [expr {round(([machine_info time]-$::source_started)*3579545)}]
                incr ::sources
            }
            debug set_bp $::symbols(adapt_done) {} {
                puts -nonewline $::adapters [debug read_block memory 0xC000 128][debug read_block memory 0xC100 32]
                set s [read $::scenes 32]
                require_movement {[string length $s]==32} missing-scene
                set presentation_mode [debug read_block memory 0xC11E 2]
                debug write_block memory 0xC100 [string range $s 0 29]
                debug write_block memory 0xC11E $presentation_mode
            }
            debug set_bp $::symbols(paced_commit) {} {
                set now [machine_info time]
                if {$::last_commit>=0} {lappend ::period_cycles [expr {round(($now-$::last_commit)*3579545)}]}
                if {$::count==240} {finish_movement;return}
                set ::last_commit $now
                lappend ::frames [machine_info VDP_frame_count]
                lappend ::commits [machine_info VDP_msx_y_pos]
                slots_movement
                lappend ::step_counts [expr {[debug read memory 0xC218]+256*[debug read memory 0xC219]}]
                lappend ::mode_samples [expr {2*[debug read memory 0xC11F]+[debug read memory 0xC11E]}]
                incr ::count
            }
            debug set_bp $::symbols(commit_end) {} {
                if {$::inject_fault eq "pixel"} {debug write VRAM 0 128;debug write VRAM 0x2000 240}
                if {$::inject_fault eq "guard"} {debug write memory 0xD000 0}
                if {$::inject_fault eq "sprite"} {
                    debug write VRAM 0x1B20 [debug read VRAM 0x1B00]
                    debug write VRAM 0x1B21 200
                    debug write VRAM 0x1B22 0
                    debug write VRAM 0x1B23 15
                    debug write VRAM 0x1B24 208
                }
                require_movement {([reg IFF]&3)==0 && [debug read ioports 168]==$::slot_guard} interrupts-or-slots
                slots_movement
                lappend ::commit_cycles [expr {round(([machine_info time]-$::last_commit)*3579545)}]
                lappend ::commit_end_y [machine_info VDP_msx_y_pos]
                puts -nonewline $::presented [debug read_block VRAM 0 16384]
                puts -nonewline $::presented_regs [debug read_block {VDP regs} 0 8]
            }
            debug set_bp $::symbols(prepare) {} {
                set ::prepare_start [machine_info time]
                set ::frozen_canonical [debug read_block memory 0xC000 128]
                set ::frozen_scene [debug read_block memory 0xC100 32]
                puts -nonewline $::scene_actual $::frozen_scene
                puts -nonewline $::before_vram [debug read_block VRAM 0 16384]
                puts -nonewline $::before_regs [debug read_block {VDP regs} 0 8]
            }
            debug set_bp $::symbols(paced_wait) {} {
                require_movement {$::frozen_canonical eq [debug read_block memory 0xC000 128] && $::frozen_scene eq [debug read_block memory 0xC100 32]} renderer-changed-logical-state
                puts -nonewline $::prepared [debug read_block VRAM 0 16384]
                puts -nonewline $::prepared_regs [debug read_block {VDP regs} 0 8]
                lappend ::prepare_cycles [expr {round(([machine_info time]-$::prepare_start)*3579545)}]
                if {$::count>0} {lappend ::busy [expr {round(([machine_info time]-$::last_commit)*3579545)}]}
            }
            if {$::inject_fault eq "spacing"} {
                set entry $::symbols(paced_frame_start)
                debug write_block memory 0xC6D0 [binary format cu* [list 62 85 211 152 211 152 195 [expr {$entry&255}] [expr {$entry>>8}]]]
                reg PC 0xC6D0
            }
            frame_devices
            debug cont
        }
    }]
}
after time 20 {fail_movement watchdog}
