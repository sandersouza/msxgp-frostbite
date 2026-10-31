.DEFAULT_GOAL := build
PYTHON ?= .venv/bin/python
.PHONY: environment environment-check environment-dry-run build run smoke package test source-check ci-verify reference-check reference-rebuild mechanics-check
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
