# An Auditable Architecture for LLM-Assisted Qualitative Coding

**Design, Limits, and Evaluation Roadmap**

*Version 1.2 — 2026-06-19*

> **Revision note (v1.2).** A reviewer graded v1.1 a credible architecture paper
> but a premature *methods* paper: it still reached for the word "rigor" while
> reporting no methodological results. v1.2 fixes the genre rather than faking the
> evidence. It (a) retitles the document as an **architecture + evaluation-roadmap**
> paper; (b) replaces "rigor" with "rigor *scaffold*" wherever results are absent;
> (c) adds a full cross-tool feature matrix (§2); (d) states the methodological
> family the system actually fits (§3.1); (e) demotes negative-case analysis to an
> *experimental feature*, not credibility evidence (§6); (f) describes
> schema enforcement accurately by provider tier (§4); (g) turns the ethics section
> into a control matrix (§8); and (h) completes and verifies the references. No
> empirical results are claimed; the evaluation in §7 is explicitly a plan.
> **What this paper is:** a description of a working system's architecture and an
> honest ledger of what is proven (the software runs and fails safely), what is
> merely *measured* (computational consistency, not validity), and what remains
> (methodological evaluation, span-anchored grounding, hardened disconfirmation, GT
> fidelity). **What it is not:** a validated qualitative-methods paper.

---

## Abstract

Qualitative coding — the systematic interpretation of unstructured text such as interview transcripts into a structured, defensible set of themes — is labor-intensive, expertise-bound, and historically resistant to automation. Most shipping AI-assisted qualitative data analysis (QDA) products treat large language models (LLMs) as an *assistive feature* beside a manual workflow, while a fast-growing body of research prototypes (AcademiaOS, LOGOS, MindCoder, TAMA, Auto-TA, HICode) automates thematic-analysis or grounded-theory workflows as research artifacts. This paper describes a system positioned deliberately between those poles: a **methodology-aware pipeline with the LLM as its engine and the human as reviewer and director**, engineered for *auditability* — structured output contracts, fail-loud inter-stage dependencies, human-in-the-loop review with provenance, consistency/stability reporting, an (experimental) disconfirmation search, multi-format QDA export, and end-to-end observability.

The contribution is an **integration and auditability claim, not a novelty-of-automation claim.** To our knowledge no *widely adopted QDA platform* (defined in §2) combines thematic-analysis (TA) and grounded-theory-*inspired* (GT-inspired) LLM pipelines with typed state, schema-constrained generation, fail-loud orchestration, human-review provenance, agreement/stability metrics, disconfirmation search, observability, and QDPX export in one inspectable system. We are explicit that what the system provides today is a **rigor *scaffold*** — the machinery rigor requires — not demonstrated rigor, which is an empirical outcome we have not yet measured. We describe the architecture as built, state honestly which methodological tradition it fits (codebook/post-positivist analysis, not reflexive TA or constructivist GT), lay out the evaluation that would establish validity, and enumerate the limits — systematic LLM bias, non-determinism, the pseudo-replication risk in treating LLM passes as raters, brittle quote attribution, and partial GT fidelity.

---

## 1. Introduction

Qualitative research converts human language into knowledge. The central craft is *coding*: reading data closely, attaching short interpretive labels to spans of text, organizing those labels into a hierarchy or theory, and grounding every claim in verbatim evidence. Done well, coding is slow and demands trained judgment.

LLMs are well-suited to the *recognition* half of this task. But three things stand between "an LLM can suggest codes" and "an LLM can do publishable qualitative analysis": **methodology** (real methods are multi-stage processes, not single prompts), **rigor** (reviewers expect agreement evidence, audit trails, disconfirmation, and saturation; LLM output is non-deterministic and can be *systematically* biased), and **trust engineering** (a research instrument must fail loudly, log provenance, and let a human intervene).

This system addresses the *engineering* preconditions of all three — and this paper is careful to claim only that. Building the scaffold that rigor needs is not the same as demonstrating rigor; we mark the boundary throughout. §2 positions the work against commercial tools, open-source QDA, and the LLM research prototypes. §3–4 describe the design principles and architecture. §5 describes the encoded methodologies and which qualitative tradition they fit. §6 describes the rigor *scaffold* and its limits. §7 separates the software validation we have done from the methodological evaluation we have not. §8 gives an ethics control matrix. §9–10 give limitations and roadmap.

---

## 2. Related Work and Positioning

The honest comparison is granular and feature-by-feature, not a single "we are first" assertion. We define a **"widely adopted QDA platform"** as a tool with substantial institutional research use, a commercial or mature open-source distribution, and documented adoption in published qualitative studies — operationally, the four commercial suites below plus QualCoder. The LLM research prototypes are *not* yet widely adopted in that sense; they are the closest *methodological* comparators and we treat them as the primary related work.

**Feature matrix.** Cells reflect public documentation and papers as of mid-2026; tools change frequently. ✓ = supported, ~ = partial/assistive, ✗ = not a focus, ? = not determinable from public sources. "Methodology pipeline" means an *ordered, inspectable execution of a named method*, not the mere presence of AI coding.

| System | Type | AI coding | Methodology pipeline | Schema-constrained output | Human-review provenance | Span-anchored grounding | Disconfirmation search | Agreement / stability | QDPX export | Published empirical eval |
|---|---|---|---|---|---|---|---|---|---|---|
| ATLAS.ti | Commercial | ✓ | ~ | ? | ~ | ✓ | ✗ | ✓ (ICR) | ✓ | ✗ |
| MAXQDA | Commercial | ✓ | ✗ | ? | ~ | ✓ | ✗ | ✓ (ICR) | ✓ | ✗ |
| NVivo | Commercial | ~ | ✗ | ? | ~ | ✓ | ✗ | ✓ (ICR) | ✓ | ✗ |
| Dedoose | Commercial | ~ | ✗ | ✗ | ~ | ✓ | ✗ | ✓ | ~ | ✗ |
| QualCoder | OSS desktop | ~ | ✗ | ✗ | ~ | ✓ | ✗ | ✓ (κ) | ✓ | ✗ |
| AcademiaOS | Research prototype | ✓ | ✓ (GT) | ~ | ✗ | ? | ✗ | ✗ | ✗ | ✓ (user study) |
| LOGOS | Research prototype | ✓ | ✓ (GT) | ✓ (schema induction) | ✗ | ? | ✗ | ~ (5-dim metric) | ✗ | ✓ (5 corpora) |
| MindCoder | Research prototype | ✓ | ✓ (inductive) | ~ | ✓ (interaction logs) | ? | ✗ | ✗ | ✗ | ✓ |
| TAMA | Research prototype | ✓ | ✓ (TA) | ~ | ✓ | ? | ✗ | ✓ | ✗ | ✓ (clinical) |
| Auto-TA | Research prototype | ✓ | ✓ (TA) | ~ | ✗ (automated) | ? | ✗ | ~ | ✗ | ✓ |
| HICode | Research prototype | ✓ | ✓ (hierarchical) | ~ | ✗ | ? | ✗ | ✓ (human-theme alignment) | ✗ | ✓ (3 datasets) |
| **This system** | OSS tool | ✓ | ✓ (TA + GT-inspired) | ✓ | ✓ | ✗ (roadmap) | ~ (experimental) | ✓ | ✓ | ✗ (planned) |

Two honest readings of this matrix are essential and were missing from earlier drafts:

1. **Established QDA tools beat this system on span-anchored grounding and published adoption.** ATLAS.ti, MAXQDA, NVivo, Dedoose, and QualCoder anchor coded segments to exact source offsets; this system currently does not (§5.1). That is a real deficit, not a footnote.
2. **The research prototypes beat this system on published empirical evaluation.** AcademiaOS reports a user study; LOGOS reports ~80% alignment with an expert schema across five corpora; HICode validates against human-constructed themes; TAMA/Auto-TA report multi-agent TA results. This system reports *none* yet (§7).

The defensible contribution is therefore the **specific integration**: the only column-combination this system holds that the others do not is *{schema-constrained typed output + human-review provenance + agreement/stability + QDPX export + observability + a named TA *and* GT-inspired pipeline}* in one auditable open-source tool. It does **not** lead on grounding or on evidence. Commercial AI-coding is real (ATLAS.ti's Intentional AI Coding chunks text, queries a model repeatedly, and recombines results; MAXQDA's AI Assist offers single/multi-document coding, code/subcode suggestions, chat, summaries, translation), so the claim is about *methodological orchestration and auditability*, never about whether AI coding exists. A 2026 scoping review documents how crowded and fast-moving this space is.

---

## 3. Design Principles

Five principles govern every component.

- **LLM-first, schema-constrained.** Every semantic step returns a Pydantic model with a description on every field. **Scope of this claim:** schema constraint is the largest lever on output *regularity, parseability, and failure detection* — it guarantees a `confidence` field exists, a `quote` field is a string, a `code_name` is present. It does **not** establish that the quote appears in the transcript, that the code is analytically useful, that a category is more than a banal paraphrase, or that a confidence score is calibrated. Those are interpretive-validity questions structure cannot answer; they are the job of grounding checks, human review, and evaluation (§6–7).
- **Fail loud, never silently degrade.** Inter-stage dependencies are explicit (`ctx.require(...)` raises, naming the missing field and the needing stage). No `except: pass` fallbacks. On failure the engine logs full state context and re-raises. This is the most genuinely valuable property of the design: silent degradation is the dominant failure mode of LLM pipelines, and this architecture forecloses it.
- **Single portable state, with a path to stronger auditability.** All state lives in one `ProjectState` JSON model — good for local reproducibility and portability, *insufficient* as a complete audit substrate for large or collaborative projects. An append-only event log, export content hashes, and optional DB backing are roadmap (§10).
- **Human-in-the-loop by design.** A `ReviewManager` supports approve/reject/modify/merge/split over CLI and a browser UI; every code carries provenance (LLM vs. human).
- **Maximum observability.** Every LLM call logs model, schema, prompt length, tokens, latency, and cost; every stage logs entry context. Cost and failure profiles are queryable, not estimated.

These are enforced by the codebase and by a deterministic test suite (527 tests) plus live end-to-end tests.

### 3.1 Which qualitative tradition this fits

Treating qualitative analysis as a pipeline is an *engineering model*, not a neutral methodological stance, and different traditions hold incompatible assumptions about researcher subjectivity and what counts as a theme. The system's emphasis on agreement metrics, structured outputs, and codebook stability aligns most naturally with **codebook / post-positivist qualitative analysis** (e.g., codebook thematic analysis, framework analysis). It is **not** a good fit for **reflexive thematic analysis** (Braun & Clarke), which treats coder subjectivity as a resource rather than noise and rejects inter-coder agreement as a quality criterion, nor for **constructivist grounded theory** (Charmaz), which foregrounds the researcher's interpretive standpoint. We state this explicitly so the tool is not misapplied to traditions whose epistemology it contradicts.

---

## 4. System Architecture

The system is a **stage-based pipeline over a single typed state object**: `Ingest → [methodology-specific stages] → Negative Case → Cross-Interview`.

- **`AnalysisPipeline`** orchestrates ordered `PipelineStage`s over `ProjectState`.
- **`PipelineContext`** (`extra="forbid"`) threads model, budget, trace id, review flags, and optional per-stage prompt overrides; a bad config key fails at construction.
- **`create_pipeline(methodology)`** assembles the stage sequence.
- **`LLMHandler`** is a thin adapter over the shared `llm_client` library (retry/backoff, batching, model routing across any LiteLLM-supported provider incl. local Ollama/vLLM, observability).
- **Schemas/adapters.** LLM-output schemas define what the model returns; the domain model defines what is stored; `adapters.py` is the single tested seam between them.

**Provider-dependent schema enforcement (accurate statement).** "Schema-constrained" does *not* mean decode-time constraint everywhere. `llm_client` uses three tiers: (1) GPT-5-class models route through the provider's **Responses API** with native structured output (constrained generation); (2) models with native JSON-schema `response_format` support use it (provider-side structural enforcement at decode time); (3) all others — including many local models — fall back to **instructor**, which is **post-hoc**: it parses, validates against the Pydantic model, and re-asks on failure. Additionally `litellm.enable_json_schema_validation` performs post-generation validation. So the guarantee is "structural validity is enforced — by constrained decoding where the provider supports it, otherwise by validate-and-retry." Value-level constraints (ranges, non-empty, patterns) are never enforced at decode time by any provider and are handled by field descriptions plus post-generation validation.

**A design lesson:** mocked unit tests do not catch integration bugs. Hundreds of passing unit tests once hid two defects in the *seams* between stages; only end-to-end runs surfaced them, and `ctx.require()` then localized each immediately. The suite now pairs deterministic tests (including schema-omission regression tests) with live end-to-end runs.

---

## 5. Encoding Methodology

Two methodologies are implemented as distinct pipelines. We label the grounded-theory pipeline **GT-*inspired*** deliberately: it performs the *visible procedural steps* of GT (open/constant-comparison → axial → selective → integration) — **procedural mimicry** — but does not yet instantiate GT's core epistemic logic — **methodological fidelity**. Specifically, it lacks *theoretical sampling* (collecting new data to elaborate weak categories), *category-level saturation* (properties/dimensions ceasing to change), *analytic memoing* that builds conceptual relations (current memos lean toward summary logging), full *axial decomposition* (causal vs. context vs. intervening conditions), and *reflexivity* (explicit accounting for the researcher's standpoint). GT is an iterative epistemic process; this system approximates parts of it.

### 5.1 Thematic / Default Analysis (7 stages)
`Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Negative Case → Cross-Interview`. Ingest parses `.txt/.docx/.pdf/.rtf` and segments by speaker.

**Quote attribution is currently substring matching** — better than blind duplication but brittle to OCR artifacts, smart vs. straight quotes, transcript cleanup, partial quotations, and phrases repeated across interviews. This is a **first-order weakness, not a minor gap**: it undermines confirmability (tracing claims to data), disconfirmation evidence, QDPX export integrity (whether exported segments map to true source spans), and auditability by human reviewers. Until span-anchored attribution lands (doc + speaker + char/turn offsets + quote hash, with every generated quote required to resolve to an anchored span; §10), the system is honestly a *prototype with audit aspirations* on the grounding dimension, not a finished research instrument.

### 5.2 Grounded-Theory-Inspired Pipeline (7 stages)
`Ingest → Constant Comparison Coding → Axial Coding → Selective Coding → Theory Integration → Negative Case → Cross-Interview`. Constant Comparison codes each segment against an evolving codebook with a saturation check per pass (incident-to-code comparison; incident-to-incident and category-to-category are partial). Supporting capabilities: **incremental re-coding** (`project recode`) and **codebook-level saturation detection** — neither yet implements theoretical sampling or per-category saturation.

---

## 6. The Rigor *Scaffold* (and its limits)

This section describes the machinery rigor requires. We call it a **scaffold** advisedly: scaffolding is architecture, rigor is an empirical outcome (§7), and the two must not be conflated.

**Lincoln & Guba (1985) trustworthiness — mapped, with limits:**

- *Dependability — memos and audit trail.* Every stage emits an analytical memo; every code carries per-code reasoning; provenance flags distinguish LLM from human. (Gap: summary logging vs. true analytic memoing.)
- *Confirmability — provenance.* Quote-to-code attribution links claims to data — subject to the §5.1 brittleness, which currently limits this.
- *Credibility — disconfirmation search is an **experimental feature**, not credibility evidence.* The system asks a model to find evidence contradicting the codes it just produced. Because the *same model and prompt lineage* searches its own output, this risks **confirmation laundering** — appearing to challenge itself while staying inside its own assumptions. We therefore do **not** count current negative-case search as credibility support. It is reported as experimental. The version that *would* support credibility (roadmap, §10) requires: retrieval-first search over the corpus; a *different* model or adversarial prompt family; mandatory anchored quote-span evidence; human adjudication before synthesis; and explicit "no negative case found" handling distinguishing *absence of evidence* from *failure to search*.

**Consistency measurement (not "inter-rater reliability").** Running coding multiple times with prompt variation, or across a model panel, and computing percent agreement, Cohen's kappa, and Fleiss' kappa, measures **LLM-pass agreement** — *computational consistency*, not human inter-rater reliability and not validity:

- **Pseudo-replication.** Repeated runs of one model, or multiple frontier models trained on overlapping corpora under similar prompts, are *not* independent raters; panels reduce but do not remove shared-dependency risk. We report "computational raters with shared-dependency risk."
- **Kappa fragility.** Kappa is fragile under unitization (which span is the unit), multi-label overlap, rare codes, and lexically-different-but-semantically-similar codes. We plan to report raw agreement, confidence intervals, and prevalence effects alongside kappa, add **Krippendorff's alpha**, and treat Landis & Koch bands as a heuristic.
- **`project stability`** runs identical coding N times to quantify the model's own non-determinism (per-code stable/moderate/unstable) — a genuine and useful consistency measure, still not validity.

**Reporting/interoperability.** Memos, audit trails, agreement results, and stability scores export to Markdown, CSV, JSON, and **QDPX** (ATLAS.ti/NVivo). A planned "methods appendix" export will map run metadata to **COREQ** (32 items) and **SRQR** (21 items): data source, model and version, prompt, parameters, human review, audit trail, analytic decisions, saturation evidence, limitations.

**Prompt quality as an experiment.** Coding prompts are overridable per stage; the system integrates with a prompt-evaluation library so prompt/model choices can be compared on frozen case sets with an LLM-judge rubric and statistical comparison rather than spot-checked.

---

## 7. Software Validation Done; Methodological Evaluation Planned

**Software / integration validation (done).** The pipeline runs end-to-end against real transcripts, with automated end-to-end tests for default, GT, incremental, graph, and export flows. These establish that the *software* behaves: stages compose, schemas validate, failures are caught and localized, exports are valid, single- and multi-document corpora work. This is integration testing, and we name it as such. It taught the lessons baked into the system: LLMs omit fields (so every LLM-facing collection field defaults to empty, locked by regression tests); output is non-deterministic (so software assertions are loose-but-meaningful); fail-loud checks localize seam bugs.

**Methodological evaluation (planned, not executed — no results are claimed below).** Software working is not analysis being correct. The following is the bar we hold ourselves to before claiming methodological validity:

| Evaluation target | Required evidence |
|---|---|
| Code grounding | % of generated quotes resolving exactly to anchored transcript spans; count of unresolvable/hallucinated quotes |
| Code quality | Blind expert ratings: clarity, specificity, usefulness, grounding |
| Codebook coverage | Human comparison across multiple datasets |
| Stability | N repeated runs with confidence intervals |
| Bias | Error stratification by respondent attributes where ethically available |
| Disconfirmation | Recall/precision vs. human-identified disconfirming evidence |
| GT fidelity | Expert review of constant comparison, category development, memo quality, saturation claims |
| Baselines | Generic ChatGPT prompting; ATLAS.ti/MAXQDA where feasible; LLMCode, HICode, TAMA/Auto-TA, LOGOS/AcademiaOS by task |
| Interoperability | QDPX import success into ATLAS.ti/NVivo |

A 2026 blinded mixed-methods comparison (PLOS Digital Health) found LLMs performed comparably to humans for *applying predefined deductive codes* (low hallucination) but were more variable for *inductive* theme generation (tone, nuance, conversational context). That directly shapes the plan: expect parity on deductive application; be most skeptical of inductive generation.

---

## 8. Ethics and Security — Control Matrix

Qualitative transcripts frequently contain protected, confidential, or re-identifiable data, so security and ethics are first-order. The current posture suits a single-researcher local tool and is **not** a multi-tenant deployment; the table states, per risk, the current control, the missing control, how it should be tested, and deployment status.

| Risk | Current control | Missing control | Test method | Status |
|---|---|---|---|---|
| Transcript egress to hosted model | Local-model routing (Ollama/vLLM) supported | Enforced "local-only" mode; egress audit | Network egress test under local-mode | Partial |
| Provider data retention | Documented model choice | Per-provider retention policy surfaced in run metadata | Config/metadata review | Missing |
| PII in prompts | — | De-identification/pseudonymization pre-call | Re-identification test on outputs | Missing |
| Prompt injection *from transcripts* | — | Treat transcript as untrusted input; injection-resistant prompting; output bounds | Red-team transcripts with injected instructions | Missing |
| Arbitrary file write (MCP export) | `_confine_export_path` sandbox to exports dir | — | Traversal-payload tests (present) | Done |
| Stored XSS in web UI | `markupsafe.escape` on all dynamic values | — | XSS payload tests | Done |
| Unauthenticated local API/MCP | Loopback binding | AuthN/AuthZ for any non-loopback use | Bind-address + auth test | Partial |
| Accidental raw-data export / cross-project leakage | Per-project store | Export scoping + content hashes | Export audit | Partial |
| Sensitive text in logs | — | Log redaction policy | Log inspection | Missing |
| Right-to-delete | File deletion | Cascade across state, exports, logs, observability DB | Deletion-completeness test | Missing |

We will publish a full threat model before describing the system as a "trusted research instrument" in any external venue. Until then the honest label is **"auditable local research tool with a known, bounded security posture."**

---

## 9. Limitations

- **LLM bias may be systematic, not random** (Ashwin, Chhabra & Rao, 2025): errors can correlate with respondent characteristics and mislead inference. Agreement/stability detect *inconsistency*, never a *consistent* shared bias.
- **Reliability ≠ validity; consistency ≠ truth.**
- **Pseudo-replication** in treating LLM passes/models as raters (§6).
- **GT fidelity is partial** — hence "GT-inspired," and "procedural mimicry," not "full GT" (§5).
- **Quote attribution is brittle** until span anchoring lands (§5.1) — the highest-priority technical gap.
- **Disconfirmation is experimental**, not credibility evidence (§6).
- **Auditability is partial** until an append-only log and export hashes exist.
- **Methodological validity is unmeasured** (§7).
- **Non-determinism is inherent**; we measure and report it.

---

## 10. Roadmap (Beyond Current Prototypes)

Each item is a stage or layer over the existing typed state, observability, and consistency metrics — none requires abandoning the foundation.

1. **Span-anchored grounding** — stable span ids with a hard requirement that every generated quote resolve to an anchored span (precondition for the §7 grounding metric and for trustworthy disconfirmation).
2. **Hardened, retrieval-first disconfirmation** — different model/adversarial prompt, mandatory spans, human adjudication (defeats confirmation laundering).
3. **Multi-model consensus** — merge codebooks across providers; report agreement; diversify the *source* of bias.
4. **True theoretical sampling** — identify under-developed categories and recommend data to develop them.
5. **Per-category saturation** — property/dimension tracking.
6. **Active learning from review** — treat approve/reject/modify/merge/split as a signal refining project prompting.
7. **Append-only audit log + export hashes (+ optional DB)** — a defensible audit substrate.
8. **Collaborative coding** — multiple reviewers with conflict resolution.
9. **Retrieval grounding** — corpus semantic search (the capability QualCoder has and this system lacks).
10. **Methodological evaluation** — execute the §7 plan; report real numbers.

---

## 11. Conclusion

Most shipping QDA products bolt AI onto a manual workflow; a wave of research prototypes automates parts of TA and GT but as artifacts rather than integrated tools. This system's contribution is an **auditable integration** — TA and GT-inspired pipelines, schema-constrained typed output, fail-loud orchestration, human-review provenance, consistency/stability reporting, multi-format export including QDPX, and observability, assembled into one inspectable open-source tool.

We deliberately do **not** claim to be beyond the state of the art, first to automate, or to have demonstrated methodological rigor. The credible claim is narrower: an *auditable, methodology-aware engineering integration* that supplies the **scaffold** rigor requires, with an explicit ledger of what is proven (the software runs and fails safely), what is merely measured (computational consistency, not validity), and what remains (span-anchored grounding, hardened disconfirmation, GT fidelity, a published threat model, and — above all — the methodological evaluation in §7). On two dimensions it currently *lags* its comparators: established QDA tools beat it on span-anchored grounding, and the research prototypes beat it on published evaluation. The wager of the design is that the future of qualitative analysis is neither pure-human (slow, inconsistently documented) nor pure-LLM (fast but unfalsifiable), but a disciplined collaboration in which programmatic code guarantees coverage, the LLM supplies semantic judgment, and the human supplies direction and final authority — *once the evidence in §7 is in hand*.

---

## References

**Qualitative methodology and reporting standards**
- Strauss, A., & Corbin, J. (2008). *Basics of Qualitative Research* (3rd ed.). Sage.
- Charmaz, K. (2014). *Constructing Grounded Theory* (2nd ed.). Sage.
- Braun, V., & Clarke, V. (2021). *Thematic Analysis: A Practical Guide*. Sage. (Reflexive TA.)
- Lincoln, Y. S., & Guba, E. G. (1985). *Naturalistic Inquiry*. Sage.
- Tong, A., Sainsbury, P., & Craig, J. (2007). Consolidated criteria for reporting qualitative research (COREQ). *Int. J. Qual. Health Care*, 19(6), 349–357.
- O'Brien, B. C., et al. (2014). Standards for Reporting Qualitative Research (SRQR). *Academic Medicine*, 89(9), 1245–1251.

**Reliability and agreement**
- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educ. Psychol. Meas.*, 20(1).
- Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. *Psychol. Bull.*, 76(5).
- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1).
- Krippendorff, K. (2004). *Content Analysis* (2nd ed.). Sage.
- O'Connor, C., & Joffe, H. (2020). Intercoder reliability in qualitative research: debates and practical guidelines. *Int. J. Qual. Methods*, 19.

**LLMs in qualitative analysis — bias, evaluation, prototypes** *(verified June 2026)*
- Ashwin, J., Chhabra, A., & Rao, V. (2025). Using large language models for qualitative analysis can introduce serious bias. *Sociological Methods & Research*. doi:10.1177/00491241251338246 (preprint arXiv:2309.17147).
- Hill, C., Dahil, A., Simpson, G., Hardisty, D., Keast, J., Pinn, C. K., et al. (2026). Large language models for thematic analysis in healthcare research: a blinded mixed-methods comparison with human analysts. *PLOS Digital Health*. doi:10.1371/journal.pdig.0001189.
- (2026). The use and methodological reporting of large language models in qualitative research: a scoping review. *BMC Medical Research Methodology*. doi:10.1186/s12874-026-02913-1.
- Übellacker, T. (2024). AcademiaOS: automating grounded theory development in qualitative research with large language models. arXiv:2403.08844.
- Pi, X., Yang, Q., & Nguyen, C. (2025). LOGOS: LLM-driven end-to-end grounded theory development and schema induction for qualitative research. arXiv:2509.24294.
- Gao, J., Shu, Z., Yeo, S. Y., Prakash, A., Huang, C.-M., Dredze, M., & Xiao, Z. (2025). Efficiency with rigor! A trustworthy LLM-powered workflow for qualitative data analysis (system: MindCoder). arXiv:2501.00775.
- Xu, H., Yi, S., Lim, T., et al. (2025). TAMA: a human–AI collaborative thematic analysis framework using multi-agent LLMs for clinical interviews. arXiv:2503.20666.
- Yi, S., Nguyen, J., Xu, H., Lim, T., Well, A., Markey, M., & Ding, Y. (2025). Auto-TA: towards scalable automated thematic analysis via multi-agent LLMs with reinforcement learning. arXiv:2506.23998.
- Zhong, M., Wang, P., & Field, A. (2025). HICode: hierarchical inductive coding with LLMs. *Proc. EMNLP 2025* (arXiv:2509.17946).
