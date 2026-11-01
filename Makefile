.DEFAULT_GOAL := build
PYTHON ?= .venv/bin/python
.PHONY: native-check native-phase-check native-input-check movement-build movement-check movement-run
native-check:
	@$(PYTHON) -B scripts/native_contract.py
native-phase-check:
	@$(PYTHON) -B scripts/native_contract.py --fast-phase
native-input-check:
	@$(PYTHON) -B scripts/native_input_check.py
	@$(PYTHON) -B scripts/native_input_check.py --fast-phase
movement-build:
	@$(PYTHON) -B scripts/movement_build.py
movement-check: movement-build
	@$(PYTHON) -B scripts/movement_bench.py --suite
movement-run: movement-build
	@openmsx -machine C-BIOS_MSX1 -cart outputs/movement/frostbite-0.0.3-movement.rom -romtype ASCII16
.PHONY: environment environment-check environment-dry-run build run smoke package test source-check ci-verify reference-check reference-rebuild mechanics-check reference-traces reference-cpu reference-ale reference-refuge reference-console reference-report render-build render-bench graphics-check
graphics-check:
	@$(PYTHON) -B scripts/graphics_reference.py
source-check:
	@$(PYTHON) -B scripts/source_policy.py
ci-verify:
	@$(PYTHON) -B scripts/ci_verify.py
environment:
	@bash scripts/setup.sh
environment-check:
	@bash scripts/setup.sh --check
environment-dry-run:
	@bash scripts/setup.sh --dry-run
build:
	@$(PYTHON) -B scripts/rom.py build
run: build
	@$(PYTHON) -B scripts/rom.py run
smoke: build
	@$(PYTHON) -B scripts/smoke.py
package:
	@$(PYTHON) -B scripts/package_diagnostic.py
test:
	@$(PYTHON) -B -m unittest discover -s tests -v
reference-check:
	@$(PYTHON) -B scripts/reference_inventory.py
reference-rebuild:
	@$(PYTHON) -B scripts/reference_rebuild.py
mechanics-check:
	@$(PYTHON) -B scripts/mechanics_probe.py
reference-traces:
	@$(PYTHON) -B scripts/reference_traces.py
reference-cpu:
	@$(PYTHON) -B scripts/reference_cpu_check.py
reference-ale:
	@$(PYTHON) -B scripts/reference_ale_check.py
reference-refuge:
	@$(PYTHON) -B scripts/reference_routes.py
reference-console:
	@$(PYTHON) -B scripts/reference_routes.py --route console
reference-report:
	@$(PYTHON) -B scripts/reference_report.py
render-build:
	@$(PYTHON) -B scripts/render_build.py
render-bench: render-build
	@$(PYTHON) -B scripts/render_bench.py --suite
