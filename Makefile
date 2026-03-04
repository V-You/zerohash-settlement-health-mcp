SHELL := /bin/bash

.PHONY: encrypt-tse check-deps

encrypt-tse: check-deps
	@if [ -z "$(PASSWORD)" ]; then read -sp "Password: " PASS && echo; else PASS="$(PASSWORD)"; fi && \
	mkdir -p html && \
	.venv/bin/grip --export TSE-IQ_2026-03-03.md index.reg.html && \
	npx staticrypt index.reg.html \
	  --password "$$PASS" \
	  -d docs/TSE-IQ_20260303 && \
	mv docs/TSE-IQ_20260303/index.reg.html docs/TSE-IQ_20260303/index.html && \
	rm index.reg.html
	@echo "Done → docs/TSE-IQ_20260303/index.html"

check-deps:
	@test -f .venv/bin/grip || \
	  { echo "Error: grip not found. Run: uv sync --extra dev"; exit 1; }
	@command -v npx >/dev/null 2>&1 || \
	  { echo "Error: npx not found. Install Node.js from https://nodejs.org"; exit 1; }
