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
1. Next evaluation-harness slice after embedding-hybrid retrieval: make D7
   retrieval-mode comparison agent-drivable so lexical/query-expanded and
   embedding-hybrid candidate predictions can be exported/scored against held-out
   gold without mutating project state.
2. Continue through the ranked roadmap without pausing after each verified
   commit unless a canonical stop condition is reached.

**Completed checkpoint:** INV-2 embedding-hybrid retrieval now provides an
opt-in `embedding_hybrid` disconfirmation retrieval mode with exact source
anchors, explicit embedding-model configuration, and fail-loud invalid
configuration. It is not held-out D7 evidence and has no validated default
embedding/reviewer policy.
