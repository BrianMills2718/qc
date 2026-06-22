# Plan #106: Adjudication Import Preflight Guard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #105 Adjudication response preflight
**Blocks:** safer held-out D3/D7 gold import workflow

---

## Outcome

Implemented and pushed in commit `5715722`:

- Added optional `--protocol-package` and `--sample-package` arguments to
  `scripts/import_adjudication_responses.py`.
- Guarded imports now run response preflight before writing D3/D7 outputs when
  both guard files are supplied.
- Failed preflight emits non-zero machine-readable JSON with the full
  `preflight_report` and writes no gold-package outputs.
- Passing guarded imports preserve the existing output behavior and include
  `preflight_report` in stdout JSON.
- `make import-adjudication-responses` now accepts optional
  `PREFLIGHT_PROTOCOL=... PREFLIGHT_SAMPLE=...` variables.
- Docs recommend the guarded path for held-out benchmark input creation while
  preserving claim discipline.

Verification:

- `python -m pytest tests/test_adjudication_import.py -q` failed before
  implementation with unrecognized `--protocol-package` /
  `--sample-package`, as expected.
- `python -m pytest tests/test_adjudication_import.py
  tests/test_adjudication_response_preflight.py
  tests/test_adjudication_preflight.py tests/test_adjudication_protocol.py
  tests/test_adjudication_sample.py -q` -> 31 passed.
- `python -m ruff check scripts/import_adjudication_responses.py
  tests/test_adjudication_import.py qc_clean/core/adjudication_response_preflight.py
  scripts/preflight_adjudication_responses.py` -> passed.
- `make docs-check` -> passed.
- `make -n import-adjudication-responses ... PREFLIGHT_PROTOCOL=protocol.json
  PREFLIGHT_SAMPLE=sample.json` -> expected `--protocol-package` /
  `--sample-package` invocation.
- `make check` -> 911 passed, 1 skipped, 8 deselected; Ruff/docs green; type
  check not yet configured.

---

## Gap

**Current:** `make adjudication-response-preflight` can independently check that
a completed response package matches a registered protocol and concrete sample
package. `make import-adjudication-responses` still imports any response package
that passes shape/completeness validation, so operators can accidentally skip
the provenance gate before creating D3/D7 gold package inputs.

**Target:** Add an optional import-time guard:

- `scripts/import_adjudication_responses.py` accepts:
  - `--protocol-package protocol.json`
  - `--sample-package sample.json`
- If either guard input is supplied, both are required.
- When both are supplied, the script runs
  `preflight_adjudication_responses_payloads(protocol, sample, responses,
  sample_file_sha256=sha256(sample))` before calling
  `build_adjudication_gold_import`.
- A failed preflight exits non-zero, emits machine-readable JSON, and writes no
  D3/D7 outputs.
- A passing preflight allows the existing import and includes the preflight
  report in the output JSON.
- Default import behavior without guard inputs remains compatible.
- `make import-adjudication-responses` exposes optional
  `PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json` variables and
  passes them through when supplied.

**Why:** Plan #105 created the deterministic gate. This slice makes the safer
path easy to use at the exact point where response labels become benchmark input
artifacts, without silently changing existing dev/test workflows.

---

## References Reviewed

- `scripts/import_adjudication_responses.py` - import CLI behavior and output.
- `qc_clean/core/adjudication_import.py` - response-to-D3/D7 conversion.
- `qc_clean/core/adjudication_response_preflight.py` - response preflight report.
- `tests/test_adjudication_import.py` - current script and core import tests.
- `tests/test_adjudication_response_preflight.py` - protocol/sample/response
  fixtures and preflight expectations.
- `Makefile` - `import-adjudication-responses` target.
- `docs/plans/completed/ADJUDICATION_RESPONSE_PREFLIGHT.md` - prior plan and
  deferred question.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No external research required. This is local workflow enforcement over already
implemented package contracts.

---

## Capabilities

Internal CLI/Make workflow guard only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `import_adjudication_responses_with_preflight` | response package + optional protocol/sample package files | import report with optional response preflight report | qualitative_coding | agents/operators creating D3/D7 gold inputs | free |

### Capability Validation

- [x] Guard defaults are backward-compatible.
- [x] Supplying only one guard input fails loud before import.
- [x] Failed preflight blocks import and leaves output files unwritten.
- [x] Passing preflight imports as before and includes report metadata.
- [x] Make target can pass guard variables through.

---

## Files Affected

- `scripts/import_adjudication_responses.py` (modify)
- `tests/test_adjudication_import.py` (modify)
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

1. Add TDD tests for valid guarded import, failed preflight blocking output,
   one-sided guard arguments failing loud, default compatibility, and Make
   dry-run pass-through.
2. Implement guarded preflight in `scripts/import_adjudication_responses.py`.
3. Add Make vars `PREFLIGHT_PROTOCOL` / `PREFLIGHT_SAMPLE`.
4. Update docs to recommend guarded import for held-out D3/D7 package creation
   while preserving claim discipline.
5. Run focused tests, focused Ruff, docs checks, Make dry-run, and full
   `make check`.
6. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Changed Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_import.py` | `test_import_script_with_preflight_writes_outputs` | Valid protocol/sample/responses import succeeds and includes preflight report. |
| `tests/test_adjudication_import.py` | `test_import_script_preflight_failure_blocks_outputs` | Mismatched sample/protocol fails before writing D3/D7 output files. |
| `tests/test_adjudication_import.py` | `test_import_script_rejects_one_sided_preflight_args` | Supplying only protocol or sample guard input fails loud. |
| `tests/test_adjudication_import.py` | existing script import test | Default unguarded import remains compatible. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_adjudication_response_preflight.py` | Guard reuses response preflight semantics. |
| `tests/test_adjudication_import.py` | Import conversion remains unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `scripts/import_adjudication_responses.py --protocol-package ...
  --sample-package ...` runs response preflight before import.
- [x] Failed preflight returns non-zero JSON and does not write requested gold
  package outputs.
- [x] Passing guarded import writes the same D3/D7 outputs as the existing
  import path and includes `preflight_report` in stdout JSON.
- [x] Supplying exactly one of protocol/sample guard inputs fails loud.
- [x] Existing unguarded import remains compatible.
- [x] `make import-adjudication-responses ... PREFLIGHT_PROTOCOL=...
  PREFLIGHT_SAMPLE=...` is discoverable/dry-runs correctly.
- [x] Docs recommend guarded import for held-out benchmark input creation
  without claiming evidence from the guard itself.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should guarded import become mandatory for `--split held_out`? — Status:
  DEFERRED | Decision in this slice: preserve compatibility and expose the
  safer guarded path explicitly. Mandatory held-out enforcement is a future
  workflow-policy change after operators confirm the protocol package file
  lifecycle.

---

## Notes

This guard prevents provenance mismatches at import time. It still does not
make labels expert-produced, correct, held out, or benchmark evidence.
