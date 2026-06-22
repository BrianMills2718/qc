# Plan #183: D7 Comparison Package Writer

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** #182
**Blocks:** Reproducible held-out D7 retrieval/live-baseline comparison packages without hand-written manifests

---

## Gap

**Current:** `scripts/run_d7_comparison_package.py`, `make compare-d7-package`,
and `qc_cli.py compare-d7-package` can run strict D7 comparison manifests, but
operators still have to hand-write those manifests. That leaves a manual
coordination point for project ID, gold file, ordered prediction files,
optional protocol, output path, artifact root, and artifact verification flag.

**Target:** Add a deterministic D7 comparison package writer:

- `scripts/write_d7_comparison_package.py <project_id> --output package.json
  --gold-file gold.json --predictions-file a.json --predictions-file b.json`
  writes a `schema_version=1` package accepted by the D7 comparison package
  runner.
- The writer validates the supplied D7 gold package and every D7
  retrieval/live-baseline prediction package before writing.
- If a protocol package is supplied, the writer runs the existing D7 comparison
  preflight against the exact gold/prediction set before writing.
- Paths inside the generated manifest are relative to the manifest directory
  when possible; prediction order is preserved exactly.
- Optional `--comparison-output`, `--artifact-dir`, and `--verify-artifact`
  fields are recorded.
- `make write-d7-comparison-package ...` and
  `qc_cli.py write-d7-comparison-package ...` delegate to the writer.

**Why:** The D7 comparison runner made execution reproducible once a manifest
exists. A writer makes manifest creation itself agent-drivable and checkable,
removing another hand-written command/file before real held-out D7
retrieval/live-baseline runs.

**Non-target:** This slice does not create held-out data, run retrieval, run
live baselines, choose embedding/adversarial model policy, sign artifacts,
verify post-run artifact contents, or license held-out D7 evidence,
live-baseline evidence, superiority evidence, methodological-validity evidence,
or SOTA claims.

---

## References Reviewed

- `scripts/write_phase0_adjudication_package.py` - manifest writer, relative
  path style, and machine-readable report pattern.
- `tests/test_phase0_adjudication_package.py` - package-writer tests.
- `scripts/run_d7_comparison_package.py` - strict D7 comparison manifest schema.
- `scripts/preflight_d7_comparison.py` - existing D7 protocol/gold/prediction
  preflight.
- `qc_clean/core/d7_gold.py` - D7 gold package loader.
- `qc_clean/core/d7_baseline_package.py` - D7 retrieval/live-baseline package
  loader.
- `Makefile` - package writer and D7 target style.
- `qc_cli.py` - top-level wrapper and dispatch pattern.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions'
  --project qualitative_coding` returned no conflicting in-flight decision.

---

## Research Basis For This Slice

No external research is needed. This is deterministic orchestration over
repo-local D7 comparison package, preflight, and validation surfaces.

---

## Capabilities

Internal D7 comparison package authoring only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `write_d7_comparison_package` | project ID + versioned D7 gold/prediction files + optional protocol/output/artifact settings | strict D7 comparison package manifest + machine-readable write report | qualitative_coding | agents/operators running `compare-d7-package` | free |

### Capability Validation

- [ ] Valid D7 gold and prediction packages produce a strict runner-compatible
  manifest.
- [ ] Manifest paths are relative to the manifest directory when possible.
- [ ] Ordered prediction files are preserved.
- [ ] Invalid D7 gold or prediction packages fail before writing.
- [ ] Optional protocol packages trigger existing D7 comparison preflight before
  writing.

---

## Files Affected

- `scripts/write_d7_comparison_package.py`
- `tests/test_d7_comparison_package_writer.py`
- `tests/test_qc_cli_d7_retrieval.py`
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

1. Write failing tests for manifest writing, invalid input rejection, optional
   preflight invocation, Make dry-run, and `qc_cli.py` forwarding.
2. Add `scripts/write_d7_comparison_package.py` with a machine-readable report,
   D7 gold/prediction validation, optional preflight, and path normalization.
3. Add Make and `qc_cli.py` surfaces.
4. Update docs with package-writer-only claim caveats.
5. Regenerate `AGENTS.md`.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_package_writer.py` | `test_writes_manifest_for_valid_d7_comparison_inputs` | Valid D7 gold and ordered prediction packages produce a runner-compatible manifest with relative paths and optional output/artifact fields. |
| `tests/test_d7_comparison_package_writer.py` | `test_rejects_non_versioned_d7_gold_file` | Raw/non-versioned D7 gold fails before manifest write. |
| `tests/test_d7_comparison_package_writer.py` | `test_rejects_invalid_prediction_package` | Invalid prediction packages fail before manifest write. |
| `tests/test_d7_comparison_package_writer.py` | `test_protocol_runs_preflight_before_write` | Protocol package triggers existing D7 comparison preflight with the exact files in order before writing. |
| `tests/test_d7_comparison_package_writer.py` | `test_script_outputs_machine_readable_report` | Script writes the package and emits JSON status/report/caveat. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_write_d7_comparison_package_forwards_args` | `qc_cli.py` delegates package-writing arguments to the canonical writer. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_package_writer.py tests/test_d7_comparison_package_runner.py tests/test_qc_cli_d7_retrieval.py -q` | Writer output, runner compatibility, and CLI wrapper. |
| `python -m ruff check scripts/write_d7_comparison_package.py tests/test_d7_comparison_package_writer.py tests/test_qc_cli_d7_retrieval.py qc_cli.py` | Focused lint. |
| `make -n write-d7-comparison-package ID=project GOLD=gold.json PREDICTIONS="a.json b.json" OUTPUT=d7_package.json` | Make target forwards to canonical script. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Valid inputs write a strict D7 comparison package accepted by the runner.
- [ ] D7 gold files are validated as versioned D7 gold packages.
- [ ] Prediction files are validated as versioned D7 retrieval/live-baseline
  packages.
- [ ] Prediction file order is preserved.
- [ ] Relative manifest paths are emitted when files are inside the manifest
  directory.
- [ ] Optional protocol packages run existing D7 comparison preflight before
  writing.
- [ ] Optional comparison output, artifact directory, and verify-artifact flag
  are recorded.
- [ ] Invalid inputs return a JSON error and do not write a manifest.
- [ ] Make and `qc_cli.py` surfaces delegate to the canonical writer.
- [ ] Docs state this package writer is reproducibility/provenance
  infrastructure only, not held-out D7 evidence, live-baseline evidence,
  superiority evidence, methodological-validity evidence, or SOTA.

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
| Writer accepts raw gold | Loader bypassed | Require `load_d7_gold_set()` before writing. |
| Writer accepts malformed predictions | Baseline package validation bypassed | Require D7 baseline package loader/validator for every prediction file. |
| Prediction order changes | Writer sorts paths | Preserve argv/list order exactly. |
| Paths point to cwd-dependent files | Writer emits cwd-relative paths | Emit package-relative paths when possible; leave external absolute paths explicit. |
| Protocol drift not caught | Writer records protocol without preflight | Run existing D7 comparison preflight when protocol is supplied and block on failure. |
| Docs imply evidence | Caveat omitted | State package writing is reproducibility/provenance only. |
