# Plan #145: INV-11 Add-Docs Recode Hook

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** INV-11 hard invalidation
**Blocks:** fuller corpus-mutation auto-recompute design

---

## Gap

**Current:** `project add-docs` mutates the corpus and saves newly uncoded
documents, while `project recode` is a separate command that incrementally codes
those documents and invalidates stale higher-order outputs it cannot refresh.
That split is safe, but it leaves corpus mutation and recomputation as a manual
two-step sequence.

**Target:** Add an explicit `project add-docs --recode` hook that performs the
document addition and then invokes the existing incremental recode path in the
same command when at least one document was added. The hook must remain opt-in
so adding documents does not silently spend model budget. It must preserve
existing failure semantics and the current INV-11 warning that perspective,
relationship, synthesis, and GT higher-order outputs are invalidated rather than
fully recomputed by the incremental pipeline.

**Why:** The remaining INV-11 roadmap item is auto-recompute on corpus mutation.
Full automatic higher-order recomputation is still an architectural problem
because the omitted stages require coding-stage context that incremental recode
does not rebuild. This slice makes the already-supported recode step
agent-drivable from the mutation command without overclaiming full refresh.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-11 status and roadmap item #9.
- `qc_clean/core/cli/commands/project.py` - `add-docs` and `recode` handlers.
- `qc_cli.py` - project subcommand parser.
- `qc_clean/core/pipeline/pipeline_factory.py` - incremental pipeline stage list.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - hard invalidation behavior.
- `tests/test_project_commands.py` - CLI command tests with mocked pipelines.
- Memory context: `agent-memory recall 'qualitative_coding INV-11 auto recompute corpus mutation stale outputs recode' --project qualitative_coding --limit 5` - no blocking in-flight decision found.

---

## Research Basis For This Slice

No external research is needed. This is a repo-local operational hook for an
already-defined invariant and existing incremental pipeline.

---

## Capabilities

This plan modifies the repo-local CLI behavior only. It does not create a
cross-project shared capability.

---

## Files Affected

- `qc_cli.py` (modify)
- `qc_clean/core/cli/commands/project.py` (modify)
- `tests/test_project_commands.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify if operational wording changes)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/INV11_ADD_DOCS_RECODE_HOOK.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `--recode` and `--model` options to `project add-docs`.
2. Preserve existing add-docs behavior when `--recode` is not supplied.
3. When `--recode` is supplied and at least one document was added, save the
   mutated state and invoke the existing `_recode_project` handler with the same
   project ID/model.
4. When `--recode` is supplied but zero documents were added, fail loudly after
   saving no false recompute claim.
5. Add focused tests proving no-recode compatibility, recode invocation after
   addition, no invocation on failed additions, and model forwarding.
6. Update docs to describe the new hook as explicit recode-on-add, not full
   higher-order auto-recompute.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_commands.py` | `test_add_docs_with_recode_invokes_incremental_recode` | `project add-docs --recode` adds a document, saves state, forwards the model, and invokes the recode handler. |
| `tests/test_project_commands.py` | `test_add_docs_with_recode_does_not_recode_when_no_documents_added` | Failed document additions do not trigger recode and return a failure exit. |
| `tests/test_project_commands.py` | `test_add_docs_without_recode_preserves_existing_behavior` | Plain `add-docs` still only adds and saves documents. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_project_commands.py` | Direct CLI behavior. |
| `tests/test_incremental_staleness_inv11.py tests/test_incremental.py` | Existing INV-11 invalidation remains intact. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `qc_cli.py project add-docs --recode` is available.
- [ ] `--recode` invokes the existing incremental recode path after successful additions.
- [ ] `--model` on `add-docs --recode` is forwarded to the recode path.
- [ ] Plain `add-docs` behavior remains unchanged.
- [ ] Zero successful additions do not trigger recode.
- [ ] Docs preserve the claim that INV-11 remains partial: this is explicit incremental recode-on-mutation, not full higher-order auto-recompute.

> Process criteria (quality gates):
- [ ] Required focused tests pass.
- [ ] Full test suite passes (`make check`).
- [ ] Type check status is reported.
- [ ] Docs updated.

---

## Open Questions

- [ ] What should full higher-order auto-recompute mean: complete full-pipeline
  rerun, stage-context reconstruction, or a dedicated recomputation pipeline? -
  Status: DEFERRED | Why it matters: each option changes how human review
  decisions, existing codebooks, stale claims, and LLM budget are handled.

---

## Notes

This slice intentionally does not make `add-docs` auto-run LLM calls by default.
The operator must opt in with `--recode`.
