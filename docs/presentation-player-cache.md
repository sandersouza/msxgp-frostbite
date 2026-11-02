# Player variant cache under development

Status: integrated private Task 3 candidate after `dffe337`; timing still fails.

The current exact seven-byte player key has one retained variant per generation.
The 120-frame keyboard probe repeatedly constructs the shoreline player at Y=27,
X=64–69 and poses 0/1. Player MISSes reach 73,254 cycles for the sprite stage;
emission includes 25,906 cycles, pattern expansion 9,987 and band counting 7,284.
These are nested component costs, not independent frame budgets.

The [Texas Instruments 1982 data manual, section 2.4.5, pages 2-25–2-27](https://peacockmedia.software/tms/TMS9918datasheet.pdf#page=34)
defines a 2,048-byte sprite generator table and 32-byte 16×16 patterns. This
permits 64 pattern slots in the existing 16 KiB VRAM. It does not increase the
32 SAT entries or the four full sprite rectangles allowed per scanline.

The proposed template profile reserves four six-pattern player variants for
each inactive generation, with independent door/logo slots and the same mask.

| Role | Pattern slots | VRAM |
| --- | --- | --- |
| Player generation 0, four ways | 0–23 | 3800–3AFF |
| Player generation 1, four ways | 24–47 | 3B00–3DFF |
| Door/logo generation 0 | 48–52 | 3E00–3E9F |
| Door/logo generation 1 | 53–57 | 3EA0–3F3F |
| Unused | 58–62 | 3F40–3FDF |
| Immutable HMOVE mask | 63 | 3FE0–3FFF |

Eight 32-byte metadata entries fit at C080–C17F, already reserved renderer RAM.
Each retains the current valid byte, exact seven-byte key, sprite count, cut
offset and per-sprite band/color records. A HIT repositions the same complete
patterns; a MISS invalidates one way of the inactive generation. Its valid byte
must follow every required upload. Per-generation replacement cursors, selected
pattern base and candidate density count own four bytes at E610–E613.

An uncached frame may require more than six player patterns. Before emitting
such a frame, the renderer invalidates all four ways of its inactive generation
and uses that generation's first contiguous slots. It does not reduce the actor,
colors or rectangles to fit a cache way. The frame cannot publish a six-slot
cache entry afterward. The generation's 24-slot region also contains the prior
uncached renderer's maximum of sixteen patterns.

Static sprite lookup must use its own generation metadata, independently of the
chosen player way. SAT count, priority, full rectangles, positions, colors and
early-clock bits stay unchanged. Pattern indices and upload addresses change
together. Existing active-byte auditing already protects each full 32-byte
pattern referenced by the active SAT, including patterns above 3C00.

For shoreline Y=19–29, the absolute X key remains necessary near the left edge.
X=24–83 permits a normalized key: the source prefix cutoff is at most 22 after
two address carries; the earliest suffix cutoff is 91. All eight source pixels
stay between them. Parity, pose, displacement, F0 color state, reflection,
vertical/coarse phase and hold length remain in the key. Positions outside this
bounded interval retain their old key behavior. Host proof covers all 30,720
symbolic mask/reflection/X combinations and 120 derived translations from the
two eligible player states among 439 retained source observations. Those derived
translations are not additional original raster captures.

Actual Z80 selection passes 883 stateful operations, including each key bit,
both generations, replacement, default selection, invalid pages and full
inactive-generation invalidation. Maximum 3,465 cycles includes RPC. The synthetic
eight-pattern emission probe uses four full rectangles in each of two visible
bands. The earlier candidate overwrites two active opposite-generation patterns
and fails the active-byte guard. The corrected candidate preserves all active
bytes and matches complete VRAM, metadata, eight SAT entries and fallback fields
on both generations, maximum 49,886 cycles including RPC. An initial negative
fixture used a band outside the emitter's source-coordinate preconditions; it
is retained separately and is not the active-overwrite regression witness.

Private ROM `0feceba65193bae2f3d8a169db94cdf31569b71e1cdbf444e19adf051e6685b5`
passes all 2,115 original full-scene, physical ownership and active-byte checks;
controlled maximum preparation is 669,973 cycles. In the 120-frame keyboard probe,
expensive sprite stages fall from twelve to seven and total sprite-stage work
falls from 1,665,689 to 1,495,606 cycles. Complete timing still fails: maximum
691,812 busy cycles, 22 overruns and 53 skipped frames. A fresh original/default
control remains byte-identical at
`0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`.
The same candidate separately passes all twelve original input-only CPU routes:
24,820 complete CPU/all128RAM checkpoints, zero canonical injections and maximum
26,372 native-step cycles. That CPU-only RPC does not execute graphics, PSG or
paced presentation. The original-free host suite passes 458 tests.
This cache does not establish the cold or first-variant frame deadline by itself.
