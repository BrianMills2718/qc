# Plan #223: INV-4 Theory Ledger Refresh

**Status:** Active
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
| `grep -RIn "theoretical_sampling_smoke_2026_06_23" docs/PROJECT_THEORY_AND_GOALS.md CLAUDE.md AGENTS.md` | Confirms the canonical ledgers mention the committed artifact. |
| `grep -RIn "not theoretical sampling execution\\|not sampling adequacy\\|not category-saturation\\|not GT-fidelity\\|not methodological-validity\\|not SOTA" docs/PROJECT_THEORY_AND_GOALS.md CLAUDE.md AGENTS.md` | Confirms caveats are present. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

- [ ] `docs/PROJECT_THEORY_AND_GOALS.md` records the committed
  `docs/benchmarks/theoretical_sampling_smoke_2026_06_23/` artifact.
- [ ] `CLAUDE.md` records the artifact in the recent structural-work summary.
- [ ] `AGENTS.md` is regenerated and in sync.
- [ ] The docs preserve the artifact caveat: workflow/provenance smoke only,
  not theoretical sampling execution, sampling adequacy, category saturation,
  GT-fidelity, methodological-validity, or SOTA evidence.
- [ ] Targeted grep checks pass.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Outcome

Pending.

---

## Open Questions

- [ ] Should this mark INV-4 complete?
  Default: no. The committed artifact proves package workflow/provenance only;
  true theoretical sampling and saturation remain unmet.
