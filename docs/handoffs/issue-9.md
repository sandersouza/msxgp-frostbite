# Issue #9 handoff — original graphics preparation

Issue:https://github.com/sandersouza/msxgp-frostbite/issues/9.
Branch:`codex/feat/9-original-graphics`; base
`518229220e7633eb7c9b119aefc708e23cda7855`. Exact-head review/CI and integration
readbacks are linked from the issue/PR. Issue9 retains exclusive checkout ownership
until its explicit transfer; no successor implementation starts in this chat.

## Frozen evidence and local assets

Producer:`82ac6a37447b65ef132c8d9b9370f85f95ae8e43`; canonical ignored directory
`outputs/graphics/issue9-final/`. Full private evidence SHA-256
`10c41e91c7fea93b5c40997f7ab67ce3a23b2b9d71d7479f93cfd6ab4e75ec45`.
The [public report](../../references/graphics-result.json) contains only compact
facts/identities; [graphics operations](../original-graphics.md) and
[mapping contract](../../references/graphics-contract.json) define adaptations.
The local catalog, raw source pixels/states, mapped pixels, VRAM and PNGs must
remain ignored. Later docs commits do not relabel the producer.

Verified:544 fixtures repeated under two fresh seeded ALE0.12.1 instances;398table
views;382nonblank original-raster matches and4blank views. Six corruptions reject;
16visible igloo stages and actual day/night palette probes pass. Both independent
VRAM decoders equal mapped source pixels in every captured frame. The compact
report carries exact tile/sprite maxima. Mapping preserves serialized original
state and RAM. These are controlled presentation fixtures, not natural/full-game
or native performance proof. Host suite147tests passes at this checkpoint.

```sh
make source-check
make test
.venv/bin/python -B scripts/graphics_reference.py --out outputs/graphics/fresh-handoff-check
make ci-verify
```

Source ROM remains4096bytes,SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
No ROM/runtime changes occur in9. Latest testable MSX ROM remains
[v0.0.2-renderer](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.2-renderer),
32768bytes,Normal/plain32KiB,SHA-256
`111ded95de3c91ff92093abe5fcee4b436150a99ee96a5a9634dfc9ebeffd4c7`,
frozen producerb249373be1cc2382f87b5bb97caa865ae0c6641c.
Correct package:`outputs/releases/v0.0.2-renderer-reviewed`; the older default
package contains a rejected candidate and must never be uploaded. No new release
is warranted for unchanged runtime bytes. Every future changed testable ROM needs
a new VERSION/prerelease, exact attached tested ROM, source/hash/current/next/human
instructions, appropriate checks and fresh downloaded-asset hash verification.

## Integration decisions and costs

- Owner-approved native inline execution and exclusive shared checkout supersede
 routine permission/worktree menus. Cost: one writer only; old chat stops edits.
- Prepare assets/offline fit in9; runtime integration follows in10. Cost: no
 dynamic upload, native timing, mapper capacity or playable ROM acceptance yet.
- The initial source7–198 viewport was rejected when right-edge rendering put
 footer pixels on199. Final mapping keeps7–185 and189–201 at1:1Y, removes only
 three verified-black separator rows. Cost: every new state needs the crop gate;
 unusual states may need revised viewport. X=8+floor(3*x/2), all160columns retained.
- Constrain chromatic palette choices to keep water blue; grayscale contrast bins
 retain dark bear/gray igloo/white shore. Cost: brightness/gray levels differ;
 physical/manual palette acceptance remains pending. The first RGB candidate
 produced magenta grays and was rejected before final freeze.
- Use offline bounded sprite repairs to avoid background two-color pixel loss.
 Cost: this allocation differs from #8's active cache and sprite roles; packing
 static frames proves VRAM capacity, not real-time integration feasibility.
- Split validation into repeat/file/target boundaries. Cost: only the complete
 capture orchestration establishes all proof; invoking one helper alone does not.
- Operational graphics documentation is outside service C4/Backstage generation.
 Cost: no service catalog artifact is produced.

Igloo preparation needs one settling source frame before capture; changing CD
alone initially produced15identicalimages. Owned RED→GREEN tests now require16
distinct rasters and actual day/night colors (level bit2). The rejected first
candidate remains local under outputs/issue9/, never Frostbite acceptance.

The original bear is24target pixels wide. #8's resident sprite table is full and
its synthetic geometry/grid differ. Native integration must choose/reallocate
active variants/background bear and measure exact original placement. Observed
interior source anchors:player(E6,E4+28),bear(E8+1,58),row0object(D4,160); clipped
frames are authoritative, not a promise these formulas cover every positioning
phase. Logical row0 is the bottom,3the top. Never alter source collision geometry.
Do not silently spend the747cycleNTSCsyntheticmargin or the1920ROMpadding bytes.
The failed unaligned independent-strip prototype does not prove fused compositing
impossible; the latter remains unmeasured. See issue8 handoff for ABI/SP/DI guards.

## Completion and successor

One fresh independent whole-branch review, material-finding disposition, exact-head
CI and merge readbacks belong to this issue's delivery. Close/Done only after its
own acceptance and integration. Manual GUI/framebuffer, listening, expanded slots
and physical MSX evidence remain pending; source/target local previews do not
establish those results. Preserve .legacy/seaquest and verified external snapshot;
final cleanup is17after working replacement acceptance.

Start/reuse a dedicated `Frostbite — ISSUE #10` fork in project
`0fd5a899-599e-40d4-988e-46b3d31433dd`, cwd
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`. Dependencies7/8/9 must be
integrated; move10In progress and take `codex/feat/10-<slug>`. Transfer clean main,
exact commit, no pending implementation ownership, source/ROM identities and these
limits. #10 owns native input/jump/air/floe transport, source-state equivalence,
asset integration where needed and full active-play timing. No #10 code belongs
in this issue chat. After explicit transfer issue9 stops all checkout edits.

## Independent review and delivery checkpoint

[PR29](https://github.com/sandersouza/msxgp-frostbite/pull/29) carries the focused
delivery. One fresh read-only reviewer at160c4d6 found no Critical, Important or
Minor findings. It reran147host tests, all544original ALE fixtures with exact
before/after RAM/full states, both private artifact runs and producer/backend
manifests. It regenerated all544mappings/VRAM images, checked both decoders,
45/31/47tiles,3slots,352SPTbytes and6032repairs with zero final pixel loss. It also
verified the16igloo differences occur in the construction region. No fix pass or
redundant second review was needed.

[Push CI41260445125](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41260445125)
and [PR CI41260491893](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41260491893)
passed at160c4d6. Downloaded CI reports contain exactly the three allowed files,
147tests and zero skipped results; CI builds the unchanged111ded95renderer ROM.
Final documentation-head CI/merge/closure readbacks are recorded in PR29/issue9.

Review boundaries were explicitly accepted: native upload/cache/input/audio timing
and adapter integration remain10; controlled fixtures do not prove natural/full
gameplay; finite edge coverage cannot certify all future states; physical RGB,
manual viewing/listening and hardware verdicts remain pending. Costs are latent
integration/performance, rare-state and hardware defects until those gates run.
The reviewer did not certify future GitHub delivery; the executor must verify
exact final-head CI and clean merged main before closure. No ROM changed, so no
new release/testable-ROM claim follows from this asset preparation.

## Verified integration receipt

PR29 merged as `340c0beed6ff5842ecceaee519c1c91c5437914f`.
[Final-head CI41260698227](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41260698227)
and [merged-main CI41260780952](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41260780952)
passed. Final CI reports were downloaded:three allowed files,147tests,zero skipped
results and unchanged renderer ROM111ded95. Local merged147tests and source policy
pass; main was clean. Final integrated helper/contract blobs equal frozen82ac6a3,
whose private artifact and original/target identities remain unchanged.

The final documentation receipt is linked from issue9; close/Done follows its
integration. Prepared successor `Frostbite — ISSUE #10`, thread
`01a194b3-49d2-76b0-868a-693d1d876035`, was forked, titled and assigned to Frostbite
project `0fd5a899-599e-40d4-988e-46b3d31433dd`; its idle cwd is this checkout.
It starts only after explicit exclusive ownership transfer. No implementation
files are pending. Preserve all original/generated/legacy local material.
