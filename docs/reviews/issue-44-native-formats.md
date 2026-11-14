# Independent native-format diagnostic review

Reviewed whole Issue44 branch `57d32b52..424aab9` with a fresh-context,
read-only reviewer, then the working-tree native IRQ qualification adaptation.
The reviewer independently ran721 host tests and verified delivery-03's exact
five artifacts, runtime commit and maintained-source archive hashes.

No Critical or Important runtime findings were identified. Minor fixes applied:
correct the checker's startup-provenance docstring, describe the ZX0 executable
hash as recorded rather than verified, and validate scenario/video-mode routing.

The native IRQ test correctly replaces obsolete mapper PCs with the actual
interrupt-restoration entry/next instruction, and replaces the foreign-bank
invariant with exact fixed RAM and actual primary/subslot restoration. CPU,
alternate/index registers, SP/IFF, VRAM, snapshots and all nine completion
checks remain. Both video families passed against the selected32K ROM. The
first two labels are relocated native tests; their perturbed rates are not
performance evidence.

The review supports diagnostic publication with explicit cadence limits. It
does not approve Issue44 completion, cadence parity, owner playtest, listening
or physical hardware. PR45 remains draft and Issue44 remains open.

## Final additive review and acceptance

A separate read-only focused review of0e17966..6e65057 found no Critical,
Important or Minor findings:1872 SAT rows, unchanged default image, actual
three-way compiled cache coverage, and all original ordered-audio/PSG/CPU/
GPIO/unowned/stack/slot/VRAM guards retained. Positive/negative audio receipts
are bound to the exact published4ddec8fb ROM. The optional SAT experiment was
not selected. Subsequent standing-body exploration is also unselected and
archived; defaults and published product bytes stay unchanged. Its component
proof covered unclipped planes, not final viewport-edge acceptance. A failed
historical controlled-injection matrix setup is explicitly excluded.

On2026-11-14 the owner explicitly accepted v31 fluency as pleasant likev30
after disclosure of the measured4.1–8.3% lower cadence. This resolves Issue44
cadence approval, without claiming parity, listening or physical hardware.
Final pending diff consists of this acceptance/archival documentation, receipt
and passive profile entries. It adds no selected runtime or product change.

Final staged review found no Critical/Important blockers. Two minor status
wording inconsistencies were corrected: publication-time next-work text is
labelled historical, and the rejected standing receipt no longer says pending.
The reviewer independently rehashed the selected ROM and reran staged source
policy; final721-test log is green.
