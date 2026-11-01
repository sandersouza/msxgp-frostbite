set save_settings_on_exit false
set renderer none
set throttle off
set speed 999
set count 0
set files {}
set source_file [open $floe_dir/cases.bin rb]
fconfigure $source_file -translation binary
set actual [open $floe_dir/actual.bin wb]
fconfigure $actual -translation binary
set bp -1
if {![info exists step_fixture]} {set step_fixture 0}
proc fail_floe {message} {puts stderr "FLOE_NATIVE_FAIL $message case=$::count pc=[reg PC] fault=[debug read memory 0xC6FD]";exit 1}
proc saved_floe_cpu {} {
    binary scan [debug read_block memory 0xC6F0 5] cu* r
    set flags [lindex $r 0]
    set p [expr {($flags&128)|(($flags&64)>>5)|([lindex $r 4]&1)|[debug read memory 0xC600]|[debug read memory 0xC601]}]
    return [binary format cu* [list [lindex $r 1] [lindex $r 3] [lindex $r 2] $p [debug read memory 0xC602]]]
}
proc finish_floe {} {
    close $::source_file;close $::actual
    if {[debug read_block memory 0xD000 0x2300] ne [string repeat [binary format c 165] 0x2300]} {fail_floe heap-guard}
    if {[debug read ioports 168]!=$::slot || [reg IFF]&3} {fail_floe slots-or-interrupts}
    set stack_min 0xF380
    binary scan [debug read_block memory 0xF300 128] cu* stack
    for {set i 0} {$i<128} {incr i} {if {[lindex $stack $i]!=165} {set stack_min [expr {0xF300+$i}];break}}
    if {$stack_min<0xF340} {fail_floe stack-reserve}
    set f [open $::floe_dir/complete.json w]
    puts $f "\{\"complete\":true,\"cases\":$::count,\"stack_min\":$stack_min,\"clock_hz\":[machine_info z80_freq],\"ram_bytes\":[debug size {Main RAM}],\"canonical_ram_injections\":[expr {$::natural ? 0 : $::count}]\}"
    close $f;exit
}
proc devices_floe {swcha swchb fire} {
    set mask [expr {(($swcha&16) ? 0 : 32)|(($swcha&32) ? 0 : 64)|(($swcha&64) ? 0 : 16)|(($swcha&128) ? 0 : 128)|($fire ? 1 : 0)}]
    keymatrixup 8 255;keymatrixdown 8 $mask
    set console [expr {(($swchb&1) ? 0 : 32)|(($swchb&2) ? 0 : 64)}]
    keymatrixup 6 96;keymatrixdown 6 $console
}
proc dispatch_floe {} {
    if {$::natural} {
        set input [read $::source_file 3]
        if {[string length $input]==0} {finish_floe;return}
        if {[string length $input]!=3} {fail_floe truncated-input}
        binary scan $input cu* values
        devices_floe {*}$values
    } else {
        set record [read $::source_file 133]
        if {[string length $record]==0} {finish_floe;return}
        if {[string length $record]!=133} {fail_floe truncated-fixture}
        binary scan [string range $record 128 132] cu* r
        set p [lindex $r 3]
        set flags [expr {($p&128)|(($p&2) ? 64 : 0)}]
        debug write_block memory 0xC000 [string range $record 0 127]
        debug write_block memory 0xC6F0 [binary format ssc [expr {256*[lindex $r 0]+$flags}] [expr {256*[lindex $r 1]+[lindex $r 2]}] [expr {$p&1}]]
        debug write memory 0xC600 [expr {$p&64}]
        debug write memory 0xC601 [expr {$p&60}]
        debug write memory 0xC602 [lindex $r 4]
        if {$::step_fixture} {
            set input [read $::source_file 3]
            if {[string length $input]!=3} {fail_floe truncated-phase-input}
            binary scan $input cu* values
            devices_floe {*}$values
        }
    }
    debug write memory 0xC6FD 0
    set ::started [machine_info time]
    reg PC 0xC6D0
    debug cont
}
proc capture_floe {} {
    if {$::inject eq "contact" && !$::natural} {debug write memory 0xC036 [expr {128^[debug read memory 0xC036]}]}
    puts -nonewline $::actual [saved_floe_cpu][debug read_block memory 0xC000 128][binary format i [expr {round(([machine_info time]-$::started)*3579545)}]]
    if {[debug read memory 0xC6FD]!=0} {fail_floe native-fault}
    incr ::count
    dispatch_floe
}
set boot_bp [debug set_bp $symbols(native_reset_done) {} {
    debug remove_bp $::boot_bp
    debug break
    after break {
        if {[machine_info z80_freq]!=3579545 || [debug size {Main RAM}]!=65536} {fail_floe clock-or-ram}
        if {[dict get [machine_info device VDP] version] ni {TMS9918A TMS9929A} || [llength [machine_info extension]]!=1} {fail_floe vdp-or-expansion}
        set ::slot [debug read ioports 168]
        debug write_block memory 0xD000 [string repeat [binary format c 165] 0x2300]
        debug write_block memory 0xF300 [string repeat [binary format c 165] 128]
        if {$::natural} {
            set input [read $::source_file 3]
            if {$input ne [binary format ccc 255 63 0]} {fail_floe first-cold-input}
            puts -nonewline $::actual [saved_floe_cpu][debug read_block memory 0xC000 128][binary format i 0]
            incr ::count
        }
        set entry [expr {($::natural || $::step_fixture) ? $::symbols(native_step) : $::symbols(visible_step)}]
        debug write_block memory 0xC6D0 [binary format cu* [list 205 [expr {$entry&255}] [expr {$entry>>8}] 195 214 198 24 254]]
        debug set_bp 0xC6D6 {} {debug break;after break capture_floe}
        if {$::inject eq "port2_fire"} {
            debug set_bp $::symbols(sample_native_return) {} {debug write memory 0xC30D [expr {128^[debug read memory 0xC30D]}]}
        }
        dispatch_floe
    }
}]
after time 120 {fail_floe watchdog}
