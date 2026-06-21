# Evaluation Harness — Design

**The keystone for a public, state-of-the-art qualitative coding system.**

*Version 0.1 (design) — 2026-06-19*

> **Why this exists.** Per `PROJECT_THEORY_AND_GOALS.md` (Ambition), the product
> goal is to be provably SOTA on the measurable rigor dimensions and at
> expert-parity on interpretation. "Provably" is the operative word: **you cannot
> beat a state of the art you cannot measure.** This harness is simultaneously
> (a) the *evidence* for every SOTA claim and (b) the *feedback loop* that makes
> the system better. It closes **INV-3** (validity adjudication separate from
> consistency) and operationalizes **INV-5** (bias). It is roadmap item #1.
>
> **Build on, don't hand-roll.** This harness will be built on `prompt_eval`
> (`~/projects/prompt_eval`) — frozen case sets, evaluators (`llm_judge`,
> `kappa`, `exact_match`, `contains`), bootstrap CIs, Welch's test, instruction
> search — and `llm_client` observability. *Current integration is minimal:* one
> optimization script imports `prompt_eval` (`scripts/optimize_thematic_prompt.py`)
> and `PipelineContext.prompt_overrides` exists. **Built so far (Phase 0):**
> `make bench ID=<project_id>` / `qc_cli.py bench <project_id>` →
> `qc_clean/core/bench.phase0_scorecard` (D1
> grounding + D2 coverage, optional D7/INV-7 externally supplied fixture scores,
> and D10 cost/latency from observability rows plus last-run wall-clock metadata, with scorecard input hashes and optional versioned `benchmark_results/` artifact packaging; deterministic, LLM-free). **Not yet built:** the full `prompt_eval`-backed
> suite — frozen case sets, the QC-specific evaluators below, gold-vs-agreement
> (D3), held-out D7 benchmark runs, bias (D6), calibration, baselines — remains a design target. Do not
> reimplement scoring, statistics, or experiment tracking — extend `prompt_eval`.

---

## 1. What it must measure

Each dimension maps to a SOTA claim and (where relevant) an invariant. The bar is **"≥ the relevant baseline / human ceiling, with a confidence interval that excludes the baseline."** A claim is licensed only for dimensions that pass that bar.

| # | Dimension | What it answers | Invariant | SOTA bar (target) |
|---|-----------|-----------------|-----------|-------------------|
| D1 | **Evidentiary grounding** | Do quotes resolve to the exact source span? | INV-1 | ≥0.95 exact-span resolution; ~0 unresolvable. (Machine advantage via hard enforcement.) |
| D2 | **Coverage** | Did every textual unit get a coding decision (incl. null)? | INV-8 | 1.0 over the segment universe. Edge vs *humans* (who rarely code exhaustively); **not** vs all tools — MAXQDA 26.2 (Mar 2026) ships segment-level AI coding. So the defensible edge is exhaustive coverage *with a scored, span-anchored denominator* (`examined_rate` + `make bench`), not segment-level coding per se. |
| D3 | **Application validity vs gold** | Do code→segment assignments match an adjudicated gold? | INV-3 | Agreement with gold ≥ human–human agreement on the same task (κ/α in the human band, see §3). |
| D4 | **Codebook quality** | Are the codes clear, specific, useful, grounded? | — | Blind expert ratings ≥ human-generated codebook. |
| D5 | **Reliability (consistency, not validity)** | Is the system self-consistent across passes? | — | Report LLM-pass agreement + stability with bootstrap CIs. Necessary, not sufficient. |
| D6 | **Bias** | Does coding track identity cues rather than meaning? | INV-5 | Counterfactual identity-swap code-change rate ≈ 0; stratified error parity. ≤ human bias where measurable. |
| D7 | **Disconfirmation** | Does it find the contrary evidence humans find? | INV-2/6 | Negative-case recall/precision vs human-identified disconfirming evidence ≥ human. |
| D8 | **GT fidelity** | Constant comparison / category development / saturation, if claimed | INV-4 | Expert-rubric acceptance (only if the GT path claims theory generation). |
| D9 | **Interpretive depth (the hard wall)** | Latent meaning, tone, conversational context | — | Blind expert *preference* parity (≈50/50 system vs human), augmented by human-in-the-loop. **Target parity, not dominance.** |
| D10 | **Cost / latency** | $ and wall-clock per transcript | — | Report; machine advantage is expected, not the headline. |

**Honest sequencing of the claim:** SOTA is *earned per dimension*. We expect to clear it decisively on D1–D2, D5, D7, D10 and credibly on D3–D4; D9 is parity-at-best near-term; D6/D8 are frontiers we measure before claiming.

## 2. Metrics (concrete and computable)

- **D1 grounding:** `% quotes whose normalized text resolves to a unique anchored span (doc_id + char offsets + hash)`; count of unresolvable / multiply-resolvable / hallucinated quotes. **Implemented** — `qc_clean/core/grounding.verify_grounding` (INV-1 landed); surfaced via `make bench` and MCP `qc_grounding_report`.
- **D2 coverage:** **implemented** — `qc_clean/core/segmentation.compute_coverage` reports both *traversal* coverage (`covered/total`) and, under **exhaustive coding** (`--exhaustive`), *examined-and-judged* coverage (`examined_rate`, `coded_segments`) over the char-anchored segment universe (INV-8). Surfaced in `make bench` / `qc_grounding_report`. The defensible denominator the harness needs.
- **D3 application validity:** against adjudicated gold on the **same units** — Cohen's κ (2 raters) / **Krippendorff's α** (handles multi-label, missing, boundary disagreement), precision/recall/F1 on code labels, and **span alignment via IoU + Modified Hausdorff Distance** (the LLMCode metrics). **Scoring substrate implemented:** `phase0_scorecard` / `make bench D3_GOLD=d3_gold.json` reports exact code/source-anchor TP/FP/FN, precision, recall, F1, recall/precision Wilson intervals, a deterministic exact-key F1 bootstrap interval, and local same-code/same-document char-span IoU plus discrete Modified Hausdorff diagnostics when D3 application gold is supplied through project metadata or an external file. Gold files may be raw anchor lists, objects with `application_gold` / `code_applications`, or versioned schema_version=1 D3 gold-set packages validated by `make validate-d3-gold GOLD=gold_set.json`; when a versioned package is used, the scorecard includes compact `gold_provenance` with dataset/split/hash/freeze/adjudication metadata. This exact/span-distance scorer is not full D3: κ/α/AC1, human ceiling, and expert parity remain future work. The unit-of-analysis fix the IRR caveat (theory doc §11) demands. **Report a prevalence-robust coefficient (Gwet's AC1) alongside κ:** qualitative codes are often rare, and κ collapses under skewed prevalence even at high raw agreement (the 2026 PLOS study reported κ≈0.34 despite high agreement, and reports AC1 for exactly this reason). Make prevalence attenuation a first-class reported quantity, not a caveat.
- **D4 codebook quality:** `llm_judge` rubric (clarity / specificity / usefulness / grounding, 0–1 each) **plus** a blind human expert panel; report both and their agreement.
- **D5 reliability:** existing `project irr` / `project stability`, but reported with **bootstrap CIs**, prevalence, and a prevalence-robust coefficient (**Gwet's AC1**) alongside κ, and labeled *codebook-discovery* vs *application-level* agreement. Application-level reporting requires INV-8 and includes both positive segment x code application agreement and segment-decision agreement (`coded` / `no_code` / `not_examined`). (GT reliability now measures the actual constant-comparison stage — fixed; see theory doc §11.)
- **D6 bias:** (i) stratified error rate by respondent attribute where ethical; (ii) **counterfactual masking/swap** — hold substantive text constant, vary identity markers, measure code-change rate (target ≈0).
- **D7 disconfirmation:** recall/precision of system negative cases against a human-built gold set of disconfirming passages. **Scoring substrate implemented:** `phase0_scorecard` / `make bench` computes exact target-claim/source-anchor TP/FP/FN, recall, precision, F1, 95% Wilson intervals for recall/precision, and deterministic exact-key F1 bootstrap intervals when `ProjectState.config.extra["disconfirmation_gold"]` contains adjudicated contrary-evidence anchors, or when an external gold JSON file is supplied via `make bench ID=<project> GOLD=gold.json` / `scripts/bench_phase0.py --gold-file`. Gold files may be raw anchor lists, objects with `contrary_evidence`, or versioned schema_version=1 D7 gold-set packages validated by `make validate-d7-gold GOLD=gold_set.json`; when a versioned package is used, the scorecard includes compact `gold_provenance` with dataset/split/hash/freeze/adjudication metadata. It can also score externally supplied baseline predictions from `ProjectState.config.extra["disconfirmation_baselines"]` or `make bench ID=<project> BASELINES=baselines.json` / `scripts/bench_phase0.py --d7-baselines-file`, reporting baseline TP/FP/FN, recall, precision, F1, recall/precision Wilson intervals, F1 bootstrap intervals, system-minus-baseline deltas, and local paired exact-key bootstrap intervals for recall/precision/F1 deltas. `make run-d7-retrieval ID=<project> OUTPUT=predictions.json [MODE=lexical_bm25|embedding_hybrid]` exports configured retrieval-mode candidates as baseline-compatible predictions for that same `BASELINES=` path; `make compare-d7-retrieval ID=<project> GOLD=gold.json PREDICTIONS="a.json b.json"` scores multiple exported packages in one exact-span local comparison report. External gold and baseline files are applied in memory and do not mutate saved project state. **Not yet done:** no held-out D7 gold set has been populated/run, no live baseline run exists, no retrieval-mode comparison has been run on held-out data and prompt_eval-tested, and this score is exact-span only.
- **INV-7 prompt-injection fixture outcomes:** `phase0_scorecard` / `make bench` reports `prompt_injection_inv7` as `not_available` until fixture results are supplied through `ProjectState.config.extra["prompt_injection_evaluations"]`, `make bench ID=<project> PROMPT_INJECTION=inv7.json`, or `scripts/bench_phase0.py --prompt-injection-file`. `make run-inv7-fixtures OUTPUT=inv7.json` now writes a deterministic structural-boundary fixture result file that can feed that scorecard path. When supplied, the scorecard reports pass/fail counts, pass rate, attack-success rate, failed fixture IDs, and per-surface summaries. This is a measurement substrate only; the structural runner checks prompt construction, not live model obedience, and the current repo still has no live adversarial model benchmark.
- **D8 GT fidelity:** expert rubric on constant comparison, category property/dimension development, memo quality, saturation justification.
- **D9 interpretive depth:** forced-choice blind preference (expert picks the better of system vs human code/theme for latent-meaning items); report win rate with CI; parity = CI spans 0.5.
- **D10 cost/latency:** **scoring substrate implemented** — `make bench` reports `cost_latency_d10` from real `llm_client` `llm_calls` rows and `wall_clock_d10` from the last local `project run` metadata. Default cost matching uses the local project trace prefix (`qualitative_coding/project/<project_id>`), with `TRACE_ID=` / `--trace-id` for exact non-default traces and `OBS_DB=` / `--observability-db` for DB path overrides. Missing DB, matching rows, or run timing reports `not_available`; costs and wall-clock durations are never estimated from `ProjectState`. The cost-latency value is summed observed LLM-call latency; `wall_clock_d10.duration_s` is end-to-end elapsed time for the last local run, not a public benchmark runtime.

## 3. Gold standards and datasets

**The human ceiling (target band).** Published inter-coder agreement: **κ ≈ 0.72–0.82 for inductive coding schemes, 0.58–0.73 for unconstrained schemes.** "Expert parity" (D3) = agreement-with-gold in/above that band; "SOTA" = ≥ the human–human agreement measured on the *same* corpus (compute it; don't assume).

**Reuse released gold (fast, head-to-head, but contamination-flagged):**
- **LLMCode** (github.com/PerttuHamalainen/LLMCode) — human-annotated data + tooling that compares LLM to human codes with IoU / Modified Hausdorff. Closest ready-made evaluator; reuse its metrics and data.
- **HICode** (github.com/mianzg/HICode) — 3 datasets with human-constructed themes; reported **P=0.72 / R=0.74** — a concrete head-to-head target for hierarchical coding.
- **LOGOS** (arXiv:2509.24294) — 5 corpora + a 5-dimensional metric and an expert-developed schema (≈80.4% alignment reported) for GT-style evaluation.
- **Design rule (not just a caveat):** public datasets may be in model training data → **train/test contamination**. Therefore public sets are **regression/comparator suites only** (head-to-head vs HICode/LOGOS/etc.); the **headline SOTA/parity claims must rest on fresh in-house held-out gold** the models have never seen. "Contamination-checked" means: search for verbatim overlap, prefer post-cutoff data, and treat any public-set result as a comparator, never as the headline.

**Build a small in-house adjudicated gold set (for headline claims):** follow the expert-consensus-panel method — ≥2 qualified coders independently code, a third adjudicates disagreements, producing gold codes with labels, definitions, supporting anchored spans, and a recorded human–human agreement (the ceiling). Target the actual product domain (interviews/focus groups). Keep it held-out and prompt-frozen. The repo now has versioned D3 and D7 gold-set package validators (`scripts/validate_d3_gold_set.py` / `make validate-d3-gold`, `scripts/validate_d7_gold_set.py` / `make validate-d7-gold`) for application and contrary-evidence anchors, but no human-populated held-out package has been created or scored.

## 4. Baselines to beat

- **Generic single-prompt ChatGPT** (the "just ask an LLM" baseline most practitioners use).
- **This system** (the candidate).
- **Commercial AI coding** — ATLAS.ti Intentional AI Coding / MAXQDA AI Assist, where API access permits.
- **Human-only** — the gold panel's own inter-coder agreement = the ceiling for D3/D9.
- **Task-matched research prototypes** — HICode, LOGOS, TAMA/Auto-TA, re-run on shared data where reproducible.

## 5. Protocol (pre-registered before any run)

- **Datasets & domains:** ≥3 corpora, ≥2 domains, including ≥1 *messy* transcript set (disfluencies, overlap, timestamps).
- **Unit of analysis:** fixed in advance — turn-level for deductive application; researcher-delimited segment for inductive (requires the INV-8 segment universe to be defensible).
- **Blinding:** raters blind to whether codes are human- or machine-generated (D4, D9).
- **Frozen + hashed:** all prompts and model ids frozen and hashed before evaluation; no tuning against the test sets; held-out gold.
- **Pre-registered thresholds:** the §1 bars are written down *before* results, so nothing is graded post hoc.
- **Statistics:** bootstrap CIs and Welch's test (via `prompt_eval`); report prevalence and CIs alongside every κ/α; correct for multiple comparisons across dimensions.
- **Multi-label & near-synonym handling:** a reconciliation rubric for lexically-different-but-semantically-equivalent codes (don't penalize "trust" vs "confidence in system" as disagreement without check).

## 6. Infrastructure

- **`prompt_eval`** owns experiments, frozen case sets, evaluators, optimization (`instruction_search`), persistence, and stats. New QC-specific evaluators (grounding-rate, IoU/Hausdorff span alignment, coverage, counterfactual-swap, disconfirmation recall) are added as `prompt_eval` evaluator functions, not bespoke scripts.
- **`llm_client`** owns the runs and observability (cost/tokens/latency per `task`/`trace_id`).
- **QC surface:** current surfaces are `qc_cli.py bench <project_id>` and `make bench ID=<project_id>` for the deterministic Phase 0 local scorecard, with optional `D3_GOLD=d3_gold.json` / `--d3-gold-file`, `GOLD=gold.json` / `--gold-file`, `BASELINES=baselines.json` / `--d7-baselines-file`, `PROMPT_INJECTION=inv7.json` / `--prompt-injection-file`, `OBS_DB=` / `--observability-db` plus `TRACE_ID=` / `--trace-id` overrides for D10 cost/latency, and `ARTIFACT_DIR=benchmark_results` / `--artifact-dir` for a versioned Phase 0 package. The scorecard includes `_meta.input_hashes` for the loaded project state, corpus, and supplied benchmark files. Target future behavior behind `qc bench` is a frozen `prompt_eval` suite against a dataset that writes a scored report. Agent-drivable end to end (no manual steps).
- **Outputs:** Phase 0 scorecards now include input hashes for the loaded project state, corpus, and supplied external files. When `--artifact-dir` / `ARTIFACT_DIR=` is supplied, Phase 0 writes a versioned run directory with `scorecard.json` and `manifest.json`; the manifest records input hashes, scorecard hash, CLI provenance, claim-discipline text, and an explicit `prompt_eval.status=not_run` caveat. The target full harness output remains a richer `benchmark_results/` package with per-dimension scores, CIs, baseline deltas, dataset + prompt + model hashes, and a generated scorecard. These hashes are the artifact evidence the theory doc's claim discipline requires before any public SOTA statement; Phase 0 hashes and packages are provenance metadata, not validity evidence.

## 7. Acceptance criteria (the SOTA gate)

Two different statistical tests, because we make two different kinds of claim — do not conflate them:

- **Superiority** (for "more X than existing methods", e.g. D1/D2/D7): licensed only when the system is ≥ the named baseline with a **CI that excludes the baseline** (a one-sided superiority test).
- **Non-inferiority / parity** (for "matches expert humans", e.g. D9 and D3 where parity is the claim): licensed only when the system is within a **pre-registered non-inferiority margin** of the human ceiling — i.e. the CI for (system − human) lies above −δ for a δ fixed *before* the run. A superiority test is the wrong tool for a parity claim; using "CI excludes baseline" everywhere would either over-reject parity or smuggle in an unearned superiority claim.

Both require a held-out, prompt-frozen, contamination-checked dataset, recorded with dataset/prompt/model hashes. Until a dimension passes its appropriate test, claim discipline (theory doc §14) applies: describe capability, not superiority/parity.

## 8. Phasing (smallest real slice first)

- **Phase 0 local scorecard — DONE.** `qc_cli.py bench <project>` / `make bench ID=<project>` (`qc_clean/core/bench.py` → `phase0_scorecard`) computes **D1 grounding** (now real: `verify_grounding` returns the fraction of applications whose span anchor verifies — INV-1 landed), **D2 coverage** (including examined-and-judged coverage under `--exhaustive`), surfaces **D5** reliability/stability when present, includes a gold-dependent exact code/source-anchor **D3 application-validity** score with recall/precision Wilson intervals, F1 bootstrap intervals, and local same-code/doc span-IoU plus Modified Hausdorff diagnostics when adjudicated application gold is supplied through `D3_GOLD=d3_gold.json` (including versioned D3 gold-set packages with surfaced provenance), includes a gold-dependent **D7 disconfirmation** exact-anchor score with recall/precision Wilson intervals, F1 bootstrap intervals, and local paired baseline-delta bootstrap intervals when adjudicated gold contrary evidence is present in project metadata or supplied through `GOLD=gold.json` (including versioned D7 gold-set packages with surfaced provenance), can score externally supplied D7 baseline predictions through `BASELINES=baselines.json`, reports externally supplied **INV-7 prompt-injection** fixture outcomes when supplied through `PROMPT_INJECTION=inv7.json`, reports **D10 cost/latency** from matching `llm_client` observability rows, reports **D10 wall-clock runtime** from the last local `project run`, includes `_meta.input_hashes` for project/corpus/external inputs, and can write a versioned Phase 0 `benchmark_results/` package containing `scorecard.json` plus manifest. Deterministic and LLM-free. Remaining harness work: wire into `prompt_eval` for frozen case sets beyond the local exact-key bootstrap, build/run held-out D3/D7 gold sets, add D3 κ/α/AC1 and human-ceiling comparison, run actual/live baselines on held-out data, run live adversarial prompt-injection fixtures, turn public benchmark timing into full benchmark artifacts, and run on reused public gold as a comparator.
- **Phase 1 — small adjudicated gold.** Build/borrow a small expert gold set; compute D3 (κ/α, IoU/Hausdorff), D4 (codebook quality), D7 (disconfirmation recall) vs the human ceiling.
- **Phase 2 — full benchmark + public scorecard.** Add baselines (ChatGPT, commercial, prototypes), D6 (bias + counterfactual), confidence calibration, D8 (GT fidelity), D9 (interpretive-depth preference). Publish the scorecard with the SOTA gate (§7) applied per dimension.

## 9. Threats to the evaluation itself

- **Benchmark construct validity** — does each metric measure the dimension it names? (cf. "Measuring what Matters," arXiv:2511.04703). Document the construct for each.
- **Gold disagreement** — humans disagree; always report the human–human ceiling, never treat one coder as truth.
- **Train/test contamination** — public datasets may be in training data; flag, and base headline claims on fresh in-house gold.
- **Prompt overfitting** — freeze prompts/models and hold out test sets; `instruction_search` optimizes on a *separate* dev split only.
- **LLM-judge bias** — `llm_judge` (D4) can favor LLM-style prose; cross-check against the blind human panel.

## 10. References

Human IRR bands and gold-via-consensus method: qualitative content-analysis IRR literature; PLOS Digital Health / medRxiv blinded comparison (expert consensus panels). Span-alignment metrics + released human-coded data: LLMCode (Oksanen, Lucero, Hämäläinen). Hierarchical-coding head-to-head: HICode (Zhong, Wang, Field, EMNLP 2025). GT-style schema alignment: LOGOS (Pi, Yang, Nguyen). Systematic-bias caution: Ashwin, Chhabra & Rao (2025, *Sociological Methods & Research*). Benchmark construct-validity caution: "Measuring what Matters" (arXiv:2511.04703). Stats + experiment infra: `prompt_eval` (bootstrap CI, Welch's test, evaluators). See `PROJECT_THEORY_AND_GOALS.md` §11/§15 for the consistency-vs-validity and unit-of-analysis context this harness resolves.
