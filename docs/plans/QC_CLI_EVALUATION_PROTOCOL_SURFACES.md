# Plan #191: QC CLI Evaluation Protocol Surfaces

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** D4/D6/D8/D9/confidence protocol scripts and Make targets
**Blocks:** Top-level CLI parity for Phase 0 evaluator protocol/preflight workflows

---

## Gap

**Current:** Phase 0 evaluator protocol validation and result-preflight surfaces
exist through scripts and Make targets for D4, D6, D8, D9, and confidence
calibration:

- `validate-d4-codebook-quality-protocol`
- `d4-codebook-quality-preflight`
- `validate-d6-bias-protocol`
- `d6-bias-preflight`
- `validate-d8-gt-fidelity-protocol`
- `d8-gt-fidelity-preflight`
- `validate-d9-interpretive-preference-protocol`
- `d9-interpretive-preference-preflight`
- `validate-confidence-calibration-protocol`
- `confidence-calibration-preflight`

`qc_cli.py` supports the corresponding score-time `bench` flags, but it does
not expose these protocol validation/preflight steps as top-level commands.

**Target:** Add ten thin `qc_cli.py` wrappers, one for each existing Make/script
surface, delegating to the matching canonical script `main()` with exact argv
forwarding.

**Why:** The documented benchmark workflow should be agent-drivable through the
canonical CLI as well as Make/scripts. These surfaces are prerequisite
orchestration/provenance checks for populated D4/D6/D8/D9/confidence benchmark
inputs.

**Non-target:** This slice does not change protocol schemas, preflight
semantics, score-time guards, scorecards, Make targets, or benchmark evidence.
It does not generate labels, run LLM-judge/human panels, run bias audits,
collect GT-fidelity ratings, collect blind preference outcomes, calibrate
confidence, prove methodological validity, or create SOTA evidence.

---

## References Reviewed

- D4 scripts: `scripts/validate_d4_codebook_quality_protocol.py`,
  `scripts/preflight_d4_codebook_quality_protocol.py`.
- D6 scripts: `scripts/validate_d6_bias_protocol.py`,
  `scripts/preflight_d6_bias_protocol.py`.
- D8 scripts: `scripts/validate_d8_gt_fidelity_protocol.py`,
  `scripts/preflight_d8_gt_fidelity_protocol.py`.
- D9 scripts: `scripts/validate_d9_interpretive_preference_protocol.py`,
  `scripts/preflight_d9_interpretive_preference_protocol.py`.
- Confidence scripts: `scripts/validate_confidence_calibration_protocol.py`,
  `scripts/preflight_confidence_calibration_protocol.py`.
- `Makefile` protocol/preflight targets.
- Existing protocol/preflight tests for D4/D6/D8/D9/confidence.
- `docs/EVALUATION_HARNESS.md` D4/D6/D8/D9/confidence caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` roadmap and claim-discipline caveats.

---

## Research Basis For This Slice

No external research is needed. This is deterministic CLI parity for existing
repo-local scripts.

---

## Capabilities

Internal CLI delegation only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `qc_cli.py validate-d4-codebook-quality-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py d4-codebook-quality-preflight` | protocol path + optional quality path | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py validate-d6-bias-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py d6-bias-preflight` | protocol path + optional stratified/counterfactual paths | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py validate-d8-gt-fidelity-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py d8-gt-fidelity-preflight` | protocol path + optional GT-fidelity path | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py validate-d9-interpretive-preference-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py d9-interpretive-preference-preflight` | protocol path + optional preference path | canonical preflight report | qualitative_coding | agents/operators | free |
| `qc_cli.py validate-confidence-calibration-protocol` | protocol path | canonical validator output | qualitative_coding | agents/operators | free |
| `qc_cli.py confidence-calibration-preflight` | protocol path + optional calibration path | canonical preflight report | qualitative_coding | agents/operators | free |

### Capability Validation

- [ ] Each command parses through `qc_cli.py`.
- [ ] Each handler delegates to the matching script `main()`.
- [ ] Positional protocol paths are forwarded exactly.
- [ ] Optional result-file arguments are forwarded only when supplied.
- [ ] D6 preflight preserves both optional `--stratified-file` and
  `--counterfactual-file` arguments.
- [ ] Docs state these are protocol/preflight/accounting surfaces only, not
  populated label/evaluation evidence or SOTA support.

---

## Files Affected

- `qc_cli.py`
- `tests/test_qc_cli_evaluation_protocol_surfaces.py`
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
| `tests/test_qc_cli_evaluation_protocol_surfaces.py` | `test_qc_cli_evaluation_protocol_surface_forwards_args` | All ten wrappers delegate exact argv to canonical scripts. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_qc_cli_evaluation_protocol_surfaces.py tests/test_d4_codebook_quality_protocol.py tests/test_d4_codebook_quality_preflight.py tests/test_d6_bias_protocol.py tests/test_d6_bias_preflight.py tests/test_d8_gt_fidelity_protocol.py tests/test_d8_gt_fidelity_preflight.py tests/test_d9_interpretive_preference_protocol.py tests/test_d9_interpretive_preference_preflight.py tests/test_confidence_calibration_protocol.py tests/test_confidence_calibration_preflight.py -q` | CLI wrappers and canonical script behavior. |
| `python -m ruff check qc_cli.py tests/test_qc_cli_evaluation_protocol_surfaces.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] All ten `qc_cli.py` commands parse successfully.
- [ ] Each handler calls the matching canonical script `main()`.
- [ ] Supplied arguments are forwarded exactly in canonical script form.
- [ ] Omitted optional result-file arguments are not forwarded.
- [ ] Existing Make/script behavior is unchanged.
- [ ] Docs/CLAUDE mention the top-level CLI aliases without implying populated
  evidence, validity evidence, parity/superiority evidence, or SOTA.

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
| Protocol/preflight logic duplicated in `qc_cli.py` | Wrapper reimplements script work | Keep handlers as argv delegation only. |
| Optional args forwarded as `None` strings | Handler blindly forwards fields | Forward optional flags only when non-null. |
| Wrong result flag | Handler maps to the wrong script flag | Lock exact argv with wrapper tests. |
| Docs overclaim | Protocol checks sound like benchmark evidence | Keep caveats: protocol/preflight/accounting only, not populated outcomes or validity evidence. |
