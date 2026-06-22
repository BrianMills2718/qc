# Plan #180: D7 Comparison Artifact Package

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** #179
**Blocks:** Reproducible held-out D7 retrieval/live-baseline comparison artifacts

---

## Outcome

Implemented and pushed in commit `2245d09`.

Successful `scripts/compare_d7_retrieval.py --artifact-dir ...` runs now write
one timestamped D7 comparison artifact directory containing `report.json` and
`manifest.json`. The manifest records schema version, artifact type, generated
UTC timestamp, project ID/name, report SHA-256, report `_meta.input_hashes`,
report `_meta.command`, a prompt-eval-not-run block, and an explicit
claim-discipline caveat. `make compare-d7-retrieval ARTIFACT_DIR=...` and
`qc_cli.py compare-d7-retrieval --artifact-dir ...` forward to the canonical
script. Existing stdout and `--output` JSON behavior remain compatible, and
failed preflight still writes no output report and no artifact directory.

Verification evidence:

- TDD red:
  `python -m pytest tests/test_d7_comparison_guard.py -q` initially failed with
  `SystemExit: 2` because `--artifact-dir` was not yet accepted.
- Focused D7 tests:
  `python -m pytest tests/test_d7_comparison_guard.py tests/test_qc_cli_d7_retrieval.py -q`
  passed: 15 passed.
- Focused Ruff:
  `python -m ruff check scripts/compare_d7_retrieval.py tests/test_d7_comparison_guard.py tests/test_qc_cli_d7_retrieval.py qc_cli.py`
  passed.
- Make dry-run:
  `make -n compare-d7-retrieval ... ARTIFACT_DIR=benchmark_results` emitted
  the canonical `scripts/compare_d7_retrieval.py ... --artifact-dir
  benchmark_results` command.
- Docs gate: `make docs-check` passed.
- Diff whitespace: `git diff --check` passed.
- Full gate: `make check` passed: 1176 passed, 1 skipped, 8 deselected; Ruff
  passed; docs-check passed; type check remains not configured.

This is artifact/provenance/accounting infrastructure only. It is not held-out
D7 evidence, live-baseline evidence, superiority evidence,
methodological-validity evidence, or SOTA evidence.

---

## Gap

**Current:** `make compare-d7-retrieval` /
`scripts/compare_d7_retrieval.py` can score D7 retrieval and live-baseline
prediction packages against one D7 gold file, optionally enforce a registered
comparison protocol, report metric-criteria pass/fail/missing rows, and include
`_meta.input_hashes` plus `_meta.command` provenance in successful reports. The
standalone D7 comparison path still emits only stdout and an optional single
report file; unlike Phase 0, it cannot write a versioned artifact directory with
a manifest hash tying the report, inputs, command, and claim caveats together.

**Target:** Add optional D7 comparison artifact packaging:

- `scripts/compare_d7_retrieval.py --artifact-dir <root>` writes a new
  timestamped run directory.
- The run directory contains `report.json` and `manifest.json`.
- The manifest records schema version, artifact type, generated timestamp,
  project ID, report file/hash, `_meta.input_hashes`, `_meta.command`, explicit
  claim-discipline caveats, and a `prompt_eval.status="not_run"` caveat.
- Existing stdout and `--output` behavior remains compatible.
- Failed preflight or comparison errors write no artifact directory.
- `make compare-d7-retrieval ARTIFACT_DIR=...` and
  `qc_cli.py compare-d7-retrieval --artifact-dir ...` delegate to the same
  script flag.

**Why:** D7 held-out comparison readiness needs a reviewable artifact boundary,
not just one JSON report. A manifest makes a successful comparison durable and
hash-checkable before any actual held-out/live-baseline benchmark run exists.

**Non-target:** This slice does not run live baselines, generate held-out gold
labels, create benchmark data, choose a default embedding/adversarial retrieval
policy, change D7 scores, verify artifacts after writing, or license held-out
D7 evidence, live-baseline evidence, superiority evidence,
methodological-validity evidence, or SOTA claims.

---

## References Reviewed

- `docs/plans/ACTIVE_SPRINT.md` - active sprint queue and claim-discipline stop
  conditions.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2/D7 state ledger, roadmap, and
  claim caveats.
- `docs/EVALUATION_HARNESS.md` - D7 comparison substrate and Phase 0 artifact
  package expectations.
- `scripts/compare_d7_retrieval.py` - current D7 comparison CLI, preflight
  guard, metric criteria, output, and provenance boundary.
- `tests/test_d7_comparison_guard.py` - current D7 comparison fixtures and
  regression tests.
- `scripts/bench_phase0.py` - existing versioned artifact directory and
  manifest pattern.
- `Makefile` - existing `compare-d7-retrieval` target.
- `qc_cli.py` - existing top-level D7 comparison wrapper.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions D7
  held-out retrieval comparison qualitative_coding' --project qualitative_coding`
  returned only low-relevance historical completed-task entries.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic artifact-packaging slice over an existing local comparison
surface.

---

## Capabilities

Internal D7 comparison artifact packaging only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `write_d7_comparison_artifact` | successful D7 comparison report + artifact root | run directory containing `report.json` + `manifest.json` | qualitative_coding | `make compare-d7-retrieval`, `qc_cli.py compare-d7-retrieval`, agents reviewing D7 comparisons | free |

### Capability Validation

- [x] Artifact directory contains `report.json` and `manifest.json`.
- [x] Manifest report hash matches `report.json`.
- [x] Manifest input hashes and command match report `_meta`.
- [x] Existing stdout and `--output` behavior remains compatible.
- [x] Failed preflight writes no artifact directory.

---

## Files Affected

- `scripts/compare_d7_retrieval.py`
- `tests/test_d7_comparison_guard.py`
- `Makefile`
- `qc_cli.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing D7 comparison artifact tests for successful package creation,
   manifest/report hash consistency, stdout/output compatibility, and failed
   preflight no-write behavior.
2. Add `--artifact-dir` support and reusable artifact writer helpers to
   `scripts/compare_d7_retrieval.py`.
3. Add `ARTIFACT_DIR` forwarding to `make compare-d7-retrieval` and
   `--artifact-dir` forwarding to `qc_cli.py compare-d7-retrieval`.
4. Update docs with the artifact-only claim caveat.
5. Regenerate `AGENTS.md`.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_writes_artifact_package` | Successful guarded comparison writes a run directory with report and manifest; manifest hash and metadata match report. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_failed_preflight_writes_no_artifact_package` | Failed guarded preflight still writes no output report and no artifact directory. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_guard.py -q` | D7 comparison guard, metric criteria, provenance, live-baseline, and artifact behavior. |
| `python -m ruff check scripts/compare_d7_retrieval.py tests/test_d7_comparison_guard.py qc_cli.py` | Focused lint for changed Python. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `--artifact-dir` writes exactly one timestamped D7 comparison run directory
  per successful invocation.
- [x] Artifact `report.json` matches stdout JSON.
- [x] Artifact `manifest.json` records the report SHA-256.
- [x] Manifest `input_hashes` equals report `_meta.input_hashes`.
- [x] Manifest `command` equals report `_meta.command`.
- [x] Manifest records explicit prompt-eval-not-run and claim-discipline
  caveats.
- [x] `--output` remains compatible when `--artifact-dir` is also supplied.
- [x] Failed preflight writes no artifact directory.
- [x] Make and `qc_cli.py` forward artifact-dir arguments to the canonical
  script.
- [x] Docs state this is artifact/provenance infrastructure only, not held-out
  D7 evidence, live-baseline evidence, superiority evidence,
  methodological-validity evidence, or SOTA.

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
| Failed preflight creates a partial artifact directory | Artifact writer called before preflight status check | Keep artifact writing after successful report construction only. |
| Manifest hash does not match report | Report serialized differently for stdout/artifact | Serialize once before all writes and hash those exact bytes. |
| `--output` and artifact report diverge | Separate report mutation between writes | Attach metadata before serialization and reuse one text payload. |
| Run directory collision | Timestamp/path already exists | Fail loudly with a context-rich error, matching Phase 0 behavior. |
| Docs imply held-out evidence | Caveat omitted | State artifact package is provenance/accounting only. |
