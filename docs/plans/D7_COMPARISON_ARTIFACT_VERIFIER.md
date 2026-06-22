# Plan #181: D7 Comparison Artifact Verifier

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** #180
**Blocks:** Reproducible held-out D7 retrieval/live-baseline comparison artifacts

---

## Gap

**Current:** Successful `make compare-d7-retrieval ARTIFACT_DIR=...` /
`scripts/compare_d7_retrieval.py --artifact-dir ...` runs can write a
timestamped D7 comparison artifact directory with `report.json` and
`manifest.json`. The manifest records report hash, report `_meta.input_hashes`,
report `_meta.command`, prompt-eval-not-run status, and D7 claim caveats. There
is no agent-drivable verifier that checks the manifest against the local
artifact files.

**Target:** Add deterministic artifact verification:

- `scripts/verify_d7_comparison_artifact.py <artifact-dir-or-manifest>` verifies
  one D7 comparison artifact directory or manifest file.
- `make verify-d7-comparison-artifact ARTIFACT=...` invokes the verifier.
- `qc_cli.py verify-d7-comparison-artifact ...` delegates to the same script.
- The verifier returns JSON with `status="verified"` or `status="invalid"`,
  counts, structured failure rows, and an explicit provenance-only caveat.
- Verification checks manifest shape, artifact type/schema version, local
  `report.json` existence, report SHA-256, report `_meta.input_hashes` equality,
  report `_meta.command` equality, prompt-eval-not-run status, and claim caveat
  presence.
- Exit code is `0` only for verified artifacts.

**Why:** A versioned artifact package is useful only if an agent can verify it
without conversation context. This is the next deterministic hardening slice
before real held-out/live-baseline D7 runs exist.

**Non-target:** This slice does not add manifest self-hashes, sign artifacts,
verify original gold/prediction/protocol files still exist, rerun comparison
scoring, run live baselines, create held-out gold labels, choose retrieval/model
policy, or license held-out D7 evidence, live-baseline evidence, superiority
evidence, methodological-validity evidence, or SOTA claims.

---

## References Reviewed

- `docs/plans/completed/D7_COMPARISON_ARTIFACT_PACKAGE.md` - artifact package
  contract and verification evidence.
- `scripts/compare_d7_retrieval.py` - D7 comparison artifact writer and manifest
  shape.
- `tests/test_d7_comparison_guard.py` - artifact package fixture path and D7
  comparison fixtures.
- `scripts/verify_export_audit_manifest.py` - existing JSON verifier CLI shape
  and exit-code semantics.
- `qc_clean/core/export/audit_manifest.py` - structured verification report and
  failure-row pattern.
- `Makefile` - existing verifier target style.
- `qc_cli.py` - top-level command wrapper pattern.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions D7
  comparison artifact verification qualitative_coding' --project
  qualitative_coding` returned only low-relevance historical completed-task
  entries.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic verification slice over an existing local artifact package.

---

## Capabilities

Internal D7 comparison artifact verification only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `verify_d7_comparison_artifact` | artifact directory or manifest path | JSON verification report with status/failures/caveat | qualitative_coding | `make verify-d7-comparison-artifact`, `qc_cli.py verify-d7-comparison-artifact`, agents reviewing D7 artifacts | free |

### Capability Validation

- [ ] Verified artifact reports `status="verified"` and exit code `0`.
- [ ] Report-hash mismatch reports `status="invalid"` and exit code `1`.
- [ ] Report/manifest metadata mismatches produce stable failure codes.
- [ ] Missing report file produces a stable failure code.
- [ ] Verifier caveat states this is provenance only.

---

## Files Affected

- `scripts/verify_d7_comparison_artifact.py`
- `tests/test_d7_comparison_artifact_verifier.py`
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

1. Write failing verifier tests for a valid artifact, hash mismatch, metadata
   mismatch, missing report file, Make dry-run, and `qc_cli.py` forwarding.
2. Add `scripts/verify_d7_comparison_artifact.py` with structured JSON report
   and stable failure codes.
3. Add `verify-d7-comparison-artifact` Make target and `qc_cli.py` wrapper.
4. Update docs with verifier-only claim caveat.
5. Regenerate `AGENTS.md`.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_artifact_verifier.py` | `test_verify_d7_comparison_artifact_accepts_matching_package` | Valid artifact verifies with status `verified` and no failures. |
| `tests/test_d7_comparison_artifact_verifier.py` | `test_verify_d7_comparison_artifact_detects_report_hash_mismatch` | Modified report invalidates the package with `report_sha256_mismatch`. |
| `tests/test_d7_comparison_artifact_verifier.py` | `test_verify_d7_comparison_artifact_detects_metadata_mismatch` | Manifest/report metadata drift produces stable mismatch failures. |
| `tests/test_d7_comparison_artifact_verifier.py` | `test_verify_d7_comparison_artifact_detects_missing_report` | Missing report file invalidates the package with a stable missing-file failure. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_verify_d7_comparison_artifact_forwards_path` | `qc_cli.py` delegates verifier paths to the canonical script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_artifact_verifier.py tests/test_qc_cli_d7_retrieval.py -q` | Verifier behavior and CLI wrapper. |
| `python -m ruff check scripts/verify_d7_comparison_artifact.py tests/test_d7_comparison_artifact_verifier.py tests/test_qc_cli_d7_retrieval.py qc_cli.py` | Focused lint. |
| `make -n verify-d7-comparison-artifact ARTIFACT=artifact-dir` | Make target forwards to canonical script. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Valid D7 comparison artifacts verify with status `verified`, exit code
  `0`, zero failures, and checked report count `1`.
- [ ] Report hash mismatch verifies with status `invalid`, exit code `1`, and a
  stable `report_sha256_mismatch` failure.
- [ ] Manifest/report `_meta.input_hashes` mismatch produces a stable failure.
- [ ] Manifest/report `_meta.command` mismatch produces a stable failure.
- [ ] Missing `report.json` produces a stable failure.
- [ ] Verifier accepts either artifact directory path or manifest file path.
- [ ] Make and `qc_cli.py` surfaces delegate to the canonical verifier.
- [ ] Docs state this verifier is local provenance/integrity checking only, not
  held-out D7 evidence, live-baseline evidence, superiority evidence,
  methodological-validity evidence, or SOTA.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] Make dry-run passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Verifier silently accepts malformed manifests | Manifest shape not checked | Validate required fields and emit `invalid_manifest_shape`. |
| Hash mismatch is hidden by JSON parsing | Verifier hashes parsed JSON instead of file bytes | Hash `report.json` bytes exactly. |
| Metadata mismatch is missed | Verifier checks only report hash | Compare manifest `input_hashes` and `command` against report `_meta`. |
| Directory/manifest path ambiguity | Path resolution is underspecified | If path is a directory, read `<path>/manifest.json`; otherwise treat it as manifest path and resolve report relative to its parent. |
| Docs imply benchmark evidence | Caveat omitted | State verification is local provenance/integrity checking only. |
