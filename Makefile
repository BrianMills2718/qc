.PHONY: help test test-quick test-e2e test-all bench validate-d3-gold validate-d7-gold run-d7-retrieval compare-d7-retrieval run-inv7-fixtures check lint docs-check clean status cost errors

DAYS ?= 7
PROJECT ?= qualitative_coding
LIMIT ?= 20

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

test:  ## Run deterministic test suite (excludes live LLM E2E)
	python -m pytest tests/ -m "not live_llm" -v

test-quick:  ## Run tests, minimal output
	python -m pytest tests/ -m "not live_llm" -x -q

test-e2e:  ## Run live LLM E2E tests
	python -m pytest tests/test_e2e.py -v

test-all:  ## Run deterministic tests and live LLM E2E tests
	python -m pytest tests/ -v

bench:  ## Evaluation-harness Phase 0 scorecard (ID=<project_id> [D3_GOLD=d3_gold.json] [GOLD=gold.json] [BASELINES=baselines.json] [PROMPT_INJECTION=inv7.json] [OBS_DB=path] [TRACE_ID=id] [ARTIFACT_DIR=benchmark_results])
	python scripts/bench_phase0.py $(ID) $(if $(D3_GOLD),--d3-gold-file $(D3_GOLD),) $(if $(GOLD),--gold-file $(GOLD),) $(if $(BASELINES),--d7-baselines-file $(BASELINES),) $(if $(PROMPT_INJECTION),--prompt-injection-file $(PROMPT_INJECTION),) $(if $(OBS_DB),--observability-db $(OBS_DB),) $(if $(TRACE_ID),--trace-id $(TRACE_ID),) $(if $(ARTIFACT_DIR),--artifact-dir $(ARTIFACT_DIR),)

validate-d3-gold:  ## Validate a versioned D3 application gold-set package (GOLD=gold_set.json)
ifndef GOLD
	$(error GOLD is required. Usage: make validate-d3-gold GOLD=gold_set.json)
endif
	python scripts/validate_d3_gold_set.py $(GOLD)

validate-d7-gold:  ## Validate a versioned D7 gold-set package (GOLD=gold_set.json)
ifndef GOLD
	$(error GOLD is required. Usage: make validate-d7-gold GOLD=gold_set.json)
endif
	python scripts/validate_d7_gold_set.py $(GOLD)

MODE ?= lexical_bm25

run-d7-retrieval:  ## Export D7 retrieval baseline predictions (ID=<project_id> OUTPUT=predictions.json [MODE=lexical_bm25] [MODEL=embedding-model] [CANDIDATES=5])
ifndef ID
	$(error ID is required. Usage: make run-d7-retrieval ID=<project_id> OUTPUT=predictions.json)
endif
ifndef OUTPUT
	$(error OUTPUT is required. Usage: make run-d7-retrieval ID=<project_id> OUTPUT=predictions.json)
endif
	python scripts/run_d7_retrieval.py $(ID) --output $(OUTPUT) --retrieval-mode $(MODE) $(if $(MODEL),--embedding-model $(MODEL),) $(if $(CANDIDATES),--candidates-per-claim $(CANDIDATES),)

compare-d7-retrieval:  ## Compare D7 retrieval predictions (ID=<project_id> GOLD=gold.json PREDICTIONS="a.json b.json" [OUTPUT=report.json])
ifndef ID
	$(error ID is required. Usage: make compare-d7-retrieval ID=<project_id> GOLD=gold.json PREDICTIONS="a.json b.json")
endif
ifndef GOLD
	$(error GOLD is required. Usage: make compare-d7-retrieval ID=<project_id> GOLD=gold.json PREDICTIONS="a.json b.json")
endif
ifndef PREDICTIONS
	$(error PREDICTIONS is required. Usage: make compare-d7-retrieval ID=<project_id> GOLD=gold.json PREDICTIONS="a.json b.json")
endif
	python scripts/compare_d7_retrieval.py $(ID) --gold-file $(GOLD) $(foreach file,$(PREDICTIONS),--predictions-file $(file)) $(if $(OUTPUT),--output $(OUTPUT),)

run-inv7-fixtures:  ## Run deterministic INV-7 structural fixtures (OUTPUT=inv7.json)
ifndef OUTPUT
	$(error OUTPUT is required. Usage: make run-inv7-fixtures OUTPUT=inv7.json)
endif
	python scripts/run_inv7_fixtures.py --output $(OUTPUT)

check:  ## Run deterministic tests + lint + docs checks
	python -m pytest tests/ -m "not live_llm" -x -q
	$(MAKE) lint
	$(MAKE) docs-check
	@echo "Type check not yet configured"

lint:  ## Run the configured Ruff lint gate
	python -m ruff check .

docs-check:  ## Run documentation and governance checks
	python scripts/check_markdown_links.py
	python scripts/check_doc_coupling.py --validate-config
	python scripts/sync_plan_status.py --check
	python scripts/meta/check_agents_sync.py --check

clean:  ## Remove local Python/test caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

status:  ## Show git status
	@git status --short --branch

cost:  ## Show LLM spend
	@python -m llm_client cost --days $(DAYS) --project $(PROJECT) 2>/dev/null || echo "llm_client cost not available"

errors:  ## Show error breakdown
	@python scripts/recent_errors.py --days $(DAYS) --project $(PROJECT) --limit $(LIMIT)

# >>> META-PROCESS WORKTREE TARGETS >>>
WORKTREE_CREATE_SCRIPT := scripts/meta/worktree-coordination/create_worktree.py
WORKTREE_REMOVE_SCRIPT := scripts/meta/worktree-coordination/safe_worktree_remove.py
WORKTREE_CLAIMS_SCRIPT := scripts/meta/worktree-coordination/../check_coordination_claims.py
WORKTREE_SESSION_START_SCRIPT := scripts/meta/worktree-coordination/../session_start.py
WORKTREE_SESSION_HEARTBEAT_SCRIPT := scripts/meta/worktree-coordination/../session_heartbeat.py
WORKTREE_SESSION_STATUS_SCRIPT := scripts/meta/worktree-coordination/../session_status.py
WORKTREE_SESSION_FINISH_SCRIPT := scripts/meta/worktree-coordination/../session_finish.py
WORKTREE_SESSION_CLOSE_SCRIPT := scripts/meta/worktree-coordination/../session_close.py
WORKTREE_DIR ?= $(shell python "$(WORKTREE_CREATE_SCRIPT)" --repo-root . --print-default-worktree-dir)
WORKTREE_START_POINT ?= HEAD
WORKTREE_PROJECT ?= $(notdir $(CURDIR))
WORKTREE_AGENT ?= $(shell if [ -n "$$CODEX_THREAD_ID" ]; then printf codex; elif [ -n "$$CLAUDE_SESSION_ID" ] || [ -n "$$CLAUDE_CODE_SSE_PORT" ]; then printf claude-code; elif [ -n "$$OPENCLAW_SESSION_ID" ] || [ -n "$$OPENCLAW_RUN_ID" ]; then printf openclaw; fi)
SESSION_GOAL ?=
SESSION_PHASE ?=
SESSION_NEXT ?=
SESSION_DEPENDS ?=
SESSION_STOP_CONDITIONS ?=
SESSION_NOTE ?=

.PHONY: worktree worktree-list worktree-remove session-start session-heartbeat session-status session-finish session-close

worktree:  ## Create claimed worktree (BRANCH=name TASK="..." [PLAN=N] [AGENT=name])
ifndef BRANCH
	$(error BRANCH is required. Usage: make worktree BRANCH=plan-42-feature TASK="Describe the task")
endif
ifndef TASK
	$(error TASK is required. Usage: make worktree BRANCH=plan-42-feature TASK="Describe the task")
endif
ifndef SESSION_GOAL
	$(error SESSION_GOAL is required. Name the broader objective, not the local branch)
endif
ifndef SESSION_PHASE
	$(error SESSION_PHASE is required. Describe the current execution phase)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@if [ ! -f "$(WORKTREE_CREATE_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CREATE_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree."; \
		exit 1; \
	fi
	@if [ ! -f "$(WORKTREE_CLAIMS_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CLAIMS_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree."; \
		exit 1; \
	fi
	@if [ ! -f "$(WORKTREE_SESSION_START_SCRIPT)" ]; then \
		echo "Missing session lifecycle module: $(WORKTREE_SESSION_START_SCRIPT)"; \
		echo "Install or sync the sanctioned session lifecycle module before using make worktree."; \
		exit 1; \
	fi
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --claim \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--intent "$(TASK)" \
		--claim-type program \
		--branch "$(BRANCH)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		$(if $(PLAN),--plan "Plan #$(PLAN)",)
	@mkdir -p "$(WORKTREE_DIR)"
	@if ! python "$(WORKTREE_CREATE_SCRIPT)" --repo-root . --path "$(WORKTREE_DIR)/$(BRANCH)" --branch "$(BRANCH)" --start-point "$(WORKTREE_START_POINT)"; then \
		python "$(WORKTREE_CLAIMS_SCRIPT)" --release --agent "$(WORKTREE_AGENT)" --project "$(WORKTREE_PROJECT)" --scope "$(BRANCH)" >/dev/null 2>&1 || true; \
		exit 1; \
	fi
	@if ! python "$(WORKTREE_SESSION_START_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--intent "$(TASK)" \
		--repo-root "$(CURDIR)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		--branch "$(BRANCH)" \
		--broader-goal "$(SESSION_GOAL)" \
		--current-phase "$(SESSION_PHASE)" \
		$(if $(PLAN),--plan "Plan #$(PLAN)",) \
		$(if $(SESSION_NEXT),--next-phase "$(SESSION_NEXT)",) \
		$(if $(SESSION_DEPENDS),--depends-on "$(SESSION_DEPENDS)",) \
		$(if $(SESSION_STOP_CONDITIONS),--stop-condition "$(SESSION_STOP_CONDITIONS)",) \
		$(if $(SESSION_NOTE),--notes "$(SESSION_NOTE)",); then \
		git worktree remove --force "$(WORKTREE_DIR)/$(BRANCH)" >/dev/null 2>&1 || true; \
		git branch -D "$(BRANCH)" >/dev/null 2>&1 || true; \
		python "$(WORKTREE_CLAIMS_SCRIPT)" --release --agent "$(WORKTREE_AGENT)" --project "$(WORKTREE_PROJECT)" --scope "$(BRANCH)" >/dev/null 2>&1 || true; \
		exit 1; \
	fi
	@echo ""
	@echo "Worktree created at $(WORKTREE_DIR)/$(BRANCH)"
	@echo "Claim created for branch $(BRANCH)"
	@echo "Session contract started for $(SESSION_GOAL)"

session-start:  ## Create or refresh the active session contract for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-start BRANCH=plan-42-feature TASK="..." SESSION_GOAL="..." SESSION_PHASE="...")
endif
ifndef TASK
	$(error TASK is required. Usage: make session-start BRANCH=plan-42-feature TASK="...")
endif
ifndef SESSION_GOAL
	$(error SESSION_GOAL is required. Name the broader objective, not the local branch)
endif
ifndef SESSION_PHASE
	$(error SESSION_PHASE is required. Describe the current execution phase)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_START_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--intent "$(TASK)" \
		--repo-root "$(CURDIR)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		--branch "$(BRANCH)" \
		--broader-goal "$(SESSION_GOAL)" \
		--current-phase "$(SESSION_PHASE)" \
		$(if $(PLAN),--plan "Plan #$(PLAN)",) \
		$(if $(SESSION_NEXT),--next-phase "$(SESSION_NEXT)",) \
		$(if $(SESSION_DEPENDS),--depends-on "$(SESSION_DEPENDS)",) \
		$(if $(SESSION_STOP_CONDITIONS),--stop-condition "$(SESSION_STOP_CONDITIONS)",) \
		$(if $(SESSION_NOTE),--notes "$(SESSION_NOTE)",)

session-heartbeat:  ## Refresh heartbeat and optional phase for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-heartbeat BRANCH=plan-42-feature)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_HEARTBEAT_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--branch "$(BRANCH)" \
		$(if $(SESSION_PHASE),--current-phase "$(SESSION_PHASE)",)

session-status:  ## Show live session summaries for this repo
	@python "$(WORKTREE_SESSION_STATUS_SCRIPT)" --project "$(WORKTREE_PROJECT)"

session-finish:  ## Finish the session for BRANCH=name; blocks if the worktree is dirty
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-finish BRANCH=plan-42-feature)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_FINISH_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		$(if $(SESSION_NOTE),--note "$(SESSION_NOTE)",)

session-close:  ## Close the claimed lane for BRANCH=name: cleanup worktree + branch + claim together
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-close BRANCH=plan-42-feature)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_CLOSE_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		--branch "$(BRANCH)" \
		$(if $(SESSION_NOTE),--note "$(SESSION_NOTE)",)

worktree-list:  ## Show claimed worktree coordination status
	@if [ ! -f "$(WORKTREE_CLAIMS_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CLAIMS_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree-list."; \
		exit 1; \
	fi
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --list

worktree-remove:  ## Safely remove worktree for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make worktree-remove BRANCH=plan-42-feature)
endif
	@if [ ! -f "$(WORKTREE_SESSION_CLOSE_SCRIPT)" ]; then \
		echo "Missing session lifecycle module: $(WORKTREE_SESSION_CLOSE_SCRIPT)"; \
		echo "Install or sync the sanctioned session lifecycle module before using make worktree-remove."; \
		exit 1; \
	fi
	@$(MAKE) session-close BRANCH="$(BRANCH)" $(if $(SESSION_NOTE),SESSION_NOTE="$(SESSION_NOTE)",)
# <<< META-PROCESS WORKTREE TARGETS <<<
