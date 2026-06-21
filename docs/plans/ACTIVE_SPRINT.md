# Active Long-Running Sprint

**Mission:** Continue executing the documented qualitative-coding roadmap without
pausing between verified increments. Each increment must have a plan, explicit
acceptance criteria, focused tests, full gate verification where practical, a
commit, and a push.

**Stop conditions:** Stop only for an irreversible shared-state action
(force-push, destructive data change, production mutation) or for a genuine
architectural decision not pre-made in the active plan and not safely defaultable.
Tool failures, completed phases, green tests, and uncertainty are not stop
conditions; record them in the active/completed plan and move to the next
highest-value documented lane.

**Current acceptance criteria for the sprint:**
- Every active slice is listed in `docs/plans/CLAUDE.md`.
- Every slice states what passes and what fails before implementation.
- Every verified increment is committed and pushed.
- Claim discipline from `docs/PROJECT_THEORY_AND_GOALS.md` is preserved: no
  SOTA, methodological-validity, full-GT, full-disconfirmation, or prompt-
  injection-solved claims without the required evidence.
- Final state before any handoff is either clean or precisely summarized.

**Current queue:**
1. Next evaluation-harness slice after D3 exact application scoring: choose the
   next highest-value unmet harness lane that can be advanced without pretending
   held-out expert data exists.
2. Continue through the ranked roadmap without pausing after each verified
   commit unless a canonical stop condition is reached.

**Completed checkpoint:** D3 and D7 scorecard sections now accept raw gold or
versioned `schema_version=1` gold-set packages and surface compact
`gold_provenance` when package metadata is present. D3 packages are validated by
`make validate-d3-gold GOLD=gold_set.json`; D7 packages by
`make validate-d7-gold GOLD=gold_set.json`. This remains a gold-dependent
exact-score/provenance substrate, not a populated held-out benchmark, full
D3/D7 validity, κ/α/AC1, IoU/Hausdorff, interval-tested baseline delta, or
expert-parity/SOTA evidence.
