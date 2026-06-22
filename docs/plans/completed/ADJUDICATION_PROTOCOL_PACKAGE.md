# Plan #103: Adjudication Protocol Package

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-3 adjudication sample export; INV-3 adjudication response import
**Blocks:** held-out expert adjudication runs; D3/D7 evidence claim discipline

---

## Outcome

Implemented a pre-label adjudication protocol package validator:

- `qc_clean/core/adjudication_protocol.py` defines a schema_version=1
  `adjudication_protocol` package with protocol/project/dataset IDs, split,
  corpus/project hashes, prompt-freeze/contamination/registration flags, coder
  metadata, target dimensions, sampling plan, success criteria, and a caution.
- Held-out protocols fail loudly unless `prompt_frozen=true`,
  `contamination_checked=true`, `registered_before_labeling=true`, and
  `coder_count>=2`.
- D3/D7 protocol dimensions require compatible sample item target types
  (`code_application` and `negative_case` respectively).
- `scripts/validate_adjudication_protocol.py` and
  `make validate-adjudication-protocol` provide machine-readable validation.
- Docs state protocol packages are process/provenance metadata only, not expert
  labels, correctness estimates, validity evidence, or benchmark results.

Implementation commit: `9f00782`

## Verification

- TDD red: initial `python -m pytest tests/test_adjudication_protocol.py -q`
  failed with `ModuleNotFoundError: No module named
  'qc_clean.core.adjudication_protocol'`.
- Focused behavior: `python -m pytest tests/test_adjudication_protocol.py
  tests/test_adjudication_sample.py tests/test_adjudication_import.py
  tests/test_d3_gold_set.py tests/test_d7_gold_set.py -q` -> 24 passed.
- Focused lint: `python -m ruff check
  qc_clean/core/adjudication_protocol.py
  scripts/validate_adjudication_protocol.py tests/test_adjudication_protocol.py
  qc_clean/core/adjudication_sample.py qc_clean/core/adjudication_import.py`
  -> all checks passed.
- Command discoverability: `make help` lists
  `validate-adjudication-protocol`; `make -n
  validate-adjudication-protocol PROTOCOL=protocol.json` expands to
  `python scripts/validate_adjudication_protocol.py protocol.json`.
- Documentation governance: `make docs-check` passed.
- Full gate: `make check` -> 895 passed, 1 skipped, 8 deselected; Ruff and
  docs-check passed; type check remains not configured.
- Commit `9f00782` was pushed to `main`.

---

## Gap

**Current:** The repo can export adjudication samples, validate completed
responses, import valid code-application/negative-case labels into D3/D7 gold
packages, and assemble those packages into a Phase 0 benchmark manifest. The
protocol metadata for a real expert adjudication run still lives only as free
text inside generated gold packages after labels exist.

**Target:** Add a pre-registration protocol package contract and validator:

- Core: `qc_clean/core/adjudication_protocol.py`
- Script: `scripts/validate_adjudication_protocol.py protocol.json`
- Make target: `make validate-adjudication-protocol PROTOCOL=protocol.json`
- Package shape: `schema_version=1`, protocol/project/dataset IDs,
  split/freeze/contamination/registration flags, corpus/project hashes, coder
  metadata, target dimensions, sample plan, and explicit success criteria.
- Held-out protocols must fail loudly unless `prompt_frozen=true`,
  `contamination_checked=true`, `registered_before_labeling=true`, and
  `coder_count>=2`.
- Protocol dimensions must be compatible with sample target types:
  D3 requires `code_application`; D7 requires `negative_case`.

**Why:** INV-3 requires validity adjudication to be separate from consistency.
The repo now has post-label package plumbing, but a headline-validity run also
needs an agent-checkable protocol before labels are collected. This slice makes
that protocol explicit without claiming any labels or evidence exist.

---

## References Reviewed

- `qc_clean/core/adjudication_sample.py` - adjudication sample package,
  `TargetType` vocabulary, and response validation pattern.
- `qc_clean/core/adjudication_import.py` - generated D3/D7 package metadata and
  import caveats.
- `qc_clean/core/d3_gold.py` and `qc_clean/core/d7_gold.py` - held-out
  prompt-freeze/contamination/coder-count invariants.
- `scripts/validate_adjudication_responses.py` - machine-readable validator
  script pattern.
- `scripts/validate_d3_gold_set.py` and `scripts/validate_d7_gold_set.py` -
  package validation output shape.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - INV-3,
  held-out, prompt-frozen, contamination-checked claim discipline.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references. The evaluation harness
already specifies the expert-consensus-panel requirement; this slice turns that
local design into a machine-checkable protocol manifest.

---

## Capabilities

Internal validation capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_adjudication_protocol_payload` | JSON protocol package | `AdjudicationProtocolPackage` or clear validation error | qualitative_coding | agents, future adjudication workflows | free |

### Capability Validation

- [x] Pydantic schema has `Field(description=...)` on public fields.
- [x] Held-out-specific invariants fail loudly.
- [x] Dimension/sample-target compatibility is covered by tests.
- [x] Validator script emits machine-readable JSON.

---

## Files Affected

- `qc_clean/core/adjudication_protocol.py` (create)
- `scripts/validate_adjudication_protocol.py` (create)
- `tests/test_adjudication_protocol.py` (create)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate through existing sync tooling)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)

---

## Plan

### Steps

1. Write TDD tests for valid held-out protocol loading, held-out invariant
   failures, dimension/target mismatch failures, duplicate dimensions, and
   script JSON output.
2. Implement `qc_clean/core/adjudication_protocol.py` with Pydantic models and
   loader/validator helpers.
3. Add `scripts/validate_adjudication_protocol.py` and
   `make validate-adjudication-protocol`.
4. Update docs to state protocol packages are pre-registration metadata only.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_protocol.py` | `test_validate_protocol_accepts_held_out_d3_d7_package` | Valid held-out package with D3/D7 targets validates. |
| `tests/test_adjudication_protocol.py` | `test_validate_protocol_requires_held_out_freeze_contamination_registration_and_two_coders` | Held-out runs require freeze, contamination check, pre-label registration, and coder count. |
| `tests/test_adjudication_protocol.py` | `test_validate_protocol_rejects_dimension_target_mismatch` | D3/D7 dimensions require matching sample item target types. |
| `tests/test_adjudication_protocol.py` | `test_validate_protocol_rejects_duplicate_dimensions` | Duplicate target dimensions fail loudly. |
| `tests/test_adjudication_protocol.py` | `test_validate_protocol_script_outputs_json` | CLI emits valid/invalid machine-readable JSON with exit codes. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_adjudication_sample.py tests/test_adjudication_import.py` | Sample/import contracts remain unchanged. |
| `tests/test_d3_gold_set.py tests/test_d7_gold_set.py` | Gold package invariants remain unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `schema_version=1` adjudication protocol packages can be validated.
- [x] Held-out protocols require prompt freeze, contamination check,
  pre-label registration, and at least two coders.
- [x] D3/D7 dimensions require compatible sample target types.
- [x] Duplicate dimensions and blank protocol metadata fail loudly.
- [x] `make validate-adjudication-protocol PROTOCOL=...` is available and
  discoverable.
- [x] Docs say protocol packages are pre-registration metadata only, not expert
  labels, correctness estimates, or validity evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should protocol validation compare a protocol file against a concrete
  sample package hash in this slice? — Status: DEFERRED | Why it matters: the
  protocol schema records optional sample-package hash/path metadata, but strict
  sample-package cross-checking belongs in a later protocol-to-sample preflight
  lane.

---

## Notes

Protocol validation narrows a process gap. It cannot prove labels were collected
correctly; it only makes missing or under-specified protocol metadata fail
before import/scoring workflows treat labels as benchmark inputs.
