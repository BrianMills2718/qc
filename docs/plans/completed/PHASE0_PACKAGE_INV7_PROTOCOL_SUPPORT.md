# Plan #185: Phase 0 Package INV-7 Protocol Support

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** Phase 0 benchmark package runner; INV-7 live protocol guard
**Blocks:** Package-driven Phase 0 runs preserving INV-7 score-time preflight

---

## Gap

**Current:** `make bench` / `qc_cli.py bench` support
`INV7_PROTOCOL=...` / `--inv7-live-protocol-file` and enforce INV-7 live
protocol/result preflight before scorecard, output, or artifact writes. The
strict Phase 0 package runner supports most Phase 0 protocol files but does not
accept or forward `inv7_live_protocol_file`. Because the package model forbids
extra keys, a manifest cannot currently express that guard.

**Target:** Add `inv7_live_protocol_file` to the Phase 0 package manifest schema
and package-to-bench argv conversion.

**Why:** Package-driven benchmark runs should preserve the same preflight guards
as direct `make bench` / `qc_cli.py bench` invocations. Otherwise agents can
accidentally lose INV-7 live protocol enforcement when switching from command
flags to a manifest.

**Non-target:** This slice does not change INV-7 protocol validation, run live
fixtures, create held-out adversarial data, call an LLM, modify prompt-injection
scoring, add package-writing UX, or claim prompt-injection robustness, model
obedience, methodological validity, or SOTA evidence.

---

## References Reviewed

- `scripts/run_phase0_benchmark_package.py` - strict package schema and path
  forwarding.
- `scripts/bench_phase0.py` - canonical Phase 0 `--inv7-live-protocol-file`
  support.
- `qc_cli.py` - direct `bench` support for `--inv7-live-protocol-file`.
- `tests/test_phase0_benchmark_package.py` - package forwarding tests.
- `docs/EVALUATION_HARNESS.md` - package/INV-7 caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-7 and roadmap claim discipline.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions'
  --project qualitative_coding` returned no conflicting in-flight decision.

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
| Phase 0 package INV-7 protocol forwarding | Phase 0 package manifest with optional `inv7_live_protocol_file` | canonical `bench_phase0` argv | qualitative_coding | package-driven benchmark runs | free |

### Capability Validation

- [x] Package manifests accept `inv7_live_protocol_file`.
- [x] Relative `inv7_live_protocol_file` paths resolve from the manifest
  directory.
- [x] Package-to-bench argv includes `--inv7-live-protocol-file`.
- [x] Existing unknown-key rejection remains in place for unsupported fields.
- [x] Documentation states this only preserves local protocol/preflight
  enforcement and does not create robustness evidence.

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

1. Add failing tests showing `inv7_live_protocol_file` is accepted and forwarded
   to `bench_phase0.main`.
2. Add the optional manifest field and `_PATH_FLAGS` mapping.
3. Update docs/CLAUDE claim-discipline text for package-manifest support.
4. Regenerate `AGENTS.md`.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_phase0_benchmark_package.py` | `test_phase0_benchmark_package_forwards_inv7_live_protocol` | Manifest field forwards to canonical `--inv7-live-protocol-file`. |
| `tests/test_phase0_benchmark_package.py` | update `test_phase0_package_to_bench_argv_resolves_relative_paths` | Relative INV-7 protocol paths resolve from the manifest directory. |

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
- [x] `Phase0BenchmarkPackage` accepts optional `inv7_live_protocol_file`.
- [x] `phase0_package_to_bench_argv()` resolves that path relative to the
  package manifest directory.
- [x] `phase0_package_to_bench_argv()` forwards the canonical
  `--inv7-live-protocol-file` flag.
- [x] Existing strict unknown-key behavior remains unchanged.
- [x] Docs/CLAUDE describe package support without implying evidence beyond
  local guard preservation.

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
| Manifest field still rejected | Pydantic model lacks the field or extra-forbid still sees it as unknown | Add the explicit optional field. |
| Field accepted but ignored | `_PATH_FLAGS` lacks the mapping | Add `inv7_live_protocol_file: --inv7-live-protocol-file`. |
| Relative path resolves from cwd | Path conversion bypasses `_resolve_manifest_path` | Route through existing `_PATH_FLAGS` path handling. |
| Docs overclaim | Package support sounds like robustness evidence | Keep caveats: local guard preservation only, not held-out INV-7 evidence. |

---

## Outcome

Implemented in commit `271d9260` and pushed to `main`.

`Phase0BenchmarkPackage` now accepts optional `inv7_live_protocol_file`, and
`phase0_package_to_bench_argv()` resolves that path relative to the manifest
directory before forwarding the canonical `--inv7-live-protocol-file` flag to
`bench_phase0`. Existing strict unknown-key rejection remains unchanged for
unsupported manifest fields.

Verification evidence:

- TDD red state: `python -m pytest tests/test_phase0_benchmark_package.py -q`
  initially failed because `inv7_live_protocol_file` was rejected with
  `extra_forbidden`.
- `python -m pytest tests/test_phase0_benchmark_package.py tests/test_qc_cli_bench.py -q`:
  12 passed.
- `python -m ruff check scripts/run_phase0_benchmark_package.py tests/test_phase0_benchmark_package.py`:
  passed.
- `make docs-check`: passed.
- `git diff --check`: passed.
- `make check`: 1200 passed, 1 skipped, 8 deselected; Ruff and docs-check
  passed; type check remains not configured.

Claim discipline: this preserves an existing local INV-7 protocol/result
preflight guard when using package-driven Phase 0 runs. It does not run live
fixtures, create held-out adversarial data, call an LLM, change scoring, or
license prompt-injection robustness, model-obedience, methodological-validity,
or SOTA claims.
