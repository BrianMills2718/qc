# Plan #188: QC CLI Adjudication Validation Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Adjudication validation/preflight scripts
**Blocks:** Top-level CLI parity for adjudication protocol and response checks

---

## Gap

**Current:** Adjudication protocol validation, protocol/sample preflight,
response validation, and response preflight are agent-drivable through Make and
script entrypoints:

- `scripts/validate_adjudication_protocol.py`
- `scripts/preflight_adjudication_protocol_sample.py`
- `scripts/validate_adjudication_responses.py`
- `scripts/preflight_adjudication_responses.py`

`qc_cli.py` exposes adjudication sample export and the Phase 0 adjudication
package writer, but not these validation/preflight gates.

**Target:** Add top-level `qc_cli.py` wrappers for the four existing
validation/preflight scripts:

- `validate-adjudication-protocol <protocol>`
- `adjudication-protocol-preflight <protocol> <sample>`
- `validate-adjudication-responses <package>`
- `adjudication-response-preflight <protocol> <sample> <responses>`

**Why:** The full adjudication workflow should be available from the canonical
top-level CLI without forcing agents to remember script paths. These wrappers
preserve the existing script implementations and keep validation logic in one
place.

**Non-target:** This slice does not alter validation schemas, adjudication
sample export, response import, Phase 0 package writing, Make targets, or any
evidentiary status. It only adds thin CLI aliases.

---

## References Reviewed

- `scripts/validate_adjudication_protocol.py`
- `scripts/preflight_adjudication_protocol_sample.py`
- `scripts/validate_adjudication_responses.py`
- `scripts/preflight_adjudication_responses.py`
- `Makefile` adjudication validation/preflight targets.
- `qc_cli.py` parser/dispatch/handler patterns.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md`
  adjudication caveats.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for existing
repo-local scripts.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py validate-adjudication-protocol` | protocol path | canonical validation report | qualitative_coding | agents/operators | free |
| `qc_cli.py adjudication-protocol-preflight` | protocol path + sample path | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py validate-adjudication-responses` | response package path | canonical validation report | qualitative_coding | agents/operators | free |
| `qc_cli.py adjudication-response-preflight` | protocol path + sample path + responses path | canonical preflight report | qualitative_coding | agents/operators | free |

### Capability Validation

- [ ] Each command parses through `qc_cli.py`.
- [ ] Each handler delegates to the matching script `main()`.
- [ ] Positional arguments are forwarded exactly.
- [ ] No validation logic is duplicated in `qc_cli.py`.
- [ ] Docs state these are process/provenance checks only, not labels,
  correctness estimates, validity evidence, or benchmark results.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_adjudication_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add failing wrapper tests for all four commands by monkeypatching the
   canonical script `main()` functions.
2. Add parser entries, dispatch branches, and thin handlers in `qc_cli.py`.
3. Update docs/CLAUDE with the new top-level CLI surfaces and caveats.
4. Regenerate `AGENTS.md`.
5. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
6. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_qc_cli_adjudication_surfaces.py` | `test_qc_cli_validate_adjudication_protocol_forwards_path` | Protocol validator wrapper delegates path. |
| `tests/test_qc_cli_adjudication_surfaces.py` | `test_qc_cli_adjudication_protocol_preflight_forwards_paths` | Protocol/sample preflight wrapper delegates paths. |
| `tests/test_qc_cli_adjudication_surfaces.py` | `test_qc_cli_validate_adjudication_responses_forwards_path` | Response validator wrapper delegates path. |
| `tests/test_qc_cli_adjudication_surfaces.py` | `test_qc_cli_adjudication_response_preflight_forwards_paths` | Response preflight wrapper delegates paths. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_adjudication_surfaces.py tests/test_qc_cli_bench.py -q` | New wrappers plus adjacent CLI package surfaces. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_adjudication_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `qc_cli.py validate-adjudication-protocol protocol.json` delegates to
  `scripts.validate_adjudication_protocol.main(["protocol.json"])`.
- [ ] `qc_cli.py adjudication-protocol-preflight protocol.json sample.json`
  delegates to `scripts.preflight_adjudication_protocol_sample.main(...)`.
- [ ] `qc_cli.py validate-adjudication-responses responses.json` delegates to
  `scripts.validate_adjudication_responses.main(["responses.json"])`.
- [ ] `qc_cli.py adjudication-response-preflight protocol.json sample.json responses.json`
  delegates to `scripts.preflight_adjudication_responses.main(...)`.
- [ ] Existing Make/script behavior is unchanged.
- [ ] Docs/CLAUDE mention the top-level CLI aliases without implying expert
  labels, correctness estimates, validity evidence, or benchmark results.

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
| CLI command unrecognized | Parser entry missing | Add subparser. |
| Parser accepts but does nothing | Dispatch branch missing | Add main dispatch branch. |
| Wrong script called | Handler imports wrong module | Test each wrapper with monkeypatched canonical script. |
| Validation duplicated in `qc_cli.py` | Handler reimplements script logic | Keep handler as argv delegation only. |
| Docs overclaim | Process checks sound like labels/evidence | Keep process/provenance caveats. |
