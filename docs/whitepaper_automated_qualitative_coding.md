# Methodology-Aware Automated Qualitative Coding with Large Language Models

**A white paper on the architecture, rigor, and roadmap of an LLM-native qualitative data analysis system**

*Version 1.1 — 2026-06-19*

> **Revision note (v1.1).** This revision narrows the novelty claim, makes the
> related-work comparison granular rather than rhetorical, relabels what we
> previously called "inter-rater reliability" and "validation" to claims the
> evidence actually supports, and adds an ethics/threat-model section and an
> explicit (not-yet-executed) evaluation plan. The architecture description is
> unchanged; the framing is corrected. Where this paper describes capabilities
> as *implemented*, they are in the codebase and exercised by tests; where it
> describes them as *planned*, they are roadmap.

---

## Abstract

Qualitative coding — the systematic interpretation of unstructured text such as interview transcripts into a structured, defensible set of themes — is labor-intensive, expertise-bound, and historically resistant to automation. Most shipping AI-assisted qualitative data analysis (QDA) products treat large language models (LLMs) as an *assistive feature* beside a manual workflow, while a fast-growing body of research prototypes (e.g., AcademiaOS, LOGOS, MindCoder, TAMA, Auto-TA, HICode) automate thematic-analysis or grounded-theory-style workflows but typically as research artifacts rather than auditable, integrated tools. This paper describes a system positioned deliberately between those poles: a **methodology-aware pipeline with the LLM as its engine and the human as reviewer and director**, engineered for *auditability* — structured output contracts enforced at decode time, fail-loud inter-stage dependencies, human-in-the-loop review with provenance, agreement/stability reporting, automated disconfirmation search, multi-format QDA export, and end-to-end observability.

Our contribution is not a claim to be alone in this space. It is an **integration claim**: to our knowledge no widely adopted QDA platform combines thematic-analysis (TA) and grounded-theory-*inspired* (GT-inspired) LLM pipelines with typed state, schema-constrained generation, fail-loud orchestration, human-review provenance, agreement/stability metrics, negative-case search, observability, and QDPX export in one inspectable system. We describe the system as built, separate software validation (done) from methodological validation (planned), state the limitations honestly — systematic LLM bias, non-determinism, the pseudo-replication risk in treating LLM passes as raters, and partial GT fidelity — and lay out the research agenda that would carry it beyond current prototypes.

---

## 1. Introduction

Qualitative research converts human language — what people said in an interview, a focus group, an open-ended survey — into knowledge. The central craft is *coding*: reading the data closely, attaching short interpretive labels ("codes") to spans of text, organizing those codes into a hierarchy or theory, and grounding every claim in verbatim evidence. Done well, coding is slow and demands trained judgment.

LLMs are unusually well-suited to the *recognition* half of this task. They read context, abstract latent meaning, and propose labels at a speed no human can match. But three things stand between "an LLM can suggest codes" and "an LLM can do publishable qualitative analysis":

1. **Methodology.** Real qualitative methods are *processes*, not single acts. Grounded theory (GT) requires constant comparison, axial coding, selective coding, theoretical integration, *theoretical sampling*, and *saturation* judged at the category level. Thematic analysis requires hierarchy, cross-case synthesis, and disconfirmation. A one-shot "find the themes" prompt is not thematic analysis; it is autocoding.
2. **Rigor.** Reviewers expect agreement evidence, audit trails, negative case analysis, and saturation evidence. LLM output is non-deterministic and can be *systematically* biased (not merely noisy). Without explicit machinery for consistency measurement and disconfirmation, an automated codebook is an unfalsifiable artifact.
3. **Trust engineering.** A research instrument must fail loudly, log its provenance, and let a human intervene. A pipeline that silently emits plausible-but-wrong codes is worse than no pipeline, because its errors are camouflaged by fluency.

This system was built to address all three at once, and — importantly — to be *honest about which of them it has solved and which it has only scaffolded*. The remainder of this paper describes the design principles (§3), the architecture (§4), how methodology is encoded (§5), how the rigor scaffolding is built (§6), what software validation shows and what methodological evaluation remains (§7), ethics and the threat model (§8), the honest limitations (§9), and the agenda beyond current prototypes (§10).

---

## 2. Background and Related Work

The relevant landscape has three layers, and the honest comparison is granular, dimension-by-dimension, not a single "we are first" assertion.

**Commercial QDA products with AI features.** ATLAS.ti, NVivo, MAXQDA, and Dedoose dominate institutional qualitative research. Their AI capabilities are real and improving: ATLAS.ti offers AI Coding using OpenAI models and an "Intentional AI Coding" mode that chunks text, queries a model repeatedly, and algorithmically combines results; MAXQDA's AI Assist supports single/multi-document coding, code and subcode suggestions, chat-with-data, summaries, and translations. These are genuine AI-coding features. What they generally are *not* is an *ordered, inspectable execution of a named methodology* with typed inter-stage contracts, agreement/stability reporting, and automated disconfirmation as first-class pipeline stages. The fair claim is about *methodological orchestration and auditability*, not about whether AI coding exists.

**Mature open-source QDA.** QualCoder is a full desktop QDA application with hierarchical coding, memos, Cohen's-kappa coder comparison, graphs, FAISS-based semantic search, and GPT-style AI exploration. It is manual-first with AI assistance — strong on human-coder reliability and corpus search (the semantic-search capability this system does *not* yet have), but not a methodology pipeline.

**LLM research prototypes (the most important comparison).** A rapidly growing literature automates exactly the territory this system occupies, and any honest novelty claim must engage it:

| System | Method focus | What it does | Closest overlap with this system |
|---|---|---|---|
| **AcademiaOS** (2024) | Grounded theory | Codes raw data, develops themes/dimensions into a grounded model; reports a user study; open source | GT-style automation end-to-end |
| **LOGOS** (2025) | Grounded theory | End-to-end LLM framework: coding, semantic clustering, graph reasoning, iterative refinement into a hierarchical theory | GT pipeline + structured theory output |
| **MindCoder** (2025) | Inductive coding | Preprocessing, automatic open coding, automatic axial coding, concept development (codes-to-theory) | Open/axial automation |
| **TAMA** (2025) | Thematic analysis | Human-in-the-loop multi-agent TA for clinical interviews with expert-guided refinement | TA + human review |
| **Auto-TA** (2025) | Thematic analysis | Fully automated multi-agent TA pipeline, optional RLHF | End-to-end TA automation |
| **HICode** (2025) | Hierarchical coding | Hierarchical inductive coding with LLMs | Hierarchical codebook generation |

Given these, the defensible positioning is **not** "no one does this." It is:

> To our knowledge, no *widely adopted QDA platform* integrates TA- and GT-inspired LLM pipelines with typed state, schema-constrained generation, fail-loud orchestration, human-review provenance, agreement/stability metrics, negative-case search, observability, and QDPX export in a single auditable system. The research prototypes above each automate part of this territory; this system's distinct emphasis is *engineering auditability and methodological scaffolding integrated into one inspectable tool with QDA-format interoperability*.

A 2026 scoping review of LLMs in qualitative research catalogs use across coding, theme development, summarization, drafting, and GT workflows (open/axial/selective coding, saturation testing), and stresses that LLM-based studies must report model version, configuration, prompting, human–AI interaction, and outcomes attributable to the LLM — a reporting bar this system is designed to meet (§6, §7).

---

## 3. Design Principles

Five principles govern every component.

- **LLM-first, schema-constrained.** Every semantic step returns *structured* output: a Pydantic model with a description on every field, enforced at decode time via JSON-schema response formatting. The schema *is* the generation contract. **Important scoping of this claim:** schema enforcement is the largest lever on output *regularity, parseability, and failure detection* — it guarantees a `confidence` field exists, a `quote` field is a string, a `code_name` is present. It does **not** by itself establish that the quote appears in the transcript, that the code is analytically useful, or that a confidence score is calibrated. Those are interpretive-validity questions that structure alone cannot answer; they are the job of grounding checks, human review, and evaluation (§6, §7).

- **Fail loud, never silently degrade.** Inter-stage dependencies are explicit. A downstream stage that needs upstream data calls `ctx.require(...)`, which raises immediately — naming the missing field and the needing stage — if the data is absent. There are no `except: pass` fallbacks. On failure the engine records full state context (document, code, application counts) and re-raises. This is the most genuinely valuable property of the design: silent degradation is the dominant failure mode of LLM pipelines, and this architecture forecloses it.

- **Single portable state, with a path to stronger auditability.** All analysis state lives in one `ProjectState` Pydantic model, saved/loaded as JSON — elegant for local reproducibility and as a portable interchange artifact. We are explicit that a single mutable JSON file is *not* a complete audit substrate for larger or collaborative projects: an append-only event log, content hashes on exports, and optional database-backed storage are roadmap items (§10). The JSON snapshot remains the portable artifact; the event log would become the immutable record.

- **Human-in-the-loop by design.** The pipeline can pause at review checkpoints. A `ReviewManager` supports approve, reject, modify, merge, and split over both a CLI and a self-contained browser UI. Every code carries provenance (LLM-discovered vs. human-modified). This approve/reject/modify/merge/split set is, we argue, the right abstraction for qualitative review.

- **Maximum observability.** Every LLM call logs model, schema, prompt length, token usage, latency, and cost through the shared `llm_client` library; every stage logs its entry context. The cost and failure profile of any run is queryable, not estimated.

These are enforced by the codebase and by a deterministic test suite (527 tests at the time of writing) plus live end-to-end tests against a real model.

---

## 4. System Architecture

The system is a **stage-based pipeline over a single typed state object**.

```
Ingest → [methodology-specific coding stages] → Negative Case → Cross-Interview
```

- **`AnalysisPipeline`** orchestrates an ordered list of `PipelineStage`s, each implementing one `run(state, ctx)` step over `ProjectState`.
- **`PipelineContext`** is a typed (`extra="forbid"`) config threaded through every stage: model, budget, trace id, review flags, optional per-stage prompt overrides. A typo in a config key fails at construction, not three stages later.
- **`create_pipeline(methodology)`** assembles the correct stage sequence.
- **`LLMHandler`** is a thin adapter over the shared `llm_client` library (retry/backoff, structured extraction, batching, model routing across any LiteLLM-supported provider including local Ollama/vLLM, observability). QC supplies configuration, the system prompt, and error wrapping; it does not reimplement LLM plumbing.
- **Schemas and adapters.** LLM-output schemas define what the model returns; the unified domain model defines what the system stores; `adapters.py` is the single, tested seam converting one to the other — letting the generation schema be tuned for decode-time constraint while the storage model stays stable.

Surfaces include a CLI, a FastAPI server, an MCP server exposing the system as agent-callable tools, a browser review UI, and interactive Cytoscape.js graph views.

A design lesson stated plainly: **mocked unit tests do not catch integration bugs.** Hundreds of passing unit tests once hid two real defects in the *seams* between stages; only end-to-end runs surfaced them, and the fail-loud `require()` pattern then localized each immediately. The current suite pairs deterministic tests (including schema-omission regression tests) with live end-to-end validation.

---

## 5. Encoding Methodology

The system implements two methodologies as distinct pipelines. We label the grounded-theory pipeline **GT-*inspired*** deliberately: it executes the visible procedural steps of GT but does not yet preserve the full methodological logic of theory generation (theoretical sampling, category-level saturation, full axial paradigm). See §9 for exactly what is missing.

### 5.1 Thematic / Default Analysis (7 stages)

`Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Negative Case Analysis → Cross-Interview Analysis`

- **Ingest** parses `.txt/.docx/.pdf/.rtf`, segments by speaker (handling `Name:` and `Name 0:03` timestamp formats), and attributes quotes to a source document. *Attribution is currently substring matching* — better than blind duplication, but brittle to OCR artifacts, smart vs. straight quotes, transcript cleanup, partial quotations, and phrases repeated across interviews. Span-anchored attribution (document id + speaker id + character/turn offsets + quote hash, with every generated quote required to resolve to an anchored span) is a roadmap item (§10) and is necessary for the grounding guarantees §6 relies on.
- **Thematic Coding** discovers a hierarchical codebook — codes with definitions, semantic criteria, illustrative quotes, mention counts, full-range confidence.
- **Perspective Analysis** maps participants to emphasized codes, distinguishing single-speaker introspection from multi-speaker consensus/divergence.
- **Relationship Mapping** extracts entities and typed relationships (powering the graph views).
- **Synthesis** produces an executive summary, cross-cutting patterns, prioritized recommendations.
- **Negative Case Analysis** searches for *disconfirming* evidence (see §6, including its current limits).
- **Cross-Interview Analysis** runs automatically for multi-document corpora, surfacing consensus and divergent themes.

### 5.2 Grounded-Theory-Inspired Pipeline (7 stages)

`Ingest → Constant Comparison Coding → Axial Coding → Selective Coding → Theory Integration → Negative Case Analysis → Cross-Interview Analysis`

- **Constant Comparison Coding** replaces batch open coding with an iterative mechanism: the document is segmented (by speaker turn or paragraph), each segment is coded *against an evolving codebook*, with a saturation check after each pass. This implements incident-to-code comparison; *incident-to-incident and category-to-category comparison are partial*.
- **Axial Coding** identifies relationships between categories, partially following the Strauss & Corbin paradigm (conditions, consequences) — not the full decomposition (causal vs. context vs. intervening conditions).
- **Selective Coding** identifies the core category.
- **Theory Integration** assembles a model: framework, propositions, conceptual relationships, scope conditions, implications.

Two supporting capabilities: **incremental re-coding** (`project recode` codes only newly added documents against the existing codebook, then re-runs downstream stages) and **codebook-level saturation detection** (comparing codebooks across iterations). Both move toward GT's iterative ideal; neither yet implements *theoretical sampling* (collecting new data specifically to elaborate weak categories) or *per-category property/dimension saturation*.

---

## 6. The Rigor Scaffolding (and its limits)

The defining design decision is that trustworthiness machinery is *part of the pipeline*. We map to canonical criteria — while being explicit that scaffolding is not proof.

**Lincoln & Guba (1985) trustworthiness:**

- *Credibility — Negative Case Analysis.* After coding, the model is asked to find evidence that contradicts the codes it just produced and to record structured negative-case memos. **This is currently a first-pass mechanism with a known weakness:** the same model and prompt lineage searching its own output for disconfirming evidence risks *confirmation laundering* — appearing to challenge itself while remaining inside the same assumptions. A stronger design (roadmap, §10) requires: retrieval-first search over the corpus rather than model memory; a *different* model or adversarial prompt family for disconfirmation; mandatory quote-span evidence for every negative case; human review of disconfirming evidence before synthesis; and explicit "no negative case found" handling that distinguishes *absence of evidence* from *failure to search*.
- *Dependability — memos and audit trail.* Every stage produces an analytical memo (reasoning, uncertainties, emerging patterns); every code carries per-code reasoning. We note the gap between *logging summaries* and the GT ideal of *analytic memoing that develops conceptual relations* — the current memos lean toward the former.
- *Confirmability — provenance.* Quote-to-code attribution with source/speaker links interpretive claims to data, and provenance flags distinguish LLM from human decisions — subject to the attribution-brittleness caveat in §5.1.

**Consistency measurement (not "inter-rater reliability"):**

We have relabeled what the system computes. Running coding multiple times with prompt variation, or across a panel of models, and computing percent agreement, Cohen's kappa, and Fleiss' kappa, measures **LLM-pass agreement** — *computational consistency*, not inter-rater reliability in the human sense and not validity. The reasons matter:

- **Pseudo-replication risk.** Repeated runs of one model, or even multiple frontier models trained on overlapping corpora and steered by similar prompts, are *not* independent raters. Multi-model panels reduce but do not remove this shared-dependency risk. We report these as "computational raters with shared-dependency risk," never as independent human coders.
- **Kappa fragility.** Kappa is fragile for qualitative coding because of unitization (which span is the unit), multi-label overlap, rare codes, and semantically similar but lexically different codes. We therefore plan to report raw agreement, confidence intervals, and prevalence effects alongside kappa, to add **Krippendorff's alpha** (which handles more coding situations, including boundary and multi-label disagreement), and to interpret Landis & Koch bands as a heuristic, not a verdict.
- **`project stability`** runs identical coding N times to quantify the model's *own* non-determinism, with per-code stability scores (stable/moderate/unstable) — separating "the method disagrees" from "the model is noisy." This is a genuine and useful distinction; it remains a consistency measure, not a validity measure.

**Reporting and interoperability.** Memos, audit trails, agreement results, and stability scores export to Markdown, CSV, JSON, and **QDPX** (so results drop into ATLAS.ti/NVivo). A planned "methods appendix" export will map run metadata directly to **COREQ** (32-item) and **SRQR** (21-item) reporting standards: data source, model and version, prompt, parameters, human review, audit trail, analytic decisions, saturation evidence, and limitations.

**Prompt quality as an experiment.** Coding prompts are overridable per stage (`prompt_overrides`), and the system integrates with a prompt-evaluation library so prompt/model choices can be compared on frozen case sets using an LLM-judge rubric (clarity, grounding, coverage, analytical depth) with statistical comparison — rather than spot-checked by eye.

---

## 7. Software Validation Done; Methodological Evaluation Planned

We separate two claims the previous draft conflated.

**Software / integration validation (done).** The pipeline runs end-to-end against real transcripts, with automated end-to-end tests covering the default, GT, incremental, graph, and export flows. These establish that the *software* behaves: stages compose, schemas validate, failures are caught and localized by `ctx.require`, exports produce valid output, and the system handles single- and multi-document corpora. Representative runs produce a coherent hierarchical codebook with speaker detection and memos (thematic), cross-interview consensus/divergence (multi-doc), and open codes → axial relationships → core category → theoretical model (GT). This is integration testing, and we now name it as such. It also taught the engineering lessons baked into the system: LLMs do not reliably populate every schema field (so every LLM-facing collection field defaults to empty, locked by regression tests); output is non-deterministic (so software assertions are loose-but-meaningful); fail-loud checks turn integration bugs into immediate, localized errors.

**Methodological evaluation (planned, not yet executed).** Software working is not the analysis being *correct*. The evaluation below is the bar we hold ourselves to before claiming methodological validity; none of it is reported here as a result.

| Evaluation target | Required evidence |
|---|---|
| Code grounding | % of generated quotes that resolve exactly to anchored transcript spans |
| Code quality | Blind expert ratings: clarity, specificity, usefulness, grounding |
| Codebook coverage | Human comparison across multiple datasets |
| Stability | N repeated runs with confidence intervals |
| Bias | Error stratification by respondent attributes where ethically available |
| Negative cases | Recall/precision vs. human-identified disconfirming evidence |
| GT fidelity | Expert review of constant comparison, category development, memo quality, saturation claims |
| Baselines | Generic ChatGPT prompting; ATLAS.ti/MAXQDA where feasible; LLMCode, HICode, TAMA/Auto-TA, LOGOS/AcademiaOS by task |

A recent blinded mixed-methods comparison found LLMs performed comparably to humans for *applying predefined deductive codes* but were more variable for *inductive* theme generation (tone, nuance, conversational context). That result directly shapes the plan above: deductive application is where we expect to match humans; inductive generation is where evaluation must be most skeptical.

---

## 8. Ethics and Threat Model

Qualitative transcripts frequently contain protected, confidential, or re-identifiable data, so security and ethics are first-order, not deployment afterthoughts. The current operational posture (local API and MCP surfaces loopback-bound and unauthenticated; export and web surfaces hardened against arbitrary writes and stored XSS) is appropriate for a single-researcher local tool and is **not** a multi-tenant production deployment. A research deployment must additionally address:

- **Data residency and provider retention** — where transcripts go when sent to a hosted model, and what the provider retains. Local models (Ollama/vLLM) are supported precisely so sensitive corpora need never leave the machine.
- **De-identification before LLM calls** — stripping or pseudonymizing PII prior to any external call.
- **Consent** for AI-assisted analysis of participant data.
- **Prompt injection from transcripts** — transcripts are *untrusted input* fed to an LLM; a transcript can contain text crafted to manipulate the model. This is an under-appreciated attack surface unique to this domain and must be tested.
- **Accidental raw-data export and cross-project leakage** — exports must be scoped and, ideally, checksummed.
- **Audit logs containing sensitive text**, MCP tool misuse, and localhost exposure via browsers/notebooks/tunnels.
- **Right-to-delete** handling across state, exports, and logs.

We commit to publishing an explicit threat model (likely harms and attack paths) before describing the system as a "trusted research instrument" in any external venue. Until then, the honest label is "auditable local research tool with a known, bounded security posture."

---

## 9. Limitations

- **LLM bias may be systematic, not random.** LLM coding errors can be biased with respect to respondent characteristics, which can mislead inference (Ashwin, Chhabra & Rao, 2025). Agreement and stability metrics detect *inconsistency*; neither detects a *consistent* bias shared across passes and models. Human review and (hardened) negative-case analysis are mitigations, not proofs.
- **Reliability ≠ validity.** High LLM-pass agreement means the method is *consistent*, not *correct*.
- **Pseudo-replication.** Treating LLM passes/models as independent raters overstates statistical independence; multi-model panels reduce but do not eliminate it (§6).
- **GT fidelity is partial.** Theoretical sampling, category-level saturation, full axial decomposition, and analytic (vs. summary) memoing are not yet implemented — hence "GT-inspired," not "full GT."
- **Quote attribution is brittle** (substring matching; §5.1) until span anchoring lands.
- **Auditability is partial** until an append-only event log and export hashes exist (§3, §10).
- **Non-determinism is inherent**; we measure and report it rather than hide it.

---

## 10. Beyond Current Prototypes

The architecture was designed so the next capabilities are *extensions*, not rewrites.

1. **Span-anchored grounding.** Stable span identifiers (doc/speaker/offsets/hash) with a hard requirement that every generated quote resolve to an anchored span — the precondition for the grounding metric in §7 and for trustworthy negative-case evidence.
2. **Hardened, retrieval-first negative-case search** using a *different* model/adversarial prompt family, mandatory quote spans, and human review before synthesis — to defeat confirmation laundering (§6).
3. **Multi-model consensus** that merges codebooks across providers and reports agreement with the existing statistics — diversifying the *source* of bias to attack the systematic-bias threat, while honestly reporting shared-dependency risk.
4. **True theoretical sampling** — a stage that identifies under-developed categories and recommends what kind of data would develop them, closing the GT loop.
5. **Per-category saturation** — property/dimension tracking, so the system can say "the core category is saturated but category X needs three more cases."
6. **Active learning from review** — treat approve/reject/modify/merge/split decisions as a signal that refines project prompting over time.
7. **Append-only audit log + export hashes (+ optional DB backend)** — turning "single JSON" into a defensible audit substrate for larger and collaborative projects.
8. **Collaborative coding** — multiple human reviewers with explicit conflict resolution and its own reliability accounting.
9. **Retrieval grounding** — semantic search across the corpus (the capability QualCoder has and this system lacks) to ground code application and reduce hallucinated quotes.

Each is a stage or layer over the existing typed state, observability, and consistency metrics — none requires abandoning the methodology-aware, schema-constrained, fail-loud foundation.

---

## 11. Conclusion

Most shipping QDA products bolt AI onto a manual workflow; a wave of research prototypes automates parts of TA and GT but as artifacts rather than auditable tools. This system's contribution is an *integration*: full TA and GT-inspired pipelines, structured output enforced at decode time, fail-loud inter-stage contracts, native consistency/stability reporting, automated (first-pass) negative-case search, per-stage memos and per-code provenance, multi-format export including QDPX, and end-to-end observability — assembled into one instrument whose outputs a reviewer can interrogate.

We deliberately do **not** claim to be beyond the state of the art in broad terms; that claim is falsifiable by a single literature search and would not survive review. The credible claim is narrower and, we believe, more durable: an *auditable, methodology-aware engineering integration* that improves on fragmented prototypes and assistive products by combining orchestration, structured output, provenance, review, consistency measurement, and interoperable export — with an honest ledger of what is proven (the software runs and fails safely), what is measured (consistency, not validity), and what remains (methodological evaluation, GT fidelity, span-anchored grounding, hardened disconfirmation, and a published threat model). The wager of this design is that the future of qualitative analysis is neither pure-human (too slow, inconsistently documented) nor pure-LLM (fast but unfalsifiable), but a disciplined collaboration in which programmatic code guarantees coverage, the LLM supplies semantic judgment, and the human supplies direction and final authority.

---

## References

*Note: the LLM-prototype citations below were supplied during review and should be version-/venue-verified before formal publication.*

**Qualitative methodology and reporting standards**
- Strauss, A., & Corbin, J. (2008). *Basics of Qualitative Research* (3rd ed.). Sage.
- Charmaz, K. (2014). *Constructing Grounded Theory* (2nd ed.). Sage.
- Lincoln, Y. S., & Guba, E. G. (1985). *Naturalistic Inquiry*. Sage.
- Tong, A., Sainsbury, P., & Craig, J. (2007). Consolidated criteria for reporting qualitative research (COREQ). *Int. J. Qual. Health Care*, 19(6).
- O'Brien, B. C., et al. (2014). Standards for Reporting Qualitative Research (SRQR). *Academic Medicine*, 89(9).

**Reliability and agreement**
- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educ. Psychol. Meas.*, 20(1).
- Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. *Psychol. Bull.*, 76(5).
- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1).
- Krippendorff, K. (2004). *Content Analysis* (2nd ed.). Sage. (α ≥ 0.80 reliable; ≥ 0.67 tentative.)
- O'Connor, C., & Joffe, H. (2020). Intercoder reliability in qualitative research: debates and practical guidelines. *Int. J. Qual. Methods*, 19.

**LLMs in qualitative analysis — bias, evaluation, and prototypes**
- Ashwin, J., Chhabra, A., & Rao, V. (2025). Using large language models for qualitative analysis can introduce serious bias. *Sociological Methods & Research* (online first).
- (2026). The use and methodological reporting of large language models in qualitative research: a scoping review. *BMC Medical Research Methodology*.
- (n.d.). Large language models for thematic analysis in healthcare research: a blinded mixed-methods comparison with human analysts. *PLOS Digital Health*.
- AcademiaOS (2024): Automating grounded theory development with LLMs. arXiv:2403.08844.
- LOGOS (2025): LLM-driven end-to-end grounded theory development and schema induction. arXiv:2509.24294.
- MindCoder (2025): Using an LLM to support flexible and structural inductive qualitative analysis. arXiv:2501.00775.
- TAMA (2025): A human–AI collaborative thematic analysis framework using multi-agent LLMs for clinical interviews. arXiv:2503.20666.
- Auto-TA (2025): Towards scalable automated thematic analysis via multi-agent LLMs with RL. arXiv:2506.23998.
- HICode (2025): Hierarchical inductive coding with LLMs. EMNLP 2025.
