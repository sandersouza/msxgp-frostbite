# Fresh synthetic renderer capture; never uses an original input/game backend.
set save_settings_on_exit false
if {$capture_image} {
    set renderer SDLGL-PP
    set maxframeskip 0
    set throttle on
    set speed 100
} else {
    set renderer none
    set throttle off
    set speed 999
}
set power true
set count 0
set min_spacing 999999
set last_data -1
set data_writes 0
set max_busy 0
set started 0
set frame_counts {}
set busy_cycles {}
set commit_cycles {}
set commit_y {}
set commit_start_y {}
set period_cycles {}
set last_commit -1
set step_counts {}
set surrogate_cycles {}
set max_slots 0
set signature [binary format cu* [lrange {0 1 2 3 4 5 6 7} 0 7]]
set canonical {}
for {set i 0} {$i<128} {incr i} {append canonical [binary format c $i]}
set guard [string repeat [binary format c 165] [expr {0xF300-0xD000}]]

proc fail {message} {
    puts stderr "FROSTBITE_RENDER_FAIL $message"
    exit 1
}
proc checked {script} {
    set code [catch {uplevel #0 $script} message options]
    if {$code==2 && [dict get $options -code]==0} {return}
    if {$code!=0} {fail $message}
}
proc require {expression message} {if {![uplevel 1 [list expr $expression]]} {error $message}}
proc binary_file {path} {set f [open $path wb];fconfigure $f -translation binary;return $f}
proc snapshot {channel} {puts -nonewline $channel [debug read_block VRAM 0 16384]}
proc measure_slots {} {
    binary scan [debug read_block VRAM 0x1B00 128] cu* sat
    array set lines {}
    for {set offset 0} {$offset<128} {incr offset 4} {
        set y [lindex $sat $offset]
        if {$y==208} {break}
        set top [expr {($y+1)&255}]
        for {set line $top} {$line<$top+16 && $line<192} {incr line} {
            if {![info exists lines($line)]} {set lines($line) 0}
            incr lines($line)
            if {$lines($line)>$::max_slots} {set ::max_slots $lines($line)}
        }
    }
    require {$::max_slots<=4} "SAT occupancy exceeds four"
}

proc finish {} {
    require {[debug read_block memory 0xC000 128] eq $::canonical} "canonical RAM changed"
    require {[debug read_block memory 0xD000 [string length $::guard]] eq $::guard} "RAM guard changed"
    set stack [debug read_block memory 0xF300 128]
    binary scan $stack cu* bytes
    set lowest 0xF380
    for {set i 0} {$i<128} {incr i} {
        if {[lindex $bytes $i]!=165} {set lowest [expr {0xF300+$i}];break}
    }
    require {$lowest>=0xF340} "stack reserve exhausted"
    if {$::capture_image} {screenshot -raw $::bench_dir/renderer.png}
    set f [open $::bench_dir/complete.json w]
    puts $f "\{\"complete\":true,\"cases\":$::count,\"min_spacing\":$::min_spacing,\"data_writes\":$::data_writes,\"stack_min\":$lowest,\"max_busy_cycles\":$::max_busy,\"max_sprites_per_line\":$::max_slots,\"frames\":\[[join $::frame_counts ,]\],\"busy_cycles\":\[[join $::busy_cycles ,]\],\"commit_cycles\":\[[join $::commit_cycles ,]\],\"commit_y\":\[[join $::commit_y ,]\],\"commit_start_y\":\[[join $::commit_start_y ,]\],\"period_cycles\":\[[join $::period_cycles ,]\],\"pal_flag\":[debug read memory 0xC21B],\"step_counts\":\[[join $::step_counts ,]\],\"surrogate_cycles\":\[[join $::surrogate_cycles ,]\]\}"
    close $f
    exit
}

proc dispatch_case {} {
    set input [read $::cases 32]
    if {[string length $input]==0} {finish;return}
    require {[string length $input]==32} "truncated input"
    set ::case_input $input
    debug write_block memory 0xC100 $input
    debug write memory 0xC216 1
    reg SP 0xF380
    reg PC $::symbols(rpc_start)
    if {$::inject_fault eq "spacing"} {
        set pc $::symbols(rpc_start)
        debug write_block memory 0xC600 [binary format c* [list 62 85 211 152 211 152 195 [expr {$pc&255}] [expr {$pc>>8}]]]
        reg PC 0xC600
    }
    set ::started [machine_info time]
    debug cont
}

proc complete_case {} {
    puts $::cycles [expr {round(([machine_info time]-$::started)*3579545)}]
    require {[debug read_block memory 0xC100 32] eq $::case_input} "renderer modified input ABI"
    require {[debug read_block memory 0xC000 128] eq $::canonical} "renderer modified canonical RAM"
    if {$::inject_fault eq "pixel"} {debug write VRAM 0 128;debug write VRAM 0x2000 240}
    if {$::inject_fault eq "sprite"} {debug write VRAM 0x1B00 1}
    if {$::inject_fault eq "guard"} {debug write memory 0xD000 0}
    if {$::inject_fault eq "overflow"} {
        debug write VRAM 0x1B20 [debug read VRAM 0x1B00]
        debug write VRAM 0x1B21 200
        debug write VRAM 0x1B22 0
        debug write VRAM 0x1B23 15
        debug write VRAM 0x1B24 208
    }
    measure_slots
    snapshot $::dumps
    puts -nonewline $::regs [debug read_block {VDP regs} 0 8]
    incr ::count
    dispatch_case
}

after time 5 {checked {
    require {[debug read memory 0xC2FE]==82 && [debug read memory 0xC2FF]==56} "renderer not ready"
    require {[debug size {Main RAM}]==65536 && [machine_info z80_freq]==3579545} "wrong CPU/RAM"
    require {[dict get [machine_info device VDP] version] in {TMS9918A TMS9929A}} "wrong VDP"
    require {[llength [machine_info extension]]==1} "unexpected hardware extension"
    require {[debug read memory 0x8000]!=255} "cartridge page2 not mapped"
    set ::boot_bp [debug set_bp $::symbols(paced_frame_start) {} {
        debug remove_bp $::boot_bp
        debug break
        after break {checked {
            debug write_block memory 0xC000 $::canonical
            debug write_block memory 0xD000 $::guard
            debug write_block memory 0xF300 [string repeat [binary format c 165] 128]
            set VDP.too_fast_vram_access_callback {fail "VDP rejected fast VRAM access"}
            debug set_watchpoint write_io 0x98 {} {checked {
                set now [machine_info time]
                if {$::last_data>=0} {
                    set spacing [expr {round(($now-$::last_data)*3579545)}]
                    if {$spacing<$::min_spacing} {set ::min_spacing $spacing}
                    require {$spacing>=29} "VRAM spacing $spacing"
                }
                set ::last_data $now
                incr ::data_writes
            }}
            debug set_bp $::symbols(status_sample) {} {
                if {[reg A]&64} {fail "actual fifth-sprite status"}
            }
            debug set_bp $::symbols(surrogate_call) {} {set ::surrogate_start [machine_info time]}
            debug set_bp $::symbols(surrogate_return) {} {
                lappend ::surrogate_cycles [expr {round(([machine_info time]-$::surrogate_start)*3579545)}]
            }
            if {$::bench_mode eq "rpc"} {
                set ::cases [open $::bench_dir/cases.bin rb]
                fconfigure $::cases -translation binary
                set ::dumps [binary_file $::bench_dir/vram.bin]
                set ::prepared [binary_file $::bench_dir/prepared.bin]
                set ::regs [binary_file $::bench_dir/regs.bin]
                set ::prepared_regs [binary_file $::bench_dir/prepared-regs.bin]
                set ::cycles [open $::bench_dir/cycles.txt w]
                set f [binary_file $::bench_dir/baseline.bin];snapshot $f;close $f
                debug set_bp $::symbols(prepared_marker) {} {
                    snapshot $::prepared
                    puts -nonewline $::prepared_regs [debug read_block {VDP regs} 0 8]
                }
                debug set_bp $::symbols(rpc_done) {} {debug break;after break {checked {complete_case}}}
                dispatch_case
            } else {
                debug write memory 0xC212 0
                debug write memory 0xC213 0
                debug write memory 0xC218 0
                debug write memory 0xC219 0
                set ::paced_start [machine_info time]
                debug set_bp $::symbols(paced_commit) {} {checked {
                    set now [machine_info time]
                    if {$::last_commit>=0} {lappend ::period_cycles [expr {round(($now-$::last_commit)*3579545)}]}
                    set ::last_commit $now
                    if {$::count==240} {finish;return}
                    set ::started $now
                    lappend ::frame_counts [machine_info VDP_frame_count]
                    lappend ::commit_start_y [machine_info VDP_msx_y_pos]
                    lappend ::step_counts [expr {[debug read memory 0xC218]+256*[debug read memory 0xC219]}]
                    incr ::count
                }}
                debug set_bp $::symbols(commit_end) {} {
                    measure_slots
                    lappend ::commit_cycles [expr {round(([machine_info time]-$::started)*3579545)}]
                    lappend ::commit_y [machine_info VDP_msx_y_pos]
                }
                debug set_bp $::symbols(paced_wait) {} {
                    if {$::count>0} {
                        set busy [expr {round(([machine_info time]-$::started)*3579545)}]
                        if {$busy>$::max_busy} {set ::max_busy $busy}
                        lappend ::busy_cycles $busy
                    }
                }
                reg PC $::symbols(paced_frame_start)
                debug cont
            }
        }}
    }]
}}
after time 30 {fail "bounded emulated-time watchdog"}
