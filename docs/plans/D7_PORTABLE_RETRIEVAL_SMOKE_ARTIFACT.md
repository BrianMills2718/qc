# Plan #213: D7 Portable Retrieval Smoke Artifact

**Status:** Planned
**Type:** artifact
**Priority:** High
**Blocked By:** None
**Blocks:** larger held-out D7 retrieval/live-baseline benchmark packages

---

## Gap

**Current:** D7 retrieval export and D7 comparison can now both load explicit
repo-local project stores through `PROJECTS_DIR` / `--projects-dir`, but there
is no committed D7 artifact proving the portable workflow runs end to end from
a repo-local project state through prediction export, protocol preflight,
comparison report, artifact manifest, and artifact verification.

**Target:** Commit a small synthetic D7 retrieval-comparison smoke artifact
under `docs/benchmarks/` that includes a repo-local project store, D7 gold
package, retrieval prediction package, comparison protocol, preflight/report
outputs, artifact manifest, verification evidence, and README caveats.

**Why:** This gives Brian and future agents a concrete output surface to inspect
and replay before scaling to real held-out/expert D7 evaluation. It exercises
the same package/provenance surfaces needed by the larger benchmark.

**Claim boundary:** This is software workflow smoke evidence only. It is not
semantic disconfirmation validity, expert adjudication, live-baseline evidence,
superiority evidence, methodological-validity evidence, or SOTA evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - D7 held-out comparison remains a
  high-priority gap.
- `docs/EVALUATION_HARNESS.md` - D7 package, preflight, comparison, and caveat
  workflow.
- `docs/plans/completed/D7_RETRIEVAL_PROJECTS_DIR_PARITY.md` - portable export
  prerequisite.
- `docs/plans/completed/D7_COMPARISON_PROJECTS_DIR_PARITY.md` - portable
  comparison prerequisite.
- `docs/plans/completed/D7_COMPARISON_ARTIFACT_PACKAGE.md` and
  `D7_COMPARISON_ARTIFACT_VERIFIER.md` - artifact package/verifier surfaces.
- `docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/` - precedent for
  committed small smoke artifacts with README caveats.

---

## Research Basis For This Slice

No external research. This is a repo-local smoke artifact using existing D7
package and verifier surfaces.

---

## Capabilities

Internal artifact capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| portable D7 retrieval smoke artifact | repo-local ProjectState + D7 gold/protocol files | retrieval prediction package + comparison report/artifact manifest | qualitative_coding | Brian/future agents inspecting D7 workflow | free |

### Capability Validation

Skipped for cross-project registry purposes: this commits a concrete artifact,
not a new callable capability.

---

## Files Affected

- `docs/plans/D7_PORTABLE_RETRIEVAL_SMOKE_ARTIFACT.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/` - generated smoke
  artifact directory.
- Docs after artifact:
  - `docs/EVALUATION_HARNESS.md`
  - `CLAUDE.md` and regenerated `AGENTS.md`

---

## Plan

### Steps

1. Write a repo-local synthetic `ProjectState` with one claim and one contrary
   source span in `projects/`.
2. Write a versioned D7 gold package with explicit synthetic adjudication
   metadata and held-out/provenance caveats.
3. Run `make run-d7-retrieval` with `PROJECTS_DIR=...` to produce
   `predictions.json`.
4. Write a versioned D7 comparison protocol matching the generated gold and
   prediction package hashes.
5. Run validators/preflights:
   - `make validate-d7-gold`
   - `make validate-d7-baseline-package`
   - `make validate-d7-comparison-protocol`
   - `make d7-comparison-preflight`
6. Run `make compare-d7-retrieval` with `PROJECTS_DIR=...`,
   `PROTOCOL=...`, `OUTPUT=report.json`, and `ARTIFACT_DIR=artifact`.
7. Run `make verify-d7-comparison-artifact` against the generated manifest.
8. Add README with exact commands, outcome summary, and claim caveats.
9. Run `make docs-check`, `git diff --check`, and `make check`.
10. Commit/push artifact and close the plan.

---

## Required Tests / Verification

| Command | Why |
|---------|-----|
| `make validate-d7-gold GOLD=.../gold.json` | Gold package shape/provenance guard. |
| `make validate-d7-baseline-package PACKAGE=.../predictions.json` | Retrieval prediction package validator. |
| `make validate-d7-comparison-protocol PROTOCOL=.../protocol.json` | Protocol metadata validator. |
| `make d7-comparison-preflight PROTOCOL=... GOLD=... PREDICTIONS=...` | Protocol/gold/prediction compatibility guard. |
| `make compare-d7-retrieval PROJECTS_DIR=... ID=... GOLD=... PREDICTIONS=... PROTOCOL=... OUTPUT=... ARTIFACT_DIR=...` | End-to-end portable comparison run. |
| `make verify-d7-comparison-artifact ARTIFACT=.../manifest.json` | Artifact manifest/report verifier. |
| `make docs-check` | Documentation/governance checks. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature/artifact criteria:

- [ ] Artifact directory contains project state, gold, prediction, protocol,
  comparison report, artifact report/manifest, and README.
- [ ] Retrieval export uses `PROJECTS_DIR=...` and does not require the default
  user project store.
- [ ] Comparison uses `PROJECTS_DIR=...` and does not require the default user
  project store.
- [ ] D7 gold, prediction, protocol, preflight, comparison, and artifact
  verification all pass.
- [ ] README and docs preserve claim discipline: smoke/provenance artifact only,
  not held-out D7 validity evidence.

Process criteria:

- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [x] Should this use live LLM or expert adjudication?
  Status: RESOLVED. No. This is a deterministic smoke artifact. Live/expert
  evidence belongs in a later larger benchmark plan.

---

## Notes

Use synthetic labels and caveats visibly. Do not call the result a real held-out
D7 benchmark even though package `split` may be `held_out` to exercise the
strict held-out schema invariants.
