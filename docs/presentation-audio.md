# Ordered source audio and the PSG adaptation under development

The source CPU owns F3/F4 arithmetic, envelopes, priorities and every AUDC,
AUDF and AUDV store. Presentation observes those stores without changing
canonical RAM or replacing any game rule. The native callbacks are integrated
in an explicitly selected private cartridge profile. Combined frame timing
still fails; there is no new qualified game release yet.

## Independent source observations

The frozen original streams contain 2,116 logical intervals and 3,499 ordered
writes, all after their visible-phase boundary. There are 1,553 writes whose
masked hardware value is unchanged, 1,609 silent intervals and at most 34 writes
in an interval. Every event and silent interval is retained. These interval
counts differ from the graphics proof's 2,115 normalized physical images; seeded
startup includes explicitly retained irregular physical frames.

Initial sound latches are structurally decoded from each actual complete
Stella capsule. Controlled fixtures restore their baseline independently;
natural input-only intervals carry the actual previous capsule. Applying all
observed writes reproduces the independent after-capsule's six hardware latches
in every interval. Starting all fixtures from guessed zero registers is rejected.
The PSG sequence generated alongside this audit remains a host projection.

## Measured mode periods and chosen approximation

The unmodified pinned [Stella oscillator](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/AudioChannel.cxx)
is compiled directly, with only unused serialization interfaces stubbed. Its
source files must equal the upstream Git blobs. All 16 controls × 32 frequency
values pass minimum repetition-period checks after 4,096 warm-up phase pairs,
with 32,768 checked samples each. A full phase pair averages 114 color clocks
under the pinned [audio clock schedule](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/Audio.hxx).
This proves oscillator periods, not target timbre, analog gain or phase.

The actual source writes use controls 1, 8 and 12. Control 1's 15-tick polynomial
uses an AY square carrier at the same repetition frequency; its timbre differs.
Control 8 uses AY noise at the nearest representable source bit-clock rate.
Control 12's six-tick square uses the closest AY tone period. General fallback
carriers cover other finite chip modes, with explicit 12-bit period clamping;
those controls are not additional observed Frostbite behavior.

For a mode repeating after K phase pairs and divider D=AUDF+1, the square-carrier
period is round(114×K×D/32), clamped to 1..4095. The built-in PSG clock is half
the master clock. The [General Instrument data manual](https://pub.intvprime.com/ba4ef/ie/Programming/AY-3-8910-8912-Programmable-Sound-Generator-Data-Manual.pdf)
defines its clock/16 tone and noise dividers, mixer and I/O registers. Noise
period is round(114×D/32), clamped to 1..31. The observed control-8 frequency 2
maps to noise period 11. AY and TIA polynomial sequences are different.

Source channels 0/1 use PSG A/B; C remains silent. If both active channels request
noise, source 0 owns the single AY noise clock before source 1. Both original
frequency latches remain intact. Four-bit source volume codes are transferred;
analog gain and perceptual envelope similarity still require listening evidence.
Controls 0/11 retain DC output semantics through disabled tone/noise mixing.

## Ordering, timing and peripheral ownership

The host model is invoked after every raw original write, including repeated
values. A physical PSG write is omitted when the desired register value is
already present; the original event is still retained separately. This avoids
confusing a register-write optimization with loss of source event order. Both
logical updates of a PAL double-step must reach the observer independently.

The native path handles each source write immediately. It needs no
queue and cannot overwrite an earlier logical update with the final latches.
Native write timing must be measured and documented against the original
post-visible timestamps; identical oscillator phase or analog output is not
claimed. Graphics timing remains failed and binding on the eventual release.

Audio may select/write registers 0..3, 6..10. Register 7 keeps its current upper
two peripheral-direction bits; registers 4/5 and 11..15 stay unowned. In
particular audio never writes joystick registers 14/15. Real two-port sampling,
CPU/ABI/slot/stack/interrupt guards and actual PSG histories still need native
checks.

The supplied Seaquest audio source was audited locally (SHA-256
5add6015305ab458cdf5846c9fba51173897df86e2305cb45fe16ead85f775b9).
Its alternate-register isolation and GPIO-preservation pattern is useful. Its
C015 source mapping, C460 workspace, supported control set and old results do
not apply to Frostbite; control 1 requires a new policy. No legacy result is
Frostbite acceptance. The preserved legacy and external snapshot are unchanged.

## Native callback component

The resident callback component now passes 31,252 actual Z80 calls, with the
complete expected sequence of 11,776 physical PSG writes. It covers fixed and
decoded-indexed bus writes, all 16 controls/32 frequencies, every raw byte of all
six registers, unchanged writes, noise-owner changes and four GPIO direction
states. Maximum callback cost including RPC is 1,176 cycles. These are synthetic
hardware-register streams, separate from the original-game integration below.

Every call checks AF/BC/DE/HL/IX/IY/SP/IFF, canonical/ABI/heap/VRAM/slot invariance,
all 16 physical PSG registers and all 32 workspace bytes. The I/O trace rejects
selection or writes outside 0..3 and 6..10, including initialization. Registers
4/5, 11..15 remain unchanged; initialization also preserves nonzero C tone
periods. The workspace is E000..E01F, previously unused renderer work, with only
E000..E014 currently populated. Cached slots for unowned PSG4/5 remain reserved
zero bytes; they do not mirror or authorize changes to those physical registers.

The isolated component profile sets ignorePortDirections=false. The standard
openMSX [MSX PSG convenience setting](https://raw.githubusercontent.com/openMSX/openMSX/master/src/sound/MSXPSG.cc)
otherwise repairs GPIO directions to the normal MSX arrangement, preventing four
requested direction states from actually being exercised. The component uses
the chip's real direction behavior and verifies raw I/O values too. It does not
change the application machine profile or claim four arbitrary direction states
are suitable joystick configurations. An intentional bad GPIO write fails at
the raw I/O guard. No listening, physical hardware or complete-frame acceptance
is inferred from this component.

## Original-game integration

The opt-in compiler adapter observes direct source audio stores and decoded
indexed stores whose addresses cannot be proved to stay in canonical RAM.
It restores the shared generator on success and failure; default generation
remains byte-identical. No original envelope arithmetic is replaced.

The existing source clear-loop lowering needs twelve zero-valued audio events
for its two TIA mirror passes, including repeated values. Its new wrapper emits
the applicable ordered events **before** canonical RAM is cleared, preserving
the current source frame epoch. All 256 entry-X values are checked against
independent original 6502 loop execution. Another 512 actual Z80 emitter/full
wrapper cases check the complete CPU/RAM/ABI and logged bus value/frame epoch.
An intentionally late emitter fails the epoch witness. The synthetic logging
stub's 9,179-cycle maximum is not the real PSG or game cost.

The first integrated game cartridge reproduces every one of the 3,499 ordered
raw original audio writes and all 2,472 expected physical PSG writes across
2,115 controlled post-visible intervals. Whole CPU/all128RAM after-states also
match. The remaining one of the 2,116 source intervals is the graphics-only
`hud-player-2-level20` fixture, whose impossible player selector is 2 rather
than 0/1; it has no audio writes and is explicitly accounted for, rather than
accepted as gameplay. Source audio auditing still covers all 2,116 intervals.

The integration trace observes the real joystick sampler separately: only that
sampler may select 14/15 and write 15, and its peripheral latch must be restored.
Sound writes remain restricted to their owned registers and retain register7
GPIO bits. Heap, slot, VRAM, stack and interrupts are guarded. Independent fresh
input-only replays on the same cartridge pass all 24,820 CPU/all128RAM checkpoints
of the twelve retained routes, with zero canonical-state injections.

These checks establish event ordering and register projection, not identical
TIA/AY oscillator phase. Target callbacks run inline in translated source order;
original instruction durations and analog timbres are not reproduced. Raw
original timestamps and target callback timestamps are retained locally.
The first combined 120-frame NTSC probe still reaches 571,692 busy cycles versus
the 59,736-cycle budget, with 22 overruns and 48 skipped VDP frames. The complete
2,115-scene graphics/ownership matrix passes with zero different images, but
neither that result nor the audio register trace qualifies real-time gameplay.
