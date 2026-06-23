# Plan #223: INV-4 Theory Ledger Refresh

**Status:** Completed
**Type:** documentation
**Priority:** High
**Blocked By:** None
**Blocks:** accurate continuation planning after the INV-4 smoke artifact

---

## Gap

**Current at plan start:** Plan #222 committed
`docs/benchmarks/theoretical_sampling_smoke_2026_06_23/`, but the canonical
theory/goal ledger and root operating summary only mention the underlying
theoretical-sampling package surfaces. They do not yet record the committed
synthetic smoke artifact.

**Target:** Refresh `docs/PROJECT_THEORY_AND_GOALS.md`, `CLAUDE.md`, and
generated `AGENTS.md` so they accurately record the new INV-4 smoke artifact
while preserving claim discipline.

**Claim boundary:** The documentation must state that the artifact is
workflow/provenance smoke evidence only, not theoretical sampling execution,
not sampling adequacy evidence, not category-saturation evidence, not
GT-fidelity evidence, not methodological-validity evidence, and not SOTA
evidence.

---

## References Reviewed

- `docs/benchmarks/theoretical_sampling_smoke_2026_06_23/README.md`
- `docs/PROJECT_THEORY_AND_GOALS.md` §13/§13.1/§18
- `CLAUDE.md` direction and command surfaces
- `docs/EVALUATION_HARNESS.md` theoretical-sampling surfaces
- `docs/plans/completed/THEORETICAL_SAMPLING_SMOKE_ARTIFACT.md`
- Coordination claims:
  `python scripts/meta/check_coordination_claims.py --check --project qualitative_coding --scope inv4-theory-ledger-refresh`
  returned no active claims.
- Memory context:
  `agent-memory recall 'INV-4 theory ledger smoke artifact active decisions' --project qualitative_coding`
  returned no relevant active decision.

---

## Research Basis For This Slice

No external research is needed. This is a documentation ledger refresh after a
committed repo-local artifact.

---

## Capabilities

No new capability is added.

---

## Files Affected

- `docs/plans/INV4_THEORY_LEDGER_REFRESH.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `docs/PROJECT_THEORY_AND_GOALS.md` - canonical strategic ledger.
- `CLAUDE.md` - root operating summary.
- `AGENTS.md` - generated Codex projection.

---

## Plan

### Steps

1. Commit this plan before documentation edits.
2. Update INV-4 status and roadmap text in `docs/PROJECT_THEORY_AND_GOALS.md`
   to mention the committed synthetic smoke artifact and its caveats.
3. Update the root `CLAUDE.md` direction summary to mention the INV-4 smoke
   artifact and avoid stale wording.
4. Regenerate `AGENTS.md`.
5. Run targeted grep checks for the artifact path/caveats, `make docs-check`,
   `git diff --check`, and `make check`.
6. Commit/push implementation and close the plan.

---

## Required Tests

| Test Pattern | Why |
|--------------|-----|
| `grep -RIn "theoretical_sampling_smoke_2026_06_23" docs/PROJECT_THEORY_AND_GOALS.md CLAUDE.md` | Confirms the canonical source ledgers mention the committed artifact. |
| `grep -RIn "not theoretical sampling execution\\|not sampling adequacy\\|not category-saturation\\|not GT-fidelity\\|not methodological-validity\\|not SOTA" docs/PROJECT_THEORY_AND_GOALS.md CLAUDE.md` | Confirms caveats are present in canonical source ledgers. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

- [x] `docs/PROJECT_THEORY_AND_GOALS.md` records the committed
  `docs/benchmarks/theoretical_sampling_smoke_2026_06_23/` artifact.
- [x] `CLAUDE.md` records the artifact in the recent structural-work summary.
- [x] `AGENTS.md` is regenerated and in sync.
- [x] The docs preserve the artifact caveat: workflow/provenance smoke only,
  not theoretical sampling execution, sampling adequacy, category saturation,
  GT-fidelity, methodological-validity, or SOTA evidence.
- [x] Targeted grep checks pass.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Completed in commit `ad230c90`.

Updated:

- `docs/PROJECT_THEORY_AND_GOALS.md` version 3.4, Since-v3.0 note, INV-4
  invariant status, and roadmap item 7.
- `CLAUDE.md` high-signal summary and direction paragraph.
- `AGENTS.md` was regenerated; the generator's compressed projection did not
  include the detailed direction paragraph, and `make docs-check` verified it
  remains in sync.

Verification:

- `grep -RIn "theoretical_sampling_smoke_2026_06_23" docs/PROJECT_THEORY_AND_GOALS.md CLAUDE.md`
  - passed
- `grep -RInE "not theoretical sampling execution|not sampling adequacy|not category-saturation|not GT-fidelity|not methodological-validity|not SOTA" docs/PROJECT_THEORY_AND_GOALS.md CLAUDE.md`
  - passed
- `make docs-check`
  - passed; `AGENTS.md` in sync
- `git diff --check`
  - passed
- `make check`
  - 1308 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed;
    type check is not yet configured

---

## Open Questions

- [x] Should this mark INV-4 complete?
  Status: RESOLVED. No. The committed artifact proves package
  workflow/provenance only; true theoretical sampling and saturation remain
  unmet.
