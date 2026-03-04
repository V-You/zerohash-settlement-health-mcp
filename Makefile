SHELL := /bin/bash

.PHONY: encrypt-tse check-deps

encrypt-tse: check-deps
	@read -sp "Password: " PASS && echo && \
	mkdir -p html && \
	pandoc TSE-IQ_2026-03-03.md --standalone \
	  --metadata title="TSE Interview Questions" \
	  -o TSE-IQ_2026-03-03.html && \
	npx staticrypt TSE-IQ_2026-03-03.html \
	  --password "$$PASS" \
	  -d html && \
	mv html/TSE-IQ_2026-03-03.html html/TSE-IQ_2026-03-03.enc.html && \
	rm TSE-IQ_2026-03-03.html
	@echo "Done → html/TSE-IQ_2026-03-03.enc.html"

check-deps:
	@command -v pandoc >/dev/null 2>&1 || \
	  { echo "Error: pandoc not found. Install with: sudo apt install pandoc"; exit 1; }
	@command -v npx >/dev/null 2>&1 || \
	  { echo "Error: npx not found. Install Node.js from https://nodejs.org"; exit 1; }
