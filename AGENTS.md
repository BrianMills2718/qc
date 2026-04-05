# Qualitative Coding Analysis System (v2.2)

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

*Last Updated: 2026-04-05*

## Commands

```bash
make test               # Run full test suite
make test-quick         # Run tests, minimal output
make check              # Run tests + type check + lint
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
2. Default 7-stage pipeline: Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Negative Case → Cross-Interview
3. Human review via CLI or browser; IRR via `project irr`
4. Export to JSON/CSV/Markdown/QDPX

## Machine-Readable Governance

`scripts/relationships.yaml` is the source of truth for machine-readable governance in this repo: ADR coupling, required-reading edges, and doc-code linkage. This generated file does not inline that graph; it records the canonical path and sync marker, then points operators and validators back to the source graph. Prefer deterministic validators over prompt-only memory when those scripts are available.

## References

- `CLAUDE.md` — This file (canonical operating guidance)
- `AGENTS.md` — Generated mirror for non-Claude agents
- `docs/` — Design docs and plans
- `scripts/relationships.yaml` — Doc-code coupling graph
