# Plan #190: QC CLI Theoretical Sampling Surfaces

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** Theoretical-sampling scripts and Make targets
**Blocks:** Top-level CLI parity for INV-4 theoretical-sampling package workflow

---

## Gap

**Current:** INV-4 theoretical-sampling workflow surfaces exist through scripts
and Make targets:

- `scripts/validate_theoretical_sampling_protocol.py`
- `scripts/preflight_theoretical_sampling_protocol.py`
- `scripts/export_theoretical_sampling_candidates.py`
- `scripts/export_theoretical_sampling_results.py`
- `make validate-theoretical-sampling-protocol`
- `make theoretical-sampling-preflight`
- `make export-theoretical-sampling-candidates`
- `make export-theoretical-sampling-results`

`qc_cli.py` does not expose these as top-level commands, so the canonical CLI
has a gap in the documented theoretical-sampling package workflow.

**Target:** Add four thin `qc_cli.py` wrappers:

- `validate-theoretical-sampling-protocol`
- `theoretical-sampling-preflight`
- `export-theoretical-sampling-candidates`
- `export-theoretical-sampling-results`

Each wrapper delegates to the matching canonical script `main()` with exact
argv forwarding.

**Why:** The repo's long-term plan requires agent-drivable workflows. These
theoretical-sampling surfaces are already documented as INV-4 protocol/package
infrastructure; exposing them through `qc_cli.py` makes the end-to-end workflow
consistent with the benchmark/adjudication/D7 package surfaces.

**Non-target:** This slice does not change protocol schemas, preflight
semantics, candidate/result package contents, Make targets, ProjectStore
behavior, or scorecard scoring. It does not collect new data, execute real
theoretical sampling, prove category saturation, prove GT fidelity, or create
methodological-validity evidence.

---

## References Reviewed

- `scripts/validate_theoretical_sampling_protocol.py`
- `scripts/preflight_theoretical_sampling_protocol.py`
- `scripts/export_theoretical_sampling_candidates.py`
- `scripts/export_theoretical_sampling_results.py`
- `Makefile` theoretical-sampling targets.
- `tests/test_theoretical_sampling_protocol.py`
- `tests/test_theoretical_sampling_preflight.py`
- `tests/test_export_theoretical_sampling_candidates_script.py`
- `tests/test_export_theoretical_sampling_results_script.py`
- `docs/EVALUATION_HARNESS.md` theoretical-sampling surface/caveat text.
- `docs/PROJECT_THEORY_AND_GOALS.md` INV-4 status and roadmap caveats.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for existing
repo-local scripts.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py validate-theoretical-sampling-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py theoretical-sampling-preflight` | protocol path + candidate path + optional result path | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py export-theoretical-sampling-candidates` | project ID + protocol path + optional output/candidate filters/limit | candidate package | qualitative_coding | agents/operators | free |
| `qc_cli.py export-theoretical-sampling-results` | protocol path + candidate path + selected IDs + success criteria + optional stop/output | result package | qualitative_coding | agents/operators | free |

### Capability Validation

- [x] Each command parses through `qc_cli.py`.
- [x] Each handler delegates to the matching script `main()`.
- [x] Required arguments are forwarded exactly.
- [x] Optional arguments are forwarded only when supplied.
- [x] Repeated `--candidate-name`, `--selected-candidate-id`, and
  `--success-criterion-met` values preserve order.
- [x] Boolean `--stopped-by-rule` forwards only when true.
- [x] Docs state these are package/provenance workflow surfaces only, not
  sampling execution, saturation proof, GT-fidelity evidence, or benchmark
  evidence.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_theoretical_sampling_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add failing wrapper tests that monkeypatch each canonical theoretical
   sampling script `main()` and assert exact argv forwarding.
2. Add parser, dispatch, and handler entries in `qc_cli.py`.
3. Update docs/CLAUDE with the top-level CLI surfaces and caveats.
4. Regenerate `AGENTS.md`.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_theoretical_sampling_surfaces.py` | `test_qc_cli_validate_theoretical_sampling_protocol_forwards_path` | Validator wrapper delegates protocol path. |
| `tests/test_qc_cli_theoretical_sampling_surfaces.py` | `test_qc_cli_theoretical_sampling_preflight_forwards_args` | Preflight wrapper delegates protocol/candidates/results paths. |
| `tests/test_qc_cli_theoretical_sampling_surfaces.py` | `test_qc_cli_export_theoretical_sampling_candidates_forwards_args` | Candidate export wrapper delegates project/protocol/output/repeated candidates/limit. |
| `tests/test_qc_cli_theoretical_sampling_surfaces.py` | `test_qc_cli_export_theoretical_sampling_results_forwards_args` | Result export wrapper delegates protocol/candidates/repeated selections/repeated criteria/stop/output. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_theoretical_sampling_surfaces.py tests/test_theoretical_sampling_protocol.py tests/test_theoretical_sampling_preflight.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_export_theoretical_sampling_results_script.py -q` | CLI wrappers and canonical script behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_theoretical_sampling_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_cli.py validate-theoretical-sampling-protocol protocol.json`
  delegates to `scripts.validate_theoretical_sampling_protocol.main(...)`.
- [x] `qc_cli.py theoretical-sampling-preflight protocol.json --candidates-file
  candidates.json [--results-file results.json]` delegates to
  `scripts.preflight_theoretical_sampling_protocol.main(...)`.
- [x] `qc_cli.py export-theoretical-sampling-candidates <project_id>
  --protocol protocol.json ...` delegates to
  `scripts.export_theoretical_sampling_candidates.main(...)`.
- [x] `qc_cli.py export-theoretical-sampling-results protocol.json
  --candidates-file candidates.json ...` delegates to
  `scripts.export_theoretical_sampling_results.main(...)`.
- [x] Existing Make/script behavior is unchanged.
- [x] Docs/CLAUDE mention the top-level CLI aliases without implying sampling
  execution, saturation proof, GT-fidelity evidence, validity evidence, or
  benchmark results.

> Process criteria:
- [x] TDD red state observed before implementation.
- [x] Focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Plan is moved to completed with verification evidence.
- [x] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| CLI command unrecognized | Parser entry missing | Add subparser. |
| Parser accepts but does nothing | Dispatch branch missing | Add main dispatch branch. |
| Validation/export logic duplicated in `qc_cli.py` | Wrapper reimplements script work | Keep handlers as argv delegation only. |
| Optional args forwarded as `None` strings | Handler blindly forwards fields | Forward optional flags only when non-null. |
| Repeated args collapse or reorder | Parser/handler uses scalar rather than append/list | Use `action="append"` and extend in received order. |
| Docs overclaim | Package workflow sounds like saturation evidence | Keep INV-4 caveats: package/provenance only, not sampling execution or saturation proof. |

---

## Outcome

Implemented in commit `49cb5aa9` and pushed to `main`.

`qc_cli.py` now exposes top-level wrappers for theoretical-sampling protocol
validation, candidate/result preflight, candidate package export, and result
package export. Each wrapper delegates to the matching canonical script
`main()` without duplicating validation, preflight, export, ProjectStore, or
package-building logic.

Verification evidence:

- TDD red state: focused tests initially failed with argparse rejecting all
  four theoretical-sampling commands as invalid choices.
- `python -m pytest tests/test_qc_cli_theoretical_sampling_surfaces.py tests/test_theoretical_sampling_protocol.py tests/test_theoretical_sampling_preflight.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_export_theoretical_sampling_results_script.py -q`:
  17 passed.
- `python -m ruff check qc_cli.py tests/test_qc_cli_theoretical_sampling_surfaces.py`:
  passed.
- `make docs-check`: passed.
- `git diff --check`: passed.
- `make check`: 1212 passed, 1 skipped, 8 deselected; Ruff and docs-check
  passed; type check remains not configured.
- `python qc_cli.py validate-theoretical-sampling-protocol --help` and
  `python qc_cli.py export-theoretical-sampling-results --help`: command help
  rendered with expected arguments.

Claim discipline: these are top-level CLI aliases for INV-4 package/provenance
workflow surfaces only. They do not execute theoretical sampling, collect new
data, prove category saturation, prove GT fidelity, create methodological
validity evidence, create benchmark results, establish parity/superiority, or
support SOTA claims.
