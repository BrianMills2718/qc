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
python qc_cli.py bench-package phase0_package.json  # Run a strict Phase 0 package manifest through the canonical CLI
make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json  # Validate pre-evaluation D4 rubric protocol metadata
make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json  # Preflight D4 result file against protocol
make bench ID=<project_id> D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json  # Guard D4 scoring with protocol preflight
make validate-d6-bias-protocol PROTOCOL=protocol.json  # Validate pre-run D6 bias-audit protocol metadata
make d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=bias_stratified.json COUNTERFACTUAL=bias_counterfactual.json  # Preflight D6 result files against protocol
make bench ID=<project_id> D6_PROTOCOL=protocol.json BIAS_STRATIFIED=bias_stratified.json BIAS_COUNTERFACTUAL=bias_counterfactual.json  # Guard D6 scoring with protocol preflight
make bench ID=<project_id> D9_PROTOCOL=protocol.json PREFERENCE=preference.json  # Guard D9 scoring with protocol preflight
make validate-confidence-calibration-protocol PROTOCOL=protocol.json  # Validate pre-evaluation confidence-calibration protocol metadata
make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json  # Preflight calibration result file against protocol
make bench ID=<project_id> CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json  # Guard calibration scoring with protocol preflight
make bench ID=<project_id> GOLD=gold.json BASELINES=baselines.json  # Add external D7 gold/baselines without mutating project state
make bench ID=<project_id> BIAS_STRATIFIED=bias_stratified.json  # Add external D6 stratified correctness rows without mutating state
make bench ID=<project_id> PROMPT_INJECTION=inv7.json  # Add external INV-7 fixture results without mutating state
make bench ID=<project_id> OBS_DB=path TRACE_ID=trace  # Override D10 observability DB / exact trace
make bench ID=<project_id> ARTIFACT_DIR=benchmark_results  # Write versioned Phase 0 scorecard package
make adjudication-sample ID=<project_id> OUTPUT=sample.json  # Export unlabeled human/expert review sample packet
make validate-adjudication-protocol PROTOCOL=protocol.json  # Validate pre-registered adjudication protocol metadata
make adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json  # Preflight protocol/sample package match before labeling
make validate-adjudication-responses PACKAGE=sample.json  # Validate completed adjudication response package shape/completeness
make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json  # Preflight completed responses against protocol/sample provenance before import
make import-adjudication-responses PACKAGE=sample.json GOLD_SET_ID=study-v1 DATASET_NAME="Study dev labels" CODER_COUNT=1 ADJUDICATOR=coder-1 PROTOCOL="Single adjudicator review" PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json D3_OUTPUT=d3_gold.json D7_OUTPUT=d7_gold.json  # Convert valid responses to D3/D7 gold package inputs with an import-time provenance guard
make write-phase0-adjudication-package ID=<project_id> OUTPUT=phase0_package.json D3_GOLD=d3_gold.json GOLD=d7_gold.json  # Write strict Phase 0 package manifest for imported D3/D7 gold
make lint-scope-phrasing ID=<project_id> INPUT=report.md  # Lint arbitrary text for unsafe population-generalizing scope phrasing
make export-audit-manifest ID=<project_id> FORMAT=markdown ARTIFACTS="report.md" OUTPUT=manifest.json  # Write export artifact hash manifest
make verify-export-audit-manifest MANIFEST=manifest.json BASE_DIR=. ID=<project_id>  # Verify manifest self-hash, artifact hashes, and optional project-state hash
make export-publish-preflight MANIFEST=manifest.json BASE_DIR=. ID=<project_id>  # Strict local publish/handoff preflight requiring a verified export manifest
make verify-export-audit-log LOG=export_audit_events.jsonl  # Verify opt-in local hash-linked export audit event log
make validate-d7-gold GOLD=gold_set.json  # Validate versioned held-out D7 gold-set package
make validate-theoretical-sampling-protocol PROTOCOL=theoretical_sampling_protocol.json  # Validate pre-run theoretical-sampling protocol metadata
make theoretical-sampling-preflight PROTOCOL=theoretical_sampling_protocol.json CANDIDATES=candidates.json RESULTS=results.json  # Preflight theoretical-sampling candidates/results against a protocol
make validate-d7-comparison-protocol PROTOCOL=d7_protocol.json  # Validate pre-run D7 retrieval comparison protocol
make d7-comparison-preflight PROTOCOL=d7_protocol.json GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json"  # Preflight D7 comparison inputs before scoring
make compare-d7-retrieval ID=<project_id> GOLD=d7_gold.json PREDICTIONS="lexical.json embedding.json" PROTOCOL=d7_protocol.json  # Score D7 retrieval predictions with preflight guard
make run-d7-live-baseline ID=<project_id> OUTPUT=live_baseline.json MODEL=<model>  # Write opt-in live D7 candidate-selection baseline package for BASELINES=
python qc_cli.py run-d7-retrieval <project_id> --output predictions.json  # Canonical CLI wrapper for D7 retrieval export
python qc_cli.py run-d7-live-baseline <project_id> --output live_baseline.json --model <model>  # Canonical CLI wrapper for opt-in live D7 baseline export
python qc_cli.py compare-d7-retrieval <project_id> --gold-file d7_gold.json --predictions-file lexical.json --predictions-file embedding.json --protocol-package d7_protocol.json  # Canonical CLI wrapper for D7 retrieval comparison
make run-inv7-fixtures OUTPUT=inv7.json  # Write structural INV-7 fixture package for PROMPT_INJECTION=
make run-inv7-live-fixtures OUTPUT=inv7_live.json MODEL=<model>  # Write opt-in live canary package for PROMPT_INJECTION=
python qc_cli.py run-inv7-fixtures --output inv7.json  # Canonical CLI wrapper for structural INV-7 fixtures
python qc_cli.py run-inv7-live-fixtures --output inv7_live.json --model <model>  # Canonical CLI wrapper for opt-in live INV-7 fixtures
make validate-inv7-live-protocol PROTOCOL=inv7_live_protocol.json  # Validate pre-run live protocol metadata
make inv7-live-preflight PROTOCOL=inv7_live_protocol.json PACKAGE=inv7_live.json  # Preflight live result against protocol before scoring
make validate-inv7-package PACKAGE=inv7.json  # Validate schema_version=1 INV-7 package metadata
make cost               # Show LLM spend (DAYS=7)
make errors             # Show recent error breakdown

# Pipeline (local run; `project run` needs no server, `analyze` needs the API server)
python qc_cli.py project run <project_id>
python qc_cli.py project run <project_id> --exhaustive   # code every segment (INV-8)
python qc_cli.py project scope <project_id> --phenomenon "..."  # show/update corpus scope
python qc_cli.py project claims <project_id>              # inspect first-class claim ledger (INV-9)
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
4. Inspect claim ledger via `project claims` or `/projects/{project_id}/claims`
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
