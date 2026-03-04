SHELL := /bin/bash

.PHONY: encrypt-tse check-deps

encrypt-tse: check-deps
	@if [ -z "$(PASSWORD)" ]; then read -sp "Password: " PASS && echo; else PASS="$(PASSWORD)"; fi && \
	mkdir -p html && \
	.venv/bin/grip --export TSE-IQ_2026-03-03.md index.reg.html && \
	python3 -c "\
import re; \
c = open('index.reg.html').read(); \
c = re.sub(r'(<a\b)(\s)', r'\1 target=\"_blank\" rel=\"noopener noreferrer\"\2', c); \
c = re.sub(r'(<a\b)(>)', r'\1 target=\"_blank\" rel=\"noopener noreferrer\"\2', c); \
c = re.sub(r'(<summary>)(.*?)(</summary>)', lambda m: m.group(1) + re.sub(r'<strong>(.*?)</strong>', r'<strong><u>\1</u></strong>', m.group(2)) + m.group(3), c, flags=re.DOTALL); \
c = re.sub(r'(<a\b[^>]*>)(.*?)(</a>)', r'\1<u>\2</u>\3', c, flags=re.DOTALL); \
open('index.reg.html','w').write(c); \
" && \
	npx staticrypt index.reg.html \
	  --password "$$PASS" \
	  --remember false \
	  -d docs/TSE-IQ_20260303 && \
	mv docs/TSE-IQ_20260303/index.reg.html docs/TSE-IQ_20260303/index.html && \
	rm index.reg.html
	@echo "Done → docs/TSE-IQ_20260303/index.html"

check-deps:
	@test -f .venv/bin/grip || \
	  { echo "Error: grip not found. Run: uv sync --extra dev"; exit 1; }
	@command -v npx >/dev/null 2>&1 || \
	  { echo "Error: npx not found. Install Node.js from https://nodejs.org"; exit 1; }
