# Issue42 — v25 delivery and continuation

Same root writer / Issue42 chat / `codex/feat/42-native-renderer`; no successor
issue, checkout, merge or close. PR43 remains draft/stacked on41. Project7 is
In review at this sealed delivery checkpoint; performance acceptance is open.

- Runtime `13bf76ed540b968a6a6746385a396f6e4feeba71`,191 sources/186 parent files.
- ROM `bf5c703d1e607a47bec037a1e5bac0ce32d34539f14e051f69134470d78dae41`.
- Workbook `4e395c1bdf8aac762dcef753745a6ce68f665780434262efb1a1a367bad40962`.
- Immutable notes/documentation `fe965f6bfdc7a3354d45af6b23f0a290c3daaf32`.
- Independent runtime review `7e12e1b673be8b4a829faca35bdaaa3dba50b3c4e4d527ae8b47abbb6dd1ebe0`.
- Prepublication review `f3529563234548f6eee466d3c6bfa1f109b855400dc58490ca6ebd16a11c4ffa`.
- Final delivery review `3d233e4a79c246e979d0f33eb444da0bacaa05dbf42266280a0dec8d9d71532c`.

[Release25](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.25-bear-hybrid-diagnostic)
has six exact downloaded/digest-verified assets. Tag resolves to runtime13bf;
all6v24 assets remain unchanged. See `references/bear-hybrid-result.json` and
`references/bear-hybrid-delivery.json`, architecture and release human tests.
WebMSX actually loads the downloaded ROM SHA1/ASCII16/NTSC game picture;
0errors,1deprecationwarning, session closed. This is launch proof only.

NTSC bear mean27.0953→28.1214FPS(+3.79%), foreground74126→70670cycles;
regular31.5939 unchanged. PALbear24.6899unchanged, regular29.7739→29.6550(-.40%).
All26landing/endflags unchanged, existing omissions/longframes remain. Deferred
bear cost is inside HEADER, old bear inside WORLD; no double counting. Source
CPU/allRAM/input/simulation/PSG and exact composed pixels remain unchanged.

598host/2115source/2040density/54header/2115audio/36hardwareIRQ/AF2negative/
2exactCI/fourcleanpassive5bufferparity and11714independentZ80calls pass. Workbook
40tabs preserves39/792539cells/nativefeatures,zeroformulaerrors,2mutations,5views;
initial4GBexportOOM retained, samebuilder12GB succeeds. NativeExcel, mobile,
listening, owner and physical MSX acceptance remain pending.

Freeze the5newANroots after all writers stop; use `bear-hybrid-an-seals.json`.
Together with56prior roots these are immutable controls. Internal01/02rejections,
03/04controls and05qualifiedcandidate have byte-exact archived source histories.
Never edit these controls or overwrite any released binary. Builder rollback
returns exact v24. No new visual compromise/P0 recolor/player-only scene update.

Next: profile the remaining ordinary-player/general right-air preparation and
preflight spikes, plus NAME uploads, against full routes. Regular preflight max
51100cycles and foreground128020/138173 still cause long frames. Use fresh AO
outputs for research; do not write new measurements into sealed AN roots. Review
safe code/data placement before implementation; parent191 sources stay immutable.
Stable/all-level29.97/30FPS and original fluidity remain OPEN. Human testing does
not block the next measured optimization. Root remains the only tracked writer.
