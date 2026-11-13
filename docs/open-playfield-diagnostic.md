# Open playfield diagnostic

The owner resumed Issue42 after the v26 stop. The full-height stripe proposal
was rejected. This delivery removes the crop, normalizes both native and hybrid
background programs and extends the visible world edge from X24 to X16. Source
coordinates, contacts and CPU/RAM are unchanged. Individual X0 enemy copies are
hidden; hardware-sprite X158/159 wraps use the existing native fallback.

The immutable credit uses nine bank2 tiles134..142, initialized once. Only dirty
row23 publishes its nine NAME cells. Exact PGT/CGT and physical NAME ownership
are audited before the narrow legacy ownership shadow. Dynamic footer roles,
white ice atlas and all original background patterns/colors remain unchanged.

The old raw terminal palette collapsed skin/hat to red. The normal adapted
palette now applies throughout, preserving source fade codes and silhouettes.
Some frames need five colors, so only general player planes move to E780..E7F7
and colors to C4EB..EF. Cache keys C4E4..EA and mapping C4F0..FF remain intact.
Normal recipe scratch remains C480. Existing RAM/VRAM hardware limits hold.

Performance work also removes a repeated native cache default and obsolete
left clipping work. Whole regular-route mean CPU falls2.32% NTSC/2.45% PAL and
NTSC landings improve22→24/26. Bear mean falls1.16%, but NTSC cadence regresses
29.83→29.70 with one extra long interval. Stable/all-level30FPS remains open.
The next priority is that WORLD/NAME peak, not source-speed changes.

See [release/human tests](releases/v0.0.27-open-playfield-diagnostic.md),
[validation](../references/open-playfield-result.json) and the42-tab workbook.
Clean source `e42b737f0def8dd70be9b31712b776d83258fadd`, ROM `78090dde8429a5bc6097e02cfaf278539e05ff68b9582d65e16d430d04334c8a`. Build from sealed v26 with
`scripts/build_cache_default.py`, then `scripts/build_open_view.py`; rollback
loads the untouched v26 ROM. Local raw evidence is under ignored
`outputs/presentation/open-view-aq-research`, final build in`open-view-aq`.
Independent helper review is in`open-view-aq-review`. Exact clean rebuild
reproduces all tested bytes. The only precommit source change after measurement
removed one trailing blank line in the additive ASM; all emitted bytes match.
