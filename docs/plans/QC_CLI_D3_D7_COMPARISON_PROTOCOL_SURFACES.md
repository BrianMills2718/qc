# Plan #193: QC CLI D3/D7 Comparison Protocol Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D3/D7 comparison protocol and preflight scripts
**Blocks:** Top-level CLI parity for D3/D7 comparison preflight workflows

---

## Gap

**Current:** D3 and D7 comparison protocol validation/preflight workflows exist
through Make targets and scripts:

- `make validate-d3-comparison-protocol`
- `make d3-comparison-preflight`
- `make validate-d7-comparison-protocol`
- `make d7-comparison-preflight`

`qc_cli.py` exposes D3/D7 baseline package validators and D7 comparison
run/package/artifact surfaces, but it does not expose these four protocol
validation/preflight steps as top-level commands.

**Target:** Add four thin `qc_cli.py` wrappers:

- `validate-d3-comparison-protocol <protocol>`
- `d3-comparison-preflight <protocol> <gold> <predictions...>`
- `validate-d7-comparison-protocol <protocol>`
- `d7-comparison-preflight <protocol> <gold> <predictions...>`

Each wrapper must delegate to the matching canonical script `main()` with exact
argv forwarding.

**Why:** Guarded D3/D7 comparison workflows should be agent-drivable through the
canonical CLI as well as Make/scripts. This fills a parity gap between package
validators/comparison runners and their registered protocol gates.

**Non-target:** This slice does not change D3/D7 protocol schemas, preflight
semantics, score-time guards, comparison scoring, package writers/runners,
artifact verification, Make targets, gold data, live baselines, or benchmark
evidence. It does not create held-out D3/D7 evidence, expert labels,
semantic validity evidence, retrieval policy validation, parity/superiority
evidence, or SOTA evidence.

---

## References Reviewed

- `scripts/validate_d3_comparison_protocol.py` - D3 protocol validator CLI
  contract.
- `scripts/preflight_d3_comparison.py` - D3 protocol/gold/prediction preflight
  CLI contract.
- `scripts/validate_d7_comparison_protocol.py` - D7 protocol validator CLI
  contract.
- `scripts/preflight_d7_comparison.py` - D7 protocol/gold/prediction preflight
  CLI contract.
- `Makefile` D3/D7 comparison protocol/preflight targets.
- `qc_cli.py` existing D3/D7 package validator and D7 comparison/package
  wrappers.
- `tests/test_d3_comparison_protocol.py`, `tests/test_d3_comparison_preflight.py`,
  `tests/test_d7_comparison_protocol.py`, and
  `tests/test_d7_comparison_preflight.py` - canonical behavior.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - D3/D7
  comparison caveats and claim discipline.
- Memory context:
  `agent-memory recall 'qualitative_coding D3 D7 comparison protocol preflight qc_cli wrappers active decisions' --project qualitative_coding`
  returned low-relevance historical outcomes only, no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned only an
  unrelated `llm_client` claim file.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for existing
repo-local scripts.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py validate-d3-comparison-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py d3-comparison-preflight` | protocol path + gold path + prediction paths | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py validate-d7-comparison-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py d7-comparison-preflight` | protocol path + gold path + prediction paths | canonical preflight report | qualitative_coding | agents/operators | free |

### Capability Validation

- [ ] Each command parses through `qc_cli.py`.
- [ ] Each handler delegates to the matching script `main()`.
- [ ] Protocol and gold positional paths are forwarded exactly.
- [ ] Repeated prediction paths are forwarded in order.
- [ ] Docs state these are protocol/preflight/provenance surfaces only, not
  held-out comparison evidence or SOTA support.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_d3_d7_comparison_protocol_surfaces.py`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Add failing wrapper tests that monkeypatch each canonical script `main()` and
   assert exact argv forwarding.
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
| `tests/test_qc_cli_d3_d7_comparison_protocol_surfaces.py` | `test_qc_cli_comparison_protocol_surface_forwards_args` | All four wrappers delegate exact argv to canonical scripts. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_d3_d7_comparison_protocol_surfaces.py tests/test_d3_comparison_protocol.py tests/test_d3_comparison_preflight.py tests/test_d7_comparison_protocol.py tests/test_d7_comparison_preflight.py -q` | CLI wrappers plus canonical validator/preflight behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_d3_d7_comparison_protocol_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] All four `qc_cli.py` commands parse successfully.
- [ ] Each handler calls the matching canonical script `main()`.
- [ ] Supplied arguments are forwarded exactly in canonical script form.
- [ ] Prediction package paths preserve order.
- [ ] Existing Make/script behavior is unchanged.
- [ ] Docs/CLAUDE mention the top-level CLI aliases without implying held-out
  D3/D7 evidence, validity evidence, parity/superiority evidence, or SOTA.

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
| Prediction order changes | Handler sorts or re-shapes prediction paths | Forward `args.predictions` in parsed order. |
| Protocol/preflight logic duplicated in `qc_cli.py` | Wrapper reimplements script work | Keep handlers as argv delegation only. |
| Docs overclaim | Protocol checks sound like held-out benchmark evidence | Keep caveats: protocol/preflight/provenance only, not validity or SOTA evidence. |
