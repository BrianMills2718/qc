# Plan #5: INV-6 Ledger-Wide Disconfirmation and Claim Review

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-6 full disconfirmation coverage; INV-10 claim adjudication; INV-2 retrieval-first disconfirmation hardening

*Started: 2026-06-21. Owner: autonomous agent. Re-read after any compaction.*

---

## Completion Outcome

Completed 2026-06-21. Negative-case analysis now receives bounded claim-ledger
targets by ID, `NegativeCase` can return an exact `target_claim_id`, and
disconfirmation coverage is summarized on CLI/API/MCP claim surfaces. Claim
review decisions now support `target_type="claim"` for approve, reject/withdraw,
and modify, preserving `ClaimRevision` history. This is a first slice for
INV-6/INV-10: it does **not** claim retrieval-first disconfirmation (INV-2),
methodological validity, browser-native claim review, or proof that every claim
has been human-adjudicated.

---

## Gap

**Current:** INV-9's object layer exists: substantive stage outputs are
represented in `ProjectState.claims`. `NegativeCaseStage` still prompts mainly
against the codebook plus the cross-interview memo, and negative-case outputs
can only deterministically target claims by shared code unless the model has a
claim ID field to return. `ReviewManager` records human decisions for codes,
applications, and codebooks, but not `AnalyticClaim` adjudication.

**Target:** Negative-case analysis receives a bounded ledger target list and can
return the exact claim ID it challenges. The system can summarize which claims
have faced disconfirmation. Human/agent review can approve, reject/withdraw, or
revise claim objects through the existing review-decision path, preserving
revision history.

**Why:** INV-6 cannot close while disconfirmation sees only selected prose
surfaces. INV-10 cannot close while human review cannot touch the claim ledger.
This plan deliberately does **not** claim INV-2 retrieval-first hardening or
methodological validity; it creates the deterministic substrate those later
passes need.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:252-263` — INV-2, INV-6, INV-9, INV-10 statuses and claim discipline.
- `docs/EVALUATION_HARNESS.md:42` — D7 disconfirmation metric target.
- `docs/plans/completed/INV9_CLAIM_LEDGER.md` — completed claim-ledger object-layer scope and caveats.
- `qc_clean/core/claims.py` — claim builders, negative-case target fallback, ledger summaries.
- `qc_clean/core/pipeline/stages/negative_case.py` — current prompt/schema and negative-case wiring.
- `qc_clean/core/pipeline/review.py` — current review-decision targets and unsupported claim branch.
- `qc_clean/schemas/domain.py` — `AnalyticClaim`, `ClaimScope`, `ClaimRevision`, `HumanReviewDecision`, `ReviewAction`.
- `tests/test_negative_case_inv6.py`, `tests/test_claims.py`, `tests/test_claim_ledger_pipeline.py` — current invariant coverage.
- Memory context: `agent-memory recall 'active decisions ledger-wide disconfirmation adjudication qualitative coding INV-6 INV-10' --project qualitative_coding` — 2 old completed outcomes; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contained no active claims.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic object-routing slice over an already-defined claim ledger, not a
new methodological claim.

---

## Capabilities

These are internal project capabilities, not cross-project boundary APIs.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `format_disconfirmation_targets(state, limit)` | `ProjectState`, `int` | `str` | qualitative_coding | `NegativeCaseStage`, tests | free |
| `summarize_disconfirmation_coverage(state)` | `ProjectState` | `dict[str, Any]` | qualitative_coding | CLI/API/MCP/docs later | free |
| `ReviewManager.apply_decision(target_type="claim")` | `HumanReviewDecision` | mutated `ProjectState` | qualitative_coding | CLI/API/review tooling | free |

### Capability Validation

- [x] Internal-only; no cross-project registry entry required.
- [x] Inputs/outputs use existing Pydantic state/decision models or plain summaries.
- [x] Tests verify deterministic behavior without live LLM calls.

---

## Files Affected

- `qc_clean/schemas/domain.py` — add optional negative-case target fields only if needed.
- `qc_clean/core/claims.py` — add ledger disconfirmation target enumeration and coverage summary.
- `qc_clean/core/pipeline/stages/negative_case.py` — include ledger targets in prompt and schema.
- `qc_clean/core/pipeline/review.py` — support `target_type="claim"` decisions.
- `qc_clean/core/cli/commands/project.py` / `qc_cli.py` — optionally expose coverage/review read path if needed by tests.
- `qc_clean/plugins/api/api_server.py` / `qc_mcp_server.py` — optionally expose bounded disconfirmation summary after core slice.
- `tests/test_claims.py`
- `tests/test_negative_case_inv6.py`
- `tests/test_review_manager.py` or existing review tests
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md` / generated `AGENTS.md`
- `docs/plans/CLAUDE.md`

---

## Plan

### Phases

| Phase | Scope | Verification | Commit |
|---|---|---|---|
| 1 | Ledger target enumeration and disconfirmation coverage summary over `ProjectState.claims` | DONE: `tests/test_claims.py` focused target/coverage tests | `[Plan: INV6] Add ledger disconfirmation helpers` |
| 2 | Negative-case schema/prompt wiring: include bounded claim targets and preserve explicit challenged claim IDs | DONE: `tests/test_negative_case_inv6.py`; prompt-target and builder tests | `[Plan: INV6] Target negative cases to ledger claims` |
| 3 | Claim adjudication via `ReviewManager`: approve/reject/modify claim objects, append `ClaimRevision`, preserve fail-loud unknown targets | DONE: review manager tests | `[Plan: INV10] Add claim review decisions` |
| 4 | Read surfaces for disconfirmation/adjudication summaries where useful: CLI/API/MCP bounded summary, no raw full-state dump | DONE: CLI/API/MCP tests | `[Plan: INV6] Expose disconfirmation coverage` |
| 5 | Docs/governance: update INV-6/INV-10 statuses conservatively and move plan to completed records | DONE: `make docs-check`; `make check` | `[Plan: INV6] Document ledger disconfirmation` |

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_claims.py` | `test_disconfirmation_targets_exclude_negative_and_no_claim_events` | Only substantive retained claims become disconfirmation targets. |
| `tests/test_claims.py` | `test_disconfirmation_coverage_counts_challenged_claim_ids` | Negative-case claims with `scope.claim_ids` count as challenged coverage. |
| `tests/test_negative_case_inv6.py` | `test_negative_case_prompt_includes_claim_ledger_targets` | Prompt includes non-code claims by ID, bounded and inspection-friendly. |
| `tests/test_negative_case_inv6.py` | `test_negative_case_builder_prefers_explicit_target_claim_id` | Explicit target claim ID is preserved over heuristic code matching. |
| `tests/test_review_manager.py` | `test_claim_review_approve_reject_modify_updates_claim_adjudication` | Claim decisions mutate adjudication/revision fields and fail loud on invalid claim IDs. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_claims.py tests/test_negative_case_inv6.py -q` | Fast INV-6 target/coverage proof. |
| `python -m pytest tests/test_review_manager.py tests/test_project_commands.py tests/test_mcp_server.py -q` | Protect review and agent/user surfaces. |
| `make check` | Required repo gate: deterministic tests, lint, docs checks, AGENTS sync. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] Every non-negative, non-no-claims substantive claim can be enumerated as a disconfirmation target.
- [x] Negative-case prompts include claim IDs/text/scope for all bounded ledger targets or a documented truncation.
- [x] `NegativeCase` can name an explicit challenged claim ID; builder stores it in `ClaimScope.claim_ids`.
- [x] Disconfirmation coverage summary reports total targets, challenged targets, unchallenged targets, and challenged rate.
- [x] Claim review decisions can approve, reject/withdraw, or modify an `AnalyticClaim` and append revision history.
- [x] Unknown claim IDs and unsupported claim review actions fail loudly.
- [x] Docs update INV-6 and INV-10 only to the exact implemented scope, without marking INV-2 or methodological validity as met.

Process criteria:

- [x] New targeted tests pass after each phase.
- [x] `make check` passes before final completion.
- [x] Plan tracker is updated as phases complete.
- [x] Each verified phase is committed separately with `[Plan: INV6]` or `[Plan: INV10]`.
- [x] Pre-existing `.claude/hook_log.jsonl` dirt is not staged or committed.

---

## Open Questions

- [ ] Should negative-case analysis become retrieval-first in this plan? — Status: DEFERRED | Why it matters: that is INV-2 and needs a corpus retrieval/adversarial-search design. This plan only routes the existing negative-case pass over the full ledger.
- [ ] Should the browser UI support claim review now? — Status: DEFERRED | Why it matters: full UX is larger than this substrate slice. Core `ReviewManager` support plus bounded CLI/API/MCP summaries are enough to make claim adjudication agent-drivable.
- [ ] Should prompt schemas emit all claims natively? — Status: DEFERRED | Why it matters: INV-9 object layer currently adapts validated domain objects into claims. Claim-native LLM schemas can be evaluated after ledger disconfirmation works.

---

## Notes

This plan moves INV-6/INV-10 from "selected code/cross-case surfaces only" to
"ledger-routable object substrate." It still treats negative-case outputs as
experimental until INV-2 retrieval-first, different-model/adversarial,
source-anchored disconfirmation and human adjudication are implemented and
evaluated.

Phase 1 complete 2026-06-21: added deterministic claim-target enumeration,
disconfirmation coverage summaries, and bounded target formatting for prompt
use. Verification: focused Phase 1 tests (2 passed) and `tests/test_claims.py`
(12 passed).

Phase 2 complete 2026-06-21: added `NegativeCase.target_claim_id`, injected
bounded claim-ledger targets into the negative-case prompt, and made
negative-case claim construction prefer exact live target IDs over code-name
fallbacks. Verification: focused Phase 2 tests (2 passed) and affected
claim/negative-case/pipeline suites (26 passed).

Phase 3 complete 2026-06-21: added `ReviewManager.get_pending_claims()`,
`ReviewSummary.claims_count`, and `target_type="claim"` review decisions for
approve/reject/modify with `ClaimRevision` history. Unsupported claim actions
and missing claim IDs fail loudly. Verification: focused claim-review tests
(4 passed) and broader review/fail-loud/API surface tests (51 passed).

Phase 4 complete 2026-06-21: added `disconfirmation_summary` to the existing
claim read surfaces: CLI `project claims`, API `/projects/{project_id}/claims`,
and MCP `qc_get_claims`. Verification: focused surface tests (3 passed) and
broader CLI/API/MCP suites (90 passed).

Phase 5 complete 2026-06-21: updated `docs/PROJECT_THEORY_AND_GOALS.md`,
`CLAUDE.md`, regenerated `AGENTS.md`, moved this plan to completed records, and
updated `docs/plans/CLAUDE.md`. Verification: `make docs-check` and `make check`
green at closure.
