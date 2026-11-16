.DEFAULT_GOAL := build
PYTHON ?= python3
CC ?= cc
NATIVE_OUT ?= outputs/native
ZX0 ?= .tools/zx0

NATIVE_SOURCES := $(shell find src -type f) $(wildcard scripts/*.py) Makefile
ZX0_SOURCE := src/third_party/zx0/compressor
ASSEMBLER := .tools/frostbite/sjasmplus-d379eeac9ad3857fb48fd3a3929175d0a56038ce/sjasmplus

.PHONY: build native-delivery verify run clean test ci-verify source-check environment environment-check
clean:
	rm -rf outputs
test:
	@$(PYTHON) -B -m unittest discover -s tests -v
ci-verify: test
	@$(PYTHON) -B -c 'import ast,pathlib; [ast.parse(p.read_text(),filename=str(p)) for p in pathlib.Path("scripts").glob("*.py")]; print("Maintained Python sources parsed successfully.")'
source-check:
	@$(PYTHON) -B scripts/source_policy.py
environment: $(ASSEMBLER) $(ZX0)
environment-check:
	@$(PYTHON) -B -c 'import sys; sys.path.insert(0,"scripts"); from environment import verified_tool; print(verified_tool("sjasmplus"))'
$(ASSEMBLER): references/tools-lock.json scripts/environment.py scripts/ci_setup.py
	@$(PYTHON) -B scripts/ci_setup.py
	@touch "$@"
$(ZX0): $(wildcard $(ZX0_SOURCE)/*.c) $(ZX0_SOURCE)/zx0.h
	@mkdir -p "$(@D)"
	$(CC) -O2 -o "$@" $(addprefix $(ZX0_SOURCE)/,zx0.c optimize.c compress.c memory.c)
build native-delivery: $(NATIVE_OUT)/native-delivery-build.json
$(NATIVE_OUT)/native-delivery-build.json: $(NATIVE_SOURCES) $(ASSEMBLER) $(ZX0)
	@$(PYTHON) -B scripts/build_native_delivery.py --out "$(NATIVE_OUT)" --compressor "$(ZX0)"
verify: build
	@$(PYTHON) -B scripts/release_check.py --delivery "$(NATIVE_OUT)"
run: build
	@openmsx -machine C-BIOS_MSX1 -cart "$(NATIVE_OUT)/cartridge/FROSTBIT.ROM" -romtype Normal
