# Plan #8: INV-2 Adversarial Disconfirmation Model Routing

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-2 hardened disconfirmation; D7 evaluation-harness disconfirmation metrics

---

## Completion Outcome

Completed 2026-06-21. `PipelineContext.disconfirmation_model_name` now lets
negative-case interpretation route through a configured disconfirmation model,
falling back to the normal pipeline `model_name` when unset. The negative-case
prompt now frames the task as an adversarial qualitative methods review over
retrieved candidates, explicitly requiring skeptical evidence-bound assessment
without fabrication or overstatement. The negative-case memo records the
interpretation model used.

This removes the hard same-model coupling, but does not pick a validated default
adversarial model, enforce provider/model-family diversity, or prove D7
disconfirmation quality.

Verification: targeted affected suites passed (`61 passed`), and `make check`
passed with `631 passed, 1 skipped, 8 deselected`; Ruff and docs checks were
green.

---

## Gap

**Current:** Plan #7 made negative-case analysis retrieval-first over anchored
source candidates, but interpretation still uses `ctx.model_name` by default and
the prompt does not clearly separate the disconfirmation interpreter from the
analysis-producing model lineage.

**Target:** Negative-case interpretation can be routed through a configurable
`disconfirmation_model_name`, falling back to `model_name` when unset. The
negative-case prompt should explicitly frame the model as a skeptical,
adversarial reviewer of retrieved source candidates, while still forbidding
fabrication and overclaiming. The selected interpretation model should be
visible in the negative-case memo.

**Why:** INV-2 calls for retrieval-first interpretation ideally with a different
model/adversarial prompt. This slice removes the hard same-model coupling and
locks the adversarial prompt stance without claiming D7 validity.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:255` - INV-2 remains partial because interpretation is same-model by default and not adversarial/D7-evaluated.
- `docs/plans/completed/INV2_RETRIEVAL_FIRST_DISCONFIRMATION.md` - retrieval-first candidate slice completed and left different-model/adversarial interpretation as follow-up.
- `qc_clean/core/pipeline/stages/negative_case.py` - current negative-case LLMHandler construction and prompt.
- `qc_clean/core/pipeline/pipeline_engine.py` - `PipelineContext` already owns stage routing config and disconfirmation retrieval limits.
- `tests/test_disconfirmation_retrieval_inv2.py` - current prompt-capture and retrieval-first integration tests.
- Coordination context: `~/.claude/coordination/claims/` contained no active claims.
- Memory context: `agent-memory recall 'active decisions adversarial disconfirmation different model negative case qualitative_coding INV-2' --project qualitative_coding` — no active blocking decision surfaced; only historical completed outcomes were returned.

---

## Research Basis For This Slice

No additional external research is needed. This is a configuration/routing
hardening step over the already-implemented retrieval-first negative-case path.
D7 evaluation and model-family comparison remain future empirical work.

---

## Capabilities

Skipped. This modifies internal pipeline configuration and prompt routing; it
does not create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/pipeline/pipeline_engine.py` (modify)
- `qc_clean/core/pipeline/stages/negative_case.py` (modify)
- `tests/test_disconfirmation_retrieval_inv2.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify at completion)
- `CLAUDE.md` (modify at completion)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV2_ADVERSARIAL_DISCONFIRMATION_MODEL.md` (move to completed at finish)

---

## Plan

### Steps

1. Add `PipelineContext.disconfirmation_model_name: str | None` with a field
   description explaining fallback to `model_name`.
2. Update `NegativeCaseStage` to construct `LLMHandler` with
   `ctx.disconfirmation_model_name or ctx.model_name` and log that model.
3. Strengthen the prompt stance: skeptical/adversarial reviewer of retrieved
   candidates, assess only evidence that is actually present, and return no
   cases when candidates are insufficient.
4. Record the selected disconfirmation interpretation model in the negative-case
   memo's retrieval-first summary.
5. Add tests proving separate-model routing, fallback routing, and adversarial
   prompt language.
6. Update docs conservatively: same-model-by-default caveat becomes
   configurable/different-model-capable, but full INV-2 remains partial until
   semantic retrieval, human adjudication, and D7 evaluation land.
7. Run targeted tests, `make docs-check`, and `make check`; commit and push.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_uses_configured_disconfirmation_model` | `LLMHandler` receives `disconfirmation_model_name` when configured. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_defaults_to_pipeline_model_without_disconfirmation_override` | Existing default routing remains unchanged. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_prompt_uses_adversarial_reviewer_stance` | Prompt frames the task as skeptical/adversarial review without allowing fabrication. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_disconfirmation_retrieval_inv2.py` | New model-routing and prompt stance contract. |
| `python -m pytest tests/test_negative_case_inv6.py tests/test_claims.py tests/test_claim_ledger_pipeline.py tests/test_prompt_boundaries_inv7.py` | Affected negative-case, claim, and prompt-boundary behavior. |
| `make docs-check` | Plan/governance consistency and generated docs sync. |
| `make check` | Full deterministic test, lint, and docs gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `PipelineContext` exposes a configurable disconfirmation model override.
- [x] `NegativeCaseStage` uses the override for the LLM call and falls back to `model_name` when unset.
- [x] Negative-case prompts frame interpretation as skeptical/adversarial review of retrieved source candidates.
- [x] The selected disconfirmation model is recorded in the negative-case memo.
- [x] Docs do not claim full INV-2 or D7 success.

> Process criteria:
- [x] Required targeted tests pass.
- [x] Full deterministic suite passes through `make check`.
- [x] Lint passes through `make check`.
- [x] Docs checks pass.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] What model should production use as the default adversarial reviewer? —
  Status: DEFERRED | Why it matters: this needs empirical D7 evaluation and
  cost/latency review. This slice only makes routing possible and testable.
- [ ] Should the prompt require a different provider/model family? — Status:
  DEFERRED | Why it matters: enforcing provider diversity needs model registry
  metadata and policy, not a local string comparison.

---

## Notes

This narrows one INV-2 residual risk but still leaves retrieval quality and
validity unproven. Treat disconfirmation outputs as experimental.
