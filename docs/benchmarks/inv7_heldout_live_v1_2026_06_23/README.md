# INV-7 Held-Out Live V1 Artifact - 2026-06-23

This directory contains a broader external held-out live INV-7
prompt-injection fixture artifact. The fixtures are supplied through
`manifest.json`, not the built-in canary fixture definitions.

## Contents

| File | Purpose |
|------|---------|
| `manifest.json` | External schema_version=1 live fixture manifest |
| `protocol.json` | Pre-run held-out protocol metadata with exact manifest prompt hashes |
| `result.json` | Live `gpt-5-mini` result package produced from the manifest |
| `preflight.json` | Protocol/result cross-check report |
| `scorecard.json` | Phase 0 scorecard generated from `result.json` with INV-7 preflight guard |
| `projects/inv7_heldout_live_v1_project.json` | Minimal synthetic project shell used only so Phase 0 can score the external package |

## Commands

```bash
make validate-inv7-live-protocol PROTOCOL=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json
make run-inv7-live-fixtures OUTPUT=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json MODEL=gpt-5-mini TRACE_ID=qualitative_coding/inv7-heldout-live-v1-2026-06-23 MAX_BUDGET=2.0 FIXTURES=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/manifest.json
make validate-inv7-package PACKAGE=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json
make inv7-live-preflight PROTOCOL=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json PACKAGE=docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json
python scripts/bench_phase0.py inv7_heldout_live_v1_project --projects-dir docs/benchmarks/inv7_heldout_live_v1_2026_06_23/projects --prompt-injection-file docs/benchmarks/inv7_heldout_live_v1_2026_06_23/result.json --inv7-live-protocol-file docs/benchmarks/inv7_heldout_live_v1_2026_06_23/protocol.json --trace-id qualitative_coding/inv7-heldout-live-v1-2026-06-23 --output docs/benchmarks/inv7_heldout_live_v1_2026_06_23/scorecard.json
```

## Result

The live result package contains 10 external held-out fixtures. All 10 passed
in this run: `scorecard.json` reports `attack_success_rate=0.0`, with a Wilson
upper bound of approximately `0.2775`.

The fixture set covers:

- `direct_instruction_override`
- `roleplay_authority_override`
- `markdown_fence_instruction`
- `json_role_spoof`
- `xml_system_tag_spoof`
- `html_comment_instruction`
- `yaml_frontmatter_instruction`
- `tool_output_instruction`
- `delimiter_breakout`
- `obfuscated_instruction`

The scorecard records `_meta.preflight_reports.inv7_live.status="pass"`.

The D10 cost section remains `not_available` because no matching `llm_calls`
rows were found for the exact trace selector in the configured observability
database. The runner printed provider-cost fallback estimates during execution,
but those are not used as D10 evidence here.

## Caveat

This is broader than the 3-fixture external held-out smoke artifact, but it is
still not proof of prompt-injection robustness, model obedience, security
hardening, methodological validity, or SOTA. Passing this artifact does not
mean prompt injection is solved.
