# Plan #224: Sampling-Frame Adequacy Protocol Preflight

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** governed sampling-frame adequacy evaluation beyond scope-record completeness

---

## Gap

**Current at plan start:** `ProjectState.corpus_scope` records phenomenon,
population, sampling frame, inclusion/exclusion criteria, and caveats.
`make bench` reports deterministic `corpus_scope_adequacy`, but that is only
record-completeness accounting. The roadmap explicitly says actual
sampling-frame adequacy evaluation beyond record completeness remains missing.

**Target:** Add a versioned sampling-frame adequacy protocol/result preflight
substrate:

- a schema_version=1 protocol package validator,
- a schema_version=1 result row/package contract,
- a preflight report that cross-checks result packages against the protocol,
- script, Make, and `qc_cli.py` surfaces, and
- focused tests.

**Why:** This gives future human/methodologist review of sampling frames a
governed, hash-locked, pre-registered input/output path instead of treating
`CorpusScope` field presence as adequacy evidence.

**Claim boundary:** This is protocol/preflight infrastructure only. It does not
populate reviewer judgments, prove sampling-frame adequacy, permit population
generalization, establish methodological validity, or support SOTA claims.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13/§18 - corpus boundary status and
  remaining sampling-frame adequacy gap.
- `docs/EVALUATION_HARNESS.md` - current `corpus_scope_adequacy` caveat.
- `qc_clean/core/bench.py` - deterministic `corpus_scope_adequacy_scorecard`.
- `qc_clean/schemas/domain.py` - `CorpusScope`.
- `qc_clean/core/d8_gt_fidelity_protocol.py` and
  `qc_clean/core/d8_gt_fidelity_preflight.py` - protocol/preflight pattern.
- `scripts/validate_d8_gt_fidelity_protocol.py` and
  `scripts/preflight_d8_gt_fidelity_protocol.py` - script pattern.
- `tests/test_d8_gt_fidelity_protocol.py` and
  `tests/test_d8_gt_fidelity_preflight.py` - focused test pattern.
- Coordination claims:
  `python scripts/meta/check_coordination_claims.py --check --project qualitative_coding --scope sampling-frame-adequacy`
  returned no active claims.
- Memory context:
  `agent-memory recall 'sampling frame adequacy active decisions qualitative coding' --project qualitative_coding`
  returned no relevant active decision.

---

## Research Basis For This Slice

No external research is needed. This is a local evaluation-contract substrate
mirroring existing D4/D6/D8/D9/confidence protocol/preflight patterns.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `validate_sampling_frame_adequacy_protocol` | schema_version=1 protocol JSON | normalized validation summary JSON | qualitative_coding | sampling-frame review workflows | free |
| `sampling_frame_adequacy_preflight` | protocol JSON + result package JSON | preflight report JSON | qualitative_coding | scorecard/artifact workflows | free |

### Capability Validation

Skipped for cross-project registry purposes: this is a project-local evaluation
surface.

---

## Files Affected

- `docs/plans/SAMPLING_FRAME_ADEQUACY_PROTOCOL_PREFLIGHT.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `qc_clean/core/sampling_frame_adequacy_protocol.py` - protocol/result
  contracts.
- `qc_clean/core/sampling_frame_adequacy_preflight.py` - protocol/result
  cross-checking.
- `scripts/validate_sampling_frame_adequacy_protocol.py` - protocol validator
  CLI.
- `scripts/preflight_sampling_frame_adequacy_protocol.py` - preflight CLI.
- `Makefile` - validation/preflight targets.
- `qc_cli.py` - top-level wrappers.
- `tests/test_sampling_frame_adequacy_protocol.py` - protocol tests.
- `tests/test_sampling_frame_adequacy_preflight.py` - preflight tests.
- `tests/test_qc_cli_sampling_frame_adequacy_surfaces.py` - wrapper tests.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`

---

## Plan

### Steps

1. Commit this plan before implementation.
2. Add protocol/result Pydantic contracts for sampling-frame adequacy.
3. Add preflight cross-checking for protocol/result metadata, hash locks,
   evaluator plan drift, required dimensions, result row coverage, and caveats.
4. Add script CLIs that emit machine-readable JSON and fail loud on invalid
   inputs.
5. Add Make targets and `qc_cli.py` wrappers.
6. Add focused tests for valid packages, invalid packages, preflight drift, and
   CLI forwarding.
7. Update docs conservatively with non-evidentiary caveats.
8. Run focused tests, touched Ruff, docs checks, whitespace checks, and
   `make check`.
9. Commit/push implementation and close the plan.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_sampling_frame_adequacy_protocol.py` | protocol accepts valid held-out package | Required metadata, dimensions, evaluator plan, hashes, and criteria validate. |
| `tests/test_sampling_frame_adequacy_protocol.py` | protocol rejects missing held-out gates / dimensions / bad hashes | Invalid protocols fail loud. |
| `tests/test_sampling_frame_adequacy_protocol.py` | validator script outputs JSON | Script success/failure emits parseable JSON. |
| `tests/test_sampling_frame_adequacy_preflight.py` | preflight accepts matching protocol/result package | Matching rows produce `status="pass"`. |
| `tests/test_sampling_frame_adequacy_preflight.py` | preflight rejects missing result, hash mismatch, evaluator drift, dimension drift | Cross-check failures are visible. |
| `tests/test_sampling_frame_adequacy_preflight.py` | preflight script outputs JSON | Script success/failure emits parseable JSON. |
| `tests/test_qc_cli_sampling_frame_adequacy_surfaces.py` | CLI forwards protocol validation/preflight args | Top-level `qc_cli.py` delegates to canonical scripts. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_sampling_frame_adequacy_protocol.py tests/test_sampling_frame_adequacy_preflight.py tests/test_qc_cli_sampling_frame_adequacy_surfaces.py -q` | Focused new surface coverage. |
| `python -m ruff check qc_clean/core/sampling_frame_adequacy_protocol.py qc_clean/core/sampling_frame_adequacy_preflight.py scripts/validate_sampling_frame_adequacy_protocol.py scripts/preflight_sampling_frame_adequacy_protocol.py qc_cli.py tests/test_sampling_frame_adequacy_protocol.py tests/test_sampling_frame_adequacy_preflight.py tests/test_qc_cli_sampling_frame_adequacy_surfaces.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] `make validate-sampling-frame-adequacy-protocol PROTOCOL=protocol.json`
  validates schema_version=1 protocol metadata.
- [x] `python qc_cli.py validate-sampling-frame-adequacy-protocol protocol.json`
  delegates to the same validator.
- [x] `make sampling-frame-adequacy-preflight PROTOCOL=protocol.json ADEQUACY=adequacy.json`
  preflights result packages against the protocol.
- [x] `python qc_cli.py sampling-frame-adequacy-preflight protocol.json --adequacy-file adequacy.json`
  delegates to the same preflight.
- [x] Invalid protocols/results fail loud with machine-readable errors.
- [x] Docs preserve claim discipline: this is protocol/preflight
  infrastructure only, not populated reviewer evidence, sampling-frame adequacy
  evidence, population-generalization permission, methodological-validity
  evidence, or SOTA evidence.

Process criteria:

- [x] Focused tests pass.
- [x] Touched Python Ruff gate passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Completed in commit `b30eb970`.

Implemented sampling-frame adequacy protocol/preflight infrastructure:

- `qc_clean/core/sampling_frame_adequacy_protocol.py` defines
  schema_version=1 protocol and result package contracts.
- `qc_clean/core/sampling_frame_adequacy_preflight.py` cross-checks result
  packages against protocol IDs, project/corpus/scope hashes, reviewer plans,
  required dimensions, outcome-file hashes, and caveats.
- `scripts/validate_sampling_frame_adequacy_protocol.py` emits
  machine-readable validator JSON.
- `scripts/preflight_sampling_frame_adequacy_protocol.py` emits
  machine-readable preflight reports.
- `make validate-sampling-frame-adequacy-protocol` and
  `make sampling-frame-adequacy-preflight` expose the surfaces.
- `qc_cli.py validate-sampling-frame-adequacy-protocol` and
  `qc_cli.py sampling-frame-adequacy-preflight` delegate to the scripts.
- `CLAUDE.md`, generated `AGENTS.md`, `docs/EVALUATION_HARNESS.md`, and
  `docs/PROJECT_THEORY_AND_GOALS.md` document the new surfaces while preserving
  non-evidentiary caveats.

Verification:

- `python -m pytest tests/test_sampling_frame_adequacy_protocol.py tests/test_sampling_frame_adequacy_preflight.py tests/test_qc_cli_sampling_frame_adequacy_surfaces.py -q`
  - 13 passed
- `python -m ruff check qc_clean/core/sampling_frame_adequacy_protocol.py qc_clean/core/sampling_frame_adequacy_preflight.py scripts/validate_sampling_frame_adequacy_protocol.py scripts/preflight_sampling_frame_adequacy_protocol.py qc_cli.py tests/test_sampling_frame_adequacy_protocol.py tests/test_sampling_frame_adequacy_preflight.py tests/test_qc_cli_sampling_frame_adequacy_surfaces.py`
  - passed
- CLI/Make smoke with temporary valid protocol/result packages:
  - `qc_cli.py validate-sampling-frame-adequacy-protocol` passed
  - `make -s sampling-frame-adequacy-preflight` produced `status="pass"`,
    `result_row_count=5`, and `reviewer_count=2`
- `make docs-check`
  - passed
- `git diff --check`
  - passed
- `make check`
  - 1321 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed;
    type check is not yet configured

---

## Open Questions

- [x] Should this feed `make bench` immediately?
  Status: RESOLVED. No. This slice adds the governed protocol/preflight
  substrate; a later score-time guard can feed Phase 0 once the result package
  shape is stable.

---

## Notes

This mirrors the existing evaluation-harness pattern: protocol validation and
preflight first, score-time guard later, populated evidence only when external
review rows exist.
