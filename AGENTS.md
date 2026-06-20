# Qualitative Coding Analysis System

<!-- GENERATED FILE: DO NOT EDIT DIRECTLY -->
<!-- generated_by: scripts/meta/render_agents_md.py -->
<!-- canonical_claude: CLAUDE.md -->
<!-- canonical_relationships: scripts/relationships.yaml -->
<!-- canonical_relationships_sha256: 840b164dcfa4 -->
<!-- sync_check: python scripts/meta/check_agents_sync.py --check -->

This file is a generated Codex-oriented projection of repo governance.
Edit the canonical sources instead of editing this file directly.

Canonical governance sources:
- `CLAUDE.md` — human-readable project rules, workflow, and references
- `scripts/relationships.yaml` — machine-readable ADR, coupling, and required-reading graph

## Purpose

*Last Updated: 2026-06-20*

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
make test               # Run full test suite
make test-quick         # Run tests, minimal output
make lint               # Run Ruff fatal-error lint gate
make docs-check         # Run documentation and governance checks
make check              # Run deterministic tests + lint + docs checks
make status             # Show git status
make cost               # Show LLM spend (DAYS=7)
make errors             # Show recent error breakdown

# Pipeline
python -m qc analyze interview.txt
python -m qc analyze --methodology grounded_theory interview.txt
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
4. Export to JSON/CSV/Markdown/QDPX

## Machine-Readable Governance

`scripts/relationships.yaml` is the source of truth for machine-readable governance in this repo: ADR coupling, required-reading edges, and doc-code linkage. This generated file does not inline that graph; it records the canonical path and sync marker, then points operators and validators back to the source graph. Prefer deterministic validators over prompt-only memory when those scripts are available.

## References

- `CLAUDE.md` — This file (canonical operating guidance)
- `AGENTS.md` — Generated mirror for non-Claude agents
- `docs/PROJECT_THEORY_AND_GOALS.md` — **Theory, goals, honest state, and the architectural invariants (INV-0..11).** Read its state ledger (§13), invariants (§13.1), and claim-discipline table (§14) before describing the system anywhere. The end product is public and SOTA-targeting; the UNMET invariants are a committed build spec, not a wishlist.
- `docs/EVALUATION_HARNESS.md` — **The keystone**: how we prove SOTA (metrics, gold standards, baselines, `make bench`), built on `prompt_eval`. Roadmap item #1.
- `docs/` — Other design docs and plans
- `scripts/relationships.yaml` — Doc-code coupling graph
