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
1. Create and execute the next high-value lane: export-audit manifest
   verification, so generated hash manifests can be checked against artifact
   bytes without claiming a signed or append-only audit log.
2. Continue through the ranked roadmap without pausing after each verified
   commit unless a canonical stop condition is reached.

**Completed checkpoint:** Corpus-scope warning propagation now covers Markdown,
JSON `export_warnings` metadata, and CSV `export_warnings.csv` for claim-bearing
exports without recorded scope, and CLI/MCP project creation can now persist
corpus scope when supplied while leaving no-scope creation compatible.
Claim-bearing exports now also warn on empty scope records and
population-without-sampling-frame metadata, and CSV/Markdown claim rows now carry
per-row claim scope and corpus-boundary context without rewriting claim text;
this remains report discipline, not sampling adequacy evidence. Claim-review now has a bounded API listing at
`/projects/{id}/review/claims` plus review-decision regression coverage, but no
expert adjudication protocol is claimed. The browser review page now has a
Claims mode that lists claim cards and submits claim approve/reject/modify
decisions through the shared review decision endpoint; ReviewManager and the API
now expose code/entity relationship review rows and `code_relationship` /
`entity_relationship` approve/reject/modify decisions; MCP now exposes
`qc_review_relationships` for bounded agent-side relationship review target
listing; the browser review page now has a Relationships mode for relationship
decisions; API/MCP/browser surfaces now also expose negative-case-specific
review listing over existing `ClaimKind.NEGATIVE_CASE` claim rows while keeping
review decisions on `target_type="claim"`. This is review accessibility, not
expert adjudication or D7 validity evidence. `make adjudication-sample` and
`qc_cli.py project adjudication-sample` now export unlabeled schema_version=1
sample packets over applications, claims, negative cases, and relationships for
human/expert review inputs with hashes and source context; these packets are
not labels, gold data, correctness estimates, or validity evidence. Completed
adjudication response packages can now be shape/completeness-validated through
`make validate-adjudication-responses PACKAGE=sample.json`; this is a protocol
gate only and still does not import labels, create gold, score correctness, or
provide expert evidence. `make lint-scope-phrasing` now scans arbitrary
agent/human-authored text for risky population-generalizing phrasing under
missing or under-specified corpus scope; this is report discipline only, not
sampling-frame adequacy or validity evidence. `make export-audit-manifest` now
writes schema_version=1 hash manifests for existing JSON/CSV/Markdown/QDPX
export artifacts with project-state and per-file SHA-256 hashes; this is local
integrity/provenance metadata only, not signing, append-only logging, or a full
tamper-evident audit substrate.
MCP now exposes `qc_review_decisions` for agent-driven review decisions,
including claim targets with rationale preservation, while keeping the old
`qc_review_codes` tool compatible. MCP also exposes `qc_review_claims` as a
bounded claim-review target listing for agent workflows.
Example-quote anchoring now derives `speaker` from containing same-document
segments when available; speaker attribution remains best-effort and is not part
of hash verification. INV-11 `data_warnings` now also surface on MCP
`qc_get_codebook` and graph code/entity data responses; stale-output handling
still remains invalidation, not auto-recompute.
Phase 0 scorecards and artifact manifests now include
run-configuration hashes for persisted methodology/model/config metadata while
marking prompt hashes as not-run. D10 cost/latency now preserves LLM-only fields
and adds optional observed tool-call accounting plus combined local totals when
matching `tool_calls` rows exist. D1 grounding and D2
coverage/examined/coded-segment rates now report local Wilson intervals in the
Phase 0 scorecard; coded-segment rate is over examined decisions only, not
untouched text. D3 and D7 scorecard sections now accept raw gold or
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
and attack-success rates overall, by surface, and by attack type. Current
prompt override surfaces now require bare declared protected data placeholders
and reject indexed/converted/transformed or undeclared metadata placeholders
before any LLM call; this narrows INV-7 custom-prompt governance but does not
solve prompt injection. Structural and live INV-7 fixture outputs now have a
schema_version=1 package contract, `make validate-inv7-package`, and Phase 0
`PROMPT_INJECTION=` package-loader support; this is protocol/provenance only,
not robustness evidence. D3 and D7 scorecards now report exact-key binary system-vs-gold
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
attribute, plus local bootstrap intervals for mean Jaccard distance overall and
by attribute. Phase 0 also reports local rubric-mean bootstrap intervals for
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
scorecard path and adds orchestration/provenance only. Phase 0 artifact packages
now include a hash-recorded `timing_d10.json` file for local D10 timing
sections with non-sensitive runtime environment metadata. This remains a
gold-dependent exact-score/provenance/uncertainty, human-ceiling-comparison, and
canary-fixture/counterfactual/GT-fidelity/preference/calibration-accounting substrate, not a populated held-out
benchmark, full D3/D7 validity, populated D4 LLM-judge/blind-expert evaluation,
populated D6 bias audit, populated D8 expert GT-fidelity benchmark,
populated κ/α/AC1 human agreement benchmark,
populated human-ceiling agreement,
populated D9 blind expert preference benchmark,
populated confidence-calibration benchmark,
held-out live-baseline result,
committed/scored live adversarial prompt-injection benchmark,
public benchmark timing evidence, or expert-parity/SOTA
evidence.
