# Issue #6 handoff — public-source CI and scoped tracking

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/6
Branch: `codex/chore/6-original-free-ci-tracking`.
Base: `2e25d8e502fb126a971f42592e3b8fe267bee357` (issue5 delivery recorded).
Source gate/CI checkpoint: `3af409657c2dd2181d30bba06857da60c489cd9e`.
Linux architecture correction: `c85f5575ea12edd0d083dc8a1d87b54f1e4feda3`.
Tracking checkpoint: `f15693459a76142052a59217c18969a5960cb844`.
Delivery PR: https://github.com/sandersouza/msxgp-frostbite/pull/25
Final source/integration and current CI results are linked in that PR.

## Scope and commands

- Read-only Ubuntu24.04 workflow with SHA-pinned actions, hash-locked py65,
  verified source-pinned sjasmplus, complete unit suite and repeated diagnostic
  build identity; only three named report files are uploaded.
- Staged-blob source gate, no traversal of ignored original/legacy research.
- Project7 catalog and local dry-run/apply helper, unique scoped issue matching,
  validated metadata/options/completeness and refreshed readback after writes.
- Issue/PR templates and [operational checklist](../ci-and-tracking.md).

```sh
make source-check
.venv/bin/python -B -m unittest discover -s tests -q
make ci-verify
.venv/bin/python -B scripts/project_tracking.py
.venv/bin/python -B scripts/project_tracking.py --apply
.venv/bin/python -B scripts/project_tracking.py --issue 6 --status 'In review' --apply
```

Use [clean source CI reproduction](../ci-and-tracking.md) for a new environment.
The CI setup prepares only sjasmplus; macOS full research setup stays separate.

## Verified evidence

The initial remote job compiled sjasmplus then rejected ELF'sx86-64 spelling.
A regression observed RED→GREEN adds the explicit architecture alias while
retaining mismatch rejection. No Darwin host setup check was bypassed.
[Run41244088656](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41244088656)
passed all69 tests and repeated builds at clean checkpointf156934. Downloaded
artifacts contained only unit log/build.json/SHA256SUMS; clean source/hash matched.
An additional oversized/non-UTF8 staged-file case brings the suite to70 tests.
Latest reviewed-head CI evidence belongs in the delivery PR before merge.
Both push/PR runs41244304032/41244322317 passed all70 tests on e090411; downloaded
current-head reports had no skips and exactly the three expected report files.
A source-only macOS clone with new venv/new assembler also passed this70-test
checkpoint and repeated builds without original inputs or inherited caches.

All17 catalog records match their local issue bodies. Live project audit included
all63 items, with no metadata changes planned. Apply was a verified no-op. The
helper moved only issue6 from In progress to In review, then repeated with no
write. No shared field definitions or other game's items were changed.

## ROM identity and evidence limits

No game/diagnostic source bytes changed. Repeated diagnostic bytes still match
published v0.0.1-diagnostic, 16,384bytes Normal/plain16KiB, SHA-256
`d46320aec4b148c3b885d54de051bc078539b65a7a8bf739bb4e9e956c2028ca`.
The published release source is8363b3f391caeef03dcd08ab380d26280e227831.
CI never uploads the cartridge or publishes/replaces a release. Future changed
testable ROMs require new versions and the owner's complete release/human-test gate.

CI validates build/tests, not an emulator, gameplay or hardware. Earlier issue5
NTSC MSX1 smoke/rendered preview and pending audio/PAL/physical/Intel/cold-host
checks retain their own evidence boundaries. The source guard cannot establish
provenance of arbitrary renamed textual tables; explicit review remains needed.
Project APIs are nontransactional: inspect partial/uncertain outcomes and replan;
fresh snapshots are not atomic compare-and-swap against concurrent same-item edits.

## Preservation and continuation

Original ROM/full disassembly/derived assets and .legacy/seaquest remain ignored
and untouched. Issue17 owns final cleanup after working replacements pass.
No implementation files transfer pending. On integrated delivery, close/Done6
and start dependency-ready issue7 in another dedicated Frostbite fork, preserving
exclusive shared-checkout ownership. Read issue7, issue4 mechanics contracts,
and prior handoffs:101CPUprobes are not full TIA geometry/reachability evidence;
reference backend alignment, initialization/RNG and NMOS flags require their own
validation. Do not promote a diagnostic build or old Seaquest success to gameplay proof.

## Independent review and disposition

One fresh read-only reviewer examined2e25d8e..e090411 and independently passed70
tests. No Critical/Minor findings. Three Important cases were reproduced RED,
fixed GREEN in one pass and followed by the full75-test suite:

- Renaming a marked disassembly to.txt bypassed the assembly-extension check.
  Recognizable generated headers now fail independently of filename; ordinary
  tool discussion stays allowed.
- Missing/conflicting repository/type on a canonical Frostbite URL could produce
  an attachment write. Identity indicators are now cross-checked before planning;
  valid drafts, other games and same-repository PRs remain untouched.
- Estimate's field schema was not checked. Both SingleSelect and TEXT regressions
  now fail before any transport mutation; the live NUMBER schema is obtained via
  GraphQL before the first operation. Partial-failure recovery also has coverage.

No second review cycle was requested; material fixes are covered by regression
tests and latest-head CI is required before integration. Live sync after fixes
remains a verified no-op.

Decisions retained from review: unmarked text-table provenance requires manual
review (cost if wrong: unrecognized original-derived text could be published);
concurrent same-item edits require coordination (cost: overwrite/race despite
fresh reads); emulator/gameplay/audio/hardware remain separate (cost: a build
success cannot detect runtime defects). Exclusive shared-checkout ownership is
authorized (cost: branch isolation relies on one writer); C4/Backstage generation
is outside operational documentation (cost: no service catalog output). Final
integration/closure/successor are verified as delivery actions, never inferred
from the review verdict.
