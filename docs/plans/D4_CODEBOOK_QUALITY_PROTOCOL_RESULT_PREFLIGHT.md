# Plan #118: D4 Codebook Quality Protocol Result Preflight

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D4 codebook quality protocol package
**Blocks:** D4 score-time preflight guard; populated D4 blind expert /
LLM-judge evaluation workflow

---

## Gap

**Current:** D4 has a pre-evaluation protocol validator and a Phase 0
scorecard for externally supplied codebook-quality rubric rows. There is no
deterministic preflight that cross-checks a concrete D4 result file against the
registered protocol before the rows are scored or handed off.

**Target:** Add a D4 protocol/result preflight:

- New `qc_clean/core/d4_codebook_quality_preflight.py`.
- New `scripts/preflight_d4_codebook_quality_protocol.py`.
- New `make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json`.
- Tests for pass/fail report shape, missing/invalid results, hash mismatches,
  evaluator type/count mismatches, target-scope mismatches, individual-code
  `code_id` requirements, and CLI JSON output.
- Docs updated to clarify this is process/provenance only, not blind
  expert-panel evidence, codebook-quality evidence, methodological-validity
  evidence, or SOTA evidence.

**Why:** The protocol validator freezes the intended D4 evaluation design; the
preflight proves a concrete result file matches that design before agents treat
the rows as benchmark inputs. This mirrors the D6 protocol/result preflight
pattern while preserving claim discipline.

---

## References Reviewed

- `docs/plans/completed/D4_CODEBOOK_QUALITY_PROTOCOL_PACKAGE.md` - validator
  package, deferred result preflight, and claim-discipline caveat.
- `qc_clean/core/d4_codebook_quality_protocol.py` - protocol package schema.
- `qc_clean/core/bench.py` - `CodebookQualityEvaluation` row schema and D4
  scorecard.
- `scripts/bench_phase0.py` - D4 quality-file loader and Phase 0 input hash
  pattern.
- `qc_clean/core/d6_bias_preflight.py` - protocol/result preflight report
  pattern.
- `scripts/preflight_d6_bias_protocol.py` - JSON CLI pattern.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research. This implements the deterministic package-matching
layer already implied by the D4 protocol and D6 preflight patterns.

---

## Capabilities

Internal preflight capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `preflight_d4_codebook_quality_payloads` | D4 protocol JSON + D4 quality-result JSON | schema_version=1 pass/fail preflight report | qualitative_coding | agents/operators preparing D4 result files | free |

### Capability Validation

- [ ] Matching D4 protocol and quality-result payloads produce a pass report.
- [ ] Missing, malformed, or empty quality-result payloads fail loud.
- [ ] Protocol `outcome_file_sha256` locks are checked against the actual file
  hash when present.
- [ ] Result evaluator types must match the protocol evaluator plan.
- [ ] Unique result evaluators must satisfy `planned_evaluator_count`.
- [ ] Result scopes must match protocol `target_scopes`.
- [ ] Rows with `scope="individual_code"` must include a `code_id`.
- [ ] CLI emits machine-readable JSON and returns non-zero on failed preflight.

---

## Proposed Report Shape

Top-level fields:

- `schema_version`: literal `1`
- `package_type`: literal `d4_codebook_quality_protocol_result_preflight`
- `status`: `pass` or `fail`
- `protocol_id`, `project_id`, `split`
- `rubric_metrics`, `target_scopes`
- `result_row_count`
- `evaluator_count`
- `evaluator_types`
- `errors`: list of `{field, message}`
- `caution`: protocol/result-only claim-discipline caveat

Deferred by design:

- Score-time guard in `make bench D4_PROTOCOL=...`.
- Running LLM judges or blind expert panels.
- Claiming expert acceptance, codebook quality, methodological validity, or
  SOTA performance.

---

## Files Affected

- `qc_clean/core/d4_codebook_quality_preflight.py` (add)
- `scripts/preflight_d4_codebook_quality_protocol.py` (add)
- `tests/test_d4_codebook_quality_preflight.py` (add)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Write TDD tests for matching/mismatched D4 protocol/result payloads and CLI
   JSON.
2. Implement D4 preflight report models and cross-check helpers.
3. Add preflight script and Make target.
4. Update docs with process/provenance-only caveats.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d4_codebook_quality_preflight.py` | `test_preflight_d4_codebook_quality_passes_matching_protocol_and_results` | Matching protocol/result payloads pass. |
| `tests/test_d4_codebook_quality_preflight.py` | `test_preflight_d4_codebook_quality_fails_missing_or_invalid_results` | Missing, empty, or malformed result files fail loud. |
| `tests/test_d4_codebook_quality_preflight.py` | `test_preflight_d4_codebook_quality_fails_hash_and_evaluator_mismatches` | Hash lock, evaluator type, and evaluator count mismatches fail. |
| `tests/test_d4_codebook_quality_preflight.py` | `test_preflight_d4_codebook_quality_fails_scope_and_code_id_mismatches` | Scope drift and missing individual-code `code_id` fail. |
| `tests/test_d4_codebook_quality_preflight.py` | `test_preflight_d4_codebook_quality_script_outputs_json` | CLI emits machine-readable pass/fail reports. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d4_codebook_quality_preflight.py -q` | New preflight behavior. |
| `python -m ruff check qc_clean/core/d4_codebook_quality_preflight.py scripts/preflight_d4_codebook_quality_protocol.py tests/test_d4_codebook_quality_preflight.py` | Focused lint on new surfaces. |
| `make -n d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json` | Make target routes correctly. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] A schema_version=1 D4 preflight report can be produced by importable code.
- [ ] `make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json`
  emits JSON and returns non-zero on failed preflight.
- [ ] Result payloads are validated with the same D4 scorecard row schema.
- [ ] Protocol output hash locks are enforced when present.
- [ ] Evaluator type, evaluator count, target scope, and individual-code
  `code_id` checks are enforced.
- [ ] Docs state D4 preflight is process/provenance only.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should the score-time guard be included in this same slice? — Status:
  DEFERRED | This plan creates the standalone protocol/result preflight first;
  `make bench D4_PROTOCOL=...` can follow as a separate guard slice once the
  report contract is stable.

---

## Notes

This plan creates a package-matching preflight. It does not collect expert
ratings, run LLM judges, validate rubric labels, prove codebook quality, or
license a SOTA claim.
