# Plan #179: D7 Comparison Report Provenance

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D7 comparison preflight guard; D7 comparison metric success criteria
**Blocks:** Reproducible held-out D7 retrieval/live-baseline comparison artifacts

---

## Gap

**Current:** `make compare-d7-retrieval` / `scripts/compare_d7_retrieval.py`
can score D7 retrieval or live-baseline prediction packages against one D7 gold
file, optionally enforce a pre-registered comparison protocol, and report
metric-criteria pass/fail/missing rows. The report does not yet carry a compact
`_meta.input_hashes` or command provenance block. A reviewer must infer which
state, gold file, prediction files, and protocol file produced a report from
external context.

**Target:** Add deterministic provenance metadata to every successful D7
comparison report:

- `_meta.input_hashes` records hash algorithm, project ID, loaded project-state
  hash, corpus hash, gold file SHA-256, prediction file SHA-256 values in input
  order, and optional protocol file SHA-256.
- `_meta.command` records the compared project ID, gold path, prediction paths
  in input order, optional protocol path, and optional output path.
- Stdout and `--output` JSON contain identical provenance blocks.
- Failed preflight still writes no output report.
- Existing score, preflight, metric-criteria, Make, and `qc_cli.py
  compare-d7-retrieval` surfaces remain compatible except for additive `_meta`
  metadata.

**Non-target:** This slice does not add artifact directories, run live models,
generate held-out gold labels, choose default embedding/adversarial retrieval
policy, change D7 scores, or license held-out D7 evidence, expert parity,
superiority, methodological-validity, or SOTA claims.

**Why:** Held-out comparison reports need durable input identity before they can
be treated as reviewable benchmark artifacts. Phase 0 already records this kind
of metadata; the standalone D7 comparison path should not depend on external
filenames or conversation memory.

---

## References Reviewed

- `scripts/compare_d7_retrieval.py` - current comparison CLI, preflight guard,
  metric-criteria integration, and output write boundary.
- `qc_clean/core/d7_retrieval.py` - comparison report shape and D7 scoring
  behavior.
- `tests/test_d7_comparison_guard.py` - guarded/unguarded comparison tests and
  reusable package fixtures.
- `scripts/bench_phase0.py` - existing Phase 0 input-hash and command
  provenance pattern.
- `docs/plans/completed/D7_COMPARISON_PREFLIGHT_GUARD.md` - current D7 guard
  semantics and claim caveats.
- `docs/plans/completed/D7_COMPARISON_METRIC_SUCCESS_CRITERIA.md` - current
  metric-criteria semantics and claim caveats.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions D7
  held-out retrieval comparison qualitative_coding' --project qualitative_coding`
  returned only low-relevance historical completed-task entries.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic provenance hardening slice over an existing local comparison
surface.

---

## Design Decisions

- Use additive `_meta` metadata so existing top-level report fields remain
  compatible.
- Use SHA-256 over file bytes for gold, prediction, and protocol files.
- Use canonical JSON SHA-256 over the loaded `ProjectState` and corpus for
  state/corpus hashes, matching the local deterministic style used by Phase 0.
- Record prediction file hashes as an ordered list of `{path, sha256}` rows so
  repeated `--predictions-file` order is auditable.
- Do not add timestamps; deterministic report content is more useful for tests
  and reproducible local comparisons.

---

## Capabilities

Internal comparison-report provenance only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `compare_d7_retrieval_report_provenance` | loaded ProjectState + D7 gold path + D7 prediction paths + optional D7 protocol path + optional output path | additive `_meta.input_hashes` and `_meta.command` report metadata | qualitative_coding | `make compare-d7-retrieval`, `qc_cli.py compare-d7-retrieval`, agents reviewing D7 comparison reports | free |

### Capability Validation

- [ ] Successful guarded reports include file/state/corpus hashes.
- [ ] Successful unguarded reports include hashes with `protocol_file_sha256`
  set to null.
- [ ] Stdout and output-file metadata match.
- [ ] Failed preflight still writes no output report.

---

## Files Affected

- `scripts/compare_d7_retrieval.py`
- `tests/test_d7_comparison_guard.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for guarded provenance metadata, unguarded null protocol
   hash metadata, and output-file/stdout parity.
2. Add deterministic JSON hashing and file-hash helpers to
   `scripts/compare_d7_retrieval.py`.
3. Attach `_meta.input_hashes` and `_meta.command` after successful scoring and
   before stdout/output writes.
4. Update docs with the provenance-only caveat.
5. Regenerate `AGENTS.md`.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_includes_input_hashes_and_command_provenance` | Guarded reports include state/corpus/file hashes and command paths; output file matches stdout. |
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_without_protocol_records_null_protocol_hash` | Unguarded reports remain compatible and record no protocol hash/path. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_guard.py -q` | D7 guarded, unguarded, live-baseline, metric-criteria, and provenance behavior. |
| `python -m ruff check scripts/compare_d7_retrieval.py tests/test_d7_comparison_guard.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Successful D7 comparison reports include `_meta.input_hashes`.
- [ ] Successful D7 comparison reports include `_meta.command`.
- [ ] Prediction file hashes preserve input order.
- [ ] Guarded reports include protocol file hash/path.
- [ ] Unguarded reports set protocol hash/path to null and remain compatible.
- [ ] Failed preflight still blocks output writes.
- [ ] Docs state this is provenance/accounting only, not held-out D7 evidence,
  live-baseline evidence, superiority evidence, methodological-validity
  evidence, or SOTA.

> Process criteria:
- [ ] TDD red state observed before implementation.
- [ ] Focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Plan is moved to completed with verification evidence.
- [ ] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Failed preflight writes metadata/output | Provenance is attached before guard failure returns | Keep metadata attachment after successful scoring only; preserve existing failed-preflight return. |
| Prediction hashes lose ordering | Hashes stored in an unordered mapping | Store ordered rows matching `args.predictions_file`. |
| Output file differs from stdout | Metadata attached after one serialization path | Attach metadata before JSON serialization and reuse the same `report` object. |
| Hash helper error message says every file is a prediction | Shared helper lacks a label | Add a label parameter for context-rich failures. |
| Docs overclaim provenance as evidence | Claim caveat missing | State this is local provenance/accounting metadata only. |
