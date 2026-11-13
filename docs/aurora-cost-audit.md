# Aurora cost audit from v0.0.16

The owner proposed keeping the upper color band fixed and changing only its
color table. Inspection and passive full-route profiling show that v0.0.16
already preloads its patterns and colors: eight gradient states use two tiles
each, with only two distinct pattern shapes. Animation selects the corresponding
NAME IDs on SCREEN2 row 3. It does not reconstruct all screen lines or upload
the band's PGT/CGT during preparation.

| Active-route measurement | NTSC | PAL |
|---|---:|---:|
| Coherent pictures measured | 433 | 391 |
| Complete foreground mean, cycles | 70,935 | 75,403 |
| Background stage mean, cycles | 3,321 | 3,603 |
| WORLD stage mean, cycles | 26,058 | 28,377 |
| Aurora row preparations | 217 | 213 |
| Aurora row CPU cycles / active picture | 502 | 546 |
| Aurora row CPU share of foreground | 0.71% | 0.72% |
| Row-3 NAME payload bytes, complete active route | 6,944 | 6,816 |
| Existing NAME payload estimate, cycles / picture | 465 | 506 |
| Igloo routine cycles / active picture | 3,909 | 4,259 |
| Igloo PGT writes with unchanged resulting bytes | 180/232 | 176/228 |
| Top igloo row PGT writes with unchanged bytes | 164/172 | 160/168 |

The row CPU measurement excludes common background setup and NAME IO. The
payload estimate uses the existing 29-cycle stream per byte; address/setup costs
can be shared with other dirty rows. Row 3 may also be dirty because of the
igloo. These are existing costs, not a measured optimization saving, upper bound
for the whole change, or predicted FPS increase. The igloo's unchanged-PGT
counts identify redundant output, but do not prove its constructor can simply
be skipped.

## Decision

The proposed color-table design is feasible in principle, but its baseline is
already a precomputed selection. Fixed NAME IDs would need separate per-page
color ownership or a coherent commit-time color transaction. The current
background CGT entries are shared and immutable during preparation. Updating a
shared entry while preparing the next page could change the visible page.
Igloo tiles overlapping the band also need their foreground/background colors
preserved; recoloring only the base band is insufficient.

No runtime conversion is selected from this audit alone. The direct band cost
is small compared with WORLD, while the adjacent igloo routine has more repeated
work. The concrete next lead is preserving valid igloo pattern bytes when only
background colors change, with key validity and active-page protection retained.
Any candidate must be measured on the whole route and landing distribution.

## Evidence

Control ROM SHA-256:
`9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b`.
Runtime source `a9cf5ff3ea802b79a0e328e0a9de844e9749f8d3`; all 151 bound
sources remain unchanged. The passive NTSC/PAL runs reproduce all five natural
buffers byte for byte, including timestamps and actual field indices. Original
CPU/all-RAM, graphics and owner checks pass. No candidate ROM, speed gain or new
release is claimed. v0.0.16 remains the downloadable control.

Relevant implementations: `scripts/presentation_fragments.py:background_tables`,
`src/presentation_native_background.asm:xh_bg`,
`src/presentation_name_upload.asm:p_template_upload_names_known`, and
`src/presentation_typed.asm:pt_igloo`. Live code and companions are verified
against the control build rather than inferred from retired assembly paths.

See `references/aurora-cost-audit.json`. Raw captures, producers and detailed
receipts remain local under `outputs/presentation/aurora-ac-research/`. Trial 1
failed because the profiler overwrote a Tcl channel variable; trial 2 fixes its
variable names and is the only accepted measurement. No ROM bytes changed.
