# Compact hazard edges and shared accumulation

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44).
All code here is unlinked from the accepted game. These are component results,
not a compact game release or evidence of whole-frame speed.

The maintained `compact_hazard_edge.py` reproduces the complete declared
ordinary exceptional-X domain:36,241,920cells ×228literal player views. The
shore compiler matches5,376,000cells ×228views. Both compare against the sealed
v0.0.30 ROM and separately derived source-clock models. Ordinary geometry keeps
eight visual rows although the common collision kernel uses seven. Shore
geometry keeps18rows, including the clearing row and initial fine motion.

| Actual Z80 component | Cases | Code / extra data bytes | Cycles min / mean / P95 / max |
| --- | ---: | ---: | --- |
| Ordinary horizontal context |102,400|112 /0|598 /1012.942 /1366 /1369|
| Ordinary five-mask program |73,458|402 +112context /553|8535 /10936.196 /13553 /15466|
| Generic mask accumulation |1,091,680|85 +101row /518shared|75 /5146.788 /12446 /13223|

Cycles include the fixture CALL/JP and MSX1 instruction timing. The program
generator covers1,113distinct exceptional contexts ×33shapes ×2reflections,
comparing all40output bytes. Its553data bytes comprise512glyph bytes,
33shape offsets and8sample masks; integration must share overlapping source
data rather than sum every fixture's data allocation.

The generic evaluator consumes interleaved old/equal/different/exit/visible
mask rows. It supports0/1/8/18rows without changing the qualified row operator.
The1,091,680-case corpus contains70,924sampled direct-v30 floe responses plus
the complete declared one-hot last-row boundary corpus. It is **not** all
programs ×all views ×all Y, nor a complete native hazard query proof.

Native guards verify immutable inputs/programs, permitted scratch/stack writes,
IX/IY/SP/IFF preservation and standard-speed64KiB MSX1 execution. C800 fixture
program buffers overlap current NAME storage and are not integration addresses.
The ordinary program run01 is rejected: its virtual watchdog expired after a
matching66,443-case prefix. Run02 changes only the observer watchdog, completes
all73,458cases, and preserves the kernel ROM and matching-prefix cycles.

Receipts live in `references/compact-delivery/issue-44-*-host.json`,
`issue-44-hazard-context.json`, `issue-44-hazard-program.json` and
`issue-44-generic-mask.json`. Private original-derived bytes remain ignored.
Native shore generation, complete query glue, collision integration and
whole-frame NTSC/PAL qualification are still required.
