# Implementation Plans

Track all implementation work here.

## Active Plans

| # | Name | Priority | Status | Plan doc |
|---|------|----------|--------|----------|
| 26 | D7 baseline comparison | High | Planned | `D7_BASELINE_COMPARISON.md` |

## Completed Plans

| Name | Outcome | Record |
|------|---------|--------|
| INV-1 span anchoring + harness Phase 0 | INV-1 mostly met; `make bench` Phase 0 stood up | `completed/INV1_OVERNIGHT_SPRINT.md` |
| INV-8 segment universe + exhaustive coding | INV-8 met in exhaustive mode (`--exhaustive`); coverage denominator | `completed/INV8_SEGMENT_UNIVERSE.md` |
| Application-level IRR | `project irr --application-level` reports positive segment x code agreement plus segment-decision agreement | `completed/IRR_APPLICATION_LEVEL.md` |
| INV-9 first-class claim ledger | INV-9 object layer mostly met; claims emitted/read across stages and surfaces | `completed/INV9_CLAIM_LEDGER.md` |
| INV-6 ledger-wide disconfirmation and claim review | INV-6/INV-10 first slice: negative-case targets claim ledger IDs; claim review decisions supported | `completed/INV6_LEDGER_DISCONFIRMATION.md` |
| INV-7 instruction/data separation | INV-7 first slice: raw transcript/segment prompt data is line-prefixed as untrusted; prompt-injection regressions added | `completed/INV7_INSTRUCTION_DATA_SEPARATION.md` |
| INV-2 retrieval-first disconfirmation | INV-2 first slice: negative-case analysis retrieves anchored candidate passages before LLM interpretation | `completed/INV2_RETRIEVAL_FIRST_DISCONFIRMATION.md` |
| INV-2 adversarial disconfirmation model routing | INV-2 follow-up: configurable disconfirmation model override and adversarial evidence-bound prompt stance | `completed/INV2_ADVERSARIAL_DISCONFIRMATION_MODEL.md` |
| INV-7 derived-output prompt boundaries | INV-7 follow-up: downstream LLM/codebook artifacts are also line-prefixed as untrusted data | `completed/INV7_DERIVED_OUTPUT_PROMPT_BOUNDARIES.md` |
| INV-2 D7 disconfirmation scorecard | Evaluation-harness follow-up: `make bench` reports exact-anchor D7 recall/precision/F1 when adjudicated contrary-evidence gold is supplied | `completed/INV2_D7_DISCONFIRMATION_SCORECARD.md` |
| INV-2 BM25 disconfirmation retrieval | INV-2 follow-up: disconfirmation candidate retrieval uses configurable BM25-style lexical scoring plus contrary-cue boosts | `completed/INV2_BM25_DISCONFIRMATION_RETRIEVAL.md` |
| INV-2 D7 gold file bench input | Evaluation-harness follow-up: `make bench ID=<project> GOLD=gold.json` feeds external D7 gold without mutating project state | `completed/INV2_D7_GOLD_FILE_BENCH_INPUT.md` |
| INV-7 prompt override guards | INV-7 follow-up: current prompt override surfaces fail loudly if required protected data placeholders are omitted | `completed/INV7_PROMPT_OVERRIDE_GUARDS.md` |
| INV-4 category saturation diagnostic | INV-4 first slice: `make bench` reports diagnostic-only category property/dimension/support adequacy separately from codebook stability | `completed/INV4_CATEGORY_SATURATION_DIAGNOSTIC.md` |
| INV-4 diagnostic-driven theoretical sampling | INV-4 follow-up: sampling suggestions use category adequacy gaps before falling back to low application coverage | `completed/INV4_DIAGNOSTIC_THEORETICAL_SAMPLING.md` |
| Corpus scope contract | Report-boundary first slice: optional `ProjectState.corpus_scope` records scope and Markdown export surfaces it before claims | `completed/CORPUS_SCOPE_CONTRACT.md` |
| INV-2 query-expansion disconfirmation retrieval | INV-2 follow-up: BM25-style retrieval can use weighted deterministic query-expansion terms while preserving exact candidate anchors | `completed/INV2_QUERY_EXPANSION_DISCONFIRMATION_RETRIEVAL.md` |
| D7 Wilson intervals | Evaluation-harness follow-up: gold-dependent D7 recall/precision now include 95% Wilson intervals in `make bench` | `completed/D7_WILSON_INTERVALS.md` |
| Corpus scope CLI/API surfaces | Scope contract follow-up: `project scope` and `/projects/{id}/scope` read/update `ProjectState.corpus_scope` | `completed/CORPUS_SCOPE_CLI_API.md` |
| Missing corpus scope report warning | Scope/report follow-up: Markdown claim reports without corpus scope now warn not to generalize beyond loaded documents | `completed/CORPUS_SCOPE_MISSING_REPORT_WARNING.md` |
| INV-7 prompt injection scorecard | Evaluation-harness follow-up: `make bench` can score externally supplied prompt-injection fixture outcomes without mutating project state | `completed/INV7_PROMPT_INJECTION_SCORECARD.md` |
| INV-11 incremental hard invalidation | Incremental recode now clears stale higher-order outputs, stale phase results, and stale claim rows it cannot recompute | `completed/INV11_INCREMENTAL_HARD_INVALIDATION.md` |
| INV-11 review decisions inactive on invalidation | Review decisions targeting claims removed by incremental invalidation are retained as inactive audit history | `completed/INV11_REVIEW_DECISION_INACTIVE_ON_INVALIDATION.md` |
| Review summary active inactive counts | Review summaries and CLI now distinguish active decisions from historical inactive decisions | `completed/REVIEW_SUMMARY_ACTIVE_INACTIVE_COUNTS.md` |
| D10 cost latency scorecard | Evaluation-harness follow-up: `make bench` now reports D10 cost/latency from real llm_client observability rows | `completed/D10_COST_LATENCY_SCORECARD.md` |

## Status Key

| Status | Meaning |
|--------|---------|
| Planned | Ready to implement |
| In Progress | Being worked on |
| Blocked | Waiting on dependency |
| Complete | Implemented and verified |

## Creating a New Plan

1. Copy `TEMPLATE.md` to a descriptive `NAME.md` (e.g. `INV9_CLAIM_LEDGER.md`)
2. Fill in gap, steps, required tests
3. Add a row to the **Active Plans** table above
4. Commit with a `[Plan: NAME]` prefix

## Trivial Changes

Not everything needs a plan. Use `[Trivial]` for:
- Less than 20 lines changed
- No changes to `src/` (production code)
- No new files created

```bash
git commit -m "[Trivial] Fix typo in README"
```

## Completing Plans

1. Move the plan doc to `completed/NAME.md` (add a one-paragraph outcome + verification evidence at the top)
2. Remove its row from **Active Plans** and add one to **Completed Plans** pointing at `completed/NAME.md`
3. `python scripts/sync_plan_status.py --check` (run by `make docs-check`) verifies every Completed row resolves and every record file is listed
