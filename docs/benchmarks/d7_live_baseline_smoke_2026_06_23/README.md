# D7 Live Baseline Smoke Artifact - 2026-06-23

This directory is a synthetic smoke artifact for the D7 live candidate-selection
baseline workflow. It proves the repo can export an opt-in live D7 baseline from
a repo-local project store, validate it, preflight it against versioned D7 gold,
compare it, verify the comparison artifact, and replay the same comparison from
a strict package manifest.

It is not held-out D7 validity evidence, live-baseline quality evidence,
semantic disconfirmation validity evidence, superiority evidence,
methodological-validity evidence, or SOTA evidence.

## Contents

- `projects/d7_live_baseline_smoke_project.json` - repo-local synthetic
  `ProjectState`.
- `gold.json` - schema_version=1 D7 gold package for one synthetic contrary
  span.
- `live_baseline.json` - live `gpt-5-mini` candidate-selection baseline package
  generated with `PROJECTS_DIR=projects`.
- `protocol.json` - schema_version=1 D7 comparison protocol with expected live
  baseline hash and metric criteria.
- `preflight.json` - D7 comparison preflight report.
- `report.json` - direct comparison report written by
  `make compare-d7-retrieval`.
- `package.json` - strict D7 comparison package manifest with package-local
  `projects_dir`.
- `package_report.json` - package-writer report.
- `package_replay_report.json` - comparison report written by
  `compare-d7-package`.
- `artifact/.../report.json` and `artifact/.../manifest.json` - versioned D7
  comparison artifact package.
- `verification.json` - artifact verifier output.

## Replay

```bash
make validate-d7-baseline-package PACKAGE=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json
make validate-d7-gold GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json
make validate-d7-comparison-protocol PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json
make d7-comparison-preflight PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json
make compare-d7-retrieval ID=d7_live_baseline_smoke_project PROJECTS_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects GOLD=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json PREDICTIONS=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json PROTOCOL=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json OUTPUT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/report.json ARTIFACT_DIR=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/artifact
make verify-d7-comparison-artifact ARTIFACT=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/artifact/20260623T220928828002Z-d7_live_baseline_smoke_project-d7-comparison/manifest.json
python scripts/write_d7_comparison_package.py d7_live_baseline_smoke_project --projects-dir docs/benchmarks/d7_live_baseline_smoke_2026_06_23/projects --output docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json --gold-file docs/benchmarks/d7_live_baseline_smoke_2026_06_23/gold.json --predictions-file docs/benchmarks/d7_live_baseline_smoke_2026_06_23/live_baseline.json --protocol-package docs/benchmarks/d7_live_baseline_smoke_2026_06_23/protocol.json --comparison-output package_replay_report.json
make compare-d7-package PACKAGE=docs/benchmarks/d7_live_baseline_smoke_2026_06_23/package.json
```

## Result Summary

- Gold anchors: 1
- Live baseline: `live_candidate_selector_gpt_5_mini_lexical_bm25_top1`
- Live baseline selected candidates: 1
- Baseline recall/precision/F1: 1.0 / 1.0 / 1.0
- Metric criteria: 2 passed, 0 failed
- Comparison preflight: pass
- Strict package replay: pass
- Artifact verification: verified

The system D7 score in `report.json` is 0.0 because this smoke project did not
run the negative-case stage; the artifact is exercising an externally supplied
live baseline package, not claiming the full system recovered the negative case.
