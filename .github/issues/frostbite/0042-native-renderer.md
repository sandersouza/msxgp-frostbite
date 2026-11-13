## Current delivery — v30 owner-reference lettering

Owner rejected v29's joined uppercase font and supplied a lowercase reference.
The replacement uses its4x7 glyphs with five-pixel pitch, no year or hyphen,
right edgeX247 and the existing Activision baseline/coarse shift. Only98 bytes
inside two existing PGT tables change. All executable, color and NAME bytes,
memory allocations, mechanics, input and PSG remain v29-identical.

Runtime9915dab1c4c431a62b68c4886cdf788b1983f774; ROM SHA-256
e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d.
232 bound sources retain229 parents.619host/2115source/2115dense/54header/
2115audio and four full routes pass. Source CPU, ownership, IRQ and picture
timing buffers are byte-identical to v29 across all four routes, proving no
whole-frame cost/cadence change. Independent PNG/literal-table/128nativecommit
checks pass; unchanged v29 runtime IRQ proofs are explicitly reused.
See docs/handoffs/issue-42-v30-delivery.md, references/reference-credit-result.json
and reference-credit-delivery.json. Owner visual acceptance and all-level30FPS
remain open; PR43 draft/stacked on41, no merge/close. Earlier sections are history.

## Previous delivery — v29 aligned credit

Owner-requested RETROWORKS now ends at X247 with an angular uppercase wordmark,
matching Activision's seven-pixel height/baseline, including the coarse footer
shift. The owner subsequently removed the hyphen. Original graphics outside
the credit, mechanics, controls, audio and v28 edge fixes are preserved.

Runtime5ac94c5fb282596a20cb5a5dc8bd93064e9fdb22; ROM SHA-256
94e4ee71f2ef4021e9ec16c960fa258cae6d27d660c11f3005dde0d51d0473d3.
229 source files retain225 v28 parents. Fourteen prepared tiles occupy80
additional existing VRAM bytes; the displayed phase uses one reserved RAM byte.
Changes publish only during VBlank; unchanged phases avoid mapper swaps.
Source/full-picture checks and independent native/IRQ review pass. See
docs/handoffs/issue-42-v29-delivery.md and the v29 release tests. Publication
verification is recorded in references/aligned-credit-delivery.json.
Stable/all-level30FPS and owner/physical acceptance remain open. PR43 stays
draft/stacked on41, no merge or close. Earlier sections are delivery history.

## Previous delivery — v28 viewport edge corrections

Owner feedback after v27 reproduced two visual defects: old P0 left clipping
and native enemy glyph overflow from the right to the left. Final source ece9a5a
binds225 files; ROMe85b8bc13ebd07888b91d66fc76677ca3e7d210182d40c242cdd6c1a5c2dafd8.
P0 clips exactly at X16; enemy glyphs do not wrap, while separate copies keep
their original coordinates. Prepared shore and private partial cache keys keep
the edge fast. Source mechanics, clock, controls, colors and PSG are unchanged.

Regular cadence changes about-0.2%; bear cadence stays29.70NTSC/25.08PAL.
Grounded/endpoint snapshots are unchanged, one NTSC Y run is missed versusv27.
The fallback-only prototype was rejected for75k-cycle dragged-left preparation.
619host/2115source/2115density/2272terminal/54header/2115audio pass, as do four
natural/passive routes, independent native/cache/IRQ/negative proofs and two
exact-source CI checks. The43-tab book preserves42 historical tabs/798479 cells.
All73 prior roots are unchanged. The v28 prerelease is published; all six fresh
downloads match the tested ROM/workbook, API digests and exact runtime tag.
The v27 rollback assets and notes are unchanged. WebMSX/postpublication and
tracking receipt: references/viewport-edges-delivery.json.
Stable/all-level30FPS and human/physical acceptance stay open. PR43 remains
unmerged/draft/stacked on41. Earlier sections below are historical delivery.
See docs/handoffs/issue-42-v28-delivery.md and references/viewport-edges-result.json.

## Current delivery — v27 open playfield and sinking colors

The owner explicitly resumed after v26. Same Issue42 writer/checkout/branch;
no new issue, merge or closure. Source e42b737 binds220 files. ROM SHA256:
`78090dde8429a5bc6097e02cfaf278539e05ff68b9582d65e16d430d04334c8a`.
The left stripe is removed, the visible edge is X16 and the footer adds
`Activision - Retroworks`. Sinking retains normal hat/skin/body colors and the
original water fade. Original mechanics, input, clock and PSG remain exact.

Whole regular cadence improves2.61% NTSC/1.95% PAL; foreground mean falls
2.32%/2.45%. NTSC grounded landings improve22→24/26 without losing a previous
landing or endpoint. Bear mean falls1.16%, but NTSC cadence29.83→29.70 has one
extra long interval. PAL bear cadence is unchanged. Stable/all-level30FPS and
owner/mobile/listening/physical acceptance remain open.

615 host tests,2115 source scenes,2088 density scenes,54 header scenes,2115
audio intervals, four natural/passive routes,1811 independent native calls and
9 new hardware IRQ boundaries pass. Negative controls pass. The42-tab workbook
preserves41 historical tabs/796499 cells/18 native parts. Clean rebuild and two
exact-source CI checks pass. All67 prior evidence roots/19390 files are intact.
All six release assets were freshly downloaded and independently verified.
The v26 rollback remains unchanged. Actual desktop WebMSX loads the exact ROM
and game picture; launch-only, no listening test, browser closed. Project7 is In review.
PR43 remains draft/stacked on41. See docs/handoffs/issue-42-v27-delivery.md and
references/open-playfield-result.json. Earlier sections below are history.

## Historical stop after v26 — superseded by owner resume

The owner requested stopping after the delivered v0.0.26 round on2026-11-12.
Implementation/experiments are paused pending resume. Issue remains open and
Project7 is In review; PR43 remains draft/stacked on41. Preserve local AP WIP.
Next requested additions: remove the left black stripe/enlarge the visible
playfield and add `Activision - Retroworks`; these are NOT implemented in v26.
The full-height-stripe proposal was rejected. See
docs/handoffs/issue-42-owner-stop-after-v26.md for pending-file ownership/evidence.

## Published v26 — native bands and left-edge closure

Source `eaa441806da4bb8fa4bfff2b0a6e73b3976286fe`,214 source files; exact ROM
`7765bb9e1485a237c49abe0a95c621bea918b61989aae1fc4ad97b1d8b031c84`.
Packed player bands, exact three-sprite bear, four-stream temperature update and
private warm NAME prefix preserve original mechanics/controls/palette/PSG.
The owner-requested lower-left background closure retains player foreground.

Bear NTSC28.12→29.83FPS (+6.08%); full foreground mean70670→62257cycles.
Grounded snapshots20→22/26 NTSC and14→17/26 PAL; no previous landing/endpoint
lost.612host/2115source/2040density/54header/2115audio,66IRQs, negative controls,
four clean passive/natural routes, independent native review and exact CI pass.
Workbook41tabs preserves all40 historical tabs. All six published assets were
downloaded and matched their hashes/API digests; tag resolves to runtimeeaa4418.
Unchanged v25 rollback verified. Desktop WebMSX loads the exact ROM/ASCII16/60Hz
and displays the game; this is launch-only evidence. Browser session closed.
[Release and human tests](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.26-native-bands-diagnostic).
See docs/handoffs/issue-42-v26-delivery.md and native-bands diagnostics.
Stable/all-level30FPS and owner/physical acceptance remain open; no issue close.

## Local continuation — lower left edge closure

Owner report confirmed: the black sea-edge column stopped at Y175 while water
continued below. The internal closure extends the existing black tile through
row22/Y183, with no extra sprites or memory. Source mechanics and player
foreground priority remain exact. This is part of the current AO candidate;
no new human-test ROM/release has been delivered yet.

Closure02: ROM `4b22951ec3a957f797605c9688e04debb393c77e4191d21adf2ff641d555f9c3`,
205 sources; patch only58 resident bytes. 610 host tests,256 matrix scenes and
four full regular/bear NTSC/PAL routes pass. All3497 committed pictures close the
edge on both pages; cadence is unchanged. Independent review passes67,932 native
calls and exact rebuild. See docs/handoffs/issue-42-left-edge-closure.md.
The ongoing temperature-burst optimization and release qualification remain open.

<!-- AO exact player rectangles / three-sprite bear continuation — 2026-11-12 -->
Continuing autonomously on sameIssue42/rootwriter, Inprogress; no newissue/chat/
worktree. v25 publicbf5c...8dae41/runtime13bf remains latest;61priorroots sealed.
Offline72normalP0recipes preserveRGB with3sprites/max2perline, pool70vs137. Fullbear
fits3sprites exactly (currentleftpair+thinright) inexisting132tail; SGT58/59free.
Designreview4626a1e7...30557239 includes5256sourceY/grid/logo and391680cacheguard
cases;23BdeadcodegapHALTpoison2115GREEN. Phase1internalf283...43ef5c/195dirtysource
closure gives32.0966regularNTSC and28.2605bearNTSC vs31.5939/28.1214v25,256matrix/
601host/source/RGB/owners/activeGREEN. PAL/nativecache review pending. No newhuman
ROM/release yet. Source191parents unchanged;4newatoms archived/hash-bound. Next
fullbearweightedS4/threeSGT withuniformsignedcacheABI, not playerrecolor orsource
speedshortcut. Allsource/graphics/owner guards staystrict. Stable/all-level30OPEN.
See docs/superpowers/specs/2026-11-12-player-bands-design.md and matchingplan.

<!-- AN exact hybrid bear — 2026-11-12 -->
v25 diagnostic: exact left16px sprite/right tile bear, no P0 recolor or new visual
compromise. NTSCbear27.0953→28.1214FPS(+3.79%), fullFG74126→70670, max97481→93939.
PALbear24.6899 unchanged; regularNTSC31.5939 unchanged/PAL29.7739→29.6550(-.40%).
All26landing/endflags unchanged: NTSC20/23,PAL14/23; Yruns254/235of286. Worstbear
gaps50.10msNTSC/59.81msPAL, regularFG+102/209cycles; stable/all-level30FPS OPEN.
Source13bf76ed540b968a6a6746385a396f6e4feeba71; ROM
bf5c703d1e607a47bec037a1e5bac0ce32d34539f14e051f69134470d78dae41.
191boundclean/186parents/56sealedroots unchanged;105retiredRAMcodebytes,
1777/1792kerneloccupation unchanged, no newRAM/VRAM. SATappendafterWORLD,
strictS4/capacity/viewport gates, fullnativefallback,8dirtyhistory safety.
598host/2115source/2040density/54header/2115audio/18generic+18hybridIRQ/AF2negative/
2exactCI/fourcleanpassive5bufferparity GREEN. Independent11714actualZ80calls,
5436RGB (768isolatedABIcases, explicitly separate),all96records/352programs,
80masks/8checkernegatives. Review7e12e1b673be8b4a829faca35bdaaa3dba50b3c4e4d527ae8b47abbb6dd1ebe0.
AN40tabbook preserves39historicaltabs, raw/XML/formula/renderchecks; no nativeExcel.
See docs/bear-hybrid-diagnostic.md, references/bear-hybrid-result.json, v25release
with exactROM/workbook/SHA/source and directWebMSX/humantests. Owner/mobile/
listening/physical acceptance pending. SameIssue42/rootwriter/branch, Inreview
for delivery, draftPR43stacked41; no merge/close. NextremainingP0/preflight/NAME
longframes, fullroutes before promotion. v24rollback unchanged.

<!-- AM rejected prepacked bear metadata — 2026-11-12 -->
AM prototype rejected: foreground saves435NTSC/443PALcycles, but all4routecadences
andall26landing/endflags unchanged. Exactv24publicROM4686...55c5be/runtime48be
remainsbase; no newtestableversion/release. Privatecee4...0dfdf190dirtyclosure,
4experimental sourcesarchived/hash-boundandremoved;186v24sources/52sealedroots
unchanged. Initial132143allocationpoisonfails30sourceframes dueLIVEenemyoccupancy;
correctedcompact192B132141poison2115GREEN.149P0/150partialcontact/151+treeprotected.
597hostatcheckpoint/2115source/2115audio/fourpassive5bufferparity/independent15648
actualcalls exact426outputs+registers+PGTCGT+72keys+NAME+oldpointer/SP/mapperpass.
No prototype IRQ/density/header/CI/browser/owner/physicalacceptance or30FPSclaim.
AMbook39preserves38tabs/790559cells/nativefeatures,zeroerrors/2mutations/5views.
Independentreviewa921bffc6028131afdc12a079d9832b1a6277155b74aebdecdc0ab91f3ca6dbe.
See docs/bear-rows-experiment.md and references/bear-rows-result.json.
SameIssue42/rootwriter/branch, Inprogress; draftPR43stacked41. Nextread-only
hybridbearstripfeasibility, no newvisualcompromise; stable30/alllevels stillopen.

<!-- AL prepared temperature / autonomous continuation, 2026-11-12 -->
v24 exact temperature-unit programs preserve v23 artwork/pastels/source CPU/RAM,
mechanics/controls/PSG. Regular31.5939NTSC (+0.76%)/29.7739PAL (+0.60%);
bear27.0953NTSC unchanged/24.6899PAL (+1.62%). BearNTSC foregroundmax104256→97481,
headermax18996→12221. Stable/all-level29.97/30FPS remains open; guard630 unchanged.
NTSC landing/end flags unchanged20/23of26, Yruns252→254of286. PALarc4 loses actual
landing/end snapshot (15→14/26grounded,24→23/26end); Yruns233→234. PALbearFGP95
86162→88004 andregularNTSCFGmax127789→127909 regress; different sampled pictures.
Source48be6de16c8862580b8add5fd32937d802a7feb3; ROM
4686698ca7c19cf6db27a8393d70a15297fe982b0f9a68274964233f2355c5be.
186bound/182parent sources/47sealedroots unchanged;14reservedkernelbytes,
256x32Bprograms in127..130/body131; fixed69FCgate. LIVEaa_publish60B6protected.
593host/2115source/2040density/54header/2115audio/18generic+14newhardwareIRQ/
negativeAF2/2exactCI/fourcleanpassive5bufferparity pass. Independent76640nativecalls,
2115HALTpoison/49152contactfields; exactv23rollback. ALbook38tabs preserves37/
788579cells/nativefeatures,zeroformulaerrors/2mutationrestore/5renderedregions;
no nativeExcel. See docs/temperature-programs-diagnostic.md, v24release and
references/temperature-programs-*.json. Verified v24 delivery; Inprogress for remaining work;
PR43draftstacked41, sameIssue42chat/rootsolewriter. Keep42/39/15/16open.
Noowner/mobile/manual-listening/physical/all-level acceptance. Nextremaining
bearWORLDrowmetadata/uploads andplayer/preflight longframes towardstable30NTSC.

<!-- AK exact shore-edge P0 / autonomous continuation, 2026-11-12 -->
v23 preserves v22graphics/pastels/mechanics/clock/controls/PSG. Prepared normal
standingY27 shore-edge recipes cover576base+1656rightalias cases; otherstates
retainoriginalpaths. Regular31.3564NTSC/29.5956PAL; bear27.0953/24.2955 (+4.45%/
3.87%). BearNTSCmaxgap66.75→50.10ms; foregroundP95123816→85694 (−30.79%).
All26regularlanding/endflags andYrun counts unchanged. Notstable/all-level30FPS;
regularmaxgaps66.78/79.75ms remain, bearprefix620/122X/all8poses/guard630.
Source295f3308d81bb58273ebde7f1ee8b91d675779b3; ROM
b1a1d10077e778f833cfb4cab233740cf2d705bd5d40c397e5b9c8767f1cadd9.
178parent sources/42sealedroots preserved,182closure;18reservedRAMbytes/310B
retiredbank2body/7retiredROMtails; header116118/igloo119protected. Exactv22rollback.
Rejected02coordinateoverflow fixed16bit; actualinheritedLgovernsP0eligibility/
selectedway, no blanketright-ineligibleclaim.591host/2115source/2040density/
54header/2115audio/18generic+14newIRQ/negative/CI/fourcleanpassive5bufferparitypass.
Independent24294callsperROM, all160X/2pages/3ways/cache/priority/ABI,2115HALTpoison/
57344contact pass. AKbook37preserves36historical786599cells/nativefeatures.
See docs/shore-recipes-diagnostic.md, v23release and references/shore-recipes-*.json.
SameIssue42chat/rootsolewriter/branch; PR43draftstacked41. Verifieddelivery; Inprogressforautonomousremainingworld/header/iglooburstinvestigation.
Noowner/mobile/manual-listening/physical/all-levelacceptance. Keep42/39/15/16open.

<!-- AJ specialized dirty traversal / autonomous continuation, 2026-11-12 -->
v22 preserves v21 graphics/mechanics/source clock/input/PSG while specializing
state comparison/four-lane traversal. Regular31.2970NTSC (+2.83%) /29.4768PAL
(+4.42%); bear25.9404NTSC (+7.53%)/23.3900PAL (+2.27%). RegularNTSCmaxgap
83.44→66.78ms, P9550.07 unchanged. Notstable/all-level30FPS; bearprefix620steps/
122X/all8poses/guard630. Grounded20/26NTSC (−1),15/26PAL (+2); NTSC loses
arc8grounded/end, gainsend6; PALgainsgrounded1/15,end24. Exactsourceclock stays.
Source80b5a435a28f9009812a73aecfddaf679c690b49; ROM
b0a3d2befe9c370bbec9ba9096df63143a5743949b1deeeeea63879fa843c1e2.
174parent sources/37sealedroots unchanged,178closure.16reservedkernelbytes,
no new RAM/VRAM. Exactv21rollback. Initialobsolete-span prototype rejected by
rootdirty/pixelguard andindependentreview, correctedactualparenttablederivation.
589host/2115source/2040density/54header/2115audio/fourcleanroutes/18generic+
12newactualIRQ/negativeAF2/CI pass. Independent98450Z80cases perROM/8192contact.
AJbook36tabs/35historical784619cells/nativefeatures preserved, no nativeExcel.
See docs/dirty-native-diagnostic.md, releasev22 and references/dirty-native-*.json.
SameIssue42chat/rootsolewriter/branch, Inprogress; PR43draftstacked41. No owner/
manual/mobile/physical/all-levelacceptance. Continue measured bear/player/long
framecosts without changingmechanics or desynchronizing pictures. Keep42/39/15/16open.

<!-- AI native bear / autonomous continuation, 2026-11-12 -->
v21 exact prepared bear tiles/certified rows preserve all v20 graphics/mechanics,
clock/input/PSG. Live level4 bear window15.0453→24.1245NTSC (+60.35%),
15.3333→22.8702PAL (+49.15%); whole foreground138852→81308NTSCcycles.
RegularNTSC30.4355 unchanged, PAL28.2288. Not stable/all-level30FPS; regular
maxgap83.44ms remains, grounded21/26NTSC (+1) /13/26PAL (−1), PAL loses
groundedarc15/endpointarc24. Bear prefix620steps/122X/all8poses; guard630.
Source851aa41466d7b9ea86c753a5228337c688d40a88; ROM
635876dcf352bfc2eafee908757045c7387a11653c21f4dce266fd765dd5ad15.
170 parent sources/32 sealed roots unchanged;174 source closure.142bytes
existing reserved kernel padding occupied; no new RAM region/VRAM allocation.
Exactv20 rollback; rejected P0 cache-layout experiments remain private.

586host;2115source/2040density/54header/2115ordered-audio, four clean routes,
18generic+14new realIRQs/negativeAF2, exactsourceCI pass. Independent38144Z80
calls perROM,385024contactfields. AI workbook35tabs preserves34historical/
782639cells/native features; no nativeExcel. See docs/bear-native-diagnostic.md,
v21 release and references/bear-native-*.json; direct WebMSX/human tests included.

Status In progress, same Issue42chat/root sole writer/branch; PR43draftstacked41.
No owner/manual-listening/mobile/physical/all-level acceptance. Continue next
measured dirty-state/source/renderer overhead; no desynchronized player-only
pictures. Keep42/39/15/16open. User away; routine work remains authorized.

<!-- AH immutable ice / autonomous continuation, 2026-11-12 -->
The v20 immutable-white-ice diagnostic reaches30.4355NTSC mean (+5.23%v19),
28.0505PAL (+7.03%) on the regular level0 route. Same v19 artwork/mechanics and
source/input/audio clock. No new visual adaptation. 62immutable pattern/color
slots use1,984previously free bytes in existing16KiBVRAM; originalblue/otherdelta
fallback. All165v19sources/27sealed predecessor roots remain unchanged.
Runtime665cbdf4393fca63fe33299dca35442aa8fabce8;
ROMc036c3d960da3be4331df6afbb168bc5037777d47be9f4892a16ff6f5d4e43ac.

This is not stable30FPS/all-level acceptance. Maxgaps83.44NTSC/79.75PALms remain;
grounded20/26NTSC,14/26PAL but individual losses and endpoint regressions remain.
Level4 bear prefix15.05NTSC/15.33PAL; measured generic bear tiles74,124inclusive
cycles/picture motivate next work. Earlier rejected sprite prototype stays private.

583host;2115source/2040density/54header/2115ordered-audio scenes; fullsourceRAM/
exactpixels/owners/activepage,18generic+10new realIRQ/negativeAF2,cleanreplay/
exactsourceCI pass. Independent170source rebuild,6144actualZ80transitions,
1984atlasbytecorruptions rejected,8192contactfields equal. AH workbook34tabs
preserves33historicaltabs/780419cells/native features; no nativeExcel.
See docs/ice-atlas-diagnostic.md, releasev20 and references/ice-atlas-*.json.

Status **In progress** during autonomous continuation, same Issue42 chat/root
sole writer/branch. PR43draftstacked41; keep42/39/15/16open. No owner v20,
manual listening/mobile/physical/all-level acceptance. Continue largest measured
bear composition/long-gap cost with reversible exact graphics; publish only
qualified measured ROMs with WebMSX and human tests. Exactv19 rollback available.

<!-- AG mask replacement delivery, 2026-11-12 -->
Owner accepted v18 gameplay as stable with very small visual differences and
selected option3, authorizing autonomous work toward29.97/30NTSC. The new
[v19 border diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.19-border-diagnostic)
removes seven mask SAT entries, clips enemies atX24 and substitutes fourteen
inactive NAME cells. Four extra sea-edge pixels are cropped, y64..175 only.
P0/colors/priority/grid24 contacts and source CPU/RAM/mechanics/input/audio remain.
All160v18 files and22prior sealed roots are unchanged. Sourcec863310fae363d561520dfd2138d07dc1948cefc;
ROM26260606e1ecbdeed0a8c0d3ae7ef4eb37658341da3a0ab02cd52ac8a5286ac9.

Active pictures improve27.7427to28.9237NTSC(+4.26%) and25.3762to26.2082PAL(+3.28%).
Foreground means fall3.77%/3.03%; picture populations differ, not paired savings.
NTSC P95 gaps66.72to50.13ms, grounded15to17/26, endpoints23to25/26. PAL grounded
stays13/26, endpoints20to22. Individual landing losses and sampledPAL maximum
foreground150225to162982cycles are disclosed. Long gaps/stable30FPS remain open.

579host tests,2115source/2040density/54header scenes,2115ordered-audio intervals,
4507source CPU/allRAM checkpoints/2658coherent pictures,18generic+4new-helperIRQ
boundaries and negativeAF2 pass. Independent165source rebuild,6336actualZ80
sprite/cache cases,4actualNAME cases and10560finite clipping pass. Finalclean
routes match all5profile buffers per TV; sourceCIpush43253742994/PR43254079515 pass.
AG workbook preserves all32AFtabs/778199cells and native features; formulas/export
and5visual regions checked, no nativeExcel. Release includes directWebMSX and
precise edge/dense/landing tests. See docs/border-diagnostic.md and references/border-result.json.

Status **In progress** during autonomous continuation; border diagnostic is available for human review. Same issue42 chat/branch/root sole writer.
PR43draftstacked41; keep42/39/15/16open. No ownerborder/manual/listening/alllevel/
physical acceptance inferred from v18 feedback. Continue autonomously with
immutable white-ice preparation/VRAM feasibility, preserving colors/mechanics;
no new atlas is included in v19. B rejection-reuse variant has no cadence gain
and remains private. Immediatev18 rollback stays available.

<!-- AF tile-aligned layout diagnostic, 2026-11-12 -->
Owner selected visual option 1 with easy rollback. The new
[v0.0.18 diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.18-grid24-diagnostic)
uses eight tile-aligned sea bands at24pixel pitch. Artwork/colors/counts, black
mask, bear tiles and original CPU/RAM/input/audio mechanics remain. Bailey's
whole sprite group follows a monotone contact translation. This changes the
presentation layout by up to7pixels, not the source collision/jump rules.

Source `fa26b79fece16b8b9bbc293523792aa31d4a40ed`; ROM
`6677bb8ccc9caaf440b24df6a69fe9ecd7d206743645d738623e6cfedc8a219a`.
All154v17 files and17sealed predecessor roots are preserved. Original builder
mode reproduces exactv17SHA c50a3131...9562; old ROM assets remain available.
Runtime changes occupy one additive commit, with no new RAM/VRAM.

Complete active presentation improves25.9009to27.7427NTSC (+7.11%) and
23.1226to25.3762PAL (+9.75%). Whole foreground means fall69,756to62,612 and
74,907to65,685cycles. Stage populations differ; these are observed means, not
paired CPU savings. Long picture gaps barely change. Grounded landings improve
14to15/26NTSC, stay13/26PAL; individual regressions remain documented. Stable
30FPS/original fluidity are not accepted. The moving-bear prefix gains4.08%NTSC
and effectively0%PAL; not all-level proof.

575host tests,2115source/1920density/54header scenes,2115ordered audio intervals,
4507natural CPU/all-RAM checkpoints and2580coherent pictures pass. Eighteen
generic and four new-helper real IRQ boundaries pass; AF2corruption rejected.
Independent three-mode rebuild, finite allocation/contact/NAME checks and539
natural SAT comparisons pass. Clean final routes reproduce all5measured buffers
per mode. Runtime-source push/PR CI pass. AF workbook preserves all31AE sheets
and775,979cells, with formulas/export and five visual regions checked.

See `docs/grid24-diagnostic.md`, `references/grid24-result.json` and the release's
A/B spacing/contact/fluidity tests. Human/layout preference, manual listening,
all-level and physicalMSX1 acceptance remain pending. Status **In review**;
PR43 stays draft/stacked on41. Keep42/39/15/16open. Same issue42 chat/branch is
the sole checkout writer. Next: remaining WORLD cost and long foreground tails,
tracking every landing and the owner's decision on this reversible layout.

<!-- AE bear-sprite experiment, 2026-11-12 -->
Two private variants were measured against v0.0.17. Neither is promoted; no new
release or public ROM change. All 154 v17 source files and 14 prior sealed
control roots remain unchanged. Same issue42 chat/branch is the sole writer.

A always attempts bear sprites and regresses regular active cadence 4.67% NTSC /
4.47% PAL. B gates the path to level>=3, changing regular cadence -0.229% /
effectively 0%. A separate live-clock clean-start bear-chase prefix changes
14.2057 to13.7483 NTSC (-3.22%) and13.7033 to13.7739 PAL (+0.515%). No consistent
whole-game gain supports publication. The regular route has only a stationary
level0 bear. The bear-route active window covers all8poses/122X values at level4;
its620step bound precedes the unchanged one-player guard failure at630, not a
claim over the complete702step source route.

Both prototypes pass their 4507 source CPU/all-RAM checkpoint and2115 scene
oracles, with exact pixels/owners/active-page protection. Six passive profiles
reproduce all5natural buffers. The B controlled matrix reduces paired preparation
21.24% overall /36.22% in653 nonblanked level>=3 rows, but these injected scenes
exclude live IRQ/commit/wait; they are not FPS. Independent reviews confirm both
the savings signal and the mixed live result. New audio/density/directed-IRQ
release qualification was not performed after rejection; no owner/physical or
original-fluidity acceptance is claimed.

The AE workbook preserves all30AD sheets/773129cells and adds the measured
comparison, per-arc landings and live bear window. See
`docs/bear-sprites-experiment.md` and `references/bear-sprites-result.json`.
Visual adaptation analysis proposes tile-aligned band spacing, two-color Bailey
and border clipping as separate hypotheses; none is implemented or authorized
for adoption by this experiment. Status **In review**; PR43 remains draft/stacked
on41. Keep42/39/15/16 open and v0.0.17 as the public control.

<!-- AD igloo color-only delivery, 2026-11-12 -->
Published [v0.0.17](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.17-igloo-colors-diagnostic)
from clean runtime source `059bec5f985f3aac121014016dadfa31ec3fc892`.
ROM SHA-256 `c50a3131df056011af9a037b58624d9de84930b3474579b24d2137d736e9d562`.
The scoped igloo publisher reuses exact tiles or writes only certified color
bytes; shape/cold/uncertified cases retain the full constructor. No new RAM/VRAM.
Parent 151 sources and every earlier sealed control are unchanged.

Against v0.0.16, active complete pictures/s rise 25.4519 to 25.9009 NTSC (+1.76%)
and 22.9176 to 23.1226 PAL (+0.89%). Whole foreground means fall 1.66%/0.66%;
different sampled picture populations are not paired component CPU savings.
PAL P95/maximum gaps improve 79.713/99.683 to 59.843/79.780 ms. NTSC grounded
coverage regresses 15/26 to 14/26 (arc 21/source 1672); first post-landing age
rises 2 to 3 steps there, all-arc P95 rises 5 to 6, endpoint coverage stays 21/26.
PAL grounded/endpoints improve 12/19 to 13/20 out of 26. Cold/full igloo maximum
increases 25,025 to 27,389 cycles. Stable 30 fps/original fluidity remain open.

569 host tests, 4,089 source/density/header scenes, 4,507 CPU/all-RAM checkpoints,
2,510 coherent pictures, 10,560 clipping cases and 2,115 ordered-audio intervals
pass. Eighteen generic IRQ targets plus two AD bank-119 stream IRQ probes pass;
AF2 corruption is rejected. Independent clean 154-source rebuild and constructor
review, exact-source CI and final natural/profile byte parity pass. Six release
assets are downloaded and checksum/tag verified. AD workbook preserves all 29 AB
sheets and 770,654 historical cells. No native Excel or human/physical acceptance.

See `docs/igloo-colors.md`, `references/igloo-colors-result.json`,
`references/igloo-colors-delivery.json` and the release's precise human tests.
Status: **In review**. PR43 remains draft/stacked on41; keep42/39/15/16 open.
Next: WORLD preparation, long foreground tails, cold igloo cost and landing
presentation. Same issue42 chat/branch remains sole checkout owner.

<!-- AC aurora cost audit, 2026-11-11 -->
The owner's color-table proposal was checked against the exact v0.0.16 runtime.
The band already uses preloaded patterns/colors and selects NAME IDs on row 3;
there are zero static-background PGT/CGT writes during active preparation.
Full-route passive NTSC/PAL runs reproduce all five natural buffers exactly.
Aurora row preparation averages 502/546 cycles per active picture, only
0.71%/0.72% of foreground, excluding shared setup and NAME IO. Igloo preparation
averages 3909/4259 cycles per picture; 164/172 NTSC top-row PGT writes leave
identical pattern bytes. This is a promising color-only igloo lead, not a speed
claim or proof that its constructor can be skipped. Shared CGT entries cannot
be recolored during preparation without protecting the active page.
See `docs/aurora-cost-audit.md` and `references/aurora-cost-audit.json`.
No runtime change, candidate ROM or new release from this audit. v0.0.16 remains
the control. Status: **In review**; all original cadence/owner acceptance remains open.

<!-- AB ready-picture delivery from v0.0.15, 2026-11-05 -->
Published [v0.0.16](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.16-ready-presentation-diagnostic)
from clean source `a9cf5ff3ea802b79a0e328e0a9de844e9749f8d3`, ROM SHA-256
`9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b`.
Fresh WORLD profiling and per-arc landing analysis led to current-picture enemy
eligibility reuse and first-safe-VBlank admission of complete coherent scenes.
NTSC active cadence improves 21.46 to 25.45 pictures/s (+18.60%), grounded
landings 9/26 to 15/26, endpoints 20/26 to 21/26, and missed pose runs 2 to zero.
P95/maximum NTSC gaps remain 66.75/83.44 ms. Original clock, mechanics, graphics,
input and ordered audio are preserved in the bounded checks.

**PAL limitation:** throughput improves 20.20 to 22.92, but grounded landings
fall 13/26 to 12/26, endpoints 21/26 to 19/26, and P95 gaps rise 59.91 to79.71ms.
First post-landing ages at source1732/1762 rise3 to7 and2 to6steps. No general
PAL landing improvement, stable30FPS or original fluidity acceptance is claimed.
Whole foreground mean is70,935 versus80,142cycles over different picture
populations; this is not paired CPU savings. Long tails remain the next target.

565 host tests,4089source/density/header scenes,4507CPU/all-RAM checkpoints,
2497coherent pictures,18realIRQ boundaries plus rejectedAF2fault,10560clipping
cases and2115ordered-audio intervals pass. Exact-source CI and independent clean
rebuild verify151sources; final natural runs reproduce all5measurement buffers.
All6published assets were downloaded and byte-verified; tag/source identity is
exact. AB workbook preserves27AA sheets/767714cells. See `docs/ready-presentation.md`,
`references/ready-presentation-result.json` and `references/ready-presentation-delivery.json`.

Status: **In review** for diagnostic owner tests. PR43 remains draft/stacked on41.
Next: WORLD/floe NAME costs, long preparation tails and PAL landing sampling.
The NAME residency idea is only an offline upper bound, not a measured ROM gain.
Keep42/39/15/16open. Root/current issue chat remains sole checkout owner; previous
versions are preserved. No owner-fluidity, all-level or physical acceptance.

<!-- Historical AA floe transaction delivery, 2026-11-05 -->
Published [v0.0.15](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.15-floe-transactions-diagnostic)
from clean source `e5dd710a910272150709f7b806fb3c62403fa009`, ROM SHA-256
`d28c68590a27004d6624af3d1ecb9d80dc422ed3f4f4241caed2df278d1a5db0`.
The owner reports a large improvement in v0.0.14 and authorized the next
playfield optimization. Fresh passive profiling identified floes as the largest
average WORLD cost. Native floe setup/publication and an exact resident color
lookup raise active NTSC/PAL presentation from 20.11/19.07 to 21.46/20.20
pictures/s; complete foreground falls 86,984 to 80,142 cycles (7.87%).

NTSC longest gap falls 100.10 to 83.44 ms; P95 remains four fields. Jump states
shown increase 251/390 to 266/390, but grounded landings regress 14/26 to 9/26.
Endpoint Y improves 19/26 to 20/26. No original simulation state/contact rule is
removed; graphics and mechanics match the bounded oracles. **Original fluidity
and stable 30 FPS remain open.** The NAME-layout experiment was rejected before
ROM construction because its proposed allocation did not fit.

557 host tests, 4,089 source/density/header scenes, 4,507 CPU/all-RAM checkpoints,
1,829 coherent pictures, 18 IRQ boundaries plus negative control, 10,560 clipping
cases and 2,115 ordered-audio intervals pass. Exact-source CI, independent clean
rebuild of all 147 sources, and final NTSC/PAL raw-buffer parity pass. All six
published assets were downloaded and byte-verified; remote tag targets the exact
source. AA workbook preserves all 25 Z tabs / 765,304 cells. See
[the report](https://github.com/sandersouza/msxgp-frostbite/blob/e5dd710a910272150709f7b806fb3c62403fa009/docs/floe-transactions.md),
`references/floe-transactions-result.json` and `references/floe-transactions-delivery.json`.

Status: **In review** for diagnostic owner tests. PR #43 remains draft/stacked
on #41. Continue WORLD preparation and long-gap costs while tracking landings.
No owner-fluidity, all-level or physical acceptance; keep #42/#39/#15/#16 open.
Root/current issue chat remains sole checkout owner. Prior versions are preserved.

<!-- Historical Z delivery checkpoint, 2026-11-05 -->
Published [v0.0.14](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.14-core-cadence-diagnostic)
from source `2c1891635553e07b6fd096a58cc0e34905acd568`; ROM SHA-256
`e59d719e9169a4a73300eb9099008d1a92c77a247b205c78d6961015d16886c5`.
Exact source-core summaries plus direct header/player/static work improve
active NTSC/PAL pictures from 18.22/17.22 to 20.11/19.07 per second.
NTSC gap P95 falls 83.44 to 66.79 ms; jump updates shown rise 229/390 to
251/390. Whole foreground falls 95,808 to 86,984 cycles; complete active ISR
falls 23,689 to 21,933. The original source clock and tested CPU/RAM, graphics,
input and ordered PSG contracts are preserved. **Original fluidity remains open.**

557 host tests, all natural/directed/density/IRQ/audio/clipping gates and both
exact-source CI runs pass. Independent review and clean rebuild reproduce the
measured bytes; final NTSC/PAL reruns reproduce all five measurement buffers.
All six downloaded release assets match the tested package. Workbook Z preserves
all 23 Y tabs. See [the report](https://github.com/sandersouza/msxgp-frostbite/blob/2c1891635553e07b6fd096a58cc0e34905acd568/docs/core-cadence.md),
`references/core-cadence-result.json` and `references/core-cadence-delivery.json`.
Status: **In review** for owner diagnostic tests; PR43 stays draft/stacked on41.
Next: remaining world/preparation cost and long gaps. No owner, all-level or
physical acceptance; keep this issue and39/15/16 open.

<!-- Historical Y investigation after X, superseded by Z delivery above -->
The owner reports noticeable improvement in v0.0.13, but gameplay remains far
from smooth. Motion acceptance remains open. Status: **In progress**; preserve
X as the public control. Follow-up measurements rejected three isolated changes
as standalone delivery: static SAT +1.2%, player selector no cadence gain, direct
header +3.2% with effectively unchanged P95. At that checkpoint no combination
or new release was claimed. Judge the next candidate by complete-picture gaps and visible
jump trajectory coverage, not average FPS alone.

Passive profiles preserve all five natural X buffers. Two NTSC fields leave
about 72,094 cycles outside IRQ service, against 95,808 foreground cycles; the
mean deficit is 23,714. The translated core excluding input/audio is the largest
measured source component at 14,211 cycles per active step. Next work profiles
its executed blocks before proof-backed lowering, alongside native floe work.
Original mechanics, input/audio sampling and coherent snapshots stay required.

<!-- Native lane X delivery checkpoint, 2026-11-05 -->
Published [v0.0.13](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.13-native-lanes-cadence-diagnostic) measures18.2214NTSC/17.2158PAL active pictures/s, compared
with W10.6131/10.5441. Whole foreground falls182,896→95,808cycles; NTSC gapP95
falls133.47→83.44ms. Jump-state coverage rises132/390→229/390, still incomplete.
Original-speed/smooth-motion acceptance remains OPEN. See
[the native lane report](https://github.com/sandersouza/msxgp-frostbite/blob/2318fe1b5b96e528a1864d43ebca093dd60194ba/docs/native-lanes-cadence.md) for exact scope,
reproduction, guards and pending owner tests. Exact-source push/PR CI passed;
all six release assets were downloaded and byte-verified. Source commit:
`2318fe1b5b96e528a1864d43ebca093dd60194ba`. Publication status was In review; performance and
owner acceptance remain open, with no automatic close or successor handoff.

# Replace generic rendering with an MSX1-native residency and band pipeline

GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/42

Implementation child of #39. Owner approved architectural replacement and
resuming GitHub. Original Atari 2600 mechanics remain authoritative; preserve
graphics, colors, actors, viewport, input order and audio event timing. The Atari
400/800 fan port and Seaquest are implementation references, not gameplay specs.

## Movement fluidity rejected by owner — 2026-11-05

The owner reports that the third diagnostic still presents player movement as
a slideshow, despite responsive controls. Status is **In progress**. Original
presentation cadence and owner acceptance remain unmet; another small mean-FPS
improvement is not sufficient evidence of a fix.

The immutable W control presents active pictures at 10.6131 fps NTSC, with
133.47 ms observed-order p95 and 150.19 ms maximum gaps. Of 84 contiguous active
animation-pose runs, 12 are never presented; ten last four source steps. These
pose runs describe animation states, not every individual position.

Current work measures whole-frame tails and source-step/pose coverage while
replacing generic world traversal, player construction and fixed HUD work.
An internal combined prototype reaches 16.2723 fps but still has 100.10 ms p95
gaps and five unpresented four-step pose runs. It is **not** a fluidity solution
or a new human-test release. Investigate those remaining worst cases before
delivery. Mechanics, input/audio order, colors, viewport and coherent snapshots
remain required; asynchronous player-only motion over an older world has not
been adopted. W and every prior sealed artifact remain unchanged.

## Player palette and selective header diagnostic — 2026-11-05

Published [v0.0.12](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.12-player-palette-header-diagnostic).
Source `48f570ea2b4c3894b2a77cb6555c226fe0b11863`; ROM
`98904b6bb592f78964158d154545764eda0e986c9c979196d60e9a7ed03f30b4`.
Normal player uses yellow hat, cream face/legs and gray torso; death colors remain
unchanged. Header updates rebuild only affected columns. Mechanics/input/PSG
remain unchanged in the complete controlled CPU/all-RAM comparison.

Active picture rates10.3356->10.6131 NTSC (+2.69%) and10.2829->10.5441 PAL (+2.54%).
Complete foreground preparation -2.85%; header -15.07%. Long active gaps remain
~133ms p95/~150ms maximum: original-speed presentation and owner cadence
acceptance are still open. Fast input does not establish smooth rendering.

553 host tests,4089 source/density/directed scenes,4507 CPU/all-RAM checkpoints,
1401 coherent pictures,18 directed IRQ boundaries and AF2 negative control pass.
Independent review found no blockers; blank transitions and oracle fingerprint
follow-ups passed. Source48f570e push/PR CI pass. See release notes and
references/header-palette-result.json. In review for diagnostic/human checks;
do not close this issue or parents from these bounded proofs.

## Previous world transaction diagnostic — 2026-11-05

Published [v0.0.11](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.11-world-transactions-diagnostic), exact source `a43e2f1b265ef956ee154e82a198a17f9831a220`, ROM `fbf81a5eafa536f95497be22c787812046cf59a38eb962ee28230b3fc8f9ec99`.

Final ice NAME templates, compact enemy occupancy and register-held NAME cursors reduce NTSC active world foreground cost12.19% and full foreground preparation6.48%. Active pictures rise9.7979→10.3356NTSC (+5.49%) and9.6986→10.2829PAL (+6.02%). Source logic remains59.92steps/s; all graphics/colors/actors/player/mask and mechanics are retained. The gain is modest; original presentation cadence is still unmet.

548host tests and both exact-source CI runs pass. The exact final ROM passes4035source/density scenes,4507native CPU/all128RAM checkpoints,1379coherent pictures,18directed IRQ boundaries, an AF2 negative control and the forced-geometry-failure stack regression. Independent review checked2560NAME contexts/8448occupancy entries and complete patch replay; its one Important error-path finding was fixed in one correction pass.

See `docs/world-transactions-diagnostic.md`, `references/world-transactions-result.json`, and the release human tests. Status moves to In review for this diagnostic/human comparison; full issue acceptance and #39/#15/#16 remain open. Owner/audio/controllers/physical acceptance is pending. Prior T and earlier controls are preserved.

## Measured checkpoint — 2026-11-04

### Owner cadence feedback

After0.0.10delivery the owner reports excessive speed, cadence unlike the original
and apparent picture skipping. Gameplay cadence is not accepted;42returns to
In progress. Controlled replay confirms2..9original states between active
pictures (mean6.043), with normal29-frame jumps shown in only4..5pictures.
An original-frame-counter audit and2253CPU/allRAM recheck found one source update
per original frame after startup, not a doubled update rate. Real acceleration
has not been reproduced in the owner's setup. Do not halve simulation as an
unmeasured workaround. New disjoint profiling puts world preparation at100566
of201312mean foreground cycles per active snapshot. See
docs/fixed-clock-cadence-feedback.md and references/fixed-clock-cadence-feedback.json.
No ROM bytes or published attachments changed in this investigation.

### Fixed-clock diagnostic delivery

The public F→I/J/K/L/M/contact14/P/Q chain now reproduces sealed Q exactly.
The T independent-clock diagnostic runs59.92275NTSC/59.92467PALlogical steps/s
in input-only original routes, with4507CPU/allRAM and1355coherent-picture checks.
Active drawing remains9.79790/9.69859fps: original-speed presentation is unmet.
It is a diagnostic, not the final performance solution. All original colors,
actors, player and mask remain. R's marginal header/igloo path is preserved and
rejected. See docs/fixed-clock-diagnostic.md and the0.0.10human tests. Do not close
#42/#39/#15/#16 from the source-clock result.

[v0.0.10](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.10-fixed-clock-diagnostic)
is published from clean854dcf462b56274f60f1f0cf978bc487d124e57a, exact ROM
`29b4588b62d4b44a88401c691512d415b26bdaf559198d889730ee2b49763b1e`.
All four attachments were downloaded again and verified byte-identical.545host
tests, both exact-source CI runs and all natural/directed gates pass. The T
workbook preserves all Q cells/features and clearly separates the two clocks.
Issue status is In review for diagnostic/human feedback; original-time drawing
and the implementation issue's full DoD remain open. See public fixed-clock
validation/publication receipts and docs/handoffs/issue-42.md.

Independent review found no demonstrated kernel blocker and required directed
hardware-IRQ boundary alignment in addition to natural replay. The new harness
checks nine mapper/VDP/stream/snapshot boundaries, complete main/alternate/index
registers, SP and bank after RETI; an AF2 mutation must fail its oracle. Manual
listening, alternating controllers, unseen levels and physical MSX remain pending.

### Preserved Q measurements

Shared residency O-B is correct but rejected(-6.91%/-6.90%). Prepared ice P-C
improves4.87%/5.35% against M-C. Eager enemy bands Q-C regress against P-C;
lazy-key bands Q-E improve2.85% NTSC /3.10% PAL over P-C, or7.85%/8.62% over M-C.
Active source cadence33.6350 /35.2938 updates/s remains below the original goal.
NTSC whole-frame mean102843 cycles, P95 219663; complete-route maximum484270.

Q validation:209088 actual Z80 actor cases,2115 original scenes,1920 dense
synthetic scenes,4139 source-model images,4508 source CPU/all-RAM checkpoints.
The complete host suite passes531 tests. Independent review found an evidence
binding gap; corrected reporters reject mixed-ROM proofs and altered audited
buffers. Fresh v2 owner receipts and bound reports preserve identical timings.

The O/P and Q workbooks each contain8278 paired observations and424 cost rows;
historical M and all previous artifacts are preserved. No manual/listening/
physical or complete-game acceptance is claimed. Q-E remains an internal test;
At that checkpoint canonical source integration and a useful human ROM/release
were pending; the current clock diagnostic above supersedes that source gap.

Next: redesign the wider prepare pipeline and its tails. Even zero world work
would leave66928 mean NTSC cycles, above59736. Further enemy-only changes cannot
solve the complete-frame target. See docs/direct-enemy-progress.md and
docs/issue-42-review.md. Keep draft PR43 stacked on41; #39/#42 remain open.

## Goal and first implementation boundary

Build an MSX1-oriented rendering pipeline with a credible complete-frame budget.
Start with shared ice-pattern residency across NAME generations and bounded
per-band NAME preparation. Keep displayed references pinned, including both
colors and vertical phases. Rework physical ownership/key recovery and its
independent checker together; do not weaken active-display protection.

Measure allocation, metadata, lookup, composition, IO and scheduling together.
Replace further generic stages when the whole-frame ledger requires it. The
56-slot host model avoids about 60% of semantic misses; this is a hypothesis
for implementation, not an FPS prediction. N-B traversal alone gained only
1.49% NTSC / 1.99% PAL and is retained as internal evidence.

## Dependencies / Definition of Ready

#39 research and sealed M-C control are available. Read
`docs/native-band-feasibility.md`, its design/plan, and the dedicated handoff.
Start in a forked `Frostbite — ISSUE #42` chat with exclusive checkout
ownership and branch `codex/feat/42-native-renderer`.
No next-issue implementation in the predecessor chat.

## Acceptance / Definition of Done

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918 and built-in PSG only.
- Original CPU/state/input/collision/audio contracts remain equivalent; full
  physical pixels, colors and actors match the sealed control on all tested
  scenes. No frame skipping or reduced simulation rate used to claim success.
- Independent VRAM allocation/visible-reference checks pass, including overlap,
  wrap, phases, blue/white rows, transitions and dense four-lane cases.
- Paired active NTSC/PAL whole-frame mean/P95/max and source cadence identify
  actual gains and remaining shortfall. Update the performance workbook and
  record exact ROM/source/tool/input hashes. Do not sum inclusive helper costs.
- Independent review and focused PR delivery are integrated before closing.
  If original cadence is not achieved, explicitly retain #39's unmet goal;
  #15/#16 remain independent final timing/full-game/hardware qualification.
- Preserve all prior versions. Publish a useful human-test candidate as a new
  prerelease with exact ROM, SHA/source, current limits, next work and concrete
  setup/action/expected-result tests. Internal rejected experiments are archived.

Player-as-tiles remains on hold. Any material visual compromise needs a concrete
owner decision. Do not assume a complete permanent atlas fits VRAM. Automated,
manual-emulator and physical-hardware evidence remain separate.

## Tracking

MSX Game Ports project #7. Type: Task (repository native types unavailable).
Priority P1; size XL; estimate 40 hours, exploratory engineering and validation,
not a deadline. No new labels, milestones or shared project settings required.
