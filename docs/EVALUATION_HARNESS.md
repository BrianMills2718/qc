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
> **Build on, don't hand-roll.** This harness is built on `prompt_eval`
> (`~/projects/prompt_eval`) — frozen case sets, evaluators (`llm_judge`,
> `kappa`, `exact_match`, `contains`), bootstrap CIs, Welch's test, instruction
> search — and `llm_client` observability. QC already integrates `prompt_eval`
> (see CLAUDE.md "prompt_eval Integration"). Do not reimplement scoring,
> statistics, or experiment tracking.

---

## 1. What it must measure

Each dimension maps to a SOTA claim and (where relevant) an invariant. The bar is **"≥ the relevant baseline / human ceiling, with a confidence interval that excludes the baseline."** A claim is licensed only for dimensions that pass that bar.

| # | Dimension | What it answers | Invariant | SOTA bar (target) |
|---|-----------|-----------------|-----------|-------------------|
| D1 | **Evidentiary grounding** | Do quotes resolve to the exact source span? | INV-1 | ≥0.95 exact-span resolution; ~0 unresolvable. (Machine advantage via hard enforcement.) |
| D2 | **Coverage** | Did every textual unit get a coding decision (incl. null)? | INV-8 | 1.0 over the segment universe. Humans rarely code exhaustively → categorical edge. |
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

- **D1 grounding:** `% quotes whose normalized text resolves to a unique anchored span (doc_id + char offsets + hash)`; count of unresolvable / multiply-resolvable / hallucinated quotes. Depends on INV-1 anchoring landing first.
- **D2 coverage:** `|units with an explicit decision| / |segment universe|`, including explicit "examined, not relevant" nulls. Depends on INV-8.
- **D3 application validity:** against adjudicated gold on the **same units** — Cohen's κ (2 raters) / **Krippendorff's α** (handles multi-label, missing, boundary disagreement), precision/recall/F1 on code labels, and **span alignment via IoU + Modified Hausdorff Distance** (the LLMCode metrics). The unit-of-analysis fix the IRR caveat (theory doc §11) demands.
- **D4 codebook quality:** `llm_judge` rubric (clarity / specificity / usefulness / grounding, 0–1 each) **plus** a blind human expert panel; report both and their agreement.
- **D5 reliability:** existing `project irr` / `project stability`, but reported with **bootstrap CIs** and prevalence, and labeled *codebook-discovery* vs *application-level* agreement (the latter requires INV-8).
- **D6 bias:** (i) stratified error rate by respondent attribute where ethical; (ii) **counterfactual masking/swap** — hold substantive text constant, vary identity markers, measure code-change rate (target ≈0).
- **D7 disconfirmation:** recall/precision of system negative cases against a human-built gold set of disconfirming passages.
- **D8 GT fidelity:** expert rubric on constant comparison, category property/dimension development, memo quality, saturation justification.
- **D9 interpretive depth:** forced-choice blind preference (expert picks the better of system vs human code/theme for latent-meaning items); report win rate with CI; parity = CI spans 0.5.
- **D10 cost/latency:** from `llm_client` observability DB (real per-call cost/tokens/latency — never estimated).

## 3. Gold standards and datasets

**The human ceiling (target band).** Published inter-coder agreement: **κ ≈ 0.72–0.82 for inductive coding schemes, 0.58–0.73 for unconstrained schemes.** "Expert parity" (D3) = agreement-with-gold in/above that band; "SOTA" = ≥ the human–human agreement measured on the *same* corpus (compute it; don't assume).

**Reuse released gold (fast, head-to-head, but contamination-flagged):**
- **LLMCode** (github.com/PerttuHamalainen/LLMCode) — human-annotated data + tooling that compares LLM to human codes with IoU / Modified Hausdorff. Closest ready-made evaluator; reuse its metrics and data.
- **HICode** (github.com/mianzg/HICode) — 3 datasets with human-constructed themes; reported **P=0.72 / R=0.74** — a concrete head-to-head target for hierarchical coding.
- **LOGOS** (arXiv:2509.24294) — 5 corpora + a 5-dimensional metric and an expert-developed schema (≈80.4% alignment reported) for GT-style evaluation.
- *Caveat:* public datasets may be in model training data → **train/test contamination**. Flag it; do not base the *headline* SOTA claim on possibly-contaminated public sets.

**Build a small in-house adjudicated gold set (for headline claims):** follow the expert-consensus-panel method — ≥2 qualified coders independently code, a third adjudicates disagreements, producing gold codes with labels, definitions, supporting anchored spans, and a recorded human–human agreement (the ceiling). Target the actual product domain (interviews/focus groups). Keep it held-out and prompt-frozen.

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
- **QC surface:** a `make bench` target + a `qc bench` CLI/MCP path that runs a frozen suite against a dataset and writes a scored report. Agent-drivable end to end (no manual steps).
- **Outputs:** a versioned `benchmark_results/` with per-dimension scores, CIs, baseline deltas, dataset + prompt + model hashes, and a generated scorecard. These hashes are the artifact evidence the theory doc's claim discipline requires before any public SOTA statement.

## 7. Acceptance criteria (the SOTA gate)

A public claim of the form "more X than existing methods" is licensed **only** when, for dimension X, the harness shows the system ≥ the named baseline/human ceiling on a held-out, prompt-frozen, contamination-checked dataset, with a CI excluding the baseline — recorded with hashes. Until then, claim discipline (theory doc §14) applies: describe capability, not superiority.

## 8. Phasing (smallest real slice first)

- **Phase 0 — plumbing + cheap metrics (no new human coding).** Wire QC into `prompt_eval`; compute D1 (grounding, once INV-1 lands — until then report the *resolution-failure rate* of current substring matching as the baseline to beat), D5 (reliability/stability with CIs), D10 (cost), on existing transcripts + reused public gold. Goal: real numbers and the harness skeleton in days, not the full study.
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
