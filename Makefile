SHELL := /bin/bash

.PHONY: encrypt-tse check-deps

encrypt-tse: check-deps
	@if [ -z "$(PASSWORD)" ]; then read -sp "Password: " PASS && echo; else PASS="$(PASSWORD)"; fi && \
	mkdir -p html && \
	.venv/bin/grip --export TSE-IQ_2026-03-03.md TSE-IQ_2026-03-03.html && \
	npx staticrypt TSE-IQ_2026-03-03.html \
	  --password "$$PASS" \
	  -d html && \
	mv html/TSE-IQ_2026-03-03.html html/TSE-IQ_2026-03-03.enc.html && \
	rm TSE-IQ_2026-03-03.html
	@echo "Done → html/TSE-IQ_2026-03-03.enc.html"

check-deps:
	@test -f .venv/bin/grip || \
	  { echo "Error: grip not found. Run: uv sync --extra dev"; exit 1; }
	@command -v npx >/dev/null 2>&1 || \
	  { echo "Error: npx not found. Install Node.js from https://nodejs.org"; exit 1; }
