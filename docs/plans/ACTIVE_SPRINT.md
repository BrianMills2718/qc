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
1. Brian review gate: Plan #208 clarified code-only bulk approval and repaired
   graph tab rendering. The corrected demo server is running for review.
2. After review or explicit continuation, continue through the ranked roadmap
   without pausing after each verified
   commit unless a canonical stop condition is reached.

**Active checkpoint:** Plan #214
`D7_LIVE_BASELINE_PROJECTS_DIR_PARITY.md` is active. The next slice adds
explicit `PROJECTS_DIR` / `--projects-dir` support to D7 live-baseline export
through script, Make, and `qc_cli.py`, so future live-baseline packages can load
the same repo-local project stores used by retrieval export and comparison.
This is portability/provenance support only, not live-baseline evidence,
held-out D7 evidence, superiority evidence, methodological-validity evidence,
or SOTA evidence.

**Completed checkpoint:** Plan #213
`completed/D7_PORTABLE_RETRIEVAL_SMOKE_ARTIFACT.md` committed a small synthetic
D7 retrieval-comparison smoke artifact under
`docs/benchmarks/d7_portable_retrieval_smoke_2026_06_23/` that runs from a
repo-local project store through retrieval export, protocol preflight,
comparison report, artifact manifest, and artifact verification. This is
workflow/provenance smoke evidence only, not semantic disconfirmation validity,
expert adjudication, live-baseline evidence, superiority evidence,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** Plan #212
`completed/D7_COMPARISON_PROJECTS_DIR_PARITY.md` added explicit `PROJECTS_DIR` /
`--projects-dir` support to D7 retrieval comparison through script, Make, and
`qc_cli.py`, so future D7 comparison artifacts can load the same repo-local
project stores used by retrieval export without hidden environment coupling.
This is portability/provenance support only, not held-out D7 evidence,
live-baseline evidence, superiority evidence, methodological-validity evidence,
or SOTA evidence.

**Completed checkpoint:** Plan #211
`completed/D7_RETRIEVAL_PROJECTS_DIR_PARITY.md` added explicit `PROJECTS_DIR` /
`--projects-dir` support to D7 retrieval export through script, Make, and
`qc_cli.py`, so future held-out D7 artifacts can use repo-local project stores
without mutating the default user store. This is portability/provenance support
only, not held-out D7 evidence, live-baseline evidence, superiority evidence,
or SOTA evidence.

**Completed checkpoint:** Plan #210
`completed/INV7_EXTERNAL_HELDOUT_SMOKE_ARTIFACT.md` committed a
protocol-registered 3-fixture external held-out INV-7 smoke artifact at
`docs/benchmarks/inv7_external_heldout_smoke_2026_06_23/`.

**Completed checkpoint:** Plan #209
`completed/INV7_HELD_OUT_FIXTURE_MANIFEST_RUNNER.md` added external INV-7 live
fixture manifest execution through script, Make, and `qc_cli.py`, preserving
manifest split/provenance metadata and held-out invariants.

**Completed checkpoint:** Plan #208
`completed/GRAPH_REVIEW_UI_CLARITY_FIXES.md` clarified code-only bulk approval
and fixed graph tab re-rendering after the Cytoscape loading placeholder was
removed. Browser verification confirmed Code Relationships renders 3 nodes /
2 edges and Entity Map renders 2 nodes / 1 edge.

**Completed checkpoint:** Plan #207
`completed/REVIEW_UI_ORIENTATION_AIDS.md` added concise reviewer guidance and
tooltips to the browser review page. Verification included focused UI tests,
Ruff, docs checks, full `make check`, HTTP route checks, and headless browser
confirmation that the Start Here guidance and Negative Cases tab help render.

**Completed checkpoint:** Plan #206
`completed/REVIEWER_DEMO_RUN_PACKET.md` added `make reviewer-demo` and
`scripts/build_reviewer_demo.py` to build an isolated synthetic review packet
with fixture transcripts, project JSON, Markdown/JSON exports, claim/review/
graph API snapshots, Phase 0 scorecard artifacts, README instructions, and
self-review caveats. `ProjectStore()` now honors `QC_PROJECTS_DIR` for isolated
CLI/API/browser review stores when no explicit store path is supplied. This is
software-surface demonstration only, not live LLM evidence, expert
adjudication, held-out benchmark evidence, methodological-validity evidence, or
SOTA evidence.

**Completed checkpoint:** Plan #205
`completed/REVIEW_SURFACE_OFFSET_PAGINATION.md` added offset traversal to
review-specific API/MCP claim, negative-case, and relationship list surfaces.
This is review-surface pagination/accounting only, not claim-validity evidence,
human/expert adjudication, held-out D3/D7 evidence, relationship validity,
semantic disconfirmation validity, or SOTA.

**Completed checkpoint:** Plan #204
`completed/CLAIM_LEDGER_CLI_MCP_OFFSET_PAGINATION.md` added offset traversal to
MCP `qc_get_claims` and CLI `project claims --offset` so non-API claim-ledger
read surfaces can page through bounded rows. This is read-surface
pagination/accounting only, not claim-validity evidence, human/expert
adjudication, held-out D7 evidence, semantic disconfirmation validity, or SOTA.

**Completed checkpoint:** Plan #203
`completed/CLAIM_LEDGER_API_OFFSET_PAGINATION.md` added an explicit
non-negative `offset` query parameter and response metadata to API
`/projects/{project_id}/claims` so agents can traverse claim ledgers by
repeated bounded pages. This is API pagination/accounting only, not
claim-validity evidence, human/expert adjudication, held-out D7 evidence,
semantic disconfirmation validity, or SOTA.

**Completed checkpoint:** Plan #202
`completed/CLAIM_LEDGER_API_LIMIT_METADATA.md` made API
`/projects/{project_id}/claims` expose its first-window row cap through an
explicit `limit` query parameter and `returned` / `total_claims` / `limit`
metadata while preserving existing claim row fields. This is read-surface
accounting only, not claim-validity evidence, human/expert adjudication,
held-out D7 evidence, semantic disconfirmation validity, or SOTA.

**Completed checkpoint:** Plan #201
`completed/CLAIM_LEDGER_SCOPE_READ_SURFACES.md` extended `ClaimScope`
visibility from review rows to general claim-ledger read surfaces: API
`/projects/{project_id}/claims`, MCP `qc_get_claims`, and opt-in CLI
`project claims --show-scope`. It is structural scope visibility only, not
claim-validity evidence, human/expert adjudication, held-out D7 evidence,
semantic disconfirmation validity, or SOTA.

**Completed checkpoint:** Plan #200
`completed/CLAIM_LEDGER_ANCHOR_DETAIL_READ_SURFACES.md` extended bounded
supporting/contrary anchor details from review rows to general claim-ledger
read surfaces: API `/projects/{project_id}/claims`, MCP `qc_get_claims`, and
opt-in CLI `project claims --show-anchors`. It is evidence visibility only,
not claim-validity evidence, expert adjudication, held-out D7 evidence,
semantic disconfirmation validity, or a SOTA claim.

**Completed checkpoint:** Plan #199
`completed/NEGATIVE_CASE_REVIEW_ANCHOR_DETAILS.md` added bounded
supporting/contrary anchor-detail payloads to existing API/MCP/browser claim
review rows so negative-case review exposes anchored contrary evidence for
inspection. It does not change claim-decision semantics, propagate
negative-case decisions to challenged claims, add expert adjudication, expose
candidate scores, create held-out D7 evidence, prove disconfirmation validity,
or produce SOTA claims.

**Completed checkpoint:** Plan #198
`completed/MCP_EXPORT_PUBLISH_PREFLIGHT_GATE.md` added explicit opt-in
`publish_preflight` / `scope_lint` parameters to confined MCP JSON/Markdown
export tools so agents can request the local publish/handoff gate inside one MCP
export call. It does not change default MCP export payloads, make preflight
mandatory, validate sampling adequacy, sign artifacts, make logs append-only,
create external tamper evidence, or produce SOTA claims.

**Completed checkpoint:** Plan #197
`completed/PROJECT_EXPORT_PUBLISH_PREFLIGHT_GATE.md` added explicit opt-in
`qc_cli.py project export --publish-preflight [--scope-lint]` flags so
one-command exports can run the local publish/handoff gate immediately after
writing the export manifest. It does not change default export behavior, make
preflight mandatory, validate sampling adequacy, sign artifacts, make logs
append-only, create external tamper evidence, or produce SOTA claims.

**Completed checkpoint:** Plan #196
`completed/EXPORT_PUBLISH_PREFLIGHT_SCOPE_LINT.md` added an explicit opt-in
`--scope-lint` / `SCOPE_LINT=1` publish-preflight gate that blocks risky
population-generalizing Markdown/text handoff artifacts when the loaded project
state has missing or under-specified corpus scope. The gate is report-boundary
discipline only; it does not validate sampling-frame adequacy, claim
correctness, methodological validity, audit signing, external tamper evidence,
or SOTA claims.

**Completed checkpoint:** `qc_cli.py` now wraps the scope-phrasing and
prompt-override governance lint scripts through top-level commands:
`lint-scope-phrasing` and `lint-prompt-overrides`. The wrappers delegate exact
argv to the canonical scripts without changing scope-lint rules,
prompt-override registry rules, prompt rendering, corpus-scope semantics, or
claim discipline. These are governance lint CLI parity surfaces only; they do
not prove sampling-frame adequacy, prompt-injection robustness, model
obedience, methodological validity, or SOTA claims.

**Completed checkpoint:** `qc_cli.py` now wraps the standalone export-audit
scripts through top-level commands: `export-audit-manifest`,
`verify-export-audit-manifest`, `export-publish-preflight`,
`verify-export-audit-log`, `mirror-export-audit-db`, and
`verify-export-audit-db`. Each wrapper delegates exact argv to the canonical
script and preserves repeated artifacts plus optional project/audit flags
without duplicating manifest, event-log, or SQLite verification logic. These are
local integrity/provenance CLI parity surfaces only; they do not provide
signing, append-only storage, external tamper evidence,
methodological-validity evidence, or SOTA claims.

**Completed checkpoint:** `qc_cli.py` now wraps D3/D7 comparison protocol
validation and comparison-preflight scripts through top-level commands:
`validate-d3-comparison-protocol`, `d3-comparison-preflight`,
`validate-d7-comparison-protocol`, and `d7-comparison-preflight`. Each wrapper
delegates exact argv to the canonical script and preserves protocol, gold, and
ordered prediction paths without duplicating protocol/preflight logic. These are
protocol/preflight/provenance CLI parity surfaces only; they do not create
held-out D3/D7 evidence, methodological-validity evidence, parity/superiority
evidence, or SOTA claims.

**Completed checkpoint:** `ProjectConfig.auto_refresh_higher_order_on_recode`
now records a durable project-level recode refresh default. New projects can opt
in with `project create --auto-refresh-higher-order-on-recode`, existing
projects can inspect/update it through `project recode-policy`, and one-run
`--refresh-higher-order` / `--no-refresh-higher-order` overrides control
`project recode` and `project add-docs --recode`. Existing projects keep
hard-invalidation defaults unless configured. This is an INV-11 policy surface,
not global auto-refresh, full INV-11 completion, methodological-validity
evidence, saturation evidence, parity/superiority evidence, or SOTA.

**Completed checkpoint:** `qc_cli.py` now wraps the D4/D6/D8/D9/confidence
protocol validation and result-preflight scripts through top-level commands:
`validate-d4-codebook-quality-protocol`, `d4-codebook-quality-preflight`,
`validate-d6-bias-protocol`, `d6-bias-preflight`,
`validate-d8-gt-fidelity-protocol`, `d8-gt-fidelity-preflight`,
`validate-d9-interpretive-preference-protocol`,
`d9-interpretive-preference-preflight`,
`validate-confidence-calibration-protocol`, and
`confidence-calibration-preflight`. Each wrapper delegates exact argv to the
canonical script and forwards optional result-file arguments only when supplied.
These are protocol/preflight/accounting CLI parity surfaces only; they do not
create populated labels, evaluation outcomes, expert ratings, bias-audit
evidence, calibration evidence, parity/superiority evidence,
methodological-validity evidence, or SOTA claims.

**Completed checkpoint:** `qc_cli.py` now wraps the theoretical-sampling
protocol validation, candidate/result preflight, candidate package export, and
result package export scripts through top-level commands. The wrappers preserve
required paths, optional output/result paths, repeated candidate/selection/
success-criterion arguments, and boolean `--stopped-by-rule` forwarding without
duplicating validation, preflight, export, ProjectStore, or package-building
logic. These are INV-4 package/provenance workflow surfaces only; they do not
execute theoretical sampling, collect new data, prove category saturation,
prove GT fidelity, create methodological-validity evidence, create benchmark
results, establish parity/superiority, or support SOTA claims.

**Completed checkpoint:** `qc_cli.py import-adjudication-responses` now wraps
the canonical `scripts/import_adjudication_responses.py` entrypoint. It forwards
required adjudication metadata, optional D3/D7 outputs, optional split, optional
protocol/sample preflight guard paths, boolean provenance flags, and notes
without duplicating validation, preflight, or import logic. This is CLI parity
for guarded D3/D7 package-input creation only; it does not create expert labels,
correctness estimates, validity evidence, benchmark results,
parity/superiority evidence, or SOTA claims.

**Completed checkpoint:** `qc_cli.py` now wraps the existing adjudication
validation/preflight scripts through top-level commands:
`validate-adjudication-protocol`, `adjudication-protocol-preflight`,
`validate-adjudication-responses`, and `adjudication-response-preflight`. Each
wrapper delegates positional paths to the canonical script `main()` without
duplicating validation logic. These are process/provenance checks only; they do
not create expert labels, correctness estimates, validity evidence, benchmark
results, parity/superiority evidence, or SOTA claims.

**Completed checkpoint:** `qc_cli.py write-phase0-adjudication-package` now
wraps the canonical `scripts/write_phase0_adjudication_package.py` entrypoint.
It forwards supplied package, output, artifact, observability, and trace
arguments without duplicating validation logic; `--gold-file` is accepted as an
alias for forwarded `--d7-gold-file`. This is top-level CLI parity for strict
manifest assembly only; it does not create expert labels, change adjudication
import semantics, run benchmarks, or claim validity, parity, superiority,
timing, or SOTA evidence.

**Completed checkpoint:** Strict Phase 0 package manifests can now carry
`projects_dir`. The package runner resolves the path relative to the manifest
directory and forwards `--projects-dir` to `bench_phase0`, so package-driven
runs can score package-local or other non-default project stores without
monkeypatching or ambient default user state. This is package
portability/provenance support only; it does not change project persistence,
copy project data into packages, run live LLM calls, or claim benchmark
validity, methodological validity, superiority, parity, timing, or SOTA
evidence.

**Completed checkpoint:** Strict Phase 0 package manifests can now carry
`inv7_live_protocol_file`. The package runner resolves the path relative to
the manifest directory and forwards `--inv7-live-protocol-file` to
`bench_phase0`, preserving the existing INV-7 live protocol/result preflight
guard for package-driven runs while retaining strict unknown-key rejection for
unsupported fields. This is local guard preservation only; it does not run live
fixtures, create held-out adversarial data, call an LLM, change scoring, or
claim prompt-injection robustness, model obedience, methodological validity, or
SOTA evidence.

**Completed checkpoint:** Phase 0 scorecard/timing/manifest artifact packages
can now be verified through `scripts/verify_phase0_benchmark_artifact.py`,
`make verify-phase0-benchmark-artifact ARTIFACT=...`, and
`qc_cli.py verify-phase0-benchmark-artifact ...`. The verifier accepts a run
directory or manifest path, checks local scorecard and timing hashes, compares
manifest metadata copied from scorecard `_meta`, confirms timing D10 sections
match the scorecard, requires prompt-eval-not-run metadata and
non-evidentiary caveats, emits structured failures, and exits `0` only when
verified. This is local integrity/provenance checking only; it does not run
benchmarks, create held-out data, call `prompt_eval`, verify semantic validity,
sign artifacts, provide append-only storage, or claim methodological-validity,
superiority, parity, timing, or SOTA evidence.

**Completed checkpoint:** D7 retrieval/live-baseline comparison manifests can
now be written through `scripts/write_d7_comparison_package.py`, `make
write-d7-comparison-package ...`, and `qc_cli.py
write-d7-comparison-package ...`. The writer validates versioned D7 gold
packages and versioned D7 retrieval/live-baseline prediction packages before
writing, preserves prediction order, emits package-relative manifest paths when
possible, records optional comparison output / artifact directory /
verify-artifact fields, and runs existing D7 comparison preflight before
writing when a protocol package is supplied. This is manifest
reproducibility/provenance infrastructure only; it does not create held-out D7
data, run retrieval or live baselines, choose retrieval/model policy, prove
semantic disconfirmation validity, establish superiority, or support SOTA
claims.

**Completed checkpoint:** D7 retrieval/live-baseline comparisons can now run
from strict `schema_version=1` package manifests through
`scripts/run_d7_comparison_package.py`, `make compare-d7-package PACKAGE=...`,
and `qc_cli.py compare-d7-package ...`. The runner resolves relative paths from
the manifest directory, preserves ordered prediction files, delegates to the
canonical comparison script, and can verify the one artifact directory created
by that invocation when `verify_artifact=true`. This is reproducibility and
local provenance infrastructure only; it does not create held-out D7 data, run
live baselines, choose retrieval/model policy, prove semantic disconfirmation
validity, establish superiority, or support SOTA claims.

**Completed checkpoint:** D7 comparison artifact directories/manifests can now
be verified through `scripts/verify_d7_comparison_artifact.py`, `make
verify-d7-comparison-artifact ARTIFACT=...`, and `qc_cli.py
verify-d7-comparison-artifact ...`. The verifier checks local `report.json`
bytes against manifest `report_sha256`, compares report `_meta.input_hashes`
and `_meta.command` against manifest metadata, checks prompt-eval-not-run and
claim-caveat presence, emits structured failures, and exits `0` only for
`status="verified"`. This is local integrity/provenance checking only; it is
not held-out D7 evidence, live-baseline evidence, superiority evidence,
methodological-validity evidence, or SOTA.

**Completed checkpoint:** Successful D7 retrieval/live-baseline comparison
reports can now write optional versioned artifact directories when
`ARTIFACT_DIR=` / `--artifact-dir` is supplied. Each artifact directory contains
`report.json` and `manifest.json`; the manifest records report SHA-256,
`_meta.input_hashes`, `_meta.command`, prompt-eval-not-run status, and explicit
D7 claim caveats. Stdout and `--output` remain compatible, and failed preflight
still writes no output report and no artifact directory. This is local
artifact/provenance/accounting metadata only; it is not held-out D7 evidence,
live-baseline evidence, superiority evidence, methodological-validity evidence,
or SOTA.

**Completed checkpoint:** Successful D7 retrieval/live-baseline comparison
reports now include additive `_meta.input_hashes` and `_meta.command`
provenance. The hash block records loaded ProjectState/corpus hashes, the D7
gold file hash, ordered prediction file hashes, and optional protocol file hash;
the command block records the project ID and compared file paths. Stdout and
`--output` JSON carry the same metadata, and failed preflight still writes no
output report. This is local provenance/accounting metadata only; it is not
held-out D7 evidence, live-baseline evidence, superiority evidence,
methodological-validity evidence, or SOTA.

**Completed checkpoint:** Guarded D3 comparison scorecards now evaluate
pre-registered D3 comparison protocol `metric_criteria` after
`make bench D3_PROTOCOL=...` preflight passes. The additive
`application_validity_d3.metric_criteria_report` records pass/fail/missing rows
for exact baseline metrics and local span-overlap diagnostics when criteria are
configured. Existing D3 scoring, baseline deltas, preflight semantics,
output/artifact behavior, no-criteria guarded runs, and unguarded scoring remain
compatible. This is local protocol/accounting metadata only; it does not run or
create baselines, collect held-out labels, add semantic/multi-label D3
agreement, establish expert parity, demonstrate superiority, prove
methodological validity, or support SOTA claims.

**Completed checkpoint:** `make bench D3_PROTOCOL=... D3_GOLD=...
D3_BASELINES=...`, `scripts/bench_phase0.py
--d3-comparison-protocol-file`, `qc_cli.py bench`, and Phase 0 package
manifests can now enforce the completed D3 comparison preflight at the scoring
boundary. Failed preflight blocks scorecard, output, and artifact writes;
passing preflight is recorded at `_meta.preflight_reports.d3_comparison`, and
the D3 protocol file hash/path is included in scorecard and artifact
provenance. Existing unguarded D3 gold/baseline scoring remains compatible.
This is protocol/accounting/score-time guard infrastructure only; it does not
run or create baselines, evaluate D3 structured metric criteria, collect
held-out D3 evidence, establish expert parity, demonstrate superiority, prove
methodological validity, or support SOTA claims.

**Completed checkpoint:** D3 comparison preflight now cross-checks registered
D3 comparison protocols, versioned D3 gold packages, and versioned D3 baseline
prediction packages through `qc_clean/core/d3_comparison_preflight.py`,
`scripts/preflight_d3_comparison.py`, and
`make d3-comparison-preflight PROTOCOL=... GOLD=... PREDICTIONS="..."`.
It validates package shapes first, then checks protocol/gold metadata,
expected/missing/unexpected/duplicate baseline names, baseline mode/model/
application-count drift, and optional prediction-file SHA-256 locks. This is
protocol/provenance/preflight infrastructure only; it does not add
`make bench D3_PROTOCOL=...`, score-time enforcement, held-out D3 evidence,
expert parity, superiority evidence, methodological-validity evidence, or SOTA
claims.

**Completed checkpoint:** D3 baseline comparison protocols can now be validated
through `qc_clean/core/d3_comparison_protocol.py`,
`scripts/validate_d3_comparison_protocol.py`, and
`make validate-d3-comparison-protocol PROTOCOL=...`. The schema records expected
D3 baselines, held-out freeze/provenance flags, hash locks, success criteria,
and optional exact/span metric criteria. This is protocol/provenance metadata
only; it does not run or preflight baseline packages, enforce score-time guards,
populate held-out D3 evidence, establish expert parity, demonstrate
superiority/non-inferiority, prove methodological validity, or support SOTA.

**Completed checkpoint:** D3 baseline rows now include diagnostic-only
`span_overlap` metadata under `application_validity_d3.baselines.<name>`. The
diagnostic compares baseline code-application anchors against D3 gold using the
same same-code/document character-span IoU and Modified Hausdorff logic as the
system D3 overlap section, while exact baseline TP/FP/FN, recall/precision/F1,
system-minus-baseline deltas, and bootstrap CI behavior remain unchanged. This
is local error-analysis metadata only, not semantic application validity,
held-out D3 evidence, expert parity, superiority evidence, or SOTA evidence.

**Completed checkpoint:** `make bench` / `qc_cli.py bench` can now optionally
enforce INV-7 live protocol/result preflight before scoring supplied
`PROMPT_INJECTION=` packages. Failed preflight blocks scorecard, output, and
artifact writes; passing preflight is recorded at
`_meta.preflight_reports.inv7_live`, with the protocol file hash/path carried in
scorecard and artifact provenance. Existing unguarded prompt-injection scoring
remains compatible. This is protocol/accounting infrastructure only, not a
broader held-out adversarial benchmark, prompt-injection robustness evidence,
model-obedience proof, methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** D7 comparison protocols can now include optional
structured `metric_criteria` for exact-score metrics and local span-overlap
diagnostics. `make validate-d7-comparison-protocol` reports the count, and
guarded `make compare-d7-retrieval PROTOCOL=...` output includes an additive
`metric_criteria_report` with pass/fail/missing rows after preflight passes.
Exact D7 scores, baseline deltas, span-overlap diagnostics, and preflight
semantics remain unchanged. This is protocol/accounting infrastructure only,
not held-out D7 evidence, live-baseline evidence, validated embedding/reviewer
policy, methodological-validity evidence, superiority evidence, or SOTA.

**Completed checkpoint:** D7 baseline rows now include diagnostic-only
`span_overlap` metadata. The diagnostic compares baseline contrary-evidence
anchors against D7 gold using the same same-target/document character-span IoU
and Modified Hausdorff logic as the system D7 overlap section, and
retrieval-comparison reports surface it through
`disconfirmation_d7.baselines.<name>`. Exact D7 baseline scores and
system-minus-baseline deltas remain unchanged except for this additive
diagnostic. This is local error-analysis metadata only, not semantic
disconfirmation validity, held-out evidence, expert parity, superiority
evidence, or SOTA evidence.

**Completed checkpoint:** D7 scorecards now include a diagnostic-only
`disconfirmation_d7.span_overlap` section when D7 gold is scored. It compares
character-offset contrary-evidence anchors only over the same target claim and
document, reports best IoU and Modified Hausdorff distance in both directions,
and counts segment-only/missing-offset anchors as unscored rather than guessing
spans. Exact D7 TP/FP/FN, intervals, agreement metadata, and baseline scores
remain unchanged except for this additive diagnostic. This is local
error-analysis metadata only, not semantic disconfirmation validity, held-out
evidence, expert parity, or SOTA evidence.

**Completed checkpoint:** A protocol-guarded built-in INV-7 live canary
fixture-set v2 artifact is committed at
`docs/benchmarks/inv7_live_canary_v2_2026_06_22/`: pre-run protocol, live
result package, protocol/result preflight report, Phase 0 scorecard, README,
and a repo-local synthetic project shell for rescoring. The canary scored 5/5
passed with `attack_success_rate=0.0`; the Wilson upper bound remains
approximately `0.4345` because the denominator is only 5. D10 cost is
`not_available` because no matching observability rows were found, and no cost
was estimated. This is a small built-in canary artifact only; it is not
prompt-injection robustness evidence, model-obedience proof,
held-out/adversarial benchmark evidence, methodological-validity evidence, or a
SOTA claim.

**Completed checkpoint:** Built-in INV-7 structural and opt-in live fixture
sets now include custom prompt override coverage for registered
`thematic_coding` and `gt_constant_comparison` override surfaces. The new
fixtures render through the production `render_prompt_override()` wrapper and
exercise thematic `{combined_text}` plus GT `{segment_text}` and optional
`{codebook_context}` payloads. The built-in fixture-set version is now `2`.
This is fixture-definition and canary-coverage expansion only; it is not
prompt-injection robustness evidence, model-obedience proof, methodological
validity evidence, held-out adversarial benchmark evidence, or a SOTA claim.

**Completed checkpoint:** Grounded-theory projects can now opt into
`--refresh-higher-order` for `project recode` and
`project add-docs --recode`. The refresh path incrementally codes new
documents, invalidates stale higher-order outputs before intermediate save
points, rebuilds GT open-code context from the current codebook, reruns Axial
-> Selective -> Theory Integration, then reruns Cross-Interview -> Negative
Case. Default recode still uses hard invalidation, and the existing
default/thematic refresh path remains unchanged. This is an INV-11 GT refresh
slice only; it is not full INV-11 completion, GT methodological-validity
evidence, saturation evidence, full-GT evidence, or a SOTA claim.

**Completed checkpoint:** Default/thematic projects can now opt into
`--refresh-higher-order` for `project recode` and
`project add-docs --recode`. The refresh path incrementally codes new
documents, invalidates stale higher-order outputs before intermediate save
points, rebuilds Phase 1 context from the current codebook, reruns Perspective
-> Relationship -> Synthesis, then reruns Cross-Interview -> Negative Case.
Default recode still uses hard invalidation; grounded-theory refresh was
deferred in that slice and later implemented as a separate GT refresh
checkpoint. This is an INV-11 thematic refresh slice only; it is not full
INV-11 completion, methodological-validity evidence, or a SOTA claim.

**Completed checkpoint:** Rendered custom prompt overrides are now bookended by
a repo-owned instruction/data-separation wrapper. The wrapper preserves the
operator-authored template inside a stable boundary and appends
`REPOSITORY DATA-BOUNDARY REMINDER` after arbitrary operator-authored text.
Regression tests cover thematic and GT override prompts plus a contradictory
operator-template suffix. This is deterministic custom-prompt governance only;
it is not prompt-injection robustness evidence, model-obedience proof,
held-out/adversarial benchmark evidence, methodological-validity evidence, or a
SOTA claim.

**Completed checkpoint:** A protocol-guarded built-in INV-7 live canary
artifact set is committed at
`docs/benchmarks/inv7_live_canary_2026_06_22/`: pre-run protocol, live result
package, protocol/result preflight report, Phase 0 scorecard, README, and a
repo-local synthetic project shell for rescoring. The canary scored 3/3 passed
with `attack_success_rate=0.0`; the Wilson upper bound remains approximately
0.5615 because the denominator is only 3. D10 cost is `not_available` because
no matching observability rows were found, and no cost was estimated. This is a
small built-in canary artifact only; it is not prompt-injection robustness
evidence, model-obedience proof, held-out/adversarial benchmark evidence,
methodological-validity evidence, or a SOTA claim.

**Completed checkpoint:** MCP JSON/Markdown export tools can now write confined
SQLite mirrors for audit event logs when explicitly enabled with
`audit_event_db=True`. The flag requires `audit_event_log=True`, default MCP
export payloads remain unchanged, and the mirror is derived from the confined
export artifact path under `EXPORTS_DIR`. This is local provenance/queryability
infrastructure only, not signing, immutable storage, external timestamping,
append-only infrastructure, methodological validity evidence, or a full
tamper-evident audit log.

**Completed checkpoint:** Local export-audit scripts, Make targets, and
`project export` can now update the optional SQLite event mirror whenever JSONL
audit logging is explicitly enabled. `--audit-db` / `AUDIT_DB` requires
`--audit-log` / `AUDIT_LOG`, so SQLite remains a mirror rather than a standalone
source of truth. This is local provenance/queryability infrastructure only, not
signing, immutable storage, external
timestamping, append-only infrastructure, methodological validity evidence, or
a full tamper-evident audit log.

**Completed checkpoint:** Verified export audit JSONL event logs can now be
mirrored into local SQLite and verified there. The mirror imports full event
payload JSON plus query-friendly columns, fails before DB writes when the source
JSONL log is invalid, is idempotent for already-imported events, and checks
event shape, self-hashes, previous-event links, duplicate event hashes, stored
hash columns, and row ordering. This is local provenance/queryability
infrastructure only, not signing, immutable storage, external timestamping,
append-only infrastructure, methodological validity evidence, or a full
tamper-evident audit log.

**Completed checkpoint:** Relationship claims now resolve direct evidence
strings into exact supporting anchors when the evidence uniquely grounds to the
loaded corpus. Code relationship claims prefer existing scoped code-application
anchors and skip duplicate evidence-only anchors for the same span; ambiguous
or unresolvable relationship evidence remains visibly unanchored. This is
structural traceability only, not claim truth, semantic validation of
relationship prose, methodological validity, or SOTA evidence.

**Completed checkpoint:** Code-scoped higher-order claims now inherit existing
exact code-application anchors for their scoped code IDs, with duplicate anchors
removed. Perspective, code-relationship, synthesis-recommendation, and
GT-category claims with code scope can now cite underlying exact source spans;
corpus-level/no-code-scope claims remain visibly unanchored. This is structural
traceability only, not claim truth, semantic validation of higher-order prose,
methodological validity, or SOTA evidence.

**Completed checkpoint:** Prompt override rendering now rejects structured
metadata values and string metadata values containing CR/LF before rendering.
This protects declared metadata placeholders such as GT `doc_name` from adding
unprefixed prompt lines through custom templates. It is structural boundary
hardening only, not model-obedience or live prompt-injection robustness
evidence.

**Completed checkpoint:** Prompt override rendering now rejects raw/unwrapped
values supplied for declared required or optional data placeholders before any
LLM call. Templates already had to include protected data placeholders as bare
fields; the renderer now also checks that the corresponding values carry
untrusted-data block structure. This is structural custom-prompt boundary
hardening only, not model-obedience or live prompt-injection robustness
evidence.

**Completed checkpoint:** Tracked text files are now LF-normalized and
`.gitattributes` records an LF text policy. CRLF scans over tracked text files
return no matches, and `make check` remains green. Pre-existing trailing
whitespace was not stripped in this lane to avoid changing broad source/template
literal content under a line-ending-only plan.

**Completed checkpoint:** Cost observability targets are verified in the
current environment. `make cost` returns real `llm_client` LLM-call and
embedding cost tables instead of the fallback path, and `make errors` exits 0
with a clear recent-error summary. No Makefile or helper-code changes were
needed.

**Completed checkpoint:** Ruff now gates `F541`, and the seven existing
no-placeholder f-strings were mechanically rewritten without intended runtime
behavior changes. The normal `make lint` gate includes F541 through
`pyproject.toml`; `F401` and `E402` remain deferred for separate wrapper/
re-export review.

**Completed checkpoint:** Representative API and MCP project-ID boundaries now
have regression tests for invalid/traversal-like IDs. API read/mutation
surfaces return 404 without aliasing to an existing project, MCP read/export
tools return JSON error payloads, and MCP delete does not delete valid projects
when given invalid IDs. Existing production behavior already satisfied the
tests, so no boundary implementation change was needed.

**Completed checkpoint:** Project exports now have an explicit overwrite
policy: default overwrite remains for compatibility, while
`--no-overwrite`/`overwrite=False` fail before writing existing
JSON/Markdown/QDPX targets or any existing planned CSV target. CSV preflights
the full artifact set before writing to avoid partial exports. This is local
clobber prevention only, not append-only/tamper-evident storage.

**Completed checkpoint:** Phase 0 now reports deterministic
`corpus_scope_adequacy` for the corpus boundary record: missing/empty/
missing-sampling-frame/complete status, field-level completeness, document
count, claim count, and status-specific warnings. The scorecard reuses the
scope-phrasing lint status classifier and remains report-boundary accounting
only, not sampling-frame adequacy, population-validity evidence,
methodological validity, or SOTA evidence.

**Completed checkpoint:** Phase 0 now reports deterministic
`claim_anchor_coverage` for INV-9 ledger rows: total claims,
supporting/contrary anchor counts, anchored/unanchored counts, anchored-rate
Wilson interval metadata, and breakdowns by claim kind, source stage, and
support status. Contrary anchors count as source-anchor coverage and
no-claims events remain visible as ledger rows. This is structural accounting
only, not claim truth, human adjudication, full disconfirmation coverage,
methodological validity, or SOTA evidence.

**Completed checkpoint:** `qc_cli.py validate-inv7-package`,
`qc_cli.py validate-inv7-live-protocol`, and `qc_cli.py inv7-live-preflight`
now delegate to the canonical INV-7 validation/preflight scripts while
preserving script-owned JSON output and exit codes. This is CLI parity and
process/provenance validation only, not prompt-injection robustness evidence,
model-obedience evidence, methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** `qc_cli.py validate-d3-baseline-package
<package_file>` now delegates to the canonical D3 baseline package validator
script while preserving script-owned JSON output and exit codes. This is CLI
parity/package-provenance validation only, not held-out D3 evidence,
methodological-validity evidence, or superiority evidence.

**Completed checkpoint:** Versioned D3 application-baseline packages now
validate through `qc_clean/core/d3_baseline_package.py`,
`scripts/validate_d3_baseline_package.py`, and
`make validate-d3-baseline-package PACKAGE=...`. The Phase 0 `D3_BASELINES=`
loader validates recognized versioned packages before scoring while preserving
legacy raw-list/object compatibility. This is package/provenance validation
only, not live-baseline evidence, held-out D3 evidence, methodological-validity
evidence, or superiority evidence.

**Completed checkpoint:** `qc_cli.py validate-d3-gold <gold_set>` and
`qc_cli.py validate-d7-gold <gold_set>` now delegate to the canonical D3/D7
gold-set validator scripts while preserving script-owned JSON output and exit
codes. This is CLI parity/package-provenance validation only, not held-out
gold evidence, expert-label evidence, methodological-validity evidence, or
superiority evidence.

**Completed checkpoint:** `project add-docs --recode` now explicitly adds
documents and invokes the existing incremental recode path in one opt-in
command, forwarding `--model` when supplied. Plain `add-docs` still does not
spend model budget, and zero successful additions do not trigger recode. This
is explicit incremental recode-on-mutation only; INV-11 remains partial because
full higher-order auto-recompute is still unresolved.

**Completed checkpoint:** The top-level CLI now exposes
`qc_cli.py validate-d7-baseline-package <package_file>`, delegating to the
canonical D7 baseline package validator script with script-owned JSON output and
exit-code behavior. This is CLI parity/provenance ergonomics only, not held-out
D7 evidence, live-baseline evidence, or superiority evidence.

**Completed checkpoint:** Versioned D7 retrieval and live-baseline prediction
packages now validate through `qc_clean/core/d7_baseline_package.py` and
`make validate-d7-baseline-package PACKAGE=...`. D7 comparison preflight reuses
that validator, and direct Phase 0 `BASELINES=` scoring validates recognized
versioned packages before returning baseline rows while preserving legacy raw
lists. This is package/provenance validation only, not held-out D7 evidence,
live-baseline evidence, methodological-validity evidence, or superiority
evidence.

**Completed checkpoint:** Supported custom prompt override surfaces are now
declared in `qc_clean/core/prompt_override_registry.py`, and
`make lint-prompt-overrides` emits a schema_version=1 JSON report that fails if
source uses an unregistered `prompt_overrides` key or if a registered surface is
not used in source. The current `thematic_coding` and
`gt_constant_comparison` call sites consume the registry. This is deterministic
custom-prompt governance only, not prompt-injection robustness evidence,
model-obedience evidence, or a committed live adversarial benchmark.

**Completed checkpoint:** Anchored quote speaker attribution now falls back to
explicit same-line `Speaker:` source prefixes when no containing segment speaker
is available. Containing segment speaker remains authoritative, ordinary prose
does not produce speaker attribution, and speaker is still outside hash-based
anchor verification. This narrows the INV-1 speaker caveat but is not
diarization, speaker verification, methodological-validity evidence, or SOTA
evidence.

**Completed checkpoint:** Span grounding now has a conservative deterministic
fuzzy fallback for long near-verbatim quote elisions. Exact normalized matching
still runs first; exact ambiguity remains ambiguous; fuzzy recovery only runs
when exact matching finds zero occurrences; short vague quotes are rejected; and
multiple fuzzy-qualified source regions are ambiguous rather than guessed.
Recovered spans still point to exact original source text and verify by hash.
This is deterministic near-verbatim recovery only, not semantic grounding,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** Explicit selected candidate IDs can now be recorded as
schema_version=1 theoretical-sampling result packages through
`make export-theoretical-sampling-results` /
`scripts/export_theoretical_sampling_results.py`. The exporter validates the
registered protocol and candidate package, rejects unknown selected IDs and
unregistered success criteria, derives addressed gap codes/types from selected
candidates, and writes packages compatible with `make theoretical-sampling-preflight`.
This is result-package/provenance export only, not candidate-selection judgment,
new data collection, sampling-frame adequacy evidence, methodological
saturation evidence, full grounded-theory evidence, or SOTA evidence.

**Completed checkpoint:** Loaded-document theoretical-sampling candidate
packages can now be exported through
`make export-theoretical-sampling-candidates` /
`scripts/export_theoretical_sampling_candidates.py`. The exporter loads a saved
project, validates the registered protocol against the current project/corpus
hashes, runs the existing diagnostic `suggest_next_documents()` heuristic, and
writes schema_version=1 candidate packages compatible with
`make theoretical-sampling-preflight`. This is candidate-package/provenance
export only, not candidate-selection execution, new data collection,
sampling-frame adequacy evidence, methodological saturation evidence, full
grounded-theory evidence, or SOTA evidence.

**Completed checkpoint:** Theoretical-sampling candidate/result packages can
now be preflighted against registered protocols through
`make theoretical-sampling-preflight` /
`scripts/preflight_theoretical_sampling_protocol.py`. The preflight validates
schema_version=1 candidate/result packages and checks protocol IDs,
project/corpus/state hashes, candidate-source policy, collection mode, max
suggestions, target-gap code/type coverage, selected-candidate provenance, and
result addressed-gap/success-criteria drift. This is protocol/provenance
infrastructure only, not candidate-selection execution, data collection,
sampling-frame adequacy evidence, methodological saturation evidence, full
grounded-theory evidence, or SOTA evidence.

**Completed checkpoint:** Pre-run theoretical-sampling protocol packages can
now be validated through `make validate-theoretical-sampling-protocol` /
`scripts/validate_theoretical_sampling_protocol.py`. The schema records target
gap codes/types, category adequacy thresholds, candidate-source and
collection-mode policy, collection rules, stopping rule, success criteria, and
hashes. This is protocol/provenance infrastructure only, not populated
theoretical sampling, sampling-frame adequacy evidence, methodological
saturation evidence, full grounded-theory evidence, or SOTA evidence.

**Completed checkpoint:** D7 comparison protocol/preflight can now guard
opt-in live candidate-selection baseline packages as well as retrieval
prediction packages. Protocol expectations remain backward-compatible for
retrieval packages and can now declare
`baseline_mode="live_candidate_selector"` plus expected model/config metadata;
preflight accepts matching live packages and rejects model drift before guarded
comparison output is written. This is guard/provenance infrastructure only, not
a committed held-out D7 result, live-baseline evidence, methodological-validity
evidence, or superiority evidence.

**Completed checkpoint:** Opt-in live D7 candidate-selection baseline packages
can now be generated through `make run-d7-live-baseline` and
`qc_cli.py run-d7-live-baseline`. The exporter retrieves bounded D7 candidate
passages, asks a configured live model to select existing candidate IDs through
structured output, fails loudly on unknown candidate IDs, records prompt hashes
plus model/trace/budget/retrieval metadata, and writes a scorecard-compatible
`disconfirmation_baselines` package. This is live-baseline package generation
only, not a committed held-out D7 result, unbounded generic ChatGPT baseline,
methodological-validity evidence, or superiority evidence.

**Completed checkpoint:** Structural and opt-in live INV-7 fixture package
generation can now be run through canonical local CLI commands:
`qc_cli.py run-inv7-fixtures` and `qc_cli.py run-inv7-live-fixtures`. These
commands delegate to existing scripts and preserve script-owned fixture
generation, live model calls, summaries, and output writing. This is fixture
orchestration/provenance only, not prompt-injection robustness proof or
committed live benchmark evidence.

**Completed checkpoint:** `scripts/run_d7_retrieval.py` now has direct
script-boundary tests for successful stdout/`--output` parity, missing-project
JSON errors, and typed option forwarding into the core D7 retrieval exporter.
The script behavior already satisfied those tests, so no runtime change was
required. This is test coverage for D7 orchestration only, not held-out D7
evidence, live-baseline evidence, methodological-validity evidence, or SOTA
evidence.

**Completed checkpoint:** D7 retrieval export and guarded retrieval comparison
can now be run through canonical local CLI commands:
`qc_cli.py run-d7-retrieval` and `qc_cli.py compare-d7-retrieval`. These
commands delegate to the existing D7 scripts and preserve script-owned export,
preflight, scoring, JSON error, and report-writing behavior. This is D7
orchestration/provenance only, not held-out D7 evidence, live-baseline evidence,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** Strict Phase 0 package manifests can now be run
through the canonical local CLI with
`qc_cli.py bench-package <package_file>`. The command delegates to
`scripts.run_phase0_benchmark_package.main` and preserves the package runner's
manifest validation, relative-path resolution, JSON error behavior, and
canonical scorecard invocation. This is package orchestration/provenance only,
not held-out benchmark evidence, methodological-validity evidence, or SOTA
evidence.

**Completed checkpoint:** `qc_cli.py bench` now mirrors the current Phase 0
external-input and protocol-guard flags from `scripts/bench_phase0.py`,
including D3 baselines, D4/D6/D8/D9 protocol files, D6 stratified rows, and
confidence-calibration protocol files. The wrapper forwards those flags
unchanged to the canonical Phase 0 scorecard script. This is CLI
parity/provenance only, not held-out benchmark evidence,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** `make bench` now accepts `CONFIDENCE_PROTOCOL=...`
and `scripts/bench_phase0.py --confidence-calibration-protocol-file ...` to
enforce confidence-calibration protocol/result preflight at score time. Failed
preflight returns JSON with the preflight report and blocks
scorecard/output/artifact writes; passing guarded scorecards include
`_meta.preflight_reports.confidence_calibration`, input hashes, command
provenance, and package manifests include the protocol file. This is
score-time provenance only, not calibration proof, held-out correctness
evidence, methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** Confidence-calibration result files can now be
preflighted against registered calibration protocols with
`make confidence-calibration-preflight PROTOCOL=... CALIBRATION=...` /
`scripts/preflight_confidence_calibration_protocol.py`. The preflight validates
the protocol and concrete result rows, checks optional result-file SHA-256
locks, label-source/evaluator consistency, target surfaces, planned item count,
and emits a schema_version=1 pass/fail report. This is process/provenance
metadata only, not calibration proof, held-out correctness evidence,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** Confidence-calibration protocols can now be
validated with `make validate-confidence-calibration-protocol PROTOCOL=...` /
`scripts/validate_confidence_calibration_protocol.py`. The validator checks
schema_version=1 protocol metadata, held-out prompt/model freeze,
contamination, pre-evaluation registration, corpus/state/prediction-artifact
hashes, label-source plan, target surfaces, confidence source, planned item
count, configured outcome metrics, optional outcome-file hash locks, and
success criteria. This is process/provenance metadata only, not calibration
proof, held-out correctness evidence, methodological-validity evidence, or
SOTA evidence.

**Completed checkpoint:** `make bench` now accepts `D9_PROTOCOL=...` and
`scripts/bench_phase0.py --d9-interpretive-preference-protocol-file ...` to
enforce D9 protocol/result preflight at score time. Failed preflight returns
JSON with the preflight report and blocks scorecard/output/artifact writes;
passing guarded scorecards include
`_meta.preflight_reports.d9_interpretive_preference`, input hashes, command
provenance, and package manifests include the protocol file, and the D9
scorecard uses supplied protocol metadata for non-inferiority assessment
without mutating saved state. This is score-time provenance only, not blind
expert-parity evidence, interpretive-depth evidence, methodological-validity
evidence, or SOTA evidence.

**Completed checkpoint:** D9 interpretive-preference result files can now be
preflighted against registered D9 protocols with
`make d9-interpretive-preference-preflight PROTOCOL=... PREFERENCE=...` /
`scripts/preflight_d9_interpretive_preference_protocol.py`. The preflight
validates the protocol and concrete result rows, checks optional result-file
SHA-256 locks, evaluator type/count, target criteria, target surfaces, planned
case count, and emits a schema_version=1 pass/fail report. D9 preference rows
can carry `evaluator_type` and `surface` metadata while preserving existing
scorecard compatibility through defaults. This is process/provenance metadata
only, not blind expert-parity evidence, interpretive-depth evidence,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** D9 interpretive-preference protocols can now be
validated with `make validate-d9-interpretive-preference-protocol PROTOCOL=...`
/ `scripts/validate_d9_interpretive_preference_protocol.py`. The validator
checks schema_version=1 protocol metadata, held-out prompt/model freeze,
contamination, pre-evaluation registration, blinding, corpus/state/comparison
artifact hashes, evaluator plan, target criteria/surfaces, planned case count,
non-inferiority margin, optional outcome-file hash locks, and success criteria.
This is process/provenance metadata only, not blind expert-parity evidence,
interpretive-depth evidence, methodological-validity evidence, or SOTA
evidence.

**Completed checkpoint:** `make bench` now accepts `D8_PROTOCOL=...` and
`scripts/bench_phase0.py --d8-gt-fidelity-protocol-file ...` to enforce D8
protocol/result preflight at score time. Failed preflight returns JSON with the
preflight report and blocks scorecard/output/artifact writes; passing guarded
scorecards include `_meta.preflight_reports.d8_gt_fidelity`, and input hashes,
command provenance, and package manifests include the protocol file. This is
score-time provenance only, not expert-rubric acceptance,
methodological-saturation evidence, full grounded-theory evidence, or SOTA
evidence.

**Completed checkpoint:** D8 GT-fidelity result files can now be preflighted
against registered D8 protocols with
`make d8-gt-fidelity-preflight PROTOCOL=... GT_FIDELITY=...` /
`scripts/preflight_d8_gt_fidelity_protocol.py`. The preflight validates the
protocol and concrete result rows, checks optional result-file SHA-256 locks,
evaluator type/count, target scopes, and targeted-scope `artifact_id` coverage,
and emits a schema_version=1 pass/fail report. This is process/provenance
metadata only, not expert-rubric acceptance, methodological-saturation
evidence, full grounded-theory evidence, or SOTA evidence.

**Completed checkpoint:** D8 GT-fidelity protocols can now be validated with
`make validate-d8-gt-fidelity-protocol PROTOCOL=...` /
`scripts/validate_d8_gt_fidelity_protocol.py`. The validator checks
schema_version=1 protocol metadata, held-out prompt/model freeze,
contamination, pre-evaluation registration, corpus/project-state/GT-artifact
hashes, evaluator plan, required rubric metrics, target scopes, optional
outcome-file hash locks, and per-metric success criteria. This is
process/provenance metadata only, not expert-rubric acceptance,
methodological-saturation evidence, full grounded-theory evidence, or SOTA
evidence.

**Completed checkpoint:** `make bench` now accepts `D4_PROTOCOL=...` and
`scripts/bench_phase0.py --d4-codebook-quality-protocol-file ...` to enforce
D4 protocol/result preflight at score time. Failed preflight returns JSON with
the preflight report and blocks scorecard/output/artifact writes; passing
guarded scorecards include `_meta.preflight_reports.d4_codebook_quality`, and
input hashes/command provenance/package manifests include the protocol file.
This is score-time provenance only, not blind expert-panel evidence, LLM-judge
evidence, codebook-quality evidence, methodological-validity evidence, or SOTA
evidence.

**Completed checkpoint:** D4 codebook-quality result files can now be
preflighted against registered D4 protocols with
`make d4-codebook-quality-preflight PROTOCOL=... QUALITY=...` /
`scripts/preflight_d4_codebook_quality_protocol.py`. The preflight validates
the protocol and concrete result rows, checks optional result-file SHA-256
locks, evaluator type/count, target scopes, and individual-code `code_id`
coverage, and emits a schema_version=1 pass/fail report. This is
process/provenance metadata only, not blind expert-panel evidence, LLM-judge
evidence, codebook-quality evidence, methodological-validity evidence, or SOTA
evidence.

**Completed checkpoint:** D4 codebook-quality protocols can now be validated
with `make validate-d4-codebook-quality-protocol PROTOCOL=...` /
`scripts/validate_d4_codebook_quality_protocol.py`. The validator checks
schema_version=1 protocol metadata, held-out prompt/model freeze,
contamination, pre-evaluation registration, corpus/project-state/codebook hashes,
blinding, evaluator plan, required rubric metrics, target scopes, and
per-metric success criteria. This is process/provenance metadata only, not blind
expert-panel evidence, LLM-judge evidence, codebook-quality evidence,
methodological-validity evidence, or SOTA evidence.

**Completed checkpoint:** `make bench` now accepts `D6_PROTOCOL=...` and
`scripts/bench_phase0.py --d6-bias-protocol-file ...` to enforce D6
protocol/result preflight at score time. Failed preflight returns JSON with the
preflight report and blocks scorecard/output/artifact writes; passing guarded
scorecards include `_meta.preflight_reports.d6_bias`, and input hashes/command
provenance/package manifests include the protocol file. This is score-time
provenance only, not a populated bias audit, causal proof, held-out correctness
evidence, methodological-validity evidence, or a bias-free claim.

**Completed checkpoint:** D6 bias result files can now be preflighted against a
registered D6 protocol with `make d6-bias-preflight PROTOCOL=... STRATIFIED=...
COUNTERFACTUAL=...` / `scripts/preflight_d6_bias_protocol.py`. The preflight
validates the protocol, result row shapes, required files for configured
dimensions, rejects files for unconfigured dimensions, checks optional SHA-256
locks, checks stratified attributes/surfaces, checks counterfactual attributes,
and emits a schema_version=1 pass/fail report. This is protocol/result
provenance only, not a populated bias audit, causal proof, held-out correctness
evidence, methodological-validity evidence, or a bias-free claim.

**Completed checkpoint:** D6 bias-audit protocols can now be validated with
`make validate-d6-bias-protocol PROTOCOL=...` /
`scripts/validate_d6_bias_protocol.py`. The validator checks schema_version=1
protocol metadata, ethical respondent-attribute policy, frozen case-set
metadata, configured stratified/counterfactual dimensions, matching strategies,
held-out prompt/model freeze, contamination check, pre-run registration,
project-state hash, and success criteria coverage. This is protocol/provenance
metadata only, not a populated bias audit, causal proof, held-out correctness
evidence, methodological-validity evidence, or a bias-free claim.

**Completed checkpoint:** Phase 0 now scores externally supplied D6 stratified
correctness/error rows through `make bench BIAS_STRATIFIED=...`,
`scripts/bench_phase0.py --bias-stratified-file`, package manifests, and
`ProjectState.config.extra["bias_stratified_evaluations"]`. The scorecard
reports overall accuracy/error rates with Wilson intervals, per-attribute/
per-group summaries, per-surface summaries, and max group error-rate gaps while
recording input hashes and command provenance. This is local accounting only,
not a populated bias audit, causal proof, held-out correctness evidence, or a
bias-free claim.

**Completed checkpoint:** `make compare-d7-retrieval ... PROTOCOL=...` can now
run the registered D7 comparison preflight at the scoring boundary. Failed
preflight blocks scoring and output report writes; passing guarded comparisons
include `preflight_report` in stdout/output JSON. This is score-time provenance
enforcement only, not held-out D7 evidence, live-baseline evidence,
methodological-validity evidence, or superiority evidence. D7 retrieval
prediction packages now carry
project/corpus/state/trace/budget provenance, and D7 retrieval comparisons can
be protocol-gated before scoring with `make validate-d7-comparison-protocol
PROTOCOL=...` and `make d7-comparison-preflight PROTOCOL=... GOLD=...
PREDICTIONS="..."`. The preflight requires versioned D7 gold and checks gold
metadata, project/corpus/state hashes, expected baseline names, retrieval
configuration, trace ID, budget, and optional prediction-file SHA-256 locks.
This is comparison provenance only, not held-out D7 evidence, live-baseline
evidence, methodological-validity evidence, or superiority evidence. Pre-run
live INV-7 protocol packages can now be
preflighted against concrete live result packages with
`make inv7-live-preflight PROTOCOL=... PACKAGE=...`, checking protocol/package
schema validity, live-result mode, split/fixture/model/trace/freeze/
contamination metadata, result budget, and exact prompt-hash parity before
scoring. This is package-matching provenance only, not a live benchmark result,
prompt-injection robustness evidence, model-obedience evidence, or validity
evidence. Pre-run live INV-7 protocol packages can now be
validated with `make validate-inv7-live-protocol PROTOCOL=...`, covering fixture
set metadata, exact prompt hashes, model, trace ID, budget, held-out
freeze/contamination/registration flags, and success criteria. This is protocol
provenance only, not a live result or prompt-injection robustness evidence.
Live INV-7 fixture outputs now carry
`fixture_prompt_hashes`, a fixture-ID keyed SHA-256 map of the exact prompts
sent to the live model caller. Versioned INV-7 package validation accepts
matching prompt hashes and rejects missing/extra keys or malformed digests when
the map is present, while remaining compatible with older packages that omit
hashes. Prompt hashes are provenance only, not prompt-injection robustness
evidence. Prompt override rendering now requires every exposed
value to be declared as required protected data, optional protected data, or
metadata. Thematic overrides explicitly expose `{combined_text}` plus
`{num_interviews}` metadata; GT constant-comparison exposes `{segment_text}`,
optional `{codebook_context}`, and scalar metadata `{seg_idx}`,
`{total_segments}`, `{doc_name}`. Undeclared renderer values fail before any LLM
call. This is custom-prompt governance only, not proof of prompt-injection
robustness. `make import-adjudication-responses` can now take
`PREFLIGHT_PROTOCOL=... PREFLIGHT_SAMPLE=...` and run response preflight at the
import boundary before writing D3/D7 gold-package outputs. Failed preflight
emits machine-readable JSON and writes no outputs; passing guarded imports
include the preflight report in stdout. This is an import-time provenance guard
only, not evidence that labels are expert-produced, correct, held out, or
methodologically valid. Completed adjudication response packages can now be
preflighted with `make adjudication-response-preflight PROTOCOL=...
SAMPLE=... RESPONSES=...`, which reuses protocol/sample preflight, requires
completed response validation, checks project/corpus/project-state hashes,
enforces exact sample item IDs, and confirms protocol-required target types have
completed responses before import. This is process/provenance metadata only; it
does not create labels, prove label correctness, supply expert evidence, or
license SOTA or methodological-validity claims. Corpus-scope warning propagation now covers Markdown,
JSON `export_warnings` metadata, and CSV `export_warnings.csv` for claim-bearing
exports without recorded scope, and CLI/MCP project creation can now persist
corpus scope when supplied while leaving no-scope creation compatible.
Completed adjudication response packages can now be imported through
`make import-adjudication-responses` into D3/D7 gold package inputs using only
valid completed code-application and negative-case responses while excluding
invalid/unclear labels. These generated gold-package files are still protocol
artifacts unless they were populated under a documented human/expert
adjudication protocol; they are not, by themselves, expert evidence,
methodological validity evidence, or SOTA evidence.
Imported D3/D7 gold package files can now be assembled into a strict Phase 0
package manifest with `make write-phase0-adjudication-package`, which validates
versioned package inputs together before `make bench-package` scoring. This is
repeatability/provenance infrastructure only; it does not prove that labels
were expert-produced, held out, or methodologically adequate.
Pre-label adjudication protocol metadata can now be validated with
`make validate-adjudication-protocol`, including held-out freeze,
contamination, registration, coder-count, dimension/target compatibility, and
success-criteria checks. This is protocol/provenance metadata only; it does not
create labels, correctness estimates, methodological validity evidence, or SOTA
evidence.
Registered adjudication protocols can now be preflighted against concrete sample
packages with `make adjudication-protocol-preflight`, checking project/corpus
hashes, optional project-state and sample-file hashes, required target-type
coverage, and planned sample size before labeling. This is handoff/process
metadata only, not labels, correctness estimates, validity evidence, or
benchmark evidence.
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
tamper-evident audit substrate. `make verify-export-audit-manifest` now checks
manifest self-hash, artifact sizes/hashes, and optional current project-state
hash; verification is still local integrity checking, not a signed or
append-only audit log. `qc_cli.py project export --audit-manifest ...
--verify-audit-manifest` can now write and immediately verify optional sidecars
for JSON/CSV/Markdown/QDPX exports without changing default export behavior.
MCP JSON/Markdown export tools can now do the same with confined sidecars under
`EXPORTS_DIR`; default MCP export return payloads are unchanged when audit flags
are absent. `make export-publish-preflight` now provides a strict local
publish/handoff gate that requires an existing verified export-audit manifest
and can include current project-state hash checking when `ID=<project_id>` is
supplied; this is still local integrity/provenance metadata, not signing,
append-only logging, methodological validity evidence, or a full
tamper-evident audit substrate. Local audit scripts can now append opt-in
hash-linked JSONL events for manifest write, manifest verification, and publish
preflight operations via `--audit-log` / `AUDIT_LOG=...`; `make
verify-export-audit-log` verifies event self-hashes and previous-event links.
This is local provenance/event-history metadata only, not signing, immutable
storage, external timestamping, methodological validity evidence, or a full
tamper-evident audit substrate. CLI `project export --audit-manifest ...
--audit-log ...` and MCP JSON/Markdown export tools with `audit_event_log=True`
can now append those event-log records from the main export workflows while
preserving default export behavior and MCP confined output paths.
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
