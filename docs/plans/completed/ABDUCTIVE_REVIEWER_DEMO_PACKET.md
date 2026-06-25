# Plan #230: Abductive Reviewer Demo Packet

## Outcome

Completed 2026-06-25. Extended the deterministic reviewer demo packet with
synthetic observed-pattern and provisional abductive-candidate outputs. The
fixture state now includes three `ObservedPattern` records and two
`AbductiveCandidateExplanation` records tied to those patterns. `make
reviewer-demo OUTPUT=test_output/reviewer_demo` now writes pattern and
abductive API snapshots, README inspection commands for `project patterns` and
`project abductive`, and Markdown sections for both output surfaces. I generated
the packet locally and self-inspected CLI, Markdown, and snapshot outputs before
handoff. This remains synthetic software-surface demonstration only, not live
LLM evidence, methodological-validity evidence, causal proof, or SOTA evidence.

Verification:

- `python -m pytest tests/test_reviewer_demo.py -q` — 2 passed.
- `python -m ruff check scripts/build_reviewer_demo.py tests/test_reviewer_demo.py` — passed.
- `make reviewer-demo OUTPUT=test_output/reviewer_demo` — passed and wrote `patterns_snapshot` / `abductive_snapshot`.
- `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py project patterns reviewer-demo --show-anchors --limit 5` — self-inspected 3 observed patterns with anchors/caveats.
- `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py project abductive reviewer-demo --limit 5` — self-inspected 2 provisional candidates with rivals/implications/gaps/caveats.
- `grep` inspection of `test_output/reviewer_demo/exports/reviewer-demo-report.md` confirmed `Observed Patterns` and `Abductive Candidate Explanations` sections.
- `python -m json.tool test_output/reviewer_demo/api_snapshots/abductive_snapshot.json` and `patterns_snapshot.json` confirmed expected row shapes.
- `make docs-check` — passed.
- `git diff --check` — passed.
- `make check` — 1340 passed, 1 skipped, 8 deselected; Ruff/docs passed; type check not configured.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #226, #227, #228, #229
**Blocks:** Brian review of abductive output surfaces, process-tracing handoff review

---

## Gap

**Current:** The repo has a deterministic `make reviewer-demo` packet with
claims/review/graph exports, and it has new observed-pattern and abductive
candidate read surfaces. The packet does not yet include those new surfaces, so
Brian cannot inspect the abductive output without raw JSON or manually
constructing state.

**Target:** Extend the deterministic reviewer demo packet to include synthetic
observed patterns, provisional abductive candidate explanations, API snapshots,
README commands, and Markdown report sections. Regenerate the packet locally
and self-inspect the relevant outputs before handing paths to Brian.

**Why:** Brian asked to see output only after we have run and reviewed it
ourselves. The existing deterministic packet is the safest output surface: it
uses synthetic data, no live LLM calls, an isolated `QC_PROJECTS_DIR`, and
reviewable artifacts.

---

## References Reviewed

- `scripts/build_reviewer_demo.py` - fixture state, export, snapshot, README
  generation.
- `tests/test_reviewer_demo.py` - expected packet artifacts and env-store load
  behavior.
- `qc_clean/schemas/domain.py` - `ObservedPattern` and
  `AbductiveCandidateExplanation` models.
- `qc_clean/core/export/data_exporter.py` - Markdown sections for patterns and
  abductive candidates.
- `qc_clean/plugins/api/api_server.py` - `/patterns` and
  `/abductive-explanations` endpoints.
- `docs/plans/completed/ABDUCTIVE_CANDIDATE_READ_SURFACES.md` - read-surface
  verification and caveats.

---

## Research Basis For This Slice

No external research is needed. This is deterministic demo/readiness work over
already-implemented local surfaces.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Reviewer demo packet generation | output directory path | manifest paths + isolated packet files | `scripts/build_reviewer_demo.py` | Brian, agents, future reviewers | free / no LLM calls |

### Capability Validation

- [x] Packet includes local project state and exports.
- [x] Packet includes observed-pattern and abductive candidate API snapshots.
- [x] README contains CLI/API inspection commands for both surfaces.
- [x] Demo output caveats say synthetic packet only, not validity/SOTA evidence.

---

## Files Affected

- `scripts/build_reviewer_demo.py` - add observed/candidate fixture rows,
  snapshots, README commands.
- `tests/test_reviewer_demo.py` - assert new packet artifacts and report
  content.
- `docs/plans/ACTIVE_SPRINT.md` and `docs/plans/CLAUDE.md` - plan tracking.
- Potentially generated `test_output/reviewer_demo/` artifacts if the repo
  already tracks them or if the packet is intentionally refreshed.

---

## Plan

### Steps

1. Add deterministic observed-pattern records to `_demo_state()`.
2. Add deterministic abductive candidate explanations tied to those pattern IDs.
3. Add `/patterns` and `/abductive-explanations` API snapshots to the packet
   manifest.
4. Add README commands for `project patterns`, `project abductive`, and direct
   API URLs.
5. Update tests to assert the new snapshots/report sections exist.
6. Run `make reviewer-demo OUTPUT=test_output/reviewer_demo`.
7. Self-inspect:
   - `QC_PROJECTS_DIR=... python qc_cli.py project patterns reviewer-demo`
   - `QC_PROJECTS_DIR=... python qc_cli.py project abductive reviewer-demo`
   - Markdown report sections.
   - API snapshot JSON shape.
8. Run focused tests, Ruff, docs checks, `git diff --check`, and `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_reviewer_demo.py` | update `test_build_reviewer_demo_writes_packet` | Manifest contains pattern/abductive snapshots and Markdown includes both sections/caveats. |
| `tests/test_reviewer_demo.py` | update `test_reviewer_demo_project_loads_from_env_store` | Generated state has observed patterns and abductive candidates. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_reviewer_demo.py -q` | Focused packet coverage. |
| `python -m ruff check scripts/build_reviewer_demo.py tests/test_reviewer_demo.py` | Touched-file lint. |
| `make reviewer-demo OUTPUT=test_output/reviewer_demo` | Prove actual packet generation. |
| `make docs-check` | Plan/docs/generated mirror checks. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Demo project state contains synthetic observed patterns.
- [x] Demo project state contains synthetic provisional abductive candidate
  explanations tied to observed patterns.
- [x] Packet manifest includes observed-pattern and abductive-candidate API
  snapshots.
- [x] Markdown report includes observed-pattern and abductive-candidate sections.
- [x] README tells Brian exactly which CLI/API surfaces to inspect.
- [x] All demo caveats remain synthetic/software-surface only.

> Process criteria:
- [x] Required focused tests pass.
- [x] `make reviewer-demo OUTPUT=test_output/reviewer_demo` passes.
- [x] Self-inspection commands are run and summarized.
- [x] Ruff passes for touched files.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should live LLM abductive output be included? Status: RESOLVED no. Use
  deterministic synthetic candidate rows for the review packet; live LLM output
  belongs in a later benchmark/demo lane with budget and model provenance.
- [ ] Should demo artifacts be committed? Status: FOLLOW EXISTING REPO PATTERN.
  If `test_output/reviewer_demo` is already tracked or changed by the generator,
  include only intentional generated artifacts; otherwise leave it as local
  output and commit code/tests/docs only.

---

## Notes

This packet is for review orientation. It should help Brian see what the output
surface looks like without claiming the synthetic interpretations are correct.
