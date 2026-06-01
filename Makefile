SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON ?= python3
UV ?= uv

PY_FILES := $(shell git ls-files --cached --others --exclude-standard '*.py' ':!:out/**' ':!:dist/**' ':!:node_modules/**' ':!:.venv/**' ':!:input/**' ':!:media/**' ':!:backups/**' ':!:templates/**' ':!:drafts/**' ':!:_vendor/**')
MYPY_FILES := $(shell git ls-files --cached --others --exclude-standard '*.py' ':!:tests/**' ':!:out/**' ':!:dist/**' ':!:node_modules/**' ':!:.venv/**' ':!:input/**' ':!:media/**' ':!:backups/**' ':!:templates/**' ':!:drafts/**' ':!:_vendor/**')
JS_FILES := $(shell git ls-files --cached --others --exclude-standard '*.js' '*.mjs' ':!:out/**' ':!:dist/**' ':!:node_modules/**')
SHELL_FILES := $(shell git ls-files --cached --others --exclude-standard '*.sh')

.PHONY: help lint lint-paths lint-python lint-js lint-shell type test check

help:
	@printf "Available targets:\n"
	@printf "  make lint   Run linters and source hygiene checks\n"
	@printf "  make type   Run type checks where typed source exists\n"
	@printf "  make test   Run unit tests and repository hygiene tests\n"
	@printf "  make check  Run lint, type, and test\n"

lint: lint-paths lint-python lint-js lint-shell

lint-paths:
	@$(PYTHON) tests/test_repo_hygiene.py --path-only

lint-python:
	@if [ -n "$(PY_FILES)" ]; then \
		if [ -f pyproject.toml ]; then \
			$(UV) run --extra dev ruff check $(PY_FILES); \
		else \
			$(PYTHON) -m compileall -q $(PY_FILES); \
		fi; \
	else \
		printf "No Python files to lint.\n"; \
	fi

lint-js:
	@if [ -n "$(JS_FILES)" ]; then \
		for file in $(JS_FILES); do node --check "$$file"; done; \
	else \
		printf "No JavaScript files to lint.\n"; \
	fi

lint-shell:
	@if [ -n "$(SHELL_FILES)" ]; then \
		for file in $(SHELL_FILES); do bash -n "$$file"; done; \
	else \
		printf "No shell files to lint.\n"; \
	fi

type:
	@if [ -n "$(MYPY_FILES)" ]; then \
		if [ -f pyproject.toml ]; then \
			$(UV) run --extra dev mypy $(MYPY_FILES); \
		else \
			$(PYTHON) -m compileall -q $(MYPY_FILES); \
		fi; \
	else \
		printf "No Python files to type-check.\n"; \
	fi
	@if [ -f package.json ] && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.typecheck ? 0 : 1)"; then \
		npm run typecheck; \
	elif [ -f package.json ]; then \
		printf "No npm typecheck script configured.\n"; \
	fi

test:
	@if [ -d tests ]; then $(PYTHON) -m unittest discover -s tests -v; fi
	@if [ -f package.json ] && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.test ? 0 : 1)"; then \
		npm test; \
	fi

check: lint type test
