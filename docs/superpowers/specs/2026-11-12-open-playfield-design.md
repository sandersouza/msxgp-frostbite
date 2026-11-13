# Open playfield, Retroworks credit and terminal palette

The owner resumed autonomous Issue42 execution after v26. Remove the black left
stripe, enlarge visible playfield, add `Activision - Retroworks`, preserve player
colors when falling into water, continue performance work, measure whole frames,
update the workbook and publish an exact testable ROM. The full-height stripe
was explicitly rejected. Same issue/root writer/checkout, no merge or close.

Use the complete first native world tile at targetX16 as the consistent left
edge, instead of the old maskedX24. Background column1 stays black and column2
uses the same full-width background tile as the inner field; gradient column2
does the same. This removes the shoreline overrun and adds eight sea pixels.
Native world actors/floes use the expanded tile edge; suppress only an individual
enemy copy at normalizedX0, which is the original hidden/waiting position. Keep
all original logical coordinates, contacts, movement and source CPU/RAM exact.
Retain conservative sprite admission and existing sprite/native fallbacks.

Alternatives rejected: full-height black stripe (owner rejection); simply omit
the old mask without normalizing background/actor clipping (exposes the original
shoreline overrun and hidden object fragments). No rescaling or gameplay resize.

Render the suffix `- Retroworks` in a readable5x7 white font at X120/Y184,
beside the unchanged Activision logo. Nine immutable tiles134..142 in SCREEN2
bank2 are free between six background tiles128..133 and atlas144..159. Initialize
their PGT/CGT once, using unused mapped-bank65 space after ah_end. Redirect only
the final boot t_fill call to a helper that completes that original fill before
uploading the suffix. Other atlas, source footer phases and dynamic roles remain.
Publish nine NAME cells in row23/columns15..23 only when the source screen is
visible; blank/reset transitions retain complete dirty transactions.

Keep the original normal-player palette for terminal animations as well. The
old setup deliberately selected the raw palette when EB/F0 changed; this makes
normal hat/skin colors red. Always select the existing adapted palette, retaining
the original sinking silhouette and source water-fade codes. Do not change source
animation/counters or turn underwater fade into an opaque character.

Reuse the58-byte private NAME publisher for credit cells and the unchanged
qualified prefix omission. The existing12-byte prefix compaction helper stays;
its remaining8 fixed bytes can gate visible-only credits. Shrinking the old
18-byte color selector to8 leaves10 retired RAM bytes for the individual-enemy
X0 guard. Prove placement and callers independently before promotion.

Keep all214 v26 sources and67 sealed roots immutable. The preserved AP one-byte
cache-default optimization may be composed if contracts and whole-route evidence
remain valid. Additive source models/checkers must independently derive the new
view and glyphs, audit immutable credit tiles, retain exact source/owners/active
page/dirty-list guards, and limit shadow ownership to the exact credit positions.
No blanket RGB or ownership exemptions. Test terminal frames and all edges,
full-density NTSC/PAL timing/landings, source/audio/IRQ/negative controls, clean
rebuild/CI and independent review. Every qualified human ROM gets a new version;
never replace v26 bytes. Uniform/all-level30FPS remains open until demonstrated.

## Verified implementation refinements

Actual source inspection found the old selector is20 bytes. The new8-byte
selector leaves12 bytes for inline uint8 normalization and per-copy X0 skip.
Right-edge hardware sprites at normalized158/159 cannot represent newly visible
wrapped pixels, so they use the existing native fallback. Source coordinates
and collision bounds are unchanged.

The expanded bear edge also requires the independent36-byte hybrid background
program to use full inner tiles, and both live clipping-key producers to select
unclipped masks. The general mask reader now returns after its complete8-byte
copy. Its retired19-byte clipping tail holds a visible/row23-dirty credit gate.
The old fixed gap and12-byte prefix compactor remain byte-identical.

The normal sinking palette has five distinct colors in some source frames.
Move only the general fallback's five24-byte planes to existing reserved
E780..E7F7 and its five colors to C4EB..EF, preserving cache keys C4E4..EA and
mapping C4F0..FF. Normal recipe packet scratch remains at C480. This occupies120
previously unused reserved RAM bytes without increasing the target's RAM needs.
Source water-fade colors, silhouettes and animation remain exact.
