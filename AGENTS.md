# Qualitative Coding Analysis System

<!-- GENERATED FILE: DO NOT EDIT DIRECTLY -->
<!-- generated_by: scripts/meta/render_agents_md.py -->
<!-- canonical_claude: CLAUDE.md -->
<!-- canonical_relationships: scripts/relationships.yaml -->
<!-- canonical_relationships_sha256: a5ec5ec1be37 -->
<!-- sync_check: python scripts/meta/check_agents_sync.py --check -->

This file is a generated Codex-oriented projection of repo governance.
Edit the canonical sources instead of editing this file directly.

Canonical governance sources:
- `CLAUDE.md` — human-readable project rules, workflow, and references
- `scripts/relationships.yaml` — machine-readable ADR, coupling, and required-reading graph

## Purpose

*Last Updated: 2026-06-22*

> **Canonical status/theory docs (read before describing the system).** This
> file is the **operational** reference (architecture, commands, config). The
> *strategic* layer — honest state ledger, the INV-0..11 architectural
> invariants, the **claim-discipline** table (what you may/may not assert), the
> roadmap, and the prior-art/competitive landscape — lives in
> **`docs/PROJECT_THEORY_AND_GOALS.md`**, and the SOTA-evaluation plan in
> **`docs/EVALUATION_HARNESS.md`**. Where this file and the theory doc disagree
> about *status or claims*, the theory doc wins. Do not assert "validated",
> "full grounded theory", "SOTA", or "inter-rater reliability" without the
> caveats in theory doc §14.

## Commands

```bash
make test               # Run deterministic test suite (excludes live LLM E2E)
make test-quick         # Run tests, minimal output
make test-e2e           # Run live LLM E2E tests
make test-all           # Run deterministic tests and live LLM E2E tests
make lint               # Run Ruff fatal-error lint gate
make docs-check         # Run documentation and governance checks
make check              # Run deterministic tests + lint + docs checks
make status             # Show git status
make bench ID=<project_id>              # Phase 0 scorecard (D1-D10 local accounting substrates)
python qc_cli.py bench <project_id>     # Same Phase 0 scorecard through the canonical CLI; mirrors scripts/bench_phase0.py file/protocol flags
python qc_cli.py bench-package phase0_package.json  # Run a strict Phase 0 package manifest through the canonical CLI, including package-local projects_dir when supplied
make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D4 rubric protocol metadata
make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json  # Preflight D4 result file against protocol
python qc_cli.py validate-d4-codebook-quality-protocol protocol.json  # Canonical CLI wrapper for D4 protocol validation
python qc_cli.py d4-codebook-quality-preflight protocol.json --quality-file quality.json  # Canonical CLI wrapper for D4 protocol/result preflight
make bench ID=<project_id> D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json  # Guard D4 scoring with protocol preflight
make validate-d6-bias-protocol PROTOCOL=protocol.json  # Validate pre-run D6 bias-audit protocol metadata
make d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=bias_stratified.json COUNTERFACTUAL=bias_counterfactual.json  # Preflight D6 result files against protocol
python qc_cli.py validate-d6-bias-protocol protocol.json  # Canonical CLI wrapper for D6 protocol validation
python qc_cli.py d6-bias-preflight protocol.json --stratified-file bias_stratified.json --counterfactual-file bias_counterfactual.json  # Canonical CLI wrapper for D6 protocol/result preflight
make bench ID=<project_id> D6_PROTOCOL=protocol.json BIAS_STRATIFIED=bias_stratified.json BIAS_COUNTERFACTUAL=bias_counterfactual.json  # Guard D6 scoring with protocol preflight
make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D8 GT-fidelity protocol metadata
make d8-gt-fidelity-preflight PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json  # Preflight D8 result file against protocol
python qc_cli.py validate-d8-gt-fidelity-protocol protocol.json  # Canonical CLI wrapper for D8 protocol validation
python qc_cli.py d8-gt-fidelity-preflight protocol.json --gt-fidelity-file gt_fidelity.json  # Canonical CLI wrapper for D8 protocol/result preflight
make bench ID=<project_id> D8_PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json  # Guard D8 scoring with protocol preflight
make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D9 preference protocol metadata
make d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json  # Preflight D9 result file against protocol
python qc_cli.py validate-d9-interpretive-preference-protocol protocol.json  # Canonical CLI wrapper for D9 protocol validation
python qc_cli.py d9-interpretive-preference-preflight protocol.json --preference-file preference.json  # Canonical CLI wrapper for D9 protocol/result preflight
make bench ID=<project_id> D9_PROTOCOL=protocol.json PREFERENCE=preference.json  # Guard D9 scoring with protocol preflight
make validate-confidence-calibration-protocol PROTOCOL=protocol.json  # Validate pre-evaluation confidence-calibration protocol metadata
make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json  # Preflight calibration result file against protocol
python qc_cli.py validate-confidence-calibration-protocol protocol.json  # Canonical CLI wrapper for confidence-calibration protocol validation
python qc_cli.py confidence-calibration-preflight protocol.json --calibration-file calibration.json  # Canonical CLI wrapper for confidence-calibration protocol/result preflight
make bench ID=<project_id> CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json  # Guard calibration scoring with protocol preflight
make bench ID=<project_id> GOLD=gold.json BASELINES=baselines.json  # Add external D7 gold/baselines without mutating project state
make bench ID=<project_id> BIAS_STRATIFIED=bias_stratified.json  # Add external D6 stratified correctness rows without mutating state
make bench ID=<project_id> PROMPT_INJECTION=inv7.json  # Add external INV-7 fixture results without mutating state
make bench ID=<project_id> PROMPT_INJECTION=inv7.json INV7_PROTOCOL=inv7_live_protocol.json  # Score INV-7 with live protocol preflight guard
make bench ID=<project_id> OBS_DB=path TRACE_ID=trace  # Override D10 observability DB / exact trace
make bench ID=<project_id> ARTIFACT_DIR=benchmark_results  # Write versioned Phase 0 scorecard package
make verify-phase0-benchmark-artifact ARTIFACT=benchmark_results/run-dir  # Verify Phase 0 artifact scorecard/timing/manifest hashes
make adjudication-sample ID=<project_id> OUTPUT=sample.json  # Export unlabeled human/expert review sample packet
make validate-adjudication-protocol PROTOCOL=protocol.json  # Validate pre-registered adjudication protocol metadata
python qc_cli.py validate-adjudication-protocol protocol.json  # Canonical CLI wrapper for protocol validation
make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json  # Preflight protocol/sample package match before labeling
python qc_cli.py adjudication-protocol-preflight protocol.json sample.json  # Canonical CLI wrapper for protocol/sample preflight
make validate-adjudication-responses PACKAGE=sample.json  # Validate completed adjudication response package shape/completeness
python qc_cli.py validate-adjudication-responses responses.json  # Canonical CLI wrapper for response validation
make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json  # Preflight completed responses against protocol/sample provenance before import
python qc_cli.py adjudication-response-preflight protocol.json sample.json responses.json  # Canonical CLI wrapper for response preflight
make import-adjudication-responses PACKAGE=sample.json GOLD_SET_ID=study-v1 DATASET_NAME="Study dev labels" CODER_COUNT=1 ADJUDICATOR=coder-1 PROTOCOL="Single adjudicator review" PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json D3_OUTPUT=d3_gold.json D7_OUTPUT=d7_gold.json  # Convert valid responses to D3/D7 gold package inputs with an import-time provenance guard
python qc_cli.py import-adjudication-responses responses.json --gold-set-id study-v1 --dataset-name "Study dev labels" --coder-count 1 --adjudicator coder-1 --protocol "Single adjudicator review" --protocol-package protocol.json --sample-package sample.json --output-d3 d3_gold.json --output-d7 d7_gold.json  # Canonical CLI wrapper for guarded response import
make write-phase0-adjudication-package ID=<project_id> OUTPUT=phase0_package.json D3_GOLD=d3_gold.json GOLD=d7_gold.json  # Write strict Phase 0 package manifest for imported D3/D7 gold
python qc_cli.py write-phase0-adjudication-package <project_id> --output phase0_package.json --d3-gold-file d3_gold.json --gold-file d7_gold.json  # Canonical CLI wrapper for Phase 0 adjudication package manifests
make lint-scope-phrasing ID=<project_id> INPUT=report.md  # Lint arbitrary text for unsafe population-generalizing scope phrasing
python qc_cli.py lint-scope-phrasing <project_id> --input-file report.md  # Canonical CLI wrapper for scope phrasing lint
make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json AUDIT_LOG=events.jsonl AUDIT_DB=events.sqlite  # Write export artifact hash manifest and optional audit event mirror
make verify-export-audit-manifest MANIFEST=manifest.json BASE_DIR=. ID=<project_id> AUDIT_LOG=events.jsonl AUDIT_DB=events.sqlite  # Verify manifest and optionally mirror the verification event
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id> AUDIT_LOG=events.jsonl AUDIT_DB=events.sqlite  # Strict local publish/handoff preflight with optional mirrored event
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id> SCOPE_LINT=1  # Also block risky Markdown/text scope phrasing before handoff
make verify-export-audit-log LOG=export_audit_events.jsonl  # Verify opt-in local hash-linked export audit event log
make mirror-export-audit-db LOG=export_audit_events.jsonl DB=export_audit_events.sqlite  # Mirror verified event log into local SQLite
make verify-export-audit-db DB=export_audit_events.sqlite  # Verify local SQLite export audit event mirror
python qc_cli.py export-audit-manifest <project_id> --format markdown --artifact report.md --output manifest.json --audit-log events.jsonl --audit-db events.sqlite  # Canonical CLI wrapper for export audit manifest writing
python qc_cli.py verify-export-audit-manifest manifest.json --base-dir . --project-id <project_id> --audit-log events.jsonl --audit-db events.sqlite  # Canonical CLI wrapper for export audit manifest verification
python qc_cli.py export-publish-preflight --manifest manifest.json --base-dir . --project-id <project_id> --audit-log events.jsonl --audit-db events.sqlite  # Canonical CLI wrapper for export publish preflight
python qc_cli.py export-publish-preflight --manifest manifest.json --base-dir . --project-id <project_id> --scope-lint  # Canonical CLI wrapper with optional scope phrasing preflight
python qc_cli.py project export <project_id> --format markdown --output-file report.md --audit-manifest manifest.json --publish-preflight --scope-lint  # Inline export manifest + publish preflight gate
python qc_cli.py verify-export-audit-log export_audit_events.jsonl  # Canonical CLI wrapper for export audit event-log verification
python qc_cli.py mirror-export-audit-db export_audit_events.jsonl --db export_audit_events.sqlite  # Canonical CLI wrapper for export audit SQLite mirroring
python qc_cli.py verify-export-audit-db export_audit_events.sqlite  # Canonical CLI wrapper for export audit SQLite verification
make validate-d3-baseline-package PACKAGE=d3_baseline.json  # Validate versioned D3 application baseline package
make validate-d3-comparison-protocol PROTOCOL=d3_protocol.json  # Validate pre-run D3 baseline comparison protocol, including optional metric criteria
make d3-comparison-preflight PROTOCOL=d3_protocol.json GOLD=d3_gold.json PREDICTIONS="baseline.json"  # Preflight D3 comparison inputs before scoring
make bench ID=<project_id> D3_GOLD=d3_gold.json D3_BASELINES=d3_baselines.json D3_PROTOCOL=d3_protocol.json  # Guard D3 baseline comparison scoring with protocol preflight and metric-criteria report when configured
python qc_cli.py validate-d3-baseline-package d3_baseline.json  # Canonical CLI wrapper for D3 baseline package validation
python qc_cli.py validate-d3-comparison-protocol d3_protocol.json  # Canonical CLI wrapper for D3 comparison protocol validation
python qc_cli.py d3-comparison-preflight d3_protocol.json d3_gold.json baseline.json  # Canonical CLI wrapper for D3 comparison preflight
make validate-d7-gold GOLD=gold_set.json  # Validate versioned held-out D7 gold-set package
make validate-d7-baseline-package PACKAGE=d7_baseline.json  # Validate versioned D7 retrieval/live baseline package
python qc_cli.py validate-d7-baseline-package d7_baseline.json  # Canonical CLI wrapper for D7 baseline package validation
make validate-theoretical-sampling-protocol PROTOCOL=theoretical_sampling_protocol.json  # Validate pre-run theoretical-sampling protocol metadata
python qc_cli.py validate-theoretical-sampling-protocol theoretical_sampling_protocol.json  # Canonical CLI wrapper for theoretical-sampling protocol validation
make export-theoretical-sampling-candidates ID=<project_id> PROTOCOL=theoretical_sampling_protocol.json OUTPUT=candidates.json  # Export loaded-document theoretical-sampling candidates
python qc_cli.py export-theoretical-sampling-candidates <project_id> --protocol theoretical_sampling_protocol.json --output candidates.json  # Canonical CLI wrapper for candidate export
make export-theoretical-sampling-results PROTOCOL=theoretical_sampling_protocol.json CANDIDATES=candidates.json SELECTED=loaded-doc-1 SUCCESS_CRITERION="..." OUTPUT=results.json  # Export selected theoretical-sampling candidates as a result package
python qc_cli.py export-theoretical-sampling-results theoretical_sampling_protocol.json --candidates-file candidates.json --selected-candidate-id loaded-doc-1 --success-criterion-met "..." --output results.json  # Canonical CLI wrapper for result export
make theoretical-sampling-preflight PROTOCOL=theoretical_sampling_protocol.json CANDIDATES=candidates.json RESULTS=results.json  # Preflight theoretical-sampling candidates/results against a protocol
python qc_cli.py theoretical-sampling-preflight theoretical_sampling_protocol.json --candidates-file candidates.json --results-file results.json  # Canonical CLI wrapper for theoretical-sampling preflight
make validate-d7-comparison-protocol PROTOCOL=d7_protocol.json  # Validate pre-run D7 retrieval comparison protocol, including optional metric criteria
make d7-comparison-preflight PROTOCOL=d7_protocol.json GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json"  # Preflight D7 comparison inputs before scoring
make compare-d7-retrieval ID=<project_id> GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json" PROJECTS_DIR=projects PROTOCOL=d7_protocol.json ARTIFACT_DIR=benchmark_results  # Score D7 retrieval predictions with preflight guard, metric-criteria report when configured, input-hash provenance, and optional artifact package
make write-d7-comparison-package ID=<project_id> GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json" OUTPUT=d7_comparison_package.json PROJECTS_DIR=projects  # Write strict D7 comparison package manifest after validation/preflight, including package-local projects_dir when supplied
make compare-d7-package PACKAGE=d7_comparison_package.json  # Run D7 retrieval comparison from a strict package manifest
make verify-d7-comparison-artifact ARTIFACT=benchmark_results/run-dir  # Verify D7 comparison artifact report/manifest hashes
make run-d7-retrieval ID=<project_id> OUTPUT=predictions.json PROJECTS_DIR=projects  # Export D7 retrieval predictions from an explicit project store
make run-d7-live-baseline ID=<project_id> OUTPUT=live_baseline.json PROJECTS_DIR=projects MODEL=<model>  # Write opt-in live D7 candidate-selection baseline package for BASELINES=
python qc_cli.py run-d7-retrieval <project_id> --projects-dir projects --output predictions.json  # Canonical CLI wrapper for D7 retrieval export
python qc_cli.py run-d7-live-baseline <project_id> --projects-dir projects --output live_baseline.json --model <model>  # Canonical CLI wrapper for opt-in live D7 baseline export
python qc_cli.py validate-d7-comparison-protocol d7_protocol.json  # Canonical CLI wrapper for D7 comparison protocol validation
python qc_cli.py d7-comparison-preflight d7_protocol.json d7_gold.json lexical.json embedding.json  # Canonical CLI wrapper for D7 comparison preflight
python qc_cli.py compare-d7-retrieval <project_id> --projects-dir projects --gold-file d7_gold.json --predictions-file lexical.json --predictions-file embedding.json --protocol-package d7_protocol.json --artifact-dir benchmark_results  # Canonical CLI wrapper for D7 retrieval comparison
python qc_cli.py write-d7-comparison-package <project_id> --projects-dir projects --output d7_comparison_package.json --gold-file d7_gold.json --predictions-file lexical.json  # Canonical CLI wrapper for D7 comparison package writer
python qc_cli.py compare-d7-package d7_comparison_package.json  # Canonical CLI wrapper for D7 comparison package runner
python qc_cli.py verify-d7-comparison-artifact benchmark_results/run-dir/manifest.json  # Canonical CLI wrapper for D7 comparison artifact verification
make run-inv7-fixtures OUTPUT=inv7.json  # Write structural INV-7 fixture package for PROMPT_INJECTION=
make run-inv7-live-fixtures OUTPUT=inv7_live.json MODEL=<model>  # Write opt-in live canary package for PROMPT_INJECTION=
make run-inv7-live-fixtures OUTPUT=inv7_live.json MODEL=<model> FIXTURES=manifest.json  # Run an external INV-7 live fixture manifest
python qc_cli.py run-inv7-fixtures --output inv7.json  # Canonical CLI wrapper for structural INV-7 fixtures
python qc_cli.py run-inv7-live-fixtures --output inv7_live.json --model <model>  # Canonical CLI wrapper for opt-in live INV-7 fixtures
python qc_cli.py run-inv7-live-fixtures --output inv7_live.json --model <model> --fixtures manifest.json  # Canonical CLI wrapper for external live fixture manifests
make validate-inv7-live-protocol PROTOCOL=inv7_live_protocol.json  # Validate pre-run live protocol metadata
make inv7-live-preflight PROTOCOL=inv7_live_protocol.json PACKAGE=inv7_live.json  # Preflight live result against protocol before scoring
make validate-inv7-package PACKAGE=inv7.json  # Validate schema_version=1 INV-7 package metadata
python qc_cli.py validate-inv7-package inv7.json  # Canonical CLI wrapper for INV-7 package validation
python qc_cli.py validate-inv7-live-protocol inv7_live_protocol.json  # Canonical CLI wrapper for INV-7 live protocol validation
python qc_cli.py inv7-live-preflight inv7_live_protocol.json inv7_live.json  # Canonical CLI wrapper for INV-7 live preflight
python qc_cli.py validate-d3-gold d3_gold.json  # Canonical CLI wrapper for D3 gold package validation
python qc_cli.py validate-d7-gold d7_gold.json  # Canonical CLI wrapper for D7 gold package validation
make lint-prompt-overrides  # Check prompt override source uses against registry declarations
python qc_cli.py lint-prompt-overrides --root qc_clean  # Canonical CLI wrapper for prompt override registry lint
make cost               # Show LLM spend (DAYS=7)
make errors             # Show recent error breakdown

# Pipeline (local run; `project run` needs no server, `analyze` needs the API server)
python qc_cli.py project run <project_id>
python qc_cli.py project run <project_id> --exhaustive   # code every segment (INV-8)
python qc_cli.py project scope <project_id> --phenomenon "..."  # show/update corpus scope
python qc_cli.py project claims <project_id> --limit 20 --offset 0 --show-scope --show-anchors  # inspect first-class claim ledger scope/anchors (INV-9)
python qc_cli.py project add-docs <project_id> --files new.txt --recode  # add then incremental recode
```

## Operating Rules

This projection keeps the highest-signal rules in always-on Codex context.
For full project structure, detailed terminology, and any rule omitted here,
read `CLAUDE.md` directly.

### Principles

- LLM-first: all semantic analysis uses structured LLM output via Pydantic schemas + JSON mode
- Fail loud: inter-stage dependency checks raise on failure; never silently degrade
- Single state model: `ProjectState` Pydantic model holds all state, saved/loaded as JSON
- Observability: all LLM calls log model/schema/prompt/cost/token usage via llm_client

### Workflow

1. Feed transcript files (txt/docx/pdf/rtf) to the pipeline
2. Default 7-stage pipeline: Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Cross-Interview → Negative Case (disconfirmation runs last; INV-6)
3. Human review via CLI or browser; IRR via `project irr`
4. Inspect claim ledger via `project claims` or `/projects/{project_id}/claims?limit=100&offset=0`
5. Export to JSON/CSV/Markdown/QDPX

## Machine-Readable Governance

`scripts/relationships.yaml` is the source of truth for machine-readable governance in this repo: ADR coupling, required-reading edges, and doc-code linkage. This generated file does not inline that graph; it records the canonical path and sync marker, then points operators and validators back to the source graph. Prefer deterministic validators over prompt-only memory when those scripts are available.

## References

- `CLAUDE.md` — This file (canonical operating guidance)
- `AGENTS.md` — Generated mirror for non-Claude agents
- `docs/PROJECT_THEORY_AND_GOALS.md` — **Theory, goals, honest state, and the architectural invariants (INV-0..11).** Read its state ledger (§13), invariants (§13.1), and claim-discipline table (§14) before describing the system anywhere. The end product is public and SOTA-targeting; the UNMET invariants are a committed build spec, not a wishlist.
- `docs/EVALUATION_HARNESS.md` — **The keystone**: how we prove SOTA (metrics, gold standards, baselines, `make bench`), built on `prompt_eval`. Roadmap item #1.
- `docs/` — Other design docs and plans
- `scripts/relationships.yaml` — Doc-code coupling graph
