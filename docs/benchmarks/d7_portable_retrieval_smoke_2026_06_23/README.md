# D7 Portable Retrieval Smoke Artifact - 2026-06-23

This directory is a deterministic smoke artifact for the D7 retrieval
comparison workflow. It proves the repo can run a D7 retrieval export and D7
comparison from a repo-local project store without touching the default user
project store.

It is not semantic disconfirmation validity evidence, expert adjudication,
live-baseline evidence, superiority evidence, methodological-validity evidence,
or SOTA evidence.

## Contents

- `projects/d7_portable_retrieval_smoke_project.json` - repo-local synthetic
  `ProjectState`.
- `gold.json` - schema_version=1 D7 gold package for one synthetic contrary
  span.
- `predictions.json` - retrieval baseline package generated with
  `PROJECTS_DIR=projects`.
- `protocol.json` - schema_version=1 D7 comparison protocol with two
  machine-checkable metric criteria.
- `preflight.json` - D7 comparison preflight report.
- `report.json` - comparison report written by `make compare-d7-retrieval`.
- `artifact/.../report.json` and `artifact/.../manifest.json` - versioned D7
  comparison artifact package.
- `verification.json` - artifact verifier output.

## Replay

```bash
make validate-d7-gold GOLD=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/gold.json
make validate-d7-baseline-package PACKAGE=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/predictions.json
make validate-d7-comparison-protocol PROTOCOL=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/protocol.json
make d7-comparison-preflight PROTOCOL=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/protocol.json GOLD=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/predictions.json
make compare-d7-retrieval ID=d7_portable_retrieval_smoke_project PROJECTS_DIR=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/projects GOLD=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/predictions.json PROTOCOL=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/protocol.json OUTPUT=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/report.json ARTIFACT_DIR=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/artifact
make verify-d7-comparison-artifact ARTIFACT=docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/artifact/20260623T213742348279Z-d7_portable_retrieval_smoke_project-d7-comparison/manifest.json
```

## Result Summary

- Gold anchors: 1
- Retrieval baseline: `retrieval_lexical_bm25_top1`
- Baseline recall/precision/F1: 1.0 / 1.0 / 1.0
- Metric criteria: 2 passed, 0 failed
- Comparison preflight: pass
- Artifact verification: verified

The system D7 score in `report.json` is 0.0 because this smoke project did not
run the negative-case stage; the artifact is exercising an externally supplied
retrieval baseline package, not claiming the full system recovered the negative
case.
