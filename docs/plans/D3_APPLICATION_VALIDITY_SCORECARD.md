# Plan #36: D3 Application Validity Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Held-out D3 application-validity evaluation; prompt_eval-backed expert-parity comparisons

---

## Gap

**Current:** The evaluation harness describes D3 application validity against
adjudicated gold, but Phase 0 has no input contract or scorecard for gold
code-to-source assignments. The repo can report grounding/coverage/reliability,
but not exact agreement with a human-coded application gold file.

**Target:** Add a gold-dependent exact span+code D3 scorecard section to
`make bench`, fed from `ProjectState.config.extra["application_gold"]` or an
external `--d3-gold-file`, without mutating saved state.

**Why:** This creates the first deterministic measurement substrate for
application correctness. It is intentionally narrower than the full D3 target:
no κ/α/AC1, no IoU/Hausdorff, no human ceiling, and no validity claim until
adjudicated held-out gold exists.

---

## References Reviewed

- `qc_clean/schemas/domain.py` - `CodeApplication` fields (`code_id`, `doc_id`,
  `start_char`, `end_char`, `quote_text`).
- `qc_clean/core/bench.py` - existing Phase 0 scorecard and D7 exact-anchor
  scoring pattern.
- `scripts/bench_phase0.py` - external benchmark file input and input-hash
  provenance.
- `qc_cli.py` - `bench` wrapper flags.
- `docs/EVALUATION_HARNESS.md` - D3 metric definition and current Phase 0 status.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D3 application validity gold code applications exact scoring' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a deterministic
scorecard substrate, not the full D3 methodology implementation.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `application_validity_d3_scorecard(state)` | `ProjectState` with optional application gold metadata | D3 exact score dict | qualitative_coding | `phase0_scorecard`, `make bench`, `qc_cli.py bench` | free |

### Capability Validation

- [ ] Gold input is validated with Pydantic fields and fail-loud duplicate keys.
- [ ] External gold is applied to a deep copy by the CLI and does not mutate saved
  project state.
- [ ] Scorecard reports exact TP/FP/FN, precision, recall, F1, and unscored
  system applications.

---

## Files Affected

- `qc_clean/core/d3_gold.py` (create)
- `qc_clean/core/bench.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `tests/test_qc_cli_bench.py` (modify if needed)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `ApplicationGoldAnchor` validation helpers for exact D3 gold anchors:
   `code_id`, `doc_id`, `start_char`/`end_char` or future `segment_id`, and
   optional `quote_text`.
2. Add `application_validity_d3_scorecard(state)` to `qc_clean/core/bench.py`.
   It reports `not_available` without gold and exact span+code TP/FP/FN when
   gold exists.
3. Extend `scripts/bench_phase0.py`, `qc_cli.py bench`, and `make bench` with
   `--d3-gold-file` / `D3_GOLD=...`; include the D3 file hash in input hashes.
4. Add tests for scored D3, missing gold, invalid/duplicate gold, external file
   input without saved-state mutation, and CLI flag pass-through.
5. Update docs conservatively: D3 exact span+code scoring exists, but full D3
   validity, κ/α/AC1, span-overlap metrics, and expert parity remain future.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_reports_d3_not_available_without_application_gold` | D3 section is honest when no gold is supplied. |
| `tests/test_bench_phase0.py` | `test_scorecard_scores_d3_application_gold_exact_span_and_code` | Exact code+span TP/FP/FN, precision, recall, F1 are computed. |
| `tests/test_bench_phase0.py` | `test_scorecard_invalid_d3_gold_fails_loud` | Malformed/duplicate D3 gold is rejected. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_d3_from_gold_file_without_mutating_state` | External D3 gold file is applied in memory only. |
| `tests/test_qc_cli_bench.py` | CLI bench D3 flag pass-through if current wrapper tests require it. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Existing scorecard sections remain stable. |
| `tests/test_bench_phase0_script.py` | External file handling and input hashes remain stable. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `phase0_scorecard` includes `application_validity_d3`.
- [ ] Without D3 gold, D3 reports `not_available` and does not imply quality.
- [ ] With D3 gold, exact code+source-anchor TP/FP/FN, precision, recall, F1,
  matched/missed/extra keys, and unscored system applications are reported.
- [ ] `make bench D3_GOLD=...` and `qc_cli.py bench --d3-gold-file ...` apply
  gold in memory only and include the file hash in `_meta.input_hashes`.
- [ ] Docs state this is exact-span scoring only, not full D3 validity evidence.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should D3 support IoU/Hausdorff in this slice? — Status: DEFERRED | Why it
  matters: exact span+code scoring is a safe first substrate; overlap metrics
  need a separate design to avoid obscuring the exact-match denominator.
- [ ] Should D3 report κ/α/AC1 now? — Status: DEFERRED | Why it matters:
  agreement coefficients require a stable unit universe and human-rater data,
  not just system-vs-gold exact anchors.

---

## Notes

This plan mirrors the D7 scoring-substrate pattern. It should make D3 measurable
when gold exists while preserving the claim that methodological validity remains
unmeasured.
