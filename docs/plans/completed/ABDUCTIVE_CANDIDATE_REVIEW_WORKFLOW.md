# Plan #232: Abductive Candidate Review Workflow

## Outcome

Completed 2026-06-25. Added first-class review semantics for provisional
abductive candidate explanations. `ReviewManager` now lists candidates as
review targets, `ReviewSummary` reports `abductive_candidates_count`, and
`target_type="abductive_candidate"` decisions can approve candidates into
`needs_evidence_review`, reject them without deleting evidence history, or
modify bounded explanatory fields. The API now exposes
`/projects/{project_id}/review/abductive-candidates`, review decision POST
responses include candidate counts, the CLI review summary reports candidate
counts, JSON-file review decisions work through the existing CLI path, and the
deterministic reviewer demo packet includes a candidate-review API snapshot.
This governs provisional hypotheses before handoff; it is not causal proof,
process-tracing evidence, methodological-validity evidence, or SOTA evidence.

Verification:

- `python -m pytest tests/test_review.py tests/test_review_api.py -q` — 77
  passed.
- `python -m pytest tests/test_reviewer_demo.py tests/test_review.py
  tests/test_review_api.py tests/test_project_commands.py::TestAPIEndpoints::test_get_project_endpoint_registered
  -q` — 80 passed.
- `python -m ruff check qc_cli.py qc_clean/core/cli/commands/review.py
  qc_clean/core/pipeline/review.py qc_clean/plugins/api/api_server.py
  qc_clean/schemas/domain.py scripts/build_reviewer_demo.py tests/test_review.py
  tests/test_review_api.py tests/test_reviewer_demo.py
  tests/test_project_commands.py` — passed.
- `make reviewer-demo OUTPUT=test_output/reviewer_demo` — passed.
- `python -m json.tool
  test_output/reviewer_demo/api_snapshots/review_abductive_candidates_snapshot.json`
  — self-inspected bounded candidate review rows and caveats.
- Temp-store CLI check with `qc_cli.py review reviewer-demo --file
  decision.json` — applied one `abductive_candidate` approval and
  `project abductive` showed `needs_evidence_review`.
- `make docs-check` — passed.
- `git diff --check` — passed.
- `make check` — 1347 passed, 1 skipped, 8 deselected; Ruff/docs passed; type
  check not configured.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #231
**Blocks:** #233, process-tracing handoff review

---

## Gap

**Current:** `project run --abductive` can create provisional
`AbductiveCandidateExplanation` records, and CLI/API/Markdown read surfaces can
inspect them. Review decisions support codes, code applications, codebooks,
claims, code relationships, and entity relationships, but not abductive
candidate explanations.

**Target:** Add first-class CLI/API/manager review semantics for abductive
candidates while keeping browser UI deferred. Candidates can be listed as
review targets and approved/rejected/modified through the existing
agent-drivable review decision endpoint and JSON-file CLI path.

**Why:** The next workbench/process-tracing handoff must not export unchecked
hypotheses as analyst-approved findings. Candidate review must exist before
typed handoff packages.

---

## References Reviewed

- `docs/LONG_TERM_EXECUTION_PLAN.md` - names Plan #232 as the next
  implementation slice.
- `qc_clean/schemas/domain.py` - `AbductiveCandidateExplanation`,
  `AbductiveExplanationStatus`, `HumanReviewDecision`, and `ReviewSummary`.
- `qc_clean/core/pipeline/review.py` - central review manager and target-type
  dispatch.
- `qc_clean/core/abductive.py` - existing candidate row serializer and summary.
- `qc_clean/plugins/api/api_server.py` - review-list endpoints and review
  decision POST path.
- `qc_clean/core/cli/commands/review.py` - JSON-file review decision CLI.
- `tests/test_review.py` - manager behavior tests.
- `tests/test_review_api.py` - review API fixtures and endpoint tests.
- `tests/test_project_commands.py` and `tests/test_reviewer_demo.py` - existing
  abductive read-surface/demo coverage.
- Memory context: Plan #231 memory recalls returned broad historical task
  summaries and no active decisions overriding repo docs.

---

## Research Basis For This Slice

No external research is needed. This is an internal review-semantics slice over
existing domain models and API/CLI patterns.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Review abductive candidate | `HumanReviewDecision(target_type="abductive_candidate")` | Mutated `AbductiveCandidateExplanation.status` / fields + persisted decision | `ReviewManager.apply_decision` | CLI, API, future handoff package | free / no LLM calls |
| List abductive candidates for review | `project_id`, `limit`, `offset` | Candidate review rows + summary metadata | API review endpoint | agents, future UI | free / no LLM calls |

### Capability Validation

- [x] Manager accepts `approve`, `reject`, and `modify` for
  `abductive_candidate`.
- [x] Manager fails loud for missing candidate IDs and unsupported actions.
- [x] API review list returns bounded candidate rows and summary counts.
- [x] Existing review decision POST can persist candidate decisions.

---

## Files Affected

- `qc_clean/schemas/domain.py` - add candidate count to `ReviewSummary` if
  needed.
- `qc_clean/core/pipeline/review.py` - add candidate pending rows and decision
  handling.
- `qc_clean/plugins/api/api_server.py` - add `/review/abductive-candidates`
  listing and response count.
- `tests/test_review.py` - manager tests for candidate review.
- `tests/test_review_api.py` - API listing and decision tests.
- `docs/plans/ACTIVE_SPRINT.md` and `docs/plans/CLAUDE.md` - plan tracking.
- `docs/CONCERNS.md` - close or update `QC-ABD-001` after verification.

---

## Plan

### Steps

1. Register Plan #232 as active and commit the planned state.
2. Add focused manager tests for pending candidate rows and
   approve/reject/modify semantics.
3. Add API tests for `/projects/{id}/review/abductive-candidates` and POST
   decision persistence.
4. Implement `ReviewManager.get_pending_abductive_candidates()`.
5. Implement `ReviewManager._apply_abductive_candidate_decision()`.
6. Add review summary count for abductive candidates and include API response
   count on decision POST.
7. Add API listing endpoint with bounded `limit`/`offset`.
8. Update concern register and close the plan after verification.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review.py` | `test_abductive_candidate_review_summary_and_pending_rows` | Candidates are countable/listable as review targets. |
| `tests/test_review.py` | `test_abductive_candidate_review_approve_reject_modify_updates_status_and_fields` | Decisions mutate candidate status/fields as intended. |
| `tests/test_review.py` | `test_abductive_candidate_review_invalid_id_fails_loud` | Missing candidate IDs raise clear errors. |
| `tests/test_review.py` | `test_abductive_candidate_review_rejects_unsupported_fields` | Modify cannot mutate arbitrary fields. |
| `tests/test_review_api.py` | `test_returns_abductive_candidates_for_review` | API list endpoint returns bounded rows and summary count. |
| `tests/test_review_api.py` | `test_abductive_candidate_decision_persists` | POST review decision updates candidate status/fields. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review.py tests/test_review_api.py -q` | Focused review manager/API coverage. |
| `python -m ruff check qc_clean/core/pipeline/review.py qc_clean/plugins/api/api_server.py qc_clean/schemas/domain.py tests/test_review.py tests/test_review_api.py` | Touched-file lint. |
| `make docs-check` | Plan/docs governance. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `ReviewSummary` reports abductive candidate count.
- [x] `ReviewManager` lists candidate rows for review.
- [x] `target_type="abductive_candidate"` supports approve, reject, and modify.
- [x] Approve marks candidates as `needs_evidence_review`, not causal proof.
- [x] Reject marks candidates `rejected` without deleting evidence history.
- [x] Modify can update explanatory fields and status but rejects unsupported
  fields.
- [x] API exposes `/projects/{project_id}/review/abductive-candidates` with
  pagination metadata.
- [x] Existing review decision POST persists candidate decisions.
- [x] Existing code/claim/relationship review behavior remains unchanged.

> Process criteria:
- [x] Focused tests pass.
- [x] Ruff passes for touched files.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should approval promote candidates directly to process tracing? Status:
  RESOLVED no. Approval means the candidate is worth evidence review
  (`needs_evidence_review`). Process-tracing promotion is a later handoff
  action.
- [ ] Should browser UI be updated in this slice? Status: RESOLVED no. Browser
  UI follows stable review semantics in a later UI-planned slice.

---

## Notes

This slice governs provisional candidate hypotheses. It must not claim causal
proof, process-tracing results, methodological validity, or SOTA evidence.
