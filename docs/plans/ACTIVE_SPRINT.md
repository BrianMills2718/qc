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
1. Plan #67, confidence-calibration bootstrap intervals: add deterministic
   local uncertainty metadata for Brier score and ECE without claiming
   calibrated confidence.
2. Continue through the ranked roadmap without pausing after each verified
   commit unless a canonical stop condition is reached.

**Completed checkpoint:** D1 grounding and D2 coverage/examined rates now report
local Wilson intervals in the Phase 0 scorecard. D3 and D7 scorecard sections now accept raw gold or
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
scorecard path; supplied INV-7 fixture scores report Wilson intervals for pass
and attack-success rates overall and by surface. D3 and D7 scorecards now report exact-key binary system-vs-gold
percent agreement, Cohen's κ, Gwet's AC1, Krippendorff's α, and prevalence metadata. D3/D7
scorecards also compare exact recall/precision/F1 against supplied
versioned-package human-human metrics when present and surface supplied
human-human κ/α/AC1 metadata separately. D3 scorecards can now also score
externally supplied application baseline predictions through `D3_BASELINES=` /
`--d3-baselines-file`, reporting exact-key system-minus-baseline deltas and
local paired bootstrap intervals when D3 gold is present. Phase 0 now also scores externally
supplied D4 codebook-quality rubric outcomes through `CODEBOOK_QUALITY=` /
`--codebook-quality-file`. D5 reliability now
surfaces Gwet's AC1 for LLM-pass codebook-discovery, positive application-cell,
and segment-decision consistency when IRR results exist, with rating prevalence
tables and deterministic local row-bootstrap intervals in the Phase 0 scorecard.
Phase 0 also now scores externally supplied D6 counterfactual identity-swap
outcomes through `BIAS_COUNTERFACTUAL=` / `--bias-counterfactual-file`, with
Wilson intervals for invariant-case code-change rates overall and by
attribute. Phase 0 also reports local rubric-mean bootstrap intervals for
externally supplied D4 codebook-quality outcomes. Phase 0
now scores externally supplied D8 GT-fidelity rubric outcomes through
`GT_FIDELITY=` / `--gt-fidelity-file`, with local rubric-mean bootstrap
intervals overall, by metric, by evaluator type, and by scope. Phase 0
now scores externally supplied D9 forced-choice interpretive-preference outcomes
through `PREFERENCE=` / `--interpretive-preference-file`; D9 packages can now
include protocol metadata for a local non-inferiority margin assessment without
licensing blind expert parity, and D9 tie rates now include Wilson intervals.
Phase 0 now scores
externally supplied confidence/correctness calibration records through
`CALIBRATION=` / `--confidence-calibration-file`, now with Wilson intervals for
overall, calibration-bin, and per-surface accuracy plus local bootstrap
intervals for Brier score and ECE. Phase 0 can also run from a
strict versioned benchmark package manifest with relative input paths through
`make bench-package PACKAGE=...`; that runner invokes the same canonical
scorecard path and adds orchestration/provenance only. This remains a
gold-dependent exact-score/provenance/uncertainty, human-ceiling-comparison, and
canary-fixture/counterfactual/GT-fidelity/preference/calibration-accounting substrate, not a populated held-out
benchmark, full D3/D7 validity, populated D4 LLM-judge/blind-expert evaluation,
populated D6 bias audit, populated D8 expert GT-fidelity benchmark,
populated κ/α/AC1 human agreement benchmark,
populated human-ceiling agreement,
populated D9 blind expert preference benchmark,
populated confidence-calibration benchmark,
held-out live-baseline result,
committed/scored live adversarial prompt-injection benchmark, or expert-parity/SOTA
evidence.
