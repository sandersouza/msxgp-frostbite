# Issue #3 handoff — reconstructed source and reviewed state boundaries

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/3
Branch: `codex/chore/3-reference-disassembly`.
Base: `eb8f5001550294b72ca51ae0bf5a5f719022cd1b` (issue #2 integration).
Rebuild utility commit: `f85c2e0948de8e46009005eac87c2abdbad604fb`.
Final reviewed head/integration identity: this issue's linked delivery PR.

Read [reference analysis](../reference-disassembly.md), the compact
[state map](../../references/disassembly-map.json),
[rebuild report](../../references/rebuild.json), approved design and workflow.
All public annotation is compact source-addressed research; complete original
source/listing, ROM, tool logs and rebuilt bytes stay local/ignored.

## Evidence and reproduction

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/reference_inventory.py
python3 -B scripts/reference_rebuild.py
```

The utility verifies the canonical manifest before tools, stages a verified
short-named copy and invokes DiStella/DASM with bounded waits; source is checked
again afterwards. Two fresh real runs rebuilt 4096 bytes byte-identically.
Original/rebuilt SHA-256:
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
The committed report records per-tool and generated-artifact hashes. Timestamped
source/listing text need not reproduce; exact ROM bytes must.

All 26 original-free tests pass, including changed/truncated/prefixed output,
invalid/missing input before external execution, tool failure, relative
executable resolution, private artifact location and short input names.
Pinned DiStella traps on a long absolute filename (50-byte unchecked buffer);
the regression was observed failing then passing with the verified local copy.
These are newly written Frostbite utilities, with no Atari 800/MADS dependency.

Static review plus an independent local py65 decode covers five code ranges,
3374 bytes/1769 instructions, 722 data/trailing-word bytes, all 34 direct JSRs
and 19 entries, all direct target boundaries and all 128 RAM bytes. Local
research audit scripts/results are under outputs/reference-rebuild/; they are
not original-free CI and do not imply executed path coverage. The full listing
and compact map identify all hardware reads, shared entries, flags, indirect
data pointers, frame phases and collision clear/read windows.

## Critical successor constraints

- #4 owns full mechanics contracts; #7 owns aligned deterministic replay and
  independent native-comparison oracles. No MSX gameplay or physical acceptance
  follows from this static review or issue #2's cadence measurement.
- F1 is a multi-bit phase dispatcher, not just an ALE terminal flag. C5/C6
  combine clocks/mode state. Verify names/thresholds dynamically before coding.
- TIA read aliases differ from writes: F244/F331/F3BE read CXPPMM at 07;
  F3C0 reads CXM1P at 01; F5AD reads INPT4/5 at 0C+C7. Collision state is
  sampled in raster windows, not one frame-wide overlap test.
- B0–B7 store four even floe / odd object contact pairs; B8/B9 are reduced
  indexes with negative sentinels. ED is a separate sticky shore collision.
- Preserve decimal arithmetic and live flags, multi-entry helpers FE00/03/04,
  tail paths FBCB→FE9B→FEA6→FEB8 and fractional state 99–9B.
- Audio/overscan work includes scoring at F4F7. Do not omit side effects when
  adapting TIA services. Reset with X=BF preserves 80–BE; inactivity X=D4
  preserves player records. FE77 swaps six-byte player records only.
- RNG at 82 advances three feedback iterations per FE8B call; scheduling and
  initial state still need controlled execution. #2 established only stable
  timing/control effects, not fully identical states between captures.
- .legacy/seaquest/ and the verified external snapshot remain untouched;
  final deletion belongs to #17. Do not stage original inputs/generated source.

After review and integration, close #3/Done and start dependency-ready #4 in
another fork titled `Frostbite — ISSUE #4`, within the Frostbite project.
Transfer exclusive checkout ownership; this chat stops writing after dispatch.
The next chat must verify actual GitHub/main state and read this handoff and
its local issue before editing. No pending files may silently cross ownership.

No MSX ROM was built in #3; no release is needed. Every later useful diagnostic
or playable MSX ROM requires a versioned prerelease with the exact ROM attached,
SHA-256/commit, limitations, next steps and concrete human test instructions.
