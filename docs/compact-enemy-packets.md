# Compact enemy graphics packets

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44).
`src/compact_enemy_packet.asm` reconstructs the inherited enemy buffer from the
existing original-data block, reflection table and1.5x expansion table.
The accepted game is unchanged; this constructor is not linked yet.

The old representation stores18,824payload bytes plus a3,168-byte directory:
**21,992bytes** for992physical packets. An independent host audit checks all
1,056directory entries, eight existing vertical-copy routines and all8,448
48-byte buffer results. It also reconstructs132current32-byte hardware-sprite
patterns from the same source rows.

The new Z80 routine uses **184code bytes +33extra shape-offset bytes** and
reuses1,024original-data bytes,1,024expansion bytes and256reverse bytes already
needed by the current game. It clears48output bytes, handles both reflections
and16horizontal/eight vertical phases, and returns the original third-column
empty flag. It preserves IX/IY/SP/IFF and only writes the output, five scratch
bytes and bounded stack. It does not access the mapper or VDP.

All **8,448native calls** match the sealed v0.0.30 packets and flags exactly,
including pre-poisoned output buffers. Costs including CALL/JP are4,549minimum,
5,867mean,7,245P95/maximum cycles. Run02 at commit06c8b0f reproduces run01's
ROM, output bytes and cycles. The fixture ROM SHA-256 is
`3b083da75361186ea2fe349f97fd2da53761dedbd36865116dbbe3276f679d1d`.

This is a storage opportunity, **not a proven net21,775-byte game reduction**:
integration must account for old shared LUTs, relocation, caches and any old
code removed. Construction is more expensive than packet copying. Preserve
`qe_bulk` reuse among repeated copies and measure complete-frame density and
cache misses before accepting the replacement.

```sh
env PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/compact_enemy_packet_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-enemy-packet-proof
```

See `references/compact-delivery/issue-44-enemy-packet.json`. Original bytes,
generated tables and component fixture ROMs stay local/ignored. No playable
compact ROM, COM, BIN or whole-frame cadence result is claimed here.
