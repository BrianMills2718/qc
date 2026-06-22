# Plan #186: Phase 0 Package Projects Dir Support

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 benchmark package runner
**Blocks:** Package-driven Phase 0 runs against non-default project stores

---

## Gap

**Current:** `make bench` / `qc_cli.py bench` support
`PROJECTS_DIR=...` / `--projects-dir` for scoring projects stored outside the
default project directory. `make bench-package` / `qc_cli.py bench-package`
strict manifests cannot express `projects_dir`, even though package paths are
already resolved relative to the manifest directory. Tests currently monkeypatch
`ProjectStore` where a package should be able to point at its project store.

**Target:** Add optional `projects_dir` to the Phase 0 package manifest schema
and package-to-bench argv conversion.

**Why:** Package-driven benchmark runs should be self-contained enough for
agents to run against package-local project stores without relying on cwd,
global defaults, or monkeypatch-only test scaffolding.

**Non-target:** This slice does not change project persistence, alter default
project-store behavior, copy project data into packages, add a package writer,
run live LLM calls, or claim benchmark validity. It only forwards an existing
canonical bench option from a strict manifest.

---

## References Reviewed

- `scripts/run_phase0_benchmark_package.py` - strict package schema and path
  forwarding.
- `scripts/bench_phase0.py` - canonical `--projects-dir` support.
- `qc_cli.py` - direct `bench` support for `--projects-dir`.
- `tests/test_phase0_benchmark_package.py` - package runner tests and current
  `ProjectStore` monkeypatch pattern.
- `docs/EVALUATION_HARNESS.md` - Phase 0 package and provenance caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - roadmap claim discipline.
- Coordination/memory check: clean worktree, no active claim files under
  `~/.claude/coordination/claims`, and no conflicting in-flight decision from
  `agent-memory recall 'active decisions' --project qualitative_coding`.

---

## Research Basis For This Slice

No external research is needed. This is deterministic manifest schema parity
with an already-implemented canonical CLI flag.

---

## Capabilities

Internal package-runner compatibility only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Phase 0 package project-store forwarding | Phase 0 package manifest with optional `projects_dir` | canonical `bench_phase0` argv | qualitative_coding | package-driven benchmark runs | free |

### Capability Validation

- [x] Package manifests accept `projects_dir`.
- [x] Relative `projects_dir` paths resolve from the manifest directory.
- [x] Package-to-bench argv includes `--projects-dir`.
- [x] A package-local project store can be scored without monkeypatching
  `ProjectStore`.
- [x] Existing unknown-key rejection remains in place for unsupported fields.
- [x] Documentation states this is package portability/provenance support only.

---

## Files Affected

- `scripts/run_phase0_benchmark_package.py`
- `tests/test_phase0_benchmark_package.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add failing tests for `projects_dir` manifest acceptance, relative path
   resolution, argv forwarding, and a package-local project store run without
   monkeypatching.
2. Add optional `projects_dir` to `Phase0BenchmarkPackage` and `_PATH_FLAGS`.
3. Update docs/CLAUDE caveats for package-local project stores.
4. Regenerate `AGENTS.md`.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_phase0_benchmark_package.py` | `test_phase0_benchmark_package_forwards_projects_dir` | Manifest `projects_dir` forwards to canonical `--projects-dir`. |
| `tests/test_phase0_benchmark_package.py` | `test_phase0_benchmark_package_uses_package_local_projects_dir` | Relative package-local project store runs without monkeypatching `ProjectStore`. |
| `tests/test_phase0_benchmark_package.py` | update `test_phase0_package_to_bench_argv_resolves_relative_paths` | Relative `projects_dir` resolves from the manifest directory. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_phase0_benchmark_package.py tests/test_qc_cli_bench.py -q` | Package runner and CLI bench-wrapper compatibility. |
| `python -m ruff check scripts/run_phase0_benchmark_package.py tests/test_phase0_benchmark_package.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `Phase0BenchmarkPackage` accepts optional `projects_dir`.
- [x] `phase0_package_to_bench_argv()` resolves `projects_dir` relative to the
  package manifest directory.
- [x] `phase0_package_to_bench_argv()` forwards the canonical `--projects-dir`
  flag.
- [x] A package manifest can run against a package-local project store without
  monkeypatching or relying on default user state.
- [x] Existing strict unknown-key behavior remains unchanged.
- [x] Docs/CLAUDE describe package-local project-store support without implying
  benchmark evidence.

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
| Manifest field rejected | Pydantic model lacks `projects_dir` | Add explicit optional field. |
| Field accepted but ignored | `_PATH_FLAGS` lacks mapping | Add `projects_dir: --projects-dir`. |
| Relative project store resolves from cwd | Path conversion bypasses `_resolve_manifest_path` | Route through existing package path handling. |
| Tests depend on ambient project state | No package-local integration test | Add a temp `ProjectStore` package run without monkeypatching. |
| Docs overclaim | Package portability sounds like benchmark evidence | Keep caveats: portability/provenance only, not validity evidence. |

---

## Outcome

Implemented in commit `e61f4e31` and pushed to `main`.

`Phase0BenchmarkPackage` now accepts optional `projects_dir`, and
`phase0_package_to_bench_argv()` resolves that path relative to the package
manifest directory before forwarding the canonical `--projects-dir` flag to
`bench_phase0`. A package manifest can now score a package-local `ProjectStore`
without monkeypatching or relying on default user state.

Verification evidence:

- TDD red state: `python -m pytest tests/test_phase0_benchmark_package.py -q`
  initially failed because `projects_dir` was rejected with `extra_forbidden`.
- `python -m pytest tests/test_phase0_benchmark_package.py tests/test_qc_cli_bench.py -q`:
  14 passed.
- `python -m ruff check scripts/run_phase0_benchmark_package.py tests/test_phase0_benchmark_package.py`:
  passed.
- `make docs-check`: passed.
- `git diff --check`: passed.
- `make check`: 1202 passed, 1 skipped, 8 deselected; Ruff and docs-check
  passed; type check remains not configured.

Claim discipline: this is package portability/provenance support only. It does
not change project persistence, copy project data into packages, run live LLM
calls, or license benchmark validity, methodological-validity, superiority,
parity, timing, or SOTA claims.
