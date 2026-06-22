# INV-7 Live Canary Artifact - 2026-06-22

This directory contains the first committed live INV-7 prompt-injection canary
artifact for the built-in fixture set.

## Contents

| File | Purpose |
|------|---------|
| `protocol.json` | Pre-run protocol metadata with exact built-in fixture prompt hashes |
| `result.json` | Live `gpt-5-mini` canary result package |
| `preflight.json` | Protocol/result cross-check report |
| `scorecard.json` | Phase 0 scorecard generated from `result.json` |
| `projects/inv7_canary_project.json` | Minimal synthetic project shell used only so Phase 0 can score the external package |

## Commands

```bash
make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_live_canary_2026_06_22/protocol.json
make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_live_canary_2026_06_22/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-live-canary-2026-06-22 MAX_BUDGET=0.25
make validate-inv7-package PACKAGE=docs/benchmarks/inv7_live_canary_2026_06_22/result.json
make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_live_canary_2026_06_22/protocol.json PACKAGE=docs/benchmarks/inv7_live_canary_2026_06_22/result.json
python scripts/bench_phase0.py inv7_canary_project --projects-dir docs/benchmarks/inv7_live_canary_2026_06_22/projects --prompt-injection-file docs/benchmarks/inv7_live_canary_2026_06_22/result.json --trace-id qualitative_coding/inv7-live-canary-2026-06-22 --output docs/benchmarks/inv7_live_canary_2026_06_22/scorecard.json
```

## Result

The live canary package contains 3 built-in fixtures. All 3 passed in this run:
`scorecard.json` reports `attack_success_rate=0.0`, with a Wilson upper bound
of approximately `0.5615` because the denominator is only 3.

The D10 cost section remains `not_available` because no matching `llm_calls`
rows were found for the canary trace in the configured observability database.
No cost was estimated.

## Caveat

This is a small canary artifact, not a held-out adversarial benchmark. It is not
prompt-injection robustness evidence, model-obedience proof, methodological
validity evidence, or a SOTA claim.
