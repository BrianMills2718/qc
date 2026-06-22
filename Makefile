.PHONY: help test test-quick test-e2e test-all bench bench-package write-phase0-adjudication-package validate-d3-gold validate-d7-gold validate-inv7-package validate-inv7-live-protocol validate-adjudication-responses validate-adjudication-protocol adjudication-protocol-preflight adjudication-response-preflight import-adjudication-responses lint-scope-phrasing export-audit-manifest verify-export-audit-manifest export-publish-preflight verify-export-audit-log run-d7-retrieval compare-d7-retrieval run-inv7-fixtures run-inv7-live-fixtures adjudication-sample check lint docs-check clean status cost errors

DAYS ?= 7
PROJECT ?= qualitative_coding
LIMIT ?= 20
CONTEXT_CHARS ?= 120

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

bench:  ## Evaluation-harness Phase 0 scorecard (ID=<project_id> [D3_GOLD=d3_gold.json] [D3_BASELINES=d3_baselines.json] [GOLD=gold.json] [BASELINES=baselines.json] [PROMPT_INJECTION=inv7.json] [BIAS_COUNTERFACTUAL=bias.json] [CODEBOOK_QUALITY=quality.json] [GT_FIDELITY=gt_fidelity.json] [PREFERENCE=preference.json] [CALIBRATION=calibration.json] [OBS_DB=path] [TRACE_ID=id] [ARTIFACT_DIR=benchmark_results])
	python scripts/bench_phase0.py $(ID) $(if $(D3_GOLD),--d3-gold-file $(D3_GOLD),) $(if $(D3_BASELINES),--d3-baselines-file $(D3_BASELINES),) $(if $(GOLD),--gold-file $(GOLD),) $(if $(BASELINES),--d7-baselines-file $(BASELINES),) $(if $(PROMPT_INJECTION),--prompt-injection-file $(PROMPT_INJECTION),) $(if $(BIAS_COUNTERFACTUAL),--bias-counterfactual-file $(BIAS_COUNTERFACTUAL),) $(if $(CODEBOOK_QUALITY),--codebook-quality-file $(CODEBOOK_QUALITY),) $(if $(GT_FIDELITY),--gt-fidelity-file $(GT_FIDELITY),) $(if $(PREFERENCE),--interpretive-preference-file $(PREFERENCE),) $(if $(CALIBRATION),--confidence-calibration-file $(CALIBRATION),) $(if $(OBS_DB),--observability-db $(OBS_DB),) $(if $(TRACE_ID),--trace-id $(TRACE_ID),) $(if $(ARTIFACT_DIR),--artifact-dir $(ARTIFACT_DIR),)

bench-package:  ## Run Phase 0 from a versioned package manifest (PACKAGE=phase0_package.json)
ifndef PACKAGE
	$(error PACKAGE is required. Usage: make bench-package PACKAGE=phase0_package.json)
endif
	python scripts/run_phase0_benchmark_package.py $(PACKAGE)

write-phase0-adjudication-package:  ## Write Phase 0 package manifest from D3/D7 adjudication gold (ID=<project_id> OUTPUT=phase0_package.json [D3_GOLD=d3.json] [GOLD=d7.json])
ifndef ID
	$(error ID is required. Usage: make write-phase0-adjudication-package ID=<project_id> OUTPUT=phase0_package.json D3_GOLD=d3.json)
endif
ifndef OUTPUT
	$(error OUTPUT is required. Usage: make write-phase0-adjudication-package ID=<project_id> OUTPUT=phase0_package.json D3_GOLD=d3.json)
endif
ifeq ($(strip $(D3_GOLD)$(GOLD)),)
	$(error D3_GOLD or GOLD is required)
endif
	python scripts/write_phase0_adjudication_package.py $(ID) --output $(OUTPUT) $(if $(D3_GOLD),--d3-gold-file $(D3_GOLD),) $(if $(GOLD),--d7-gold-file $(GOLD),) $(if $(SCORECARD_OUTPUT),--scorecard-output $(SCORECARD_OUTPUT),) $(if $(ARTIFACT_DIR),--artifact-dir $(ARTIFACT_DIR),) $(if $(OBS_DB),--observability-db $(OBS_DB),) $(if $(TRACE_ID),--trace-id $(TRACE_ID),)

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

validate-inv7-package:  ## Validate a versioned INV-7 prompt-injection package (PACKAGE=inv7_package.json)
ifndef PACKAGE
	$(error PACKAGE is required. Usage: make validate-inv7-package PACKAGE=inv7_package.json)
endif
	python scripts/validate_inv7_prompt_injection_package.py $(PACKAGE)

validate-inv7-live-protocol:  ## Validate a pre-run INV-7 live benchmark protocol (PROTOCOL=protocol.json)
ifndef PROTOCOL
	$(error PROTOCOL is required. Usage: make validate-inv7-live-protocol PROTOCOL=protocol.json)
endif
	python scripts/validate_inv7_live_protocol.py $(PROTOCOL)

validate-adjudication-responses:  ## Validate completed adjudication sample responses (PACKAGE=sample.json)
ifndef PACKAGE
	$(error PACKAGE is required. Usage: make validate-adjudication-responses PACKAGE=sample.json)
endif
	python scripts/validate_adjudication_responses.py $(PACKAGE)

validate-adjudication-protocol:  ## Validate pre-registered adjudication protocol package (PROTOCOL=protocol.json)
ifndef PROTOCOL
	$(error PROTOCOL is required. Usage: make validate-adjudication-protocol PROTOCOL=protocol.json)
endif
	python scripts/validate_adjudication_protocol.py $(PROTOCOL)

adjudication-protocol-preflight:  ## Preflight protocol against sample package (PROTOCOL=protocol.json SAMPLE=sample.json)
ifndef PROTOCOL
	$(error PROTOCOL is required. Usage: make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json)
endif
ifndef SAMPLE
	$(error SAMPLE is required. Usage: make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json)
endif
	python scripts/preflight_adjudication_protocol_sample.py $(PROTOCOL) $(SAMPLE)

adjudication-response-preflight:  ## Preflight completed responses against protocol/sample packages (PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json)
ifndef PROTOCOL
	$(error PROTOCOL is required. Usage: make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json)
endif
ifndef SAMPLE
	$(error SAMPLE is required. Usage: make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json)
endif
ifndef RESPONSES
	$(error RESPONSES is required. Usage: make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json)
endif
	python scripts/preflight_adjudication_responses.py $(PROTOCOL) $(SAMPLE) $(RESPONSES)

import-adjudication-responses:  ## Import completed adjudication responses to D3/D7 gold packages (PACKAGE=responses.json GOLD_SET_ID=id DATASET_NAME=name CODER_COUNT=1 ADJUDICATOR=id PROTOCOL=summary [PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json] [D3_OUTPUT=d3.json] [D7_OUTPUT=d7.json])
ifndef PACKAGE
	$(error PACKAGE is required. Usage: make import-adjudication-responses PACKAGE=responses.json GOLD_SET_ID=id DATASET_NAME=name CODER_COUNT=1 ADJUDICATOR=id PROTOCOL=summary D3_OUTPUT=d3.json)
endif
ifndef GOLD_SET_ID
	$(error GOLD_SET_ID is required)
endif
ifndef DATASET_NAME
	$(error DATASET_NAME is required)
endif
ifndef CODER_COUNT
	$(error CODER_COUNT is required)
endif
ifndef ADJUDICATOR
	$(error ADJUDICATOR is required)
endif
ifndef PROTOCOL
	$(error PROTOCOL is required)
endif
ifeq ($(strip $(D3_OUTPUT)$(D7_OUTPUT)),)
	$(error D3_OUTPUT or D7_OUTPUT is required)
endif
	python scripts/import_adjudication_responses.py $(PACKAGE) $(if $(D3_OUTPUT),--output-d3 $(D3_OUTPUT),) $(if $(D7_OUTPUT),--output-d7 $(D7_OUTPUT),) --gold-set-id "$(GOLD_SET_ID)" --dataset-name "$(DATASET_NAME)" --split "$(or $(SPLIT),dev)" --coder-count "$(CODER_COUNT)" --adjudicator "$(ADJUDICATOR)" --protocol "$(PROTOCOL)" $(if $(PREFLIGHT_PROTOCOL),--protocol-package $(PREFLIGHT_PROTOCOL),) $(if $(PREFLIGHT_SAMPLE),--sample-package $(PREFLIGHT_SAMPLE),) $(if $(PROMPT_FROZEN),--prompt-frozen,) $(if $(CONTAMINATION_CHECKED),--contamination-checked,) $(if $(NOTES),--notes "$(NOTES)",)

lint-scope-phrasing:  ## Lint report text for unsafe scope phrasing (ID=<project_id> INPUT=report.md)
ifndef ID
	$(error ID is required. Usage: make lint-scope-phrasing ID=<project_id> INPUT=report.md)
endif
ifndef INPUT
	$(error INPUT is required. Usage: make lint-scope-phrasing ID=<project_id> INPUT=report.md)
endif
	python scripts/lint_scope_phrasing.py $(ID) --input-file $(INPUT) $(if $(PROJECTS_DIR),--projects-dir $(PROJECTS_DIR),)

export-audit-manifest:  ## Write export hash manifest (ID=<project_id> FORMAT=json|csv|markdown|qdpx ARTIFACTS="file..." OUTPUT=manifest.json [AUDIT_LOG=events.jsonl])
ifndef ID
	$(error ID is required. Usage: make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json)
endif
ifndef FORMAT
	$(error FORMAT is required. Usage: make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json)
endif
ifndef ARTIFACTS
	$(error ARTIFACTS is required. Usage: make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json)
endif
ifndef OUTPUT
	$(error OUTPUT is required. Usage: make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json)
endif
	python scripts/write_export_audit_manifest.py $(ID) --format $(FORMAT) $(foreach file,$(ARTIFACTS),--artifact $(file)) --output $(OUTPUT) $(if $(BASE_DIR),--base-dir $(BASE_DIR),) $(if $(PROJECTS_DIR),--projects-dir $(PROJECTS_DIR),) $(if $(AUDIT_LOG),--audit-log $(AUDIT_LOG),)

verify-export-audit-manifest:  ## Verify export hash manifest (MANIFEST=manifest.json [BASE_DIR=exports] [ID=<project_id>] [AUDIT_LOG=events.jsonl])
ifndef MANIFEST
	$(error MANIFEST is required. Usage: make verify-export-audit-manifest MANIFEST=manifest.json)
endif
	python scripts/verify_export_audit_manifest.py $(MANIFEST) $(if $(BASE_DIR),--base-dir $(BASE_DIR),) $(if $(ID),--project-id $(ID),) $(if $(PROJECTS_DIR),--projects-dir $(PROJECTS_DIR),) $(if $(AUDIT_LOG),--audit-log $(AUDIT_LOG),)

export-publish-preflight:  ## Strict publish preflight requiring a valid export manifest (MANIFEST=manifest.json [BASE_DIR=exports] [ID=<project_id>] [AUDIT_LOG=events.jsonl])
ifndef MANIFEST
	$(error MANIFEST is required. Usage: make export-publish-preflight MANIFEST=manifest.json)
endif
	python scripts/export_publish_preflight.py --manifest $(MANIFEST) $(if $(BASE_DIR),--base-dir $(BASE_DIR),) $(if $(ID),--project-id $(ID),) $(if $(PROJECTS_DIR),--projects-dir $(PROJECTS_DIR),) $(if $(AUDIT_LOG),--audit-log $(AUDIT_LOG),)

verify-export-audit-log:  ## Verify local export audit event log (LOG=events.jsonl)
ifndef LOG
	$(error LOG is required. Usage: make verify-export-audit-log LOG=events.jsonl)
endif
	python scripts/verify_export_audit_event_log.py $(LOG)

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

run-inv7-live-fixtures:  ## Run live INV-7 model fixtures (OUTPUT=inv7_live.json [MODEL=gpt-5-mini] [TRACE_ID=id] [MAX_BUDGET=1.0])
ifndef OUTPUT
	$(error OUTPUT is required. Usage: make run-inv7-live-fixtures OUTPUT=inv7_live.json MODEL=<model>)
endif
	python scripts/run_inv7_live_fixtures.py --output $(OUTPUT) $(if $(MODEL),--model $(MODEL),) $(if $(TRACE_ID),--trace-id $(TRACE_ID),) $(if $(MAX_BUDGET),--max-budget $(MAX_BUDGET),)

adjudication-sample:  ## Export an unlabeled adjudication sample package (ID=<project_id> OUTPUT=sample.json [LIMIT=20] [CONTEXT_CHARS=120])
ifndef ID
	$(error ID is required. Usage: make adjudication-sample ID=<project_id> OUTPUT=sample.json)
endif
ifndef OUTPUT
	$(error OUTPUT is required. Usage: make adjudication-sample ID=<project_id> OUTPUT=sample.json)
endif
	python qc_cli.py project adjudication-sample $(ID) --output-file $(OUTPUT) --limit-per-type $(LIMIT) --context-chars $(CONTEXT_CHARS)

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
