# Plan #91: INV-3 Adjudication Sample Export

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Claim ledger object layer; review API/MCP/browser first slices
**Blocks:** INV-3 expert adjudication protocol; populated D3/D7/D4/D8/D9 evaluation workflows

---

## Gap

**Current:** The evaluation harness can score externally supplied D3/D7 gold
packages and other adjudicated outcome files, and the review surfaces can show
codes, claims, negative cases, and relationships. The missing upstream step is
a deterministic, agent-drivable sample export that creates the packet a human or
expert adjudicator should label. Without that sample frame, "expert
adjudication" remains procedurally ambiguous even though downstream scoring
contracts exist.

**Target:** Add a schema_version=1 adjudication sample package exporter that
collects bounded review targets from a `ProjectState`, includes enough source
context and provenance for human review, and writes JSON through CLI/Make
surfaces:

- Core package builder in `qc_clean/core/adjudication_sample.py`.
- CLI: `qc_cli.py project adjudication-sample <project_id> --output-file sample.json`.
- Make: `make adjudication-sample ID=<project_id> OUTPUT=sample.json`.

This package is **unlabeled**. It is the input to human/expert review, not
validity evidence.

**Why:** INV-3 says validity adjudication must be separate from consistency.
Existing scorecards consume labels after adjudication, but the repo needs a
deterministic way to generate the review sample itself before any populated
expert protocol can be run.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:355-356` - INV-2/INV-3 caveats around
  human-adjudicated disconfirmation and validity.
- `docs/PROJECT_THEORY_AND_GOALS.md:419-452` - roadmap priority and remaining
  held-out/expert-evidence gaps.
- `docs/EVALUATION_HARNESS.md` - scorecards consume adjudicated/gold inputs;
  this plan creates a sample export, not scores.
- `qc_clean/core/d3_gold.py` and `qc_clean/core/d7_gold.py` - downstream gold
  package provenance conventions.
- `qc_clean/schemas/domain.py` - project state objects to sample:
  `CodeApplication`, `AnalyticClaim`, code/entity relationships.
- `qc_clean/core/cli/commands/project.py` and `qc_cli.py` - project subcommand
  conventions.
- `Makefile` - agent-drivable project targets.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No new external research is required. This is a repo-local protocol/export
slice that prepares adjudication inputs without asserting results.

---

## Capabilities

| Capability | Input | Output | Consumer |
|------------|-------|--------|----------|
| `build_adjudication_sample_package` | `ProjectState`, limit/config | schema_version=1 package dict/Pydantic model | CLI, Make, future expert workflow |
| `write_adjudication_sample_package` | package + output path | JSON file | human/expert adjudicators, future validators |

---

## Files Affected

- `qc_clean/core/adjudication_sample.py` (create)
- `qc_clean/core/cli/commands/project.py` (modify)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `tests/test_adjudication_sample.py` (create)
- `tests/test_project_commands.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV3_ADJUDICATION_SAMPLE_EXPORT.md` (create, then move to completed)

---

## Plan

### Decisions

- Export is deterministic by default: stable type order and object ID order,
  capped by `limit_per_type`. No random sampling in this first slice.
- Package item types:
  `code_application`, `claim`, `negative_case`, `code_relationship`,
  `entity_relationship`.
- Negative cases remain claim rows with `claim_kind="negative_case"` but get
  `target_type="negative_case"` in the sample package so adjudicators can find
  them directly.
- Every item includes `response_template` with empty fields for:
  `validity`, `rationale`, `corrected_value`, and `adjudicator_id`.
- Package includes project/corpus hashes for provenance, corpus scope when
  available, item counts by type, and a caution note that labels are absent.
- This plan does not create D3/D7 gold labels, run experts, infer validity, or
  score anything.

### Steps

1. Add Pydantic package/item models and a builder in
   `qc_clean/core/adjudication_sample.py`.
2. Include document/code/entity lookups and compact source context for anchored
   applications/claim anchors where offsets are available.
3. Add CLI parser/action `project adjudication-sample` with
   `--output-file`, `--limit-per-type`, and `--context-chars`.
4. Add a Make target wrapping the CLI.
5. Add core and CLI tests.
6. Update docs conservatively: adjudication sample export exists, but expert
   adjudication and validity evidence remain absent until populated labels are
   collected and scored.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_adjudication_sample.py` | `test_builds_deterministic_adjudication_sample_package` | Package includes schema_version, hashes, counts, stable item order, source context, and response templates. |
| `tests/test_adjudication_sample.py` | `test_limit_per_type_and_negative_case_split` | Limit applies per target type and negative-case claims are split from generic claims. |
| `tests/test_project_commands.py` | `test_project_adjudication_sample_command_writes_json` | CLI handler writes the package file and reports item count. |
| `tests/test_project_commands.py` | `test_project_adjudication_sample_missing_project_fails` | Missing project fails loudly with nonzero exit. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_adjudication_sample.py tests/test_project_commands.py -q` | New exporter and CLI behavior. |
| `make docs-check` | Plan/doc sync and generated `AGENTS.md`. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Core builder emits schema_version=1 packages with project/corpus hashes.
- [ ] Package contains deterministic bounded samples of applications, claims,
  negative cases, code relationships, and entity relationships when present.
- [ ] Items include enough provenance/context for human adjudication and an
  explicit empty response template.
- [ ] CLI writes the JSON package and fails clearly for missing projects.
- [ ] Make target exposes the workflow for agents.
- [ ] Docs state this is an adjudication input substrate, not expert evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should future sampling be stratified/randomized by code, document, or
  uncertainty? - Status: DEFERRED | Why it matters: true evaluation sampling
  likely needs a pre-registered strategy; this slice is deterministic frame
  export only.
- [ ] Should labels entered into this sample package be transformable directly
  into D3/D7 gold files? - Status: DEFERRED | Why it matters: that requires a
  separate validator/importer so labels cannot silently become scorecard gold.

---

## Notes

This plan creates the packet to hand to adjudicators. It intentionally does not
claim that adjudication has happened, that labels are expert-quality, or that
any SOTA/validity threshold has been met.
