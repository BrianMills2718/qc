.PHONY: help test test-quick check status cost errors

DAYS ?= 7
PROJECT ?= qualitative_coding
LIMIT ?= 20

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

test:  ## Run full test suite
	python -m pytest tests/ -v

test-quick:  ## Run tests, minimal output
	python -m pytest tests/ -x -q

check:  ## Run tests + type check + lint
	python -m pytest tests/ -x -q 2>/dev/null || true
	@echo "Type check and lint not yet configured"

status:  ## Show git status
	@git status --short --branch

cost:  ## Show LLM spend
	@python -m llm_client cost --days $(DAYS) --project $(PROJECT) 2>/dev/null || echo "llm_client cost not available"

errors:  ## Show error breakdown
	@python -m llm_client errors --days $(DAYS) --project $(PROJECT) 2>/dev/null || echo "llm_client errors not available"
