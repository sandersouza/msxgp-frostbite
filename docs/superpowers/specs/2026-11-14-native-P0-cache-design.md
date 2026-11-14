# Native P0 cache cadence recovery

Continue Issue44 against the immutable v31 native payload. The owner explicitly
authorized execution to issue completion and opted out of routine approvals.
This is an implementation choice under the existing preservation requirement,
not an approved cadence exception. Keep v30/v31 and all published bytes intact.

The current P0 cache-hit publisher spends four indexed stores and four16-bit
IY increments per SAT entry. Replace that byte writer with a DE destination,
8-bit E increments within C400..C417, and IYL as the pattern counter. Read the
existing signed displacement/color pairs through HL with byte increments;
all six32-byte metadata ways keep their current placement and exact keys.
Restore the same final IY/p_s_sat pointer and clear carry on return. The caller
permits AF/BC/DE/HL scratch; IX, metadata and publication validity stay intact.

Integration inspection found the selected v31 already calls variant_lookup.scan
from B0A5, avoiding the second initialization described by older maintained
assembly. Preserve and verify that compiled direct caller and its initial
checked default. Do not claim another saving or alter miss/replacement ordering.

First certify original control assembly against the actual v31 instruction
extent. Compare native SAT bytes, final pointer, ABI and timings over both
generations, all three resident ways,1..6entries, signed-offset/wrap cases and
horizontal edge values. Then link optional experimental patches and compare
four whole-route source-defined cold RAM experiments against identical v31
control startup. A lower routine cycle count is not a whole-frame win.

Do not create another human-test ROM until whole-frame measurements justify it.
Any candidate must retain original CPU/RAM, pixels, physical keys, active-page,
IRQ, input and PSG contracts; native size/slot/stack constraints remain unchanged.
No bank switching, new RAM/VRAM or visual/mechanics adaptation is introduced.

Rejected alternative for now: another blue ice atlas. Total VRAM is not the
bank-specific budget. Read-only footer factoring found1352 bytes instead of
3008, but bank2 lacks the62 simultaneous free tile pairs required for a full
extra atlas under the current dynamic/footer roles. Unused CPU key bytes are
not proof of unused physical tile patterns.
