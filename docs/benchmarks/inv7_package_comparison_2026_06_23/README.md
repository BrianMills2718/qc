# INV-7 Package Comparison Artifact - 2026-06-23

This directory contains a deterministic comparison report over committed
schema_version=1 INV-7 prompt-injection result packages. It uses the public
`qc_cli.py compare-inv7-packages` surface added for package-level comparison.

## Contents

| File | Purpose |
|------|---------|
| `comparison.json` | Comparison report across selected committed INV-7 packages |

## Inputs

| Package | Fixture count | Split | Why included |
|---------|---------------|-------|--------------|
| `../inv7_live_canary_v2_2026_06_22/result.json` | 5 | canary | Current built-in live canary set, including custom prompt override surfaces |
| `../inv7_external_heldout_smoke_2026_06_23/result.json` | 3 | held_out | First external held-out smoke package |
| `../inv7_heldout_live_v1_2026_06_23/result.json` | 10 | held_out | Broader external held-out live v1 package |

The older `../inv7_live_canary_2026_06_22/result.json` package is intentionally
excluded because it has the same `package_id` as the v2 built-in canary, making
pairwise report rows less clear. Use the v2 canary as the current built-in
baseline.

## Command

```bash
python qc_cli.py compare-inv7-packages \
  docs/benchmarks/inv7_live_canary_v2_2026_06_22/result.json \
  docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/result.json \
  docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json \
  --output docs/benchmarks/inv7_package_comparison_2026_06_23/comparison.json
```

## Result Summary

`comparison.json` reports:

- `status="compared"`
- `package_count=3`
- package fixture counts of 5, 3, and 10
- `failed=0` and `attack_success_rate=0.0` for each compared package
- pairwise fixture comparisons with no shared fixture IDs, because these are
  distinct fixture sets

The pairwise `attack_success_rate_delta` values are all `0.0` because the
compared packages all recorded zero attack successes.

## Caveat

This artifact compares observed outcomes in already committed result packages.
It is not a new live run, not prompt-injection robustness proof, not
model-obedience proof, not methodological-validity evidence, not model/provider
superiority evidence, and not SOTA evidence. Passing these packages does not
mean prompt injection is solved.
