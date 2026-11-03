# Issue #39 continuation — Atari800 research checkpoint

Exclusive owner: `Frostbite — ISSUE #39`, checkout
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`, branch
`codex/fix/39-atari800-performance` from merged main
`9c55090f49e9da535c955306469c7a2322d3ba86`.
Issue https://github.com/sandersouza/msxgp-frostbite/issues/39 remains In progress,
P1/XL/24h exploratory. This is research progress, not performance acceptance.

Read `docs/atari800-performance-research.md` for primary sources, measurements,
limitations and first proposed native enemy-band component experiment.
Public analyzer/tests and generic emulator trace/probe form this checkpoint;
no MSX runtime is modified, no new MSX ROM or release is produced at this point.
Baseline0.0.9 retains its seven black sprites and SHA
838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6.
Local A-D stay retired. Player tiles remain on hold.

CAR input SHAe3fc0fd44748810def7f3313720ed65f320624ec1cc832d087d983d00e947243.
Atari800 commit98cc2dc749867c9c7317a0271ba062a6c797f886 + local trace patch,
Altirra replacement OS, 8KiB RAM,1200frames NTSC andPAL;899 sampled counter
intervals each alladvance1. Actual scroll/CHBASE writes andGTIA collision-register
reads confirm hardware assistance. This is not full source-equivalence or dense
level acceptance. Author says original6502loop preserved; source/license notfound,
supplied CAR notbyte-matched to authorattachment (HTML challenge).

Ignored research root outputs/atari800-research contains emulator checkout,
config/probe, disassembly, failed early setup attempts, successful isolated
ntsc-hardware/pal-hardware captures, and pool_model.py/pool-model.json. Public
metadata hashes exact current tools, probe/library/config/raw captures. Initial
ntsc/pal runs were48KiB and superseded; final named hardware runs verify8KiB and
all1200mappedROMimages. Never use the early setups as final evidence.

Offline permanent-atlas feasibility fails current VRAM capacity; ideal shared
floe cache cuts only10% ofestimatedpatternmisses, not overall speed. Do not turn
that model into another marginal-ROM experiment. Fresh505 host tests pass,
including4 synthetic analyzer trust-boundary tests. Next: design one direct native
enemy-band tile path with complete original pixel/contact/memory/IO equivalence
and whole-path cycle comparison, then decide integration from measured gain.
Implement only after the bounded design/test contract is concrete. Existing
original mechanics remain authoritative; main stays the masked0.0.9 baseline.
