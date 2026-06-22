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
versioned `schema_version=1` gold-set packages, surface compact
`gold_provenance` when package metadata is present, and report configurable local
exact-key `f1_bootstrap_ci` intervals by default. D3 scorecards also report
local same-code/doc char-span IoU and discrete Modified Hausdorff diagnostics in
`span_overlap`. D7 baseline comparisons report local paired exact-key
`system_minus_baseline_ci` intervals for recall, precision, and F1 deltas. D3
packages are validated by
`make validate-d3-gold GOLD=gold_set.json`; D7 packages by
`make validate-d7-gold GOLD=gold_set.json`. INV-7 now has both deterministic
structural fixture export (`make run-inv7-fixtures`) and opt-in live model
canary fixture export (`make run-inv7-live-fixtures`) for the `PROMPT_INJECTION=`
scorecard path. D3/D7 scorecards also compare exact recall/precision/F1 against
supplied versioned-package human-human metrics when present. D5 reliability now
surfaces Gwet's AC1 for LLM-pass codebook-discovery, positive application-cell,
and segment-decision consistency when IRR results exist, with rating prevalence
tables and deterministic local row-bootstrap intervals in the Phase 0 scorecard.
This remains a
gold-dependent exact-score/provenance/uncertainty, human-ceiling-comparison, and
canary-fixture substrate, not a populated held-out benchmark, full D3/D7
validity, κ/α/AC1 human agreement, populated human-ceiling agreement,
held-out live-baseline result,
committed/scored live adversarial prompt-injection benchmark, or expert-parity/SOTA
evidence.
