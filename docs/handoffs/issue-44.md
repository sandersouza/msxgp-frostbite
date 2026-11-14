# Published native delivery — continue Issue44 cadence work

[Prerelease v0.0.31](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.31-native-formats-diagnostic)
is published with12 assets: exact32K Normal ROM, genuine COM/BIN/BASIC companion,
ZIP, workbook, SHA-256, runtime/qualification sources and test instructions.
All downloaded bytes equal the sealed package and tested artifacts; the public
WebMSX Normal link visibly loaded the game. This is browser-startup evidence,
not manual gameplay/listening or physical MSX acceptance. Immutable receipts:
`references/compact-delivery/issue-44-native-formats.json` and
`issue-44-native-formats-delivery.json`.

Runtime source424aab92bd269821a703fda81749e74f4ca6616c; qualification/release tag
sourceee704f2c9698ca2d625ffe3cd6a89e7281212111. Product source archive:
`outputs/compact/issue44-native-delivery-03/source`; all five hashes equal the
selected artifacts listed below. Final fresh natural quartet:
`outputs/compact/issue44-native-qualification-01`; actual cold matrix2115:
`issue44-native-plain32-check-15/matrix`; density1920/header54:
`issue44-native-extended-01`; nine native IRQ boundaries per video family:
`issue44-native-extended-02`; actual DOS/BASIC NTSC/PAL quartet:
`issue44-native-disk-check-07`. All pass. Boundary timings are intentionally
perturbed and excluded from cadence metrics. First two old mapper labels now
explicitly observe native interrupt-restoration entry/+1 and fixed-RAM/slot
preservation. Fresh independent review confirms this adaptation and supports
diagnostic publication; no Critical/Important findings.721 host tests and both
exact-source GitHub CI runs pass.

Issue44 stays **In progress**; PR45 stays draft, because selected cadence is
still4.1–8.3% below accepted v30. Human feedback was requested asynchronously
against the concrete published ROM, with no assumption that silence approves
an exception. Keep working autonomously; do not stop at this publication.
Preserve v30, v31 and every previous measured candidate. No merge/Done until
Issue44's own acceptance passes. Sole writer/issue chat/branch remain unchanged.

Latest additive qualification: actual published native ROM passes2115 audio intervals,3499 ordered source writes and2472 physical PSG writes; deliberate event corruption is rejected. See references/compact-delivery/issue-44-native-audio.json. No manual listening or cadence claim. Optional P0 SAT experiment was NOT SELECTED (NTSC-0.10%, PAL+0.42%, bear unchanged); default image remains byte-identical. Continue with larger P0 band-search work.

Earlier inventory: measure a concrete representation improvement against
v31 before another game ROM. Read-only inventory found188 footer tiles can
share exact8-byte windows:600-byte literal pool +752-byte offset directory,
1352 total vs3008 frozen VRAM bytes. This is a **size observation only**. A blue
ice atlas could avoid dynamic playfield uploads but bank-specific VRAM roles
are tighter than total VRAM: legacy fixed capacities56/60/50, current footer
uses117/69/2 free tile pairs, bank2 remains the constraining bank. Do not treat
unused CPU key slots as unused physical tiles. Full blue atlas feasibility and
whole-frame win remain unproved. Plan/source-proof before changing architecture.

---

# Current Issue44 continuation — real native formats built, acceptance pending

This section supersedes the historical progress entries below. Sole writer stays
in this Issue44 chat/branch; do not start a new issue or reset the checkout.
Branch: `codex/enhancement/44-compact-native-formats`; PR45 remains draft,
Issue44 In progress. Continue autonomously; this handoff is not a stopping point.

Actual complete Normal32K cartridge: `outputs/compact/issue44-native-delivery-02/cartridge/FROSTBIT.ROM`,
SHA256 `4ddec8fb72c6e744982864a997688f0de9a9f27e8221dd488083ab7d8f5ba04d`.
It is32768 bytes with no mapper or external game payload. The shared source-built
cold RAM/VRAM were reproduced twice from maintained initializers and qualified
assets, never from emulator snapshots.219 named immutable objects occupy16512
of16886 declared free bytes;374 fragmented bytes remain. Packed payload32156B,
header157B,stage2 269B,68B payload gap. Audited backwards ZX0 requires3B overlap
slack; low decode is shifted3 bytes then relocated before entry.

Native disk files under delivery-02/disk:
- COM32527B: `4d467ba7ef6dd70c48043f9bbd9cdf7c09dc5231d7a38bebf21d46a949585577`.
- Main BASIC BIN21267B: `b90ea83e4a66656aeb846e74e90957b1546a4fe9d1261904777b5f17ad8fb83e`.
- Required VRAM companion FBGFX.BIN11797B: `789af131facff6b60c97a036decd0f39de0885d556f74e12d3d011a6c045a95f`.
- Launcher BAS80B: `8dda3742fd166fcd6448f98e7c344a92646b556f188ab2b99757aba3f0f26cd8`.

ROM same-byte evidence also exists under native-plain32-05. Four actual cold
Normal-ROM source/pixel/physical/IRQ routes pass: regular30.168185NTSC /
28.440668PAL; bear28.015826 /24.045080. These are below accepted v30
32.538961 /30.999139 and29.697792 /25.078850. Cadence recovery is OPEN.
Regular/pal and bear/ntsc: native-plain32-check-11; ntsc and bear/pal:
native-plain32-check-05. The new real-cold2115-scene matrix is running under
native-plain32-check-15; previous warm2115 matrix under native-takeover-15
passes. Never substitute a historical4MiB inner receipt's ROM id for the actual
executed native product: outer native-takeover.json distinguishes them.

Real native DOS1 COM and Disk BASIC loading already passed on an actual Sony
HB-701FD64KiB/TMS9918 profile with Microsoft BIOS/BASIC/DOS system files.
Initial product plain32-03/disk-02 passed both formats in NTSC/PAL. The current
same-byte disk-03 BASIC NTSC check passes under native-disk-check-06; finish the
remaining final same-byte disk matrix before publication. Tests compare full
cold low RAM/high RAM/VRAM before native entry, then subsequent IRQ/rendering.
No physical MSX or owner/audio-listening acceptance is claimed.

Current source: scripts/build_native_delivery.py orchestrates exact native
allocation/link/cold initialization/cartridge/COM/BIN creation and private source
archive. See docs/native-formats.md for addresses, slots, BASIC companion,
reset-only exit, reproducible commands and evidence classes. Full host suite:
721 tests pass (/tmp/fb44-native-suite-current.log); rerun before delivery.

Selected small savings: fast normal70-pattern P0 generator; exact512-case sparse
bear-row clearing; exact1280-row aligned byte increments; only source-proved
obsolete mapper CALLs are elided. Native graphic/palette/IRQ ownership stays
strict. Optional P0-clear prototype at native-link-23/cold-11/plain32-09 passes
512/2115 graphics plus natural routes but has MIXED cadence: regularNTSC30.04964,
PAL28.38117, bearNTSC28.01583/PAL24.16967. Do not select it merely because mean
prepare cycles fell. The earlier X0-empty experiment was rejected by the actual
pixel oracle: expanded accepted playfield shows the player there. It is removed
from the builder. Preserve accepted v30 and all old published bytes.

Next: complete current native matrix/final disk quartet; freeze/archive exact
sources, commit scoped files excluding unrelated build_compact_grid_experiment.py,
request independent whole-branch review, publish useful native diagnostic with
exact hashes/source/human tests and honest cadence limits. Keep44 open until its
own full acceptance passes; continue measured cadence work without another
permission/checkpoint. Publish new bytes only with a new version. No legacy
removal (Issue17), no original-derived inputs/assets staged.

---

## Current continuation: native flat link (Task5, not delivered)

Current qualified internal base: `outputs/compact/issue44-native-enemy-irq-game-02/build`,
SHA `e38fe5ce0917c5dfde1f8c6c6465438cfebae8c4812841fedd82588376b4f239`.
All four natural routes and2115 original scenes pass the independent original
source/RGB/physical owner/IRQ oracles;704 host tests passed before the additional
P0 cache allocator regression. The enemy SGT uploader now protects both VDP
address bytes against the real source IRQ;264 injected latch-reset cases also
pass. See `references/compact-delivery/issue-44-native-graphic-irq.json`.
Native bear Tasks1–4 are complete. Task5 continues to actual flat executable,
Normal32K attempt, standalone COM/BLOAD BIN, full cadence recovery and delivery.
No native product binary or new human release exists yet. Current4MiB internal
regularNTSC29.01336/PAL27.86551, bear27.75642/24.04508: below accepted cadence.

The allocation-only catalog is NOT a closed budget. Complete source IRQ edge
families49/50/51, Retroworks runtime credit and P0 grid translation must all be
linked, even where sampled ROM-read coverage misses them. Share the identical
row evaluator and contact accumulator instead of copying cartridge padding.
C080..C17F is the entire live eight-way P0 cache;C100..C17F must never be reused.

Next-link architecture: build all code/assets from maintained source and exact
finite source domains, never from a captured emulator RAM image. First run a
RAM takeover diagnostic after genuine cold initialization; use the two ASCII16
windows independently to copy linked core and resident payloads into actual
RAM. Source-qualified cold/dead routines can then hold native immutable objects.
Preserve original gameplay, fixed physical roles and independent original
oracles. A native metadata allocation may reuse only explicitly proved unused
ice/fusion key slots, with exact immutable initialization/write protection;
active bear/header/igloo/enemy/P0 keys remain intact. Audit all rare edge states
and interrupt boundaries before making any fit/compatibility claim.

# Issue44 — compact native formats

## Native bear integration, Tasks1–3 complete; Task4 active

Current new internal integration: `outputs/compact/issue44-native-bear-renderer-01/build`,
SHA547069add859bae4a6b231bbe0505f9c6c60a46de932867ad68d4ac0a7dabac8.
All four natural routes and2115 original scenes pass with original source/RGB,
exact native kind10 keys, physical role/PGT/CGT and active-page/IRQ guards.
685 host tests pass. Commits422b3a0(key/painter) and a3b2bc4(integration).
Task2 proves38400 actual native mask/palette cases and460800 host complete-tile
RGB cases. New native body491B at538A, helpers220B at6A50, atlas856B at2:9FF2.
It uses original-glyph semantic keys and canonical per-row solid background
colors; complete sprite admission and original dirty ordering are unchanged.

RegularNTSC31.503273 /PAL30.047090, bearNTSC28.274994 /PAL24.818239.
Mean prepare55190.377 /55836.294 regular,61615.059 /63942.692 bear.
This saves representation storage, NOT a cadence promotion: PAL bear is below
selected parent25.340515. Keep internal while final mapperless link recovers
accepted cadence; do not silently promote it or claim delivered COM/BIN.

Task4 retirement candidate `outputs/compact/issue44-native-bear-retirement-02/build`,
SHAfa7a2e8f2dacb67ff693c9e83e3a396c348cc40d54fe859520c648e38a89b6bb.
Expanded mask/context/records/directory/strip allocations are erased and cold
CPU-read guarded: newly retired16883 allocated foreign bytes (includes padding),
28 resident bridge bytes and130 upper helper bytes. Existing original host
oracles remain separate. Matrix/dense1920/header54/IRQ-NTSC checks running or
finishing; header54 and IRQ-NTSC already pass. Fresh source-bound output root02
supersedes root01 only because checker provenance changed, ROM bytes identical.
All source checker files frozen during active proofs. Pending five natural/
matrix repeats plus PAL IRQ and full host suite before completion.

Next Task5 must build the ACTUAL flat executable/loaders, not stop at this
component. A concrete remaining large representation is P0's standing left-
shore prepared recipe/pattern bundle (~6.5KiB). Native original row generator
already exists as exact fallback. Measure an isolated recipe bypass before
retirement; do not sacrifice accepted cadence. Compact NAME palette trial
also preserves pictures and saves3474 more RAM bytes than the current literal
windows but loses some cadence; final flat link may reconsider with full
measurements. Neither has been selected or integrated yet.

## Active native bitmap-renderer work (continue, do not stop)

Selected integration parent remains `issue44-enemy-resident-game-03/build`,
SHA5ffac6a983c6bb770bf540db33a7fb506f2120fb5c3e7d9c7d47af2e64ea9717.
The subsequent packed-record experiment is qualified but NOT selected:
`issue44-bear-record-cache-game-02/build`, SHA309c1572c47bf92cb85ab43a98fce5f65f70746a21eb3145f3039953545fd8ce.
All96 record miss+hit native cases and all five original whole-game checks pass;
cache publications1/1/10/10/40 are checked against all64 original bytes and
invalidation-before-write.6144 data bytes become3168 packed+940 raw map, with
166-byte decoder,15-byte bridge and66 bytes atDFBE..DFFF formerly unused. DFBE
publishesID+1 so cold zero is invalid; DFBF stays zero. Regular31.50327/30.04709,
bear28.27500/24.81824: PAL bear loses cadence. Receipt/source archive retained
as issue-44-bear-record-cache.json / issue44-bear-record-cache-stage-01/source.
673 host tests pass. This experiment is not a delivered native executable.

Ruling: pursue a native bitmap bear renderer from the same six source pictures,
rather than preserve all expanded raw-ID/strip representations. This is an
implementation decision under the owner's explicit autonomy and freedom to
change architecture, with no new visual/mechanics adaptation. Spec/plan:
docs/superpowers/specs/2026-11-14-native-bear-renderer-design.md and
plans/2026-11-14-native-bear-renderer.md. Ledger/Task1 brief under matching
.superpowers/sdd/2026-11-14-native-bear-renderer/. Existing checkout/branch and
sole-writer ownership remain; no new worktree or approval checkpoint is needed.

Task1 native masks: scripts/native_bear_grid_probe.py, src/native_bear_grid.asm
(direct sprite-row shifting) and src/native_bear_grid_rows.asm(preferred row
atlas). Both pass512 group/phase/coarse combinations independently against
original Atari glyph pixels through mask_tiles, with fixed96-byte4x3 output
C480..C4DF and boundedC500..C50F scratch. IX/IY/SP/IFF and unowned writes guarded.
Direct generator13200 mean/16629 max cycles. Preferred row atlas8852.5 mean /
8864 max, using22 distinct24-bit rows x8 shifts x4 bytes704, six20-byte row ID
streams120, and existing32-byte group aliases. Its code is169 bytes including
the fixture input loads. All470 old native masks are generated exactly. Proofs:
outputs/compact/issue44-native-bear-grid-01 and issue44-native-bear-rows-01.
These are component fixtures, not complete game or cadence measurements.

Next Task2: semantic kind10 keys and canonical native palette representation.
Word=(group<<9)|(phase<<5)|(coarse<<4)|cell; cell=row*4+column0..11.
Fields2..5 remain(backgroundID,clip0,foreground1..15,kind10). Bank0 slots0..7
map rows6/7, bank1 slots0..3 map row8, both pages; reject type10 elsewhere.
Independently derive each mask from ORIGINAL Atari glyphs, never new target row
atlas. For solid-per-row background(PGTFF and equal CGT nibbles), the canonical
native tile is rawmask8 plusCGT8=(FG<<4)|BG. This preserves all RGB pixels even
when mask0/FF or FG==BG, and removes the costly old per-mask merge. Reject
nonuniform/clip1 keys. Native background vectors are only five8-byte patterns;
key/physical-role and original RGB audits remain strict, not exemptions.

Then Task3 integrates a new native tile fallback while retaining complete
sprites/admission, dirty union, wrap(col31->1, skipcol1), both generations and
original source clock/controls/audio. C480..C4DF scratch is safe before HUD
selectors are freshly derived; source IRQ does not touch it. Prefer batch32-byte
PGT+CGT row upload with fixed physical roles and exact key hit checks; original
expanded native mask/record/strip tables may only be retired after readers are
superseded and all original oracles pass. No full-game integration exists yet.
Task4 full dense/header/IRQ checks, then continue actual flat link/loaders and
Issue44 delivery; do not end this task at another component milestone.

## Continuing execution: unified bear and mapper-independent enemy renderer

Current qualified internal base: `outputs/compact/issue44-enemy-resident-game-03/build`,
SHA `5ffac6a983c6bb770bf540db33a7fb506f2120fb5c3e7d9c7d47af2e64ea9717`.
Four successive stages pass all four natural routes plus2115 original scenes,
with source/pixel/physical-owner/IRQ/active-page/clock/retirement gates unchanged.
670 host tests pass again. Receipts and complete source archives:
`references/compact-delivery/issue-44-{bear-unified,enemy-ram,renderer-retirement,enemy-resident}.json`
and `outputs/compact/issue44-<same-label>-stage-01/source`.
Still4MiB ASCII16, NO linked flat game/Normal32K/COM/BIN. Do not stop here.

1. Native bear architecture: for the existing late bear publisher, try its
complete three-sprite monochrome shape with the unchanged full rectangle
admission, then exact native tile fallback. The former hybrid sprite-prefix /
prepared suffix path is source-deleted. All earlier-level ordering remains.
The initial trial moved earlier levels into the late publisher and failed the
matrix dirty-union contract; it is rejected. The corrected trial and subsequent
reclamation pass every original oracle. Sprite clipping/edge fallback and32
SAT entries/four rectangles per scanline remain enforced.994-byte body at2:9C10,
old bulk still2:A1D7; former hybrid dictionary/records8KiB, duplicate directory
1KiB,485 body bytes and15-byte bridge retired/read-guarded:9716 physical bytes.
132:B800..BBFF stays host-only for old independent packet verification; no CPU
read. Full sprite608-byte pool/info remains132:BC00..BE5F. Native fallback still
needs96x64-byte records67..69 and mask/strip dictionaries. The former hybrid
metadata/old source files are ancestry, not active input allocations.

Ruling: keep this as internal native-link work, not a human performance release.
Regular cadence unchanged vs enemy-windows parent; bearNTSC28.274994 vs29.312122
and bearPAL25.340515 vs25.078854. Source, graphics and controls pass; final flat
link still must recover the measured cadence loss before promotion. No accepted
baseline binary changed. No performance parity is inferred from size reduction.

2. Entire enemy SGT code/assets now preloaded into reclaimed upper RAM:
112-byte codeE300..E36F,1214-byte literal directory/poolDB00..DFBD. All132 native
RAM read and132 real VDP upload/readback cases pass. Old scalar NAME staging and
E300/E400 fixed-floe buffers have no current producer: their generic decoder/
loader were already retired, native world dispatch is unconditionalF400, and
old fixed-floe entry585F is guarded. Bootstrap end7CF1 JP55FF uses the former
hybrid bridge to select64:BF00 preload code/data, then restores1. New resident
SGT gates566B..56D8 preserve original public RAM entries and cold paths; hot
calls never read64:A800..B7FF. Natural exact-preload/immutable data+code guards
and unused suffix read/write guards pass. Matrix intentionally uses the old
cold constructor and forbids uninitialized new RAM reads. Remaining unused
suffixes:DFBE..DFFF66 andE370..E4FF400. These are not yet allocated to anything.

3. Superseded scalar render code reclaimed2550 resident bytes. Its typed gate
now accepts igloo kind5 only; retain pt_background, igloo and merge closures.
All old generic mono/literal/union/floe/footer constructors, scalar actor path,
old generic loaders/primitive and the unreachable scalar world tail are guarded.
Source-level dispatch proof checks the actual unconditionalJP F400 and declared
separate enemy/floe rows. Old bank7 code/data residue4519 bytes is retired:
A000..A3CC andAA26..B7FF. Original geometry/raw-floe owner expectations still
come independently from sealedv30. No oracle was relaxed to permit deletion.
These are internal retired constructor APIs; original gameplay is unchanged.

4. Remaining bank7 native renderer source-relinked into reclaimed resident:
qe_bulk/role routines+96-byte roles:5AF6..5C35(320B);
certified hybrid enemy admission/upload/clip585F..5A4B(493B);
right mask/bits/preflight/invalid masks7A13..7B0A(248B).
The complete old native code is first reproduced byte for byte from maintained
sources, incorporating the accepted grid24 anchors/role swaps, expanded border
eligibility and clip reader. Remove only old alignment padding. Four exact
world CALL operands now target relocated functions; other world bytes and all
public SGT entries remain. All bank7:A000..B7FF CPU reads are now forbidden from
cartridge entry; all checks pass. Keep same-valued bank2 labels such as x_resume
separate: symbol ownership, not numeric coincidence, controls relocation.

Latest rates:31.472117/29.987590 regularNTSC/PAL,28.274998/25.340515 bear.
Mean prepare55163.90/55839.33 regular and60961.86/63858.10 bear cycles. Enemy
residency itself changes neither cadence nor these costs; old mapper restore
calls remain until the final flat source link. Existing670 host tests pass.

Current pending work: actual conservative all-state flat object/lifetime map,
finish removal of remaining foreign data/code dependencies, compile the shared
native executable, then genuine Normal32K attempt / DOS1 COM / BASIC BLOAD BIN
loaders and complete integration/release. Continue autonomously. No native
loader or delivery artifact has been created yet.

Concrete next reduction prepared by inspection (NOT implemented): native bear
records6144 bytes contain470 one-to-one(raw_ID,dense_mask) pairs. Can encode
96 records as18 bytes of12 nine-bit dense IDs plus15 metadata bytes (3168),
plus470x2-byte raw-ID/empty-left-predicate map940 =4108 bytes. Reconstruct the
original64-byte record intoDFC0..DFFF; useDFBE as cached recordID andDFBF owned
state, claiming the66-byte currently guarded suffix. This avoids per-cell
decoding and shares one persistent original record across both pages. Unused
cells in3-column records must be reset to zero after decoding; used empty raw0
has an8000 predicate while unused original cells have four zero bytes. Keep
native IX/IY/SP/IFF and raw keys exactly. Need96 native record/miss+hit proofs,
cache publication/immutable-SGT RAM guards, source patch ofai_body record load,
initializer invalidation, and whole-frame timing before integrating. New data
can occupy erased contact prefix67:A800..BAAB, codeBB00; old67..69 record tails
become host-only/read-guarded. This is an idea, not a delivered allocation.

The maintained coverage-only `scripts/compact_flat_probe.py` ran NTSC, bearNTSC
and matrix on the enemy-window parent. It collects phase-aware physical reads
and initial RAM/VRAM with all five existing checker layers. Coverage remains a
lower bound; it never authorizes pruning unseen values. Outputs are under
outputs/compact/issue44-flat-coverage-01/. It has not yet been rerun after the
latest source relocations, and is not a flat-memory feasibility result.

## Continuing execution: literal NAME and enemy planes qualified

Current internal base: `outputs/compact/issue44-enemy-windows-game-02/build`,
SHA `739ad81460f4e3252d5cae5fef1a53bb6d48f4d65a8c11854af8ddc04d1478fa`.
All four natural routes and2115 matrix scenes pass the inherited original
source/picture/physical-owner/IRQ/clock/retirement gates.670 host tests pass.
Still4MiB ASCII16: NO flat game, Normal32K, COM, BIN or human release yet.
Keep executing the approved objective; do not stop at this internal checkpoint.

Literal NAME windows replace5632 expanded row bytes with4080 literal pool bytes
plus352 pointer bytes. Directory160 remains. Lower RAM20F0..20FF and2260..26FF
is reclaimed/poisoned and read/write guarded:1200 bytes.95-byte hot gate returns
an existing30-byte row to the unchanged row copier. Cold matrix constructor is
retained. New bank63 startup-only sources and60-byte loader are exactly checked.
All1280 phase/owner native cases produce the original32-byte reference rows.
Rates31.886999NTSC/30.285089PAL regular,29.312114/25.078848 bear.

Ruling: keep the alternative palette experiment as research, not the base.
It reclaims4674 bytes but costs~2%NTSC/~1.4%PAL versus its footer parent.
The literal pool reclaims less but avoids per-byte translation. The final flat
link still has to meet accepted cadence; no loss is silently accepted.

Correction:255:9400..A47F is the132-pattern ENEMY SGT atlas, not P0. The separate
P0 shore half-window pool remains unchanged. Both enemy paths now use528 bytes
of offsets,686 literal plane bytes and8 zero padding bytes instead4224 atlas
bytes.104-byte banked code plus86-byte bridge preserve public upload/read
entries, clipping, SAT, IX/IY and their original buffer roles. Ordinary uploads
stream four eight-byte planes with the original OUTI/JP pacing, without a RAM
SGT build.132 native read cases and132 real VDP upload/readback cases are exact.
The procedural alternative(110-byte code) was proved but rejected for its
~2960-cycle glyph-generation cost. The literal read proof is1463 cycles; its
upload+readback fixture is2821 cycles, not a whole-frame cost.

The old4224-byte atlas stays physically present for the independent original-
glyph/edge host oracle, but all CPU reads from it are forbidden from cartridge
entry. Runtime-only source closure may exclude it. The historical mode0 edge-projection script fails identically at(group0,
reflectionFalse,X1) on BOTH acceptedv30 and the new candidate: its former
X<8 clipping assumption predates the accepted open-view adaptation. It is not
claimed as a current passing proof. All132 source atlas bytes and both runtime
paths are independently exact; the maintained viewport and full-scene oracles
pass unchanged. No oracle was patched to hide the legacy mismatch.
Regular cadence31.503270NTSC/30.047092PAL, bear29.312122/25.078854: the extra
lookup/bridge costs another~1.2%NTSC/~0.8%PAL versus literal NAME parent.
This is internal size research, not a promoted performance-equivalent build.
Final native linking must remove mapper overhead/recover cadence before release.

Receipts: references/compact-delivery/issue-44-grid-window.json and
issue-44-enemy-windows.json. Complete source archives under outputs/compact/
issue44-grid-window-stage-01/source and issue44-enemy-windows-stage-01/source.

Next: finish a conservative all-state flat object/lifetime map, then link and
qualify the actual no-mapper executable and loaders. Reclaim only structurally
superseded code. Candidate obsolete512 resident bytes585F..5A5E need a finite
no-fusion proof: native enemy and floe tile rows are disjoint; all66 groups,
160X and4copy modes must be enumerated from the sealed occupancy descriptors.
Typed igloo constructor/background/merge remain live; do not erase all typed
code. Trace coverage is only a lower bound. Current resident free range is now
56C1..578F(207 bytes), plus778A..78FF(374). Main delivery remains open.

## Continuing execution: immutable footer VRAM allocation qualified

Latest internal build `outputs/compact/issue44-footer-vram-game-01/build`, SHA
`06fc8f61ca30c44b5abce683e9ffff5994604e5b5030e258b533e60ef4c581df`.
Four natural routes +2115 scenes pass with ALL prior source/picture/owner/IRQ/
retirement gates. New footer checker proves an exact188-tile cold VDP upload,
no post-preload CPU reads of13:8000..8BBF, immutable bytes in4401/3978/972/858
natural snapshots and4231 matrix snapshots, and zero references from BOTH NAME
pages to stored tiles. Native188-case store/read proof is exact2706cycles with
ABI/write guards; no dummy VDP read is needed (also matches audited Seaquest
plain loader). No physical-hardware evidence is claimed.

Allocation excludes both fixed generations(counts56/60/50), every background
ID(counts27/5/6), ice atlas1/2, both44 footer slots and14 bank2 Retroworks IDs.
216 free PGT/CGT pairs exist; first188 hold3008 original footer bytes.188x2=376
address bytes in62:B900; source/read/store code62:B800;93-byte resident bridge
at560E. cache_init now jumps to an init wrapper that calls the original fast
init then clearsC7E3. First footer miss uploads from original13:8000 through
existingC520 scratch; C7E4 indexes loading. FlagA5 publishes only after all188
pairs. Later misses read16 bytes toC520; existing footer writer/key publisher
is retained and62 always restores13. No new VRAM capacity or graph changes.

Cadence unchanged:32.215212/30.285086 regular,29.312114/25.078857 bear. Mean
preparation increases~31/114 regular and~215/277 bear cycles vs literal-window
parent, with no interval lost. The current ASCII16 image still has its footer
ROM source; the important native-link lifetime result is that3008 bytes can be
startup-only VRAM assets, avoiding that decompressed RAM allocation. Receipt:
references/compact-delivery/issue-44-footer-vram.json; archived source at
outputs/compact/issue44-footer-vram-stage-01/source.

Next: reduce the5632-byte expanded NAME matrix without a costly generic tile
constructor. Use22 normalized32-byte rows (704B),160-byte phase directory and
8 owner palettes (9 significant bytes each), plus a straight-line lookup copier.
Proposed lower RAM: directory1000, palette pages1100..1800(first9 bytes only),
normalized rows1900..1BBF, code1C00..1CFF; all other old expanded-grid bytes can
be reclaimed. Expected physical contiguous free1D00..26FF plus palette-page
holes, not a size success. White immutable ice atlas stays direct and cold
matrix keeps the existing ROM constructor. Require all1280 rows native proof,
new exact boot/immutable/read guards in all four routes, and full-frame cost
measurement. Then finish the actual flat layout and native loaders; keep going.

## Continuing execution: full occupancy dictionary and literal windows qualified

Latest fully checked internal build `outputs/compact/issue44-literal-windows-game-01/build`,
SHA `11e307b8e550f904fffaa5f8379db10476d6e7de928ca7dd566e9fee501ea110`.
Three consecutive stages (bear-fast, occupancy, literal-windows) pass all four
natural routes plus2115 scenes.667 host tests pass. Receipt and source archive:
references/compact-delivery/issue-44-literal-windows.json and
outputs/compact/issue44-literal-windows-stage-01/source.

Fast native bear contexts preserve all4230 outputs, reduce padded context data
288->144B and component mean2728->1531cycles. Native natural routes predominantly
use bulk/sprite paths, so their cadence is unchanged; do not claim a measured
whole-frame gain from this component reduction. Its188-byte runtime keepsA800.

All8448 occupancy descriptors now use528-byte(group,Y) directory plus52x16=832
phase bytes. No grid-only restriction: native8448-case proof and full gameplay
checks pass.61:B800 code,61:B900 directory/rows; EB61 RAM helper retains the same
consumer/flag logic and maps7 on return. Old142..145 tails and146:B800..B8FF
only are erased/guarded. The rest of146, including live header/player data,
remains intact. The short new RAM stub currently executes NOP padding before
its original consumer; final source link can remove that padding. No cadence
interval lost relative to its parent.

Deterministic maximum-overlap path packing retains literal byte windows; it
is an offline representation, not per-frame decompression.470 bear masks now
use940-byte offset directory at56:A900 plus1415-byte pool at56:ACAC (2355 total
vs3760). Both the193-byte tile reader and254-byte resident strip reader are
natively proved:4230 tiles,210 strips; +22cycles/tile and~88mean/strip.232 P0
halves now share2342 bytes instead3712; existing956-byte offset directory and
runtime instructions remain unchanged (all239 outputs, exactly960cycles).

The obsolete6400-byte root/base shadow at255:A700..BFFF and old1360-byte generic
header at12:B880..BDCF are erased with cold-to-end read guards. Four routes and
matrix record zero reads and unchanged source/pixels/owners/clock. Raw-floe,
geometry and header expectations remain independently derived from the sealed
control/original; no oracle was weakened. Current native font remains at lower
RAM2A00 and bank52 cold storage. Existing SGT source255:9400..A3FF is preserved.

Next concrete architecture step: use genuinely unallocated SCREEN2 tile slots
as startup-only immutable footer storage, freeing3008 runtime RAM bytes for the
flat link. Reservation proof must include both generations' fixed counts,
all static background IDs, ice atlas, both footer generations and Retroworks.
Store original16-byte footer tiles across unused PGT/CGT pairs, read misses into
existingC520 scratch, preserve runtime caches/graphics. Source data remains a
cold asset and the loader will upload it before reclaiming startup RAM. Need
native all188 store/read proof, immutable-VRAM and no-visible-NAME-alias guards,
then full routes/cadence; no prototype exists yet. This remains within16KiB VRAM.
Do not claim32K/COM/BIN until actual all-state flat layout and loaders pass.

## Continuing execution: both foreign bear bodies now share the core bank

Latest qualified internal build `outputs/compact/issue44-bear-core-game-01/build`,
SHA `8b77e72429fa094490d8cac0a441207a5d0de30feead7a4b0057aab9947b598f`.
Both core-loop and bear-core stages pass four natural routes and2115 scenes
with the full inherited source/pixel/physical-owner/clock/retirement gates.
The independent original6502/Z80 write-loop proof passes135168 cases, including
all65536 guard-index pairs. Nine padded256-byte source effect columns became
seventeen16-byte rows (272B), freeing2032B at2:9C10..A3FF. Original slow guard
path and public native entry remain intact. No frame interval lost: rates
32.215207/30.285086 regular,29.312118/25.078854 bear before the relink.

Hybrid bear body1479B now occupies2:9C10; native bulk420B immediately follows;
133 bytes remain. The80-entry cropped-mask registry240B is host verification
input, never read by runtime: moved to60:A800 under the CPU read guard. The
independent source/ROM registry comparison still runs unchanged. Original
hybrid admission, palette, SAT/SGT and physical key paths remain; bulk helper
addresses in RAM remain unchanged and now select2. The inplace old bulk strip
patch is source-relinked without dead FF/jump padding, retaining5033 and the
same strip/owner publisher. Old112/114 full tails are erased/read-guarded.
Source archival + receipt: issue44-bear-core-stage-01/source and
references/compact-delivery/issue-44-core-bank.json.660 host tests pass.

Active next component: `issue44-bear-fast-native-01` proves all4230 mask/context
tiles with specialized original-context painting. Exact outputs and ABI pass;
mean1531/max2181 cycles vs prior2728/max3648, code189B plus wrapper,144B bases
instead288B contexts. Not integrated yet. This supplies timing margin for a
smaller procedural mask representation and the eventual flat link. Main task
remains unfinished: still ASCII16, no32K/COM/BIN. Keep executing.

## Continuing execution: header RAM and hybrid plane dictionary qualified

Latest internal artifact `outputs/compact/issue44-hybrid-game-02/build`, SHA
`aebc738cffc034374657471d1e6d4540f0befe1dfae64e77eee78f31fc82bda4`.
Both header RAM and hybrid sharing pass four natural routes and2115 scenes,
including all inherited source/pixel/physical-owner/IRQ/retirement guards.
Header font1360B/phases10B/code85B now preload into29A0/2A00/2F60 before IRQ;
four natural routes verify exact immutable bytes and exercise529/481/50/50
hot calls. Matrix intentionally exercises the retained cold ROM constructor.
Header relocation shifts one PAL picture interval: regular30.285085 vs30.404084
before it; NTSC32.215209 and bear29.312120/25.078857. This is not cadence parity
with acceptedv30. Final flat link must recover the remaining losses.

All352 hybrid bear row programs now use5712 dictionary bytes instead15488,
with a152-byte paced streamer and15-byte resident bridge at55FF.
The exact stored arena is5968 bytes including code alignment.59:A000 code,
59:A100 recipes, followed by229 PGT planes and45 CGT planes. Two raw IDs and
shared background/color reconstruct both six-byte physical keys atC520.
All352 native component cases prove exact44 output bytes and bounded ABI.
The whole-game rates remain32.215209/30.285085 regular and29.312118/25.078854
bear. Mean bear preparation increases~107NTSC/~100PAL cycles; no interval lost
relative to the header-RAM parent. Full matrix has zero differing scenes.

Ruling: preserve the current36-byte background rows directly from the bound
parent before reproducing bank114. Its old generated include was stale byfive
accepted open-view bytes. Full2048-byte bank114 then reproduces exactly before
rewriting; no graphics adaptation is introduced. Final source archive includes
all bound implementation files under issue44-hybrid-stage-01/source.
Receipt: references/compact-delivery/issue-44-header-hybrid.json.

Remaining main work is actual all-state flat code/data/RAM linking and native
loaders/size qualification, not another human ROM checkpoint. Current internal
image is still4MiB ASCII16 and must not be described as32KiB or native COM/BIN.
Continue execution through the delivery objective without ending at this stage.

## Continuing execution: two resident relinks qualified

Latest fully checked stage `outputs/compact/issue44-bear-resident-game-01/build`,
ROM `01dc10ba242ea8deddcdadbffbe512a9d3c8a8b49d781267d22c58802b3aeb89`.
All four routes and2115 scenes pass both NAME-decoder reclamation and native bear
residency. Receipts: `issue-44-resident-dirty.json` and
`issue-44-bear-resident.json` under references/compact-delivery/.

12704 bank1 expansion/reverse/clip bytes and1272 resident contact-pointer bytes
were removed with cold read guards. The first attempt wrongly included literal
original pageB000..B3FF, which contains live HUD color selectors atB3F9; the
corrected stage preserves the entire original1KiB page plus colors/backgrounds.
Resident dirty traversal898B now occupies7408..7789, removing its113/2 mapper
round trip. All31752 floe,79386 hazard and402960 adversarial cached-shore native
query comparisons were rerun againstv30 and pass with exactly unchanged output
hashes/cycle ranges. These remain directed integration coverage, not Cartesian
all-view proof.374 reclaimed resident bytes remain at778A..78FF.

The obsolete NAME decoder538A..578F was then erased/guarded (live NAME uploader
52F0..5389 remains). Native bear body/context code now occupies538A..55FE(629B),
leaving401 bytes through578F. Full1024-index context proof (1015 misses) validates
the nine-case branch selector: max237cycles, no context table. The scalar sparse
prototype was slower(max718) and stays as component history. Native helper
addresses remain unchanged; copy/constructor returns no longer map102, and the
three-sprite fallback calls the resident body. Current112 bulk-strip patch is
preserved byte-for-byte; old102:B800..BFFF is erased and guarded. Rates remain
32.215210/30.404084 regular,29.312116/25.078850 bear. Still ASCII16, no32K/COM/BIN.

Corrected opcode-fetch observer now passes real matrix qualification:
`issue44-compact-active-live-03/matrix`, startup13079/runtime26578 physical bytes.
Combined with the four correctly phased natural probes: startup22606,
runtime38140, total union53471. Tested coverage is a lower bound and includes
copied code/data in the union; it is not a flat live layout or size guarantee.
654 host tests pass. No active long check remains at this checkpoint.

Next concrete RAM-residency opportunity:29A0..2FFF is free after query scratch
2990..2998 and before common code3000. Relocate hot header constructor to29A0,
font1360B to2A00 and phases to2F60, preload after cfi_boot before t_enabled=1.
Keep the existing bank52 cold constructor for matrix/pre-clock rendering.
FD00 lookup has28 padding bytes, enough for a t_enabled hot/cold gate. Current
cfi_boot ends at7CE9; its7CDF..7CE9 restore/vector tail can grow by8 bytes before
7D29's live exceptional-enemy gate.52:BE70..C000 is unused after header phases;
store relocated code and a cold copying helper there. Require exact boot-RAM
comparison and immutable-write guards in all four natural routes. Finish actual
flat linking/loaders; keep executing rather than ending at progress checkpoints.

## Continuing execution: P0 shore sharing qualified, resident reclamation next

Latest qualified internal build `outputs/compact/issue44-shore-pattern-game-01/build`,
ROM `92a9789c691f8d0c1fb3c0992e7cb05145b65da47b2b4e81dc70a62099d776ba`.
All four routes and2115 scenes pass.239 P0 patterns now use4668 bytes instead
7648, with exact32-byte component proof and existing C500 output/emit/cache ABI.
50EE bridge selects58:A800; directory58:A900, halves58:AD00.123..126 old spans
are erased/guarded. Rates remain32.215212/30.404079 regular and29.312112/
25.078843 bear. Receipt/archive: `references/compact-delivery/issue-44-shore-patterns.json`.
No native format/size result has been delivered. Latest host suite654 passes.

Next actual flat-layout step: reclaim old bank1 primitive expansion/glyph/clip
prefix8000..B59F, retaining colors and background/row-map tail, and unused
resident contact-pointer directories7408..78FF (keep7400's current floe-stream
bridge,7300 control map,7900 shape map,7A00 bear map). Native source-clock
queries use direct source modes rather than those old pointer arrays. Require
cold-to-end physical read guards on both ranges and unchanged source/pixels/
timing before using the1272 reclaimed resident bytes for code relocation.
The898-byte bank113 dirty-description module is a concrete first relocation:
reproduce it from presentation_dirty_native.asm/floe-spans.inc before moving
it into reclaimed resident space and removing its mapper-dependent entry.

Observer caveat corrected: matrix drivers set PC=C760 directly, which skips
an execution breakpoint there. The second attempted phase hook still reported
zero active bytes and was rejected. Actual-Tcl regression now disables that
breakpoint and requires a read_mem opcode-fetch watchpoint to mark matrix
activity. Corrected probe runs at `issue44-compact-active-live-03/matrix`, log
`/tmp/frostbite44-compact-active-live03-matrix.log`. Runtime phase on normal
routes remains t_main.frame after cold RAM expansion. Physical union coverage
is always a lower bound; never delete on trace absence alone.

## Continuing execution: shared-mask bulk strips and shore-pattern sharing

Latest fully checked stage `outputs/compact/issue44-bear-strip-game-02/build`, ROM
`9bc6fc071f508a08012da6484a5f5e70645f3373b99d1b72d933eb96db18ab51`.
All four guarded routes and2115 scenes pass. The210 native strips now use1680
recipe bytes plus existing3760 mask bytes, replacing13440 prepared bytes.
White strip0 remains a direct immutable64FF stream; colored strips use a
specialized resident compositor. The first scalar210-case prototype cost up to
15674cycles; specialized variant up to6372, both exact. Native callback6A50
reuses the retired generic geometry body but preserves6A49's forbidden-entry
trap.5033 is the uploader bridge;57:A800 holds recipes,57:AF00 white bytes.
103..108 tails and109:B800..BC80 are erased;110/111 are protected collision
bootstrap data, not unused strip padding. Original output/cache ownership stays.
Receipt/source archive: `references/compact-delivery/issue-44-bear-strips.json`.
Rates32.215210NTSC/30.404079PAL regular,29.312118/25.078843 bear.

Current integration under test: `outputs/compact/issue44-shore-pattern-game-01`,
ROM `92a9789c691f8d0c1fb3c0992e7cb05145b65da47b2b4e81dc70a62099d776ba`.
239 exact32-byte P0 left-shore patterns share232 sixteen-byte halves (3712B)
plus956 directory bytes vs7648 full bytes. All239 native component cases pass,
960cycles each.58:A800 code/data,50EE resident pattern bridge, original sprite
emit/cache path retained; old123..126 payload spans erased. Five whole-game
checks may still be running, logs `/tmp/frostbite44-shore-pattern01-<mode>.log`.
Do not edit bound sources until checks finish. Current nonFF153017 is not ROM size.

Candidate physical observer now separates true cold boot from active natural
play at t_main.frame, after RAM expansion. Four routes observe20-21K active ROM
bytes; those are lower bounds and exclude existing RAM-resident code/data.
Initial matrix variant never entered that loop and mislabeled its33391-byte
set as startup. Three actual-Tcl regression tests reproduce/fix phase selection:
matrix active phase now begins at its directC760 render RPC. Corrected matrix
probe is running under `issue44-compact-active-live-02/matrix`, log
`/tmp/frostbite44-compact-active-live02-matrix.log`. Earlier complete physical
unions remain valid; their matrix phase classification is explicitly superseded.
Next finish shore sharing, bind cold/hot/complete runtime intervals and perform
actual flat relocation/linking; no Normal32K/COM/BIN has been delivered.

## Continuing execution: native bear records packed64

Latest checked internal build `outputs/compact/issue44-bear-records-game-01/build`,
ROM `d231bbaca461afa6f061c845d7985b3df3afe7244daaf5109dd4895daba5b1bc`.
All four guarded routes plus2115 scenes pass.96 records now consume6144 bytes
instead24576:12 four-byte raw-ID/dense-mask cells plus16 attribute/strip bytes.
Masks carry the empty-left predicate; context words are derived at lookup.
AI native RAM/body/bulk module was first reproduced byte-for-byte againstv30,
including its accepted INC A->NOP left-clip adaptation, before coordinated
record address/stride changes. Public RAM helper addresses remain unchanged.
Records occupy67..69 tails;70..78 tails are erased and physically guarded.
Receipt/archive: `references/compact-delivery/issue-44-bear-records.json`.

Rates32.215210NTSC /30.285087PAL regular;29.306439 /25.078850 bear. PAL loses
one more picture interval versus its compact parent; final mapperless linking
must recover the accumulated cadence cost before promotion. Still4MiB ASCII16,
163053 nonFF; host zlib83435/lzma54696 are not target sizes. No native loaders.

Next in progress: reuse the literal bear masks for all210 native64-byte bulk
strips. Old210*64=13440 meaningful strip bytes can become210*8=1680 recipe
bytes sharing the existing4048 mask/context bytes. Strip0 is64FF and has a
constant fast path. Component proof is running under
`outputs/compact/issue44-bear-strip-native-01`, log
`/tmp/frostbite44-bear-strip-native01.log`; four tile recipes must match exact
PGT/CGT and remain inside existing C480/C520 scratch. Integrate only after it
passes, then measure whole-frame performance again. Keep executing toward actual
flat linking/native formats; do not return an intermediate final response.

## Continuing execution: relocated keys and native bear tile composition

Latest fully checked internal build:
`outputs/compact/issue44-bear-tile-game-01/build`, ROM
`2c730c5681a86b913eda6ccb637b31018641e028e1221f8efeb7c74798d5404b`.
Source snapshot and ten guarded route/matrix results:
`references/compact-delivery/issue-44-floe-assets-bear-tiles.json`.
All four rates are identical to the compact floe-stream parent:
32.215213/30.404087 regular,29.306450/25.078850 bear (NTSC/PAL).
Still4MiB ASCII16,181453 nonFF bytes; no Normal32K/COM/BIN or human release.

947 live owner keys (1894 bytes) moved to55:B800; all160 packet owner records
retain exact logical IDs/counts through new far pointers.50,560 obsolete raw
mask/template-key/index/NAME bytes are erased. The logical2049-ID raw-floe
oracle now lives only in exact sealedv30 host validation. Existing constructor
and pixel/owner/IRQ checks are retained; expected floe patterns are explicitly
supplied by that immutable oracle rather than deleted product bytes.

Rejected first attempt erased255:9400..A3FF. That physical region was historically
name_pairs but is now live P0 SGT storage: x_pattern_read atF89B and x_sgt_upload
select255 and read32-byte patterns. All4096 bytes are preserved in corrected
stage02. The builder's historical-name comment needs clarification at final
cleanup; do not treat metadata section names as current liveness authority.

The native bear constructor passes470 masks x9 contexts=4230 exact16-byte
PGT/CGT cases, preserving ABI and bounded scratch.3760 mask bytes plus288 context
bytes replace45760 prepared final-tile bytes. All1116 native record cells retain
original logical IDs and skip flags; their context words now select the compact
mask/context routine.56:A800..C000 holds new data/code;4FE3 is a bridge in the
retired generic-half decoder. Old79..101 tile tails are physically forbidden.
Bulk strips103..111 and hybrid bear134..137 are still live/unchanged.

Next concrete size cut: compact96 native bear records from256 to64 bytes. Each
cell needs only original logicalID plus dense-mask ID/empty-left flag; derive
the9-context code at lookup rather than storing9 words. Keep12 four-byte cells
plus16 metadata/strip bytes per record (6144 total vs24576). Update native
ai_body record addressing, ai_tile stride/context construction and ai_bulk_ids
stride together. First reproduce unchanged native module bytes from its public
source against sealedv30; reject unrelated changes. Then qualify all four
routes/matrix and whole-frame cadence before adoption. Continue toward actual
flat linking/native loaders without ending at this checkpoint.

## Continuing execution: floe dictionary and generic-atlas retirement

Latest internal build `outputs/compact/issue44-retired-templates-game-01/build`,
ROM `c8231b6c9d54d6eae9b4018e1faa34043a4d5331b835634f9e21e87ec26018cf`.
277 bound sources plus ten complete guarded checks are archived/bound by
`references/compact-delivery/issue-44-floe-template-retirement.json`.
All four routes and2115 scenes pass both the floe stream and generic-atlas
retirement stages. No generic geometry, pattern or template-load entry is called;
physical reads from every retired region remain forbidden from cartridge entry.
The host ownership decorator deliberately reads exact sealedv30 geometry,
separately from game data; source/picture/owner/IRQ audits are unchanged.
This establishes the declared finite scenarios, not a complete all-state CFG
proof. Current grid24 actor/ice rows are distinct; native sprite P0, direct enemy
packets and native/hybrid bear paths supersede generic atlas dispatch. Verify
the finite entry invariants before final flat promotion rather than infer them
from trace absence alone. Bank7 A000..B800 is conservatively protected code.

Direct floe streams replace20480 packet bytes with4686 dictionary bytes,
retaining all640 original owner-pointer bytes. The stream uses existing paced
VDP byte writes and interrupt restoration.54:A800..C000 reuses4096 retired
contact bytes plus2048 retired NAME bytes; guards exclude only that declared
replacement and forbid the old contact decoder. Current rates32.215213NTSC /
30.404087PAL regular,29.306450NTSC /25.078850PAL bear. The1-1.5percent regular
cadence cost remains experimental; no final acceptance or human build claimed.

The generic atlas retirement leaves253838 nonFF bytes in a4MiB ASCII16 image;
host zlib125594/lzma78676 are not target ROM sizes. Old banks253/254 still hold
large prepared keys/names; original packet owner keys live in those records.
Next trace under `outputs/compact/issue44-name-pair-origin-01` identifies actual
255:9400..A3FF read origins, separate from passive coverage under
`issue44-retired-templates-live-01/ntsc`. Both may still be running; logs are
`/tmp/frostbite44-name-pair-origins.log` and
`/tmp/frostbite44-retired-templates-live01-ntsc.log`. Root remains the only writer.
Continue through concrete flat layout, native loaders and final qualification;
do not end the owner task at this checkpoint.

## Continuing execution: header, retired graphics, temperature

Current qualified internal stage:
`outputs/compact/issue44-temperature-game-03/build`, ROM
`c380391e09c02e29653866e77f1be38a0ac65fb29e470b1e2b57691e19009274`.
The complete source archive and15 guarded integration results are bound by
`references/compact-delivery/issue-44-header-temperature.json`.651 host tests
pass. Every four-route/source-matrix check retains the original source, picture,
owner, active-page, clock, retired-collision and now retired-graphics guards.

Header fragments are integrated, replacing the5328-byte prepared dictionary.
50,200 superseded graphics bytes were erased with zero CPU reads from boot.
Physical template hashes had to be refreshed for banks5/6 which share reclaimed
packet space; the independent raw-floe namespace hash remains unchanged.
The temperature's8192-byte burst table becomes768 plane bytes plus native code;
all256 records match. The first2684-cycle constructor lost0.4/1.2percent NTSC/PAL
cadence and was rejected. The sparse1159-cycle constructor restores NTSC but
regular PAL remains0.38percent below its header-only parent. This is measured
internal progress, not accepted final cadence or a new release.

Current whole-route picture rates:32.538966NTSC/30.880135PAL regular,
29.306450NTSC/25.078850PAL bear. Still4MiB ASCII16; no Normal32K/COM/BIN.
The maintained candidate observer preserves all guards. Across four routes and
matrix for temperature stage02 it observes59,073 physical ROM bytes, including
copies/bootstrap data; coverage is a lower bound, not a complete flat layout.

Work continues without another owner checkpoint. A standalone floe packet
constructor passes all160 phase0 packets using4686 data bytes versus20480 old
packet bytes. Its direct-VDP integration is currently being checked under
`outputs/compact/issue44-floe-stream-game-01/` (five modes; logs
`/tmp/frostbite44-floe-stream01-<mode>.log`). The new stream reuses54:A800..C000,
keeps all640 owner metadata bytes, and retains the original VDP byte spacing.
Its result and whole-frame cadence must be read before adoption. Do not edit
bound sources until those checks finish. No source-only size figure establishes
a mapperless cartridge; continue to concrete flat linking and real native loaders.

## Current execution: all active contacts native, pools erased (2026-11-13)

Keep working autonomously until Issue44's full deliverables are complete. The
owner repeatedly objected to ending turns at progress checkpoints. This is the
same Issue44 chat/branch/root checkout, not a successor issue or a completed task.

Latest internal ROM `68cac83ed4f7c1a91f194b0ffa07656f89cd9e5446aa5c3b6e2a2095d1b24735`,
build `outputs/compact/issue44-retired-pools-game-01/build`. No human-test ROM,
release, mapperless cartridge, COM or BIN has been delivered. The image remains
4MiB ASCII16;473,275 bytes are non-FF and host zlib9 uses228,768 bytes. These
host/storage numbers are not final link or target-decompression results.

Floe HMOVE edges, exceptional ordinary hazards and shore edges now use native
source-clock mask programs plus the already-qualified row evaluator. Old
record/block/tree storage is erased over3,662,389 bytes, preserving all993
inherited noncontact allocations and every live reclaimed tail. All four
regular/bear NTSC/PAL routes and2,115 source scenes pass from cold boot with a
physical read/fetch guard over every retired prefix and a breakpoint forbidding
the old decoder. Zero retired reads and zero decoder calls, including boot.
Every source/owner/IRQ/picture/capture buffer is byte-identical to the immediate
pre-erasure parent; matrix capture/ownership/timing/scenes/bands also identical.
651 host tests pass after these changes. No source freeze or long check remains.

Directed acquisition checks against sealedv30:31,752 full four-floe calls,
79,386 ordinary hazard calls, and402,960 shore queries including same geometry
with changed P0 views to exercise program reuse. These are directed integrated
coverage, separate from the older complete mask/convolution component domains.
New shore compiler passes all153,600 programs(six modes x160PX x160bearX),
584code+290data bytes,18,023..37,297cycles before clipped integration.
Source/checker archives and public receipt:
`outputs/compact/issue44-retired-pools-stage-01/source`(271files),
`references/compact-delivery/issue-44-retired-pools.json`.

Current regular cadence32.7168NTSC/30.8206PAL; bear29.3064NTSC/25.0789PAL.
Source clock remains exact per original source route; no uniform30FPS claim.
The expanded shore common domain is PX9..152 with modulo160 distance; native
query proof covers it. Edge programs reject only geometry proven empty in the
complete native program corpus, and reuse mode/PX/bearX/Y-tag masks. Inputs at
0FA0..0FA3 are initialized FF by bootstrap (invalid mode); the cache is owned
only by the shore query. P0 pose/shift/reflection stay live evaluation inputs.

Rejected internal steps remain immutable: first shore edge bridge lost A to
the mapper (fixed by reading canonical C066); uncached shore edges slowed the
bear and one PAL attempt missed the clock. Current exact rejection/program
reuse fixes the demonstrated route issue. Floe/enemy geometry clips only tags
the row evaluator defines as misses. Default legacy component fixture rebuilds
are byte-identical after making input/scratch/output origins configurable.

Next: factor/remove remaining prepared graphics and retired payloads, establish
the complete flat code/data/RAM/VRAM budget, then build and qualify real
Normal32K/COM/BLOAD BIN entrypoints. Contact pool removal is now proven for the
declared runtime; do not resurrect the giant tables to resolve unrelated
graphics/link work. Cold fallback guards remain in code but are never reached
by the qualified boot/runtime routes. Keep all accepted v30 controls immutable.

## Active continuation: startup grid and common contacts (2026-11-13)

Continue execution toward the full Issue44 DoD; the owner explicitly rejected
ending the task at intermediate progress reports. Same branch/chat/root writer.
Current internal ROM SHA-256:
`c706c0a5d3d98d7713780913b7fea89aad4967beb075ad5903c5773cb2cfbba1`.
Build `outputs/compact/issue44-shore-common-game-01/build`;245 bound sources
are archived under `outputs/compact/issue44-common-integration-stage-01/source`.
Public receipt: `references/compact-delivery/issue-44-common-integration.json`.

New integration replaces prepared grid rows with startup expansion (160-byte
directory plus5,632 immutable RAM bytes), and uses compact native interior floe,
ordinary common-profile and common-X shore collision kernels. The cold/boundary
paths retain their exact original table reader. Native source mechanics and
pixels pass all four regular/bear NTSC/PAL routes, plus2,115 controlled scenes.
Independent directed hot-entry tests pass25,968 enemy and169,800 shore queries
against the sealed v30 tables, with forbidden-write/IX/IY/SP/IFF guards. These
are directed integration coverage, not the full Cartesian product of all views.
The preexisting standalone full kernel proofs remain separate; default kernel
fixture rebuild is byte-identical after making its input origin configurable.
651 host tests pass after these edits. New RAM grid content/immutability checks
also pass all four routes. No source freeze or long check remains active.

Active picture rates: regular32.6898NTSC/30.8206PAL; bear29.3064NTSC/25.0789PAL.
Source clock remains59.92updates/s. PAL and bear still need final cadence
qualification against the accepted baseline. No mapperless ROM, COM/BIN,
human-test release, physical evidence or Issue44 completion is claimed.

Rejected intermediate stages remain local/immutable: per-frame nibble decode
lost8% cadence; unrolled byte decode recovered most of it; the first startup
prototype failed initial-picture and cold-matrix assumptions, both corrected.
The first per-row floe integration preserved gameplay but wasted work copying
parameters four times. Current acquisition prepares shared fields once per tick.

Next: native edge contact query glue/shore event generator and their actual
whole-frame costs, then eliminate the original contact pools. Continue factoring
remaining renderer programs/assets and produce a concrete flat link/RAM budget
before implementing Normal32K/COM/BIN loaders. Do not truncate/rename this4MiB
experimental ROM or present it as a playable compact delivery. Preserve the
owner-approved v30 release and all sealed controls.

## Latest continuation: compact-grid full-route measurement (2026-11-13)

The compact prepared-grid reconstruction is lossless at component level
(1,280/1,280 rows), and its integrated experimental ROM retains exact source
CPU/RAM, committed pixels, physical owners and active-page protection on full
regular NTSC/PAL routes. It is **not acceptable as currently integrated**:

| Route | v0.0.30 | Grid experiment | Difference |
| --- | ---: | ---: | ---: |
| NTSC active pictures/s | 32.5390 | 29.7533 | -8.56% |
| PAL active pictures/s | 30.9991 | 28.5002 | -8.06% |
| NTSC mean prepare cycles | 53,629.7 | 56,431.5 | +2,801.7 |
| PAL mean prepare cycles | 54,297.9 | 57,373.5 | +3,075.6 |

Integrated ROM SHA-256 `8b6c108a39b900252a014c25c96bb9a346ba8698ee1081bf13e7227a6a3f2875`.
Exact route outputs are under `outputs/compact/issue44-grid-internal-03-ntsc/`
and `...-pal/`; the matched v30 NTSC control is under
`outputs/compact/issue44-v30-ntsc-control-01/`. The result demonstrates that
reducing prepared data alone is insufficient; this integration loses cadence
and must be optimized or excluded from any candidate. No source edits or new
public ROM/release were made for this measurement. The standalone row
constructor's 4,114-cycle average is not a whole-frame cost by itself.

The compact header constructor also passes 6,446 standalone native cases,
replacing 5,328 prepared bytes with 1,360 fragment bytes plus ten phase bytes;
it has not been integrated into a gameplay route. Its receipt is under
`outputs/compact/issue44-header-native-01/`.

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/44
Dedicated successor chat: `Frostbite — ISSUE #44`, forked in the Frostbite
project0fd5a899-599e-40d4-988e-46b3d31433dd, workspace
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`.
Branch: `codex/enhancement/44-compact-native-formats`, from the integrated PR43
main commit. Resolve and record that exact merge SHA before implementation.
The dispatch message also carries the verified integration SHA.

## Current continuation checkpoint

Issue44 remains In progress, draft PR45. Root is the only checkout writer;
`inventory_review` is read-only. Accepted v30 is still the rollback baseline.
No compact playable ROM/COM/BIN exists. No source freeze or long check from the
historical entries below remains active.

Maintained hazard host proofs are complete at38c352f:36,241,920ordinary edge
cells and5,376,000shore cells, each across228views. Native context9354be9 passes
102,400cases; ordinary programf1857a3/watchdog9d5f876 passes73,458programs.
Generic accumulation177eeb2 passes1,091,680declared cases,85wrapper bytes plus
the101-byte row operator. See `docs/compact-hazard-edges.md` and source-bound
receipts. Actual query glue/native shore generator remain pending.

Enemy packet constructor06c8b0f passes all8,448native buffer/flag cases versus
sealedv30.184code+33extra shape bytes reuse existing source/expansion/reverse
data instead of21,992packet/directory bytes. Mean5,867/max7,245cycles require
whole-frame testing after integration. See `docs/compact-enemy-packets.md`.
651host tests pass in `/tmp/frostbite44-compact-packet-tests.log`.

The read-only render audit proves prepared NAME rows can normalize from40,960
to490data bytes; header fragments to1,360bytes, temperature extra glyph data0.
Other audited factoring opportunities remain unimplemented. Private evidence:
`issue44-review-budget-01/report.json`, `issue44-review-row-packets-01/result.json`.
Selected current asset arenas alone total124,280bytes. Collision replacement
alone cannot prove32KiB or48KiB fit. Next: constructors/decoders with identity
and ownership preservation, full linked code/data/RAM budget, actual native
formats/loaders, NTSC/PAL density/oracle checks and playable release. Never
present a component fixture as the requested game ROM.

## Historical progress (later checkpoints supersede WIP wording)

Inventory continuation: integrated starting commit
`57d32b526757ac4ce3deb72323c4f163112dfe49`. Issue44 owns this checkout exclusively.
See `docs/compact-native-inventory.md` and its compact receipt for the read-only
storage/coverage measurements and finite collision-factor experiments. All
new raw work is in `outputs/compact/issue44-*`; older controls remain immutable.
No product ROM bytes or upper RAM/VRAM allocation changed. Do not mistake the
completed inventory for completion of this issue's ROM/COM/BIN deliverables.

Qualified standalone component: `scripts/compact_floe.py`, `compact_floe_probe.py` and
`src/compact_floe_kernel.asm` implement a standalone floe kernel, unlinked from
the default game. Host proof checks8,704,000shadow cells,7,888,000interior cells
and54,400cells ×228views. The shadow channel reduces further to a scalar rule
with zero table bytes. Source3370af7 passes1,193,944native cases,
186code+3,147data bytes,141..1,227cycles including CALL/JP. Independent review
verifies the final receipt with no Critical/Important blockers. This is full
qualification of the declared component corpus, not whole-game cadence or new
formats. See `docs/compact-floe-component.md`. Boundary/enemy/shore equivalents,
flat layout/loaders and whole-frame qualification remain pending. An additional
host-only ordinary-enemy experiment identifies seven collision rows versus
eight visual rows; preserve this source timing distinction.

Qualified ordinary-enemy component extends the same host/fixture/assembly files with
`--component enemy`. Its common-profile geometry matches25,740cells ×228views.
Source04a3454 passes6,094,440actual Z80 cases:192code+1,078data bytes including
shared P0glyph pages/offsets. Floe regression passes1,193,944calls with identical
ROM/cycle statistics. Independent review verifies final native receipts without
Critical/Important blockers. See `docs/compact-ordinary-component.md`.
No default-game source is changed. PR45 is draft, issue44 In progress.

Next shore research: `outputs/compact/issue44-bear-common-01` proves exact
geometry across4,267,200shore common-Xcells ×228views, playerX25..151, all
source bear positions/modes/Y.123shared17-row footprints plus a138-byte directory
occupy2,229bytes; source bottom two rows are blank in these aliases. This is
host-only; no shore Z80 implementation yet. Boundary research stays separate:
all9,859stored bit7 masks admit adjacent-byte-equality event atoms, but the
first Y-relative edge model is incomplete and must not replace the old tables.

Shore follow-through: source3d9a173 is now fully qualified for the common-X
domain,1,132,704native cases,137code+2,747data bytes (518shared),81..1,540cycles.
635host tests pass. Independent review verifies all native outputs/files and
frozen sources. Prior floe/enemy fixtures rebuild byte-identically; one-case
smokes are not new complete native reruns. All three components occupy6,451
logical bytes before integration. See `docs/compact-shore-component.md`.

Edge work remains open. `issue44-floe-edge-events-03` represents every edge
column exactly with adjacent-byte event atoms, but `issue44-edge-storage-01`
measures51,159bytes for its first explicit lookup/DAG encoding. Reject that
encoding for the compact runtime. Investigate a bounded source-clock/event
calculation instead. `issue44-edge-counter-01` captures unmodified Stella7.0
counter states across nine player positions and two ice rows. Run its helper
with SDL dummy video/audio also in the parent environment: backend `-help`
otherwise timed out before creating a capture. No default game changed.

Edge follow-through: `issue44-edge-event-model-03` corrects the rejected02 model's
GRP/ENAM one-color-clock delay; all816,000edge cells ×228views match. Sparse04
and analytic01 agree independently. Maintained sourcec79bfb2 qualifies all24,000
native horizontal mask-generator cases,652code+666data bytes,32scratch+32output,
19,352..24,969cycles (about6.98ms worst before convolution).640host tests pass.
Independent review reproduces all masks/assets and verifies final raw/native
hashes. See `docs/compact-floe-edge-masks.md`. This is geometry only; native
view/Y convolution and combined electrical outputs remain pending. Do not
promote without full-frame IRQ/cadence measurement and optimization if necessary.

`issue44-edge-evaluator-domain-01` measures666distinct five-mask row tuples and
2,086distinct39-byte full programs across the24,000horizontal cases. A row
evaluator can be qualified over all tuple/tag/view inputs, separately from the
already-qualified geometry generator. A full-program comparison can follow.
No row evaluator source exists yet at this handoff update. The earlier scope
and source hashes remain immutable; any later source extension needs its own
source-bound receipt.

Row follow-through: source78c1d8a qualifies3,340,656native tuple/tag/view calls,
101code bytes and518shared data bytes,99..419cycles.641host tests pass; the
horizontal-generator24k regression is byte/cycle identical. Independent review
reconstructed all666tuples from captured native masks and verified the final
receipt. See `docs/compact-floe-edge-row.md`.

Accumulation WIP: source322bd13 and `scripts/compact_floe_contact_probe.py`
classify actual captured geometry into2,086distinct39-byte programs. Expected
bit7 bytes come directly from v30. Independent review verifies all24,000class
members preserve source responses across34Y×228views, and reproduces the
16,170,672-byte expected corpus.100k native smoke passes,126wrapper+101row bytes.
Combined geometry calls, shadow merge and game integration remain separate.

Completed former long check: `outputs/compact/issue44-edge-contact-native-full-02`,
source322bd13. Its six sources were frozen until completion: compact_floe.py, compact_floe_edge.py,
compact_floe_contact_probe.py, compact_floe_edge.asm, compact_floe_edge_row.asm,
compact_floe_edge_contact.asm (under scripts/ or src/ as appropriate).
Raw expected count16,170,672calls, actual target48,512,016bytes. See the completion
entry below; the freeze is no longer active.

Full accumulation01 was stopped incomplete because permitted-write callbacks
made the16M run exceed its watchdog estimate. STOPPED.txt documents rejection.
The322bd13 guard watches the exact complement of allowed write regions instead.
Smoke02 is byte-identical to smoke01 across100koutputs AND cycles (38.9→13.1s
host runtime; this is observer speed, not a game gain). Negative CPU writes to
7000/C7D0/C800/F400 all fail in `issue44-edge-write-guard-neg-02`; neg01's0.1s
watchdog fired during BIOS boot and is rejected. These checks remain local.

Long-check completion: full02 now passes all16,170,672native calls. No source
freeze remains active. Receipt sourcec7a08c1 contains the same six sources as
322bd13. Cycles75/3,129.210546mean/6,711P95/6,775max. Independent review verifies
all outputs,14files and6source hashes, class membership and direct-ROM expected
bytes. See `docs/compact-floe-edge-accumulation.md`. Combined caller, shadow
merge, layout and cadence remain pending; C800 fixture buffers overlap current
NAME pages and are not an integration allocation. Logical component total7,996B.

New hazard host research: ordinary analytic03 matches every exceptional-X
cell:33shapes×2reflections×4copy counts×33playerX×160objectX×26Y,36,241,920cells
each with228views. Analytic02 was rejected (2,064columns) because its alignment
missed the X153 right-tail bit;03 corrects that threshold. Shore clock02 passes
all3aliases×2reflections×160playerX×160bearX×35Y =5,376,000cells ×228views.
Both are private host results, not target code proofs.

Untracked next files at this update: `scripts/compact_hazard_edge.py`,
`tests/test_compact_hazard_edge.py` and its plan. Six hand-derived tests pass.
The new ordinary/shore analytic compiler still needs the complete maintained
host proof and source commit, then native context/query qualification. The shore
compiler keeps18rows (including the clearing row), omitting only the final row
whose old/new source glyph bytes are both verified blank. It includes initial
bear fine motion: body=(bx+(bx<15?6:1))%160, clocks=14-(bx%15).

## Authority and ownership

The owner approved v0.0.30 as stable/enjoyable and requested closing42 and this
successor on2026-11-13. Preserve its graphics, colors, mechanics, controls, PSG
and accepted cadence. Scope is a complete <=32 KiB mapperless cartridge attempt,
an actual native MSX-DOS COM and a genuine BASIC BLOAD BIN.64 KiB RAM/16 KiB
VRAM remains the target, with no memory mapper, MegaRAM or turbo requirement.
32 KiB feasibility must be measured; do not promise it before the inventory.

Read `.github/issues/frostbite/0044-compact-native-formats.md`, AGENTS.md,
docs/project-workflow.md and current Obsidian0-/GitHub guidance. The predecessor
only prepares tracking/handoff. Product implementation starts exclusively in
this successor fork. After dispatch, the Issue42 chat stops checkout writes.
The new chat owns all subsequent pending files and must verify a clean tree.

## Exact baseline

- Release v0.0.30-reference-credit-diagnostic,4 MiB ASCII16.
- ROM e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d.
- Runtime9915dab1c4c431a62b68c4886cdf788b1983f774;232 source hashes.
- Canonical local build: `outputs/presentation/credit-reference-at/build-final`.
- Public evidence: `references/reference-credit-result.json` and
  `references/reference-credit-delivery.json`.
- Native/scene/audio checks and619 host tests pass. Four fresh regular/bear
  NTSC/PAL routes retain v29-identical source CPU, NAME ownership, IRQ and
  picture-timing buffers. Regular32.539/30.999FPS; bear29.698/25.079FPS.
- Owner approval is in `docs/handoffs/issue-42-owner-acceptance.md`. It is later
  evidence, not a rewrite of sealed publication-time acceptance flags.

All prior releases and sealed outputs are immutable. Do not regenerate inside
`credit-reference-at*`, `credit-as*`, AR/AQ or predecessor result directories.
Create fresh issue44 output roots. Original4 KiB ROM and Atari800CAR remain
local in references/roms; these and complete disassemblies/generated assets
must not be staged. Legacy removal remains issue17.

## First work and reference infrastructure

Start with a live-byte inventory: padding, duplicate/prepared tables, reachable
runtime versus diagnostic code, compression and startup versus steady-state
RAM/VRAM costs. The4 MiB format is not fixed by changing mapper metadata.
Preserve the accepted runtime as a measured rollback/control.

Read `docs/baseline-preservation.md` before selected inherited reuse. The live
Seaquest project provides audited Normal/COM precedents, but no Frostbite proof:
`../seaquest/docs/native-delivery.md`, `../seaquest/docs/handoffs/issue-35.md`,
`../seaquest/scripts/play.py` and `../seaquest/scripts/run_com.tcl` exist locally.
Audit current source before adapting. C-BIOS cannot substitute for a real
DOS boot test; use actual BIOS/DOS configurations for COM/BIN validation.

Report a concrete compact architecture from measured bytes, then implement
in this chat. Never truncate/rename the existing ROM or trade accepted graphics,
mechanics or cadence for a size claim. Keep39's remaining cadence goal and15/16
timing/full-game/physical acceptance separate. Every useful new testable ROM
gets a versioned prerelease with exact ROM/hash/source and human loading tests;
attach native COM/BIN candidates and their own provenance when available.
