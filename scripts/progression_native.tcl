# Same physical-device/guard harness; these are intentional negative witnesses.
source [file join [file dirname [info script]] hazard_native.tcl]
debug set_bp $symbols(native_return) {} {
    if {$::inject eq "score"} {debug write memory 0xC04A [expr {1^[debug read memory 0xC04A]}]}
    if {$::inject eq "record"} {debug write memory 0xC04E [expr {1^[debug read memory 0xC04E]}]}
    if {$::inject eq "player"} {debug write memory 0xC047 [expr {1^[debug read memory 0xC047]}]}
}
