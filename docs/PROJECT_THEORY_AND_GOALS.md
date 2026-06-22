# Qualitative Coding System — Theory, Goals, and Honest State

**A detailed orientation and theory reference for coding agents working on this project.**

*Version 3.2 — 2026-06-21*

> **Since v3.0:** INV-1 span anchoring landed (mostly met); INV-8 segment universe
> + coverage built, with **exhaustive per-segment coding** (`--exhaustive`) closing
> INV-8 in that mode; structured-output fix (out-of-range confidence now clamps,
> not crashes); INV-9 first-class claim ledger object layer landed; INV-6/INV-10
> first slices now route disconfirmation/review over claim IDs; corpus scope can
> be recorded and surfaced in Markdown/JSON/CSV exports; INV-7 prompt-injection fixture
> outcomes can be scored when externally supplied. Statuses below reflect this.

> **Purpose & audience.** This is the single canonical statement of *why this
> project exists, the theory it implements, the conceptual model it operates on,
> and the honest state of what is built*. It is written for the coding agents
> (and humans) who work on this repository, not for external publication. It
> complements `CLAUDE.md` (operational: commands, file map, model notes) and
> `AGENTS.md` (its generated mirror). When the two disagree about *current
> capability*, trust the code and `CLAUDE.md`; this document is for *intent,
> theory, the conceptual model, and the proven-vs-planned ledger*.
>
> **How to use it.** If you are about to *describe* the system (commit, memo,
> report, user text), read §12 (state ledger), §13 (invariants), and §14 (claim
> discipline) first — they exist to stop overclaiming. If you are about to
> *change* the analysis, read §5 (state model) and §6–7 (methodology + stage
> reference) so you know the contracts you are touching. §8 is a worked example
> that makes the abstractions concrete.

---

## Ambition (where this is going — read this to set priorities)

**The end product is public, and the target is genuinely state-of-the-art.** Not "an LLM that codes" — every tool has that now and it is not a moat. The moat is being **the qualitative coding system that can *prove*, on shared benchmarks, that it is more exhaustive, better grounded, more auditable, and more rigorously disconfirmed than anything else — while matching expert humans on interpretive validity.**

Honest shape of the SOTA claim (this is the bar we build toward, and the framing we will defend):

- **Target SOTA on the structural rigor dimensions** — coverage/exhaustiveness (INV-8), evidentiary grounding (INV-1), auditability/reproducibility (INV-9 + audit log), disconfirmation rigor (INV-2/6), reliability, scale, and cost. The defensible claim is about the **integrated bundle**, not any single dimension: several research prototypes already do parts well (HICode reports human-evaluated P/R on hierarchical coding; LOGOS a 5-dim GT metric; LLMCode IoU/Hausdorff alignment; Auto-TA end-to-end TA). What no widely-adopted tool *or* prototype combines is *all* of {exhaustive coverage + span-anchored grounding + first-class claim ledger + auditable provenance + systematic disconfirmation + QDA-format interop} in one system — and that combined claim must still be earned per dimension on a shared benchmark, not asserted. (**Landscape note, 2026-06:** the commercial field is moving — MAXQDA 26.2 (Mar 2026) shipped segment-level AI coding with an accept/decline workflow and validation against manual coding. So individual dimensions like segment-level coverage are *not* differentiating on their own; the defensible claim is the integrated, *scored* bundle, and it decays if not re-checked against the field. Re-audit competitors before any public claim.)
- **Expert-parity on interpretive validity**, augmented by human-in-the-loop — *not* "beats humans at interpretation." Current evidence (PLOS blinded study; LLMCode; Ashwin et al.) is that LLMs match humans on deductive code application but are weaker/variable on latent inductive meaning. Closing that is a research frontier; near-term we target parity and measure it.
- **Prove it on shared benchmarks.** "Better" is only credible with a ground truth to measure against. We do **not** claim to be "the only system that can prove it" — HICode/LOGOS/LLMCode publish evaluation machinery too. We claim to make evaluation *first-class for this exact integrated bundle*. The **evaluation harness (INV-3) is the keystone**: simultaneously the *proof* of each per-dimension claim and the *feedback loop* that improves the system. You cannot beat SOTA you cannot measure.

Deliberately **not** the framing: "better in *every* measurement." That sets a trap — one dimension where we tie-or-lose (deep latent interpretation) sinks an absolute claim. "SOTA on measurable rigor, expert-parity on interpretation, and the only system that can prove it on shared benchmarks" is *stronger because it survives scrutiny*, and it is still a claim no competitor can make.

**Implication for this document:** the invariants in §13.1 are a **committed build spec toward that product**, not an idealized measuring stick we shrug at. UNMET invariants are work items with a destination, ranked in §18. The evaluation harness comes first because it converts ambition into evidence — see `docs/EVALUATION_HARNESS.md`.

---

## Part I — Orientation

## 1. What this project is, in one paragraph

LLM-powered qualitative coding of interview transcripts. It treats the LLM as the **engine of a methodology-aware pipeline** — not a chat sidebar bolted onto manual coding — with the human as reviewer and director. It runs two methodologies (thematic analysis and a grounded-theory-inspired pipeline) as ordered, inspectable stages over a single typed state object (`ProjectState`), produces structured output validated against Pydantic schemas, keeps a human-in-the-loop review loop, measures its own coding consistency, and exports to the standard QDA interchange format (QDPX). The bet: good qualitative analysis is neither pure-human (slow, inconsistently documented) nor pure-LLM (fast but unfalsifiable), but a disciplined collaboration — **programmatic code orchestrates and verifies structure, the LLM supplies semantic judgment, the human supplies direction and final authority.** (Earlier drafts said "code guarantees coverage." That is too strong and is methodology-dependent: the GT constant-comparison path codes each *segment*, but the thematic path is holistic codebook discovery whose `code_applications` come from LLM-surfaced *example quotes*, not an exhaustive pass over every segment — so neither analytic coverage *nor even* segment-level processing coverage is guaranteed there. See INV-8.)

*This paragraph states intent and design, not demonstrated maturity. "Measures its own consistency" is not "is correct." See §12 (proven vs. measured vs. planned) and §13 (architectural invariants) before describing the system as methodologically validated.*

## 2. Why it exists (the gap it targets)

Three things separate "an LLM can suggest codes" from "an LLM can do defensible qualitative analysis," and the project is organized around all three:

1. **Methodology is a process, not a prompt.** Grounded theory is constant comparison → axial → selective → integration, with theoretical sampling and saturation. Thematic analysis is hierarchy + cross-case synthesis + disconfirmation. A one-shot "find the themes" call is autocoding, not method. We encode the *stages*.
2. **Rigor needs machinery.** Reviewers of qualitative work expect agreement evidence, audit trails, disconfirmation, and saturation. LLM output is non-deterministic and can be *systematically* biased. So we build the consistency/stability/provenance/memo machinery — the **scaffold** rigor requires. Building the scaffold is not the same as having *demonstrated* rigor (§12).
3. **Trust must be engineered.** A research instrument must fail loudly, log provenance, and let a human intervene — otherwise fluent-but-wrong output is camouflaged. This is the fail-loud, observability, and review design.

## 3. Domain glossary (read this if you are not a QDA expert)

The system implements real qualitative-data-analysis (QDA) concepts. An agent changing the analysis must use these terms precisely.

- **Code** — a short interpretive label attached to a span of text (e.g. `TRUST_IN_AUTOMATION`). Has a name, definition, and supporting evidence. Codes can be hierarchical (a code can have a `parent_id`).
- **Codebook** — the organized set of codes for a project, with a version.
- **Code application** — one instance of a code attached to a specific quote in a specific document (code ↔ quote ↔ source). This is the *evidence link*.
- **Memo** — analytic writing produced during analysis (reasoning, uncertainties, patterns). In real QDA, memoing is how theory is built; here memos are produced per stage.
- **Provenance** — who created/changed a thing: LLM, human, or system. Every code and application carries it.
- **Thematic analysis (TA)** — identifying patterns ("themes") across data; can be codebook-based (stable, comparable codes — what this system fits) or reflexive (coder subjectivity as a resource — which this system does *not* fit; §6).
- **Grounded theory (GT)** — building a theory *from* the data through iterative coding and constant comparison. Key sub-processes: **open/initial coding**, **constant comparison** (compare new data to existing codes/categories), **axial coding** (relate categories), **selective coding** (choose a core category), **theoretical sampling** (collect new data to develop weak categories), **saturation** (a category's properties/dimensions stop changing).
- **Negative case analysis (disconfirmation)** — actively searching for evidence that contradicts the emerging codes/claims; a credibility check.
- **Inter-rater reliability (IRR)** — agreement between independent coders on a coding scheme (here: between LLM passes — see the strong caveat in §11/§15).
- **Saturation** — *methodological* saturation (no new category properties emerging) vs. *codebook stability* (the code list stops changing). These are **different**; do not conflate them (INV-4).

---

## Part II — The system's model of the world

## 4. The single state object

All analysis state lives in one Pydantic model, `ProjectState` (`qc_clean/schemas/domain.py`), saved/loaded as JSON by `ProjectStore`. There is no database. Every stage reads from and writes to this object via a typed `PipelineContext`. Understanding `ProjectState` *is* understanding the system.

## 5. The state model (conceptual backbone)

`ProjectState` fields and what they mean:

- **`config: ProjectConfig`** — methodology, coding approach, model, etc.
- **`corpus: Corpus`** — `documents: List[Document]`. Each `Document` has `id`, `name`, `content`, `detected_speakers`, `is_truncated`, `metadata`.
- **`corpus_scope: Optional[CorpusScope]`** — explicit report boundary for corpus-level claims: phenomenon, population, sampling frame, inclusion/exclusion criteria, and notes. CLI/API read/update surfaces are available, CLI/MCP project creation can set scope at creation time, and Phase 0 reports deterministic scope-record adequacy status and field completeness. This constrains phrasing and export context; CSV/Markdown claim rows also carry compact claim-scope and corpus-boundary context. It does **not** validate that the sample supports population generalization.
- **`codebook: Codebook`** — `version`, `methodology`, `created_by`, and `codes: List[Code]`. A **`Code`** has `id`, `name`, `description`, `definition`, `parent_id` (hierarchy), `level`, `properties`, `dimensions`, `provenance`, `version`, `example_quotes`, `mention_count`, `confidence`, `reasoning` (why this code was created — the per-code audit trail).
- **`code_applications: List[CodeApplication]`** — the evidence links. A **`CodeApplication`** has `code_id`, `doc_id`, `quote_text`, `speaker`, `start_char`, `end_char`, `confidence`, `applied_by`, `codebook_version`. **Note for INV-1:** the anchor fields (`doc_id`, `speaker`, `start_char`, `end_char`) already exist in the schema; the unmet invariant is that `start_char`/`end_char` are not reliably populated (attribution is substring-derived), so the anchors cannot yet be trusted to identify the exact source instance.
- **`segments: List[Segment]`** — the **segment universe** (INV-8): every document split into char-anchored units (`doc_id`, `index`, `start_char`/`end_char`, `speaker`, `text`, `decision`), populated by ingest. `decision ∈ {coded, no_code, None}` is set by exhaustive coding (None = not examined). The denominator for coverage and for application-level segment-decision agreement; positive segment × code agreement uses these same stable segment keys.
- **`code_relationships: List[CodeRelationship]`** — typed relations between codes (axial output): `relationship_type`, `strength`, `evidence`, `conditions`, `consequences`.
- **`entities` / `entity_relationships`** — entity map (relationship stage): people, orgs, concepts, tools and their typed relations, with `supporting_evidence`.
- **`perspective_analysis: Optional[PerspectiveAnalysis]`** — per-participant viewpoints, consensus/divergent themes, `perspective_mapping` (participant → emphasized codes).
- **`synthesis: Optional[Synthesis]`** — `executive_summary`, `key_findings`, `cross_cutting_patterns`, `recommendations`, `confidence_assessment`.
- **`core_categories` / `theoretical_model`** — GT selective + integration outputs.
- **`irr_result` / `stability_result`** — reliability outputs (§11).
- **`memos: List[AnalysisMemo]`** — every stage's analytic memo. `memo_type ∈ {theoretical, methodological, pattern, cross_case, coding, negative_case, ...}`, with `code_refs`, `doc_refs`, `created_by`. The `cross_case` memo is the cross-interview claim set (now ingested by negative-case analysis; INV-6).
- **`claims: List[AnalyticClaim]`** — first-class assertion ledger (INV-9). Each claim records kind, source stage, text, scope (`claim_ids`/`doc_ids`/`code_ids`/segment/application/entity/relationship refs), supporting and contrary anchors, support status, adjudication status, and revision history. The current ledger is generated deterministically from validated domain objects, and Phase 0 reports structural claim-anchor coverage; many higher-order claims still need explicit source anchors and human adjudication.
- **`review_decisions: List[HumanReviewDecision]`** — the human audit trail (action, target, rationale, new value).
- **`phase_results`, `current_phase`, `pipeline_status`** — execution bookkeeping; each `AnalysisPhaseResult` records status, timing, input/output summaries, error message.
- **`iteration`, `codebook_history`** — support incremental re-coding and saturation comparison across iterations.
- **`data_warnings`** — surfaced non-fatal issues.

**Why one typed object:** reproducibility (the whole analytic record is one inspectable file), and fail-loud composition (a stage that needs `codebook` calls `ctx.require("codebook", ...)` and raises if it is absent). The cost: it is *inspectable*, not tamper-evidently *auditable* (INV — append-only log/hashes are roadmap).

---

## Part III — Methodology and stages

## 6. The methodology model (theory the code implements)

Two pipelines, each a fixed ordered sequence of stages over `ProjectState`. **Disconfirmation runs last in both** and now retrieves bounded source-candidate passages for claim-ledger targets before adversarially framed LLM interpretation. Default retrieval is BM25-style lexical/query-expanded; an opt-in `embedding_hybrid` mode can add embedding cosine similarity when an embedding model is explicitly configured. Retrieval remains bounded, not human-adjudicated, not held-out D7-evaluated, and without a validated default embedding/reviewer policy, so INV-2/6 are still incomplete; see §13.1.

**Thematic / default (7 stages):** Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Cross-Interview → Negative Case.

**Grounded-theory-*inspired* (7 stages):** Ingest → Constant Comparison Coding → Axial Coding → Selective Coding → Theory Integration → Cross-Interview → Negative Case.

**Why "GT-*inspired*", not "full GT" — agents must respect this.** The pipeline performs the *visible procedural steps* of GT (**procedural mimicry**) but does **not** yet instantiate GT's core epistemic logic (**methodological fidelity**). Missing: *theoretical sampling* (collecting new data to develop weak categories), *category-level saturation* (per-property/dimension, not just codebook stability), *analytic memoing* that builds conceptual relations (current memos lean toward summary logging), full *axial decomposition* (causal vs. context vs. intervening conditions), and *reflexivity*. **Do not describe the system as doing "full grounded theory."**

**Which qualitative tradition it fits.** The emphasis on agreement metrics, structured output, and codebook stability fits **codebook / post-positivist** qualitative analysis (codebook thematic analysis, framework analysis). It is a poor fit for **reflexive thematic analysis** (Braun & Clarke — coder subjectivity is a resource; rejects inter-coder agreement as a quality criterion) and **constructivist grounded theory** (Charmaz — foregrounds the researcher's standpoint), *unless* a human fully drives interpretation and the LLM is only an assistant. Don't apply the automated agreement machinery to a reflexive study and call it appropriate.

## 7. Stage reference

Each stage implements `PipelineStage` (`can_execute(state) -> bool`, `execute(state, ctx) -> state`, `name()`). LLM stages return a Pydantic schema (`analysis_schemas.py` / `gt_schemas.py`) converted to the domain model via `adapters.py`. Every stage emits a memo. Substantive output stages also update `state.claims` with first-class claim objects or an explicit no-claims ledger event (INV-9).

**Shared / thematic:**

- **Ingest** (`ingest.py`) — parses `.txt/.docx/.pdf/.rtf`, detects speakers (handles `Name:` and `Name 0:03` timestamp formats), populates `corpus.documents`. *Reads:* loaded docs. *Writes:* `corpus` (content, `detected_speakers`). *Runs:* always.
- **Thematic Coding** (`thematic_coding.py`) — LLM discovers a hierarchical codebook. *Schema:* `CodeHierarchy` (codes with id/name/description/semantic_definition/level/example_quotes/mention_count/discovery_confidence/reasoning). *Writes:* `codebook.codes`, and `code_applications` (one per `example_quote` that resolves to a **unique** span via `grounding.resolve_against_docs` — anchored with `start_char`/`end_char`/`quote_hash`; ambiguous/unresolvable quotes are dropped + warned, INV-1). *Prompt is overridable* via `ctx.prompt_overrides["thematic_coding"]`. *Runs:* always (the foundational stage). **Exhaustive mode** (`ctx.exhaustive_coding`): instead of example quotes, one batched call decides *every* `state.segments` unit (codes or `no_code`), writing applications anchored to segment spans and `Segment.decision` — closes INV-8 examined-and-judged coverage and strengthens INV-1.
- **Perspective Analysis** (`perspective.py`) — maps participants to emphasized codes; single-speaker (introspection: strongest positions / internal tensions) vs. multi-speaker (consensus / divergence) mode chosen from detected speaker count. *Schema:* `SpeakerAnalysis`. *Writes:* `perspective_analysis`. *Requires:* codebook (`ctx.require`).
- **Relationship Mapping** (`relationship.py`) — extracts entities and typed relationships (powers the graph views). *Schema:* `EntityMapping`. *Writes:* `entities`, `entity_relationships`. *Requires:* codebook.
- **Synthesis** (`synthesis.py`) — executive summary, key findings, cross-cutting patterns, prioritized recommendations. *Schema:* `AnalysisSynthesis`. *Writes:* `synthesis`. *Requires:* upstream coding/perspective.
- **Cross-Interview** (`cross_interview.py`) — **programmatic, not LLM** (`analyze_cross_interview_patterns`): shared codes, consensus themes (code present in ≥60% of interviews), divergent themes, top code co-occurrences. *Writes:* a `cross_case` memo. *Runs:* only when `corpus.num_documents > 1`. **Denominator caveat (important):** these counts are computed over `code_applications`, and in the default thematic path applications are LLM-surfaced *example quotes*, **not** all occurrences. So "consensus / prevalence / co-occurrence" here measure *salience-in-generation*, not *prevalence-in-corpus* — the denominator is "examples the LLM chose to surface," not "all coded segments." Do not report these as corpus prevalence unless the run used exhaustive segment decisions and the downstream metric explicitly uses that denominator (INV-8).
- **Negative Case** (`negative_case.py`) — retrieves bounded source-candidate passages for claim-ledger targets, then asks an adversarially framed LLM reviewer to assess whether those candidates disconfirm the codebook, cross-interview claims, or other live claims. Default retrieval is BM25-style lexical/query-expanded; opt-in `embedding_hybrid` retrieval combines that lexical score with embedding cosine similarity and fails loudly unless an embedding model is configured. `PipelineContext.disconfirmation_model_name` can route interpretation through a separate model; unset falls back to `model_name`. *Schema:* `NegativeCaseResponse` (negative_cases + optional `target_claim_id` / `candidate_id`, overall_assessment + analytical_memo). *Writes:* `negative_case` + `methodological` memos and negative-case claim objects with contrary anchors/target claim IDs where resolvable; valid `candidate_id`s attach exact candidate anchors. *Runs:* when codebook has codes. **Status: experimental** (INV-2 partial — retrieval-first, embedding-hybrid-capable, and different-model-capable, but not held-out D7-evaluated or backed by a validated embedding/reviewer policy).

**Grounded-theory-specific:**

- **Constant Comparison Coding** (`gt_constant_comparison.py`) — segments documents (speaker turn or paragraph), iteratively codes each segment against the *evolving* codebook, checks codebook-stability saturation per pass (this is codebook convergence, **not** GT category saturation; INV-4). *Schema:* `OpenCode` (per segment). *Writes:* `codebook.codes`, `code_applications`. *Prompt overridable.* Replaces the legacy batch `gt_open_coding.py`.
- **Axial Coding** (`gt_axial_coding.py`) — relates categories (partial Strauss & Corbin paradigm: conditions, consequences). *Schema:* `AxialRelationship`. *Writes:* `code_relationships`. *Requires:* codebook.
- **Selective Coding** (`gt_selective_coding.py`) — identifies the core category. *Schema:* `CoreCategory`. *Writes:* `core_categories`. *Requires:* axial output.
- **Theory Integration** (`gt_theory_integration.py`) — assembles a theoretical model (framework, propositions, conceptual relationships, scope conditions, implications). *Schema:* `TheoreticalModel`. *Writes:* `theoretical_model`. *Requires:* core categories.

**Incremental** (`incremental_coding.py`) — `project recode`: codes only *uncoded* documents against the existing codebook, merges, then re-runs downstream state-driven stages (Cross-Interview → Negative Case). `project add-docs --recode` explicitly adds documents and invokes that same recode path in one command; plain `add-docs` does not silently spend model budget. Deliberately omits stages that depend on ctx fields from a coding stage that is not re-run (Perspective/Relationship/Synthesis, Axial/Selective/Theory). **Staleness handling (INV-11, hard-invalidation first slice):** because those stages do not re-run, after a recode the stage now clears populated stale outputs (`synthesis`, `perspective_analysis`, `code_relationships`, `entities`, `entity_relationships`, `core_categories`, `theoretical_model`), removes stale phase results and stale claim-ledger rows from the invalidated source stages, and appends a `data_warnings` entry naming what was invalidated. Full higher-order auto-recompute is still future work.

## 8. Worked example (so the abstractions are testable)

A 2-document interview corpus about remote work. (Synthetic, illustrative.)

1. **Ingest** → `corpus.documents = [d1 "alex.txt", d2 "sam.txt"]`, `detected_speakers = ["Alex"]`, `["Sam"]`.
2. **Thematic Coding** produces a `Code`:
   ```
   id=AUTONOMY_VS_OVERSIGHT, level=0, confidence=0.78,
   description="Tension between wanting independence and feeling monitored",
   reasoning="Repeated across both interviews when discussing manager check-ins",
   example_quotes=["I do my best work when no one's hovering"]
   ```
   and a `CodeApplication` (now span-anchored, INV-1):
   ```
   code_id=AUTONOMY_VS_OVERSIGHT, doc_id=d1, speaker="Alex",
   quote_text="I do my best work when no one's hovering",
   start_char=14, end_char=55, quote_hash="…"   # resolved uniquely in d1.
   # If Sam had said the SAME sentence, the quote would occur twice in the corpus
   # -> AMBIGUOUS -> the application is dropped + a data_warning, never guessed.
   ```
3. **Cross-Interview** writes a `cross_case` memo: *"Consensus: both value autonomy. Divergent: Alex frames oversight as distrust; Sam frames it as support."*
4. **Negative Case** (runs last) retrieves candidate source passages for the final claim set, then asks an adversarially framed LLM reviewer to assess them: *"Sam at 12:30 says 'I actually asked for more check-ins' — partially contradicts the 'oversight = imposed' framing."* — a disconfirming case against a **cross-interview** claim (INV-6 in action). Marked experimental (INV-2): default retrieval is BM25-style lexical with deterministic query expansion, opt-in embedding-hybrid retrieval exists, no validated embedding/reviewer model policy exists yet, and absence of a found negative case is not proof none exists.

This example is the unit to test definitions against: a code, its span-anchored evidence link (INV-1), a cross-interview claim, and disconfirmation over that final claim.

---

## Part IV — How the collaboration is engineered

## 9. Design principles (operating constraints — follow these when you build)

- **LLM-first, schema-constrained.** Every semantic step returns a Pydantic model with a description on every field. Schema constraint buys *regularity, parseability, and failure detection* — **not** interpretive validity. It guarantees a `confidence` field exists; it does not guarantee the quote is real, the code is useful, or the score is calibrated. All LLM-facing list/dict fields must default to empty (LLMs omit fields); locked by `tests/test_schema_robustness.py`. *Enforcement is provider-dependent* (§10).
- **Fail loud, never silently degrade.** Inter-stage dependencies use `ctx.require(...)`, which raises naming the missing field and stage. No `except: pass`. On failure the engine logs full state context (doc/code/application counts) and re-raises. This is the most valuable property in the codebase — preserve it.
- **Single typed state** (§4–5). Good for reproducibility/portability; not yet a tamper-evident audit substrate.
- **Human-in-the-loop** (§10.1).
- **Maximum observability.** Every LLM call logs model/schema/prompt/tokens/latency/cost via `llm_client`. Query the observability DB (`~/projects/data/llm_observability.db`) for real costs; never estimate.

Before adding code, check you are not about to: hack around a root cause, add unused hypothetical branches, add silent fallbacks (should fail loud), or leave dead code. The simplest thing that works, and delete > comment.

## 10. The LLM boundary (`llm_handler.py` → `llm_client`)

`LLMHandler` is a thin adapter over the shared `llm_client` library, which owns retry/backoff, batching, model routing, observability, and structured extraction. QC supplies config, the system prompt, and `LLMError` wrapping. Required observability kwargs (`task=`, `trace_id=`, `max_budget=`) flow from `ctx.llm_call_options(stage_name)`.

**Provider-dependent schema enforcement — state it accurately.** "Schema-constrained" does *not* mean decode-time constraint everywhere. Three tiers: (1) GPT-5-class → Responses API native structured output (constrained decoding); (2) providers with native `response_format` json_schema → decode-time structural enforcement; (3) all others (incl. many local models) → **instructor** post-hoc: parse, validate, re-ask on failure. Plus `litellm.enable_json_schema_validation` for post-generation validation. So: "structural validity is enforced — by constrained decoding where supported, otherwise validate-and-retry." Value-level constraints (ranges, non-empty, patterns) are never decode-time enforced anywhere.

Default model: `gpt-5-mini` (cheap, adequate for most stages); switchable per run with `--model`, including local models (`ollama/...`, OpenAI-compatible). GPT-5 models do **not** support a temperature parameter.

### 10.1 Human review workflow

`ReviewManager` (`review.py`) implements the five operations a qualitative reviewer needs for code/codebook review, over CLI (`project review`) and a browser UI (`/review/<id>`):

- **approve** — accept a code as-is.
- **reject** — remove a code (and its applications).
- **modify** — edit name/definition/etc. (bumps the code `version`).
- **merge** — combine codes (e.g. two near-duplicates into one).
- **split** — divide an over-broad code into finer codes.

Every decision is recorded as a `HumanReviewDecision` (action, target, rationale, new value) — the human audit trail — and updates code `provenance` to `HUMAN`. `ReviewManager` also supports `target_type="claim"` for approving, rejecting/withdrawing, or revising `AnalyticClaim` objects with `ClaimRevision` history; browser-native claim review is still future work. Review raises `ValueError` on unknown target types/actions (fail loud). The pipeline can pause at review checkpoints when `enable_human_review=True`.

## 11. Reliability: IRR and stability (`irr.py`)

Two distinct measures, both **consistency, not validity** (§15):

- **Inter-rater reliability** (`project irr`) — runs coding N times with prompt variation (and optionally across multiple models) and computes **percent agreement**, **Cohen's kappa** (2 passes), **Fleiss' kappa** (2+), and **Gwet's AC1** (prevalence-robust consistency), with κ/Fleiss interpreted on the **Landis & Koch (1977)** scale. Two units of analysis:
  - *Default — codebook-discovery agreement:* a binary code × pass matrix (1 if that pass *discovered* the code). Answers "do passes surface the same codes?" — **not** whether they code the same text the same way.
  - *`--application-level` (opt-in):* runs **exhaustive** passes (per-segment decisions; INV-8) and reports two application-level consistency numbers alongside the discovery metrics. First, **positive segment × code agreement** (`IRRResult.application_*`) answers "when at least one pass applied code C to segment S, did the other passes also apply C to S?" Second, **segment-decision agreement** (`IRRResult.segment_decision_*`) compares `coded` / `no_code` / `not_examined` decisions for every segment, so shared no-code judgments are counted explicitly. Scope: thematic exhaustive; GT application-level is a follow-up. Still subject to the pseudo-replication caveat (§15, INV-3): LLM passes are not independent human raters.
- **Multi-run stability** (`project stability`) — runs identical coding N times (no prompt variation) to quantify the model's *own* non-determinism; produces per-code stability scores classified stable / moderate / unstable, plus overall stability.

The distinction is the point: IRR ≈ "does the method agree with itself under variation"; stability ≈ "is the model deterministic." Neither says the codes are *correct*.

## 12. Export and interoperability (`data_exporter.py`)

`ProjectExporter` renders `ProjectState` to:
- **JSON** — full state.
- **CSV** — codes, applications, memos (`memos.csv`), `claims.csv`, reasoning column (audit trail), stability.
- **Markdown** — human-readable report incl. audit-trail, memo, and claim-ledger sections.
- **QDPX** — the REFI-QDA interchange ZIP (`project.qde` XML + source files) for ATLAS.ti / NVivo. Filenames are sanitized against path traversal. Exported applications now carry verifiable span anchors (INV-1 mostly met); paraphrased quotes that couldn't be anchored were dropped upstream, so exported segments are trustworthy-where-present.

MCP export tools (`qc_export_json/markdown`) confine the `output_file` to a sandboxed exports directory; the CLI exporter keeps full path freedom for the trusted local user.

---

## Part V — Honest state, invariants, and discipline

## 13. Honest state ledger — proven / measured / planned

Categorize any capability before relying on or describing it.

**Proven (software works; verified by deterministic tests + live E2E):** both pipelines run end-to-end; stages compose; schemas validate; failures are caught and localized; **span-anchored grounding** (char offsets + hash + verification, ambiguous/unresolvable dropped — INV-1 mostly met); a **char-anchored segment universe** + **coverage** denominator, with **exhaustive per-segment coding** (`--exhaustive`) giving examined-and-judged coverage (INV-8 met in that mode); a **first-class claim ledger object layer** (`ProjectState.claims`, stage source/kind/scope/support/adjudication fields, CLI/API/MCP/export read surfaces — INV-9 mostly met); optional **corpus-scope contract** (`ProjectState.corpus_scope`, surfaced in Markdown exports and CSV/Markdown claim-row context, missing/incomplete-scope warnings for claim-bearing Markdown reports plus JSON/CSV warning metadata, readable/updatable through CLI/API, and arbitrary-text scope phrasing lint via `make lint-scope-phrasing`) for report boundary context; review (CLI + browser), adjudication protocol validation (`make validate-adjudication-protocol`), protocol-to-sample preflight (`make adjudication-protocol-preflight`), unlabeled adjudication sample export (`make adjudication-sample`), adjudication response shape/completeness validation (`make validate-adjudication-responses`), completed response protocol/sample preflight (`make adjudication-response-preflight`), conversion of valid completed adjudication responses into D3/D7 gold package inputs with optional import-time preflight guard inputs (`make import-adjudication-responses ... PREFLIGHT_PROTOCOL=... PREFLIGHT_SAMPLE=...`), strict Phase 0 manifest assembly for imported D3/D7 package inputs (`make write-phase0-adjudication-package`), optional CLI/MCP export-audit hash manifests, local verification, strict local publish/handoff preflight, and opt-in local hash-linked event logs (`make export-audit-manifest`, `make verify-export-audit-manifest`, `make export-publish-preflight`, `make verify-export-audit-log`, `project export --audit-manifest --verify-audit-manifest --audit-log`, MCP `audit_manifest=True`, or MCP `audit_event_log=True`), IRR/stability, incremental recode, graph views, and JSON/CSV/Markdown/QDPX export function; ruff + docs gates green. This is **software/integration validation** — "the program does what it's built to do." It is *not* evidence the analysis is correct.

**Measured (quantified, but not validity):** **grounding rate** (D1) and
**coverage** (D2 — segments with anchored evidence / total) with local Wilson
intervals and exhaustive-mode `coded_segment_rate` over examined decisions via
`verify_grounding`/`compute_coverage`/`make bench`;
**LLM-pass agreement** (`project irr` — codebook-discovery by default,
**positive segment × code application agreement plus segment-decision
agreement** with `--application-level`, including Gwet's AC1 alongside κ/Fleiss
plus prevalence tables and local row-bootstrap intervals in `make bench`) and
**stability** (`project stability`) — computational consistency, not human
inter-rater reliability and not correctness. `make bench` also has a
**gold-dependent D3 application-validity scorecard substrate** (exact
code/source-anchor TP/FP/FN, recall, precision, F1, recall/precision Wilson
intervals, local exact-key F1 bootstrap interval, local same-code/doc char-span
IoU overlap diagnostic, local discrete Modified Hausdorff distance diagnostic,
exact-key binary system-vs-gold percent agreement/κ/AC1 plus prevalence,
human-ceiling exact-metric comparison, and human-human κ/α/AC1 metadata when a
versioned package supplies it) when adjudicated application gold is supplied in
project metadata or via external `D3_GOLD=d3_gold.json`, including versioned D3
gold-set packages validated by `make validate-d3-gold` / `qc_cli.py validate-d3-gold`
with package provenance
surfaced in the scorecard, an **externally supplied D4 codebook-quality
scorecard substrate** (`CODEBOOK_QUALITY=quality.json`) that reports
clarity/specificity/usefulness/grounding rubric summaries and local bootstrap
intervals for rubric means, plus pre-evaluation D4 protocol validation via
`make validate-d4-codebook-quality-protocol PROTOCOL=protocol.json` for
held-out gates, codebook/corpus/state hashes, blinding, evaluator plans,
rubric metrics, and success criteria, plus D4 protocol/result preflight via
`make d4-codebook-quality-preflight PROTOCOL=protocol.json QUALITY=quality.json`
for result hash locks, evaluator type/count, target scopes, and
individual-code `code_id` coverage, and D4 score-time preflight guarding via
`make bench D4_PROTOCOL=protocol.json CODEBOOK_QUALITY=quality.json`, an
**externally supplied D6
counterfactual-bias scorecard substrate** (`BIAS_COUNTERFACTUAL=bias.json`)
that reports
invariant-case code-change rate with a Wilson interval, mean code-set Jaccard
distance, changed case IDs, and attribute-group summaries with code-change-rate
Wilson intervals, an **externally supplied D6 stratified-bias scorecard
substrate** (`BIAS_STRATIFIED=bias_stratified.json`) that reports
stratified correctness/error counts, accuracy/error-rate Wilson intervals,
per-attribute/per-group summaries, per-surface summaries, and per-attribute
max error-rate gaps, a **gold-dependent D7 disconfirmation scorecard substrate**
(exact target-claim/source-anchor TP/FP/FN, recall, precision, F1,
recall/precision Wilson intervals, local exact-key F1 bootstrap interval,
exact-key binary system-vs-gold percent agreement/κ/AC1 plus prevalence,
optional baseline comparisons with local paired exact-key delta bootstrap
intervals, human-ceiling exact-metric comparison, human-human κ/α/AC1 metadata
when a versioned package supplies it, and versioned-package provenance when
supplied) when adjudicated contrary-evidence gold anchors are supplied in
project metadata or via an external `GOLD=gold.json` file, an **INV-7
prompt-injection scorecard substrate** when fixture outcomes are supplied in
project metadata or via `PROMPT_INJECTION=inv7.json`, with pass/attack-rate
Wilson intervals, deterministic structural and opt-in live canary fixture
runners able to produce compatible input files, an **externally supplied D8
GT-fidelity scorecard substrate** (`GT_FIDELITY=gt_fidelity.json`) that reports
constant-comparison/category-development/memo-quality/saturation-justification
rubric summaries, evaluator-type/scope summaries, and local bootstrap intervals
for rubric means, pre-evaluation D8 GT-fidelity protocol validation via
`make validate-d8-gt-fidelity-protocol PROTOCOL=protocol.json` for
corpus/state/GT-artifact hashes, evaluator plans, rubric metrics, target
scopes, held-out gates, and success criteria, D8 protocol/result preflight via
`make d8-gt-fidelity-preflight PROTOCOL=protocol.json GT_FIDELITY=gt_fidelity.json`,
and D8 score-time preflight enforcement via `make bench D8_PROTOCOL=protocol.json`,
an **externally supplied D9 interpretive-preference scorecard
substrate** (`PREFERENCE=preference.json`) that reports forced-choice
system/human/tie counts, tie-rate Wilson intervals, non-tie system
preference-rate Wilson intervals, and evaluator/criterion summaries,
pre-evaluation D9 interpretive-preference protocol validation via
`make validate-d9-interpretive-preference-protocol PROTOCOL=protocol.json`,
protocol/result preflight via
`make d9-interpretive-preference-preflight PROTOCOL=protocol.json PREFERENCE=preference.json`,
and D9 score-time preflight enforcement via
`make bench D9_PROTOCOL=protocol.json PREFERENCE=preference.json`,
and an
**externally supplied confidence-calibration scorecard substrate**
(`CALIBRATION=calibration.json`) that reports accuracy, mean confidence, Brier
score, fixed-bin expected calibration error, Brier/ECE local bootstrap
intervals, bin summaries, and per-surface summaries, pre-evaluation
confidence-calibration protocol validation via
`make validate-confidence-calibration-protocol PROTOCOL=protocol.json` for
corpus/state/prediction-artifact hashes, label-source plan, target surfaces,
confidence source, held-out gates, outcome metrics, and success criteria,
protocol/result preflight via
`make confidence-calibration-preflight PROTOCOL=protocol.json CALIBRATION=calibration.json`
for result hash locks, label-source/evaluator metadata, target surfaces, and
planned item count, and score-time preflight enforcement via
`make bench CONFIDENCE_PROTOCOL=protocol.json CALIBRATION=calibration.json`, a
**D10 cost/latency
scorecard substrate** from real `llm_client` `llm_calls` rows plus optional
matching `tool_calls` rows when traces exist, plus last-local-run wall-clock
metadata from `project run`,
`_meta.input_hashes` provenance for loaded project/corpus/external benchmark
files, D10 timing files with runtime environment metadata inside Phase 0
artifact packages, Phase 0 input/configuration hashes with prompt hashes
explicitly marked not-run, and a
**diagnostic-only INV-4 category adequacy section** that reports
category properties/dimensions/support gaps; no populated held-out D3/D7
benchmark, populated D4 LLM-judge/blind-expert evaluation, populated D6 bias
audit, populated D8 expert GT-fidelity benchmark, populated D9 blind expert
preference benchmark, populated confidence-calibration benchmark, populated
κ/α/AC1 human-ceiling benchmark, live baseline run on held-out data,
committed/scored live adversarial prompt-injection benchmark result, public
benchmark timing evidence with controlled environment/baseline context, full D3 Krippendorff's α/semantic agreement,
or true GT saturation assessment has been run.

D4 protocol validation/preflight, D8 protocol validation/result preflight, D9
protocol validation/result preflight/score-time guard, and
confidence-calibration protocol validation/result preflight/score-time guard are
process/provenance checking only. They do not
constitute blind expert-panel evidence, LLM-judge evidence, codebook-quality
evidence, GT-fidelity evidence, blind expert-parity evidence,
interpretive-depth evidence, calibration evidence, methodological-validity
evidence, or SOTA evidence.

**D3 baseline comparison substrate:** when adjudicated D3 gold is supplied,
`make bench D3_BASELINES=d3_baselines.json` /
`scripts/bench_phase0.py --d3-baselines-file` can score externally supplied
`application_baselines` against the same exact code/source-anchor key universe
as the system and report system-minus-baseline deltas with local paired
bootstrap intervals. Versioned schema_version=1 D3 baseline packages validate
through `make validate-d3-baseline-package PACKAGE=...`, and recognized
versioned packages validate before scoring while legacy raw inputs remain
supported. This is package/provenance validation and local accounting, not a
live baseline run, held-out D3 result, or expert-parity claim.

**Exact-key alpha metadata:** D3 and D7 `system_gold_agreement` sections now
report exact-key binary Krippendorff's α beside percent agreement, Cohen's κ,
Gwet's AC1, and prevalence. This is not full semantic/multi-label D3 α or
boundary-disagreement-aware reliability evidence.

**D9 non-inferiority margin substrate:** D9 preference packages can include
explicit protocol metadata (`non_inferiority_margin` plus
`registered_before_evaluation=true`) so `make bench PREFERENCE=...` reports a
system-minus-human preference-rate interval and margin-gated
`non_inferiority_assessment`; pre-evaluation D9 protocol packages can also be
validated with `make validate-d9-interpretive-preference-protocol PROTOCOL=...`,
preflighted against result files with
`make d9-interpretive-preference-preflight PROTOCOL=... PREFERENCE=...`, and
enforced at score time with `make bench D9_PROTOCOL=... PREFERENCE=...`. When
`D9_PROTOCOL=...` is supplied, that protocol file is the authoritative local
source for D9 non-inferiority margin metadata in the scorecard.
This is not blind expert-parity evidence without populated held-out expert
outcomes.

**Confidence-calibration interval metadata:** confidence-calibration scorecards
now include Wilson intervals for overall accuracy, calibration-bin accuracy,
per-surface accuracy, and local bootstrap intervals for Brier score and ECE.
Confidence-calibration protocol packages can now be validated before labels are
collected or scored, calibration result files can now be preflighted against
those protocols, and `make bench CONFIDENCE_PROTOCOL=... CALIBRATION=...`
enforces that guard at score time. These are local uncertainty intervals and
process/provenance metadata over supplied labels, not proof that confidence is
calibrated on held-out data.

**D6 bias protocol/preflight substrate:** `make validate-d6-bias-protocol
PROTOCOL=protocol.json` / `scripts/validate_d6_bias_protocol.py` can validate
pre-run D6 bias-audit protocol metadata, including ethical respondent-attribute
policy, frozen case-set metadata, configured stratified/counterfactual
dimensions, held-out prompt/model freeze, contamination check, pre-run
registration, project-state hash, and success criteria. `make
d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=...
COUNTERFACTUAL=...` / `scripts/preflight_d6_bias_protocol.py` can check
concrete D6 result files against that protocol, including required configured
files, unexpected files, optional SHA-256 locks, stratified attributes, and
stratified surfaces; `make bench D6_PROTOCOL=...` enforces the same preflight
at the score boundary and blocks scorecard/output/artifact writes when it fails.
This is process/provenance metadata only; it is not a
populated bias audit, causal proof, bias-free evidence, methodological-validity
evidence, or a benchmark result.

**Adjudication protocol and Phase 0 package runner:** `make
validate-adjudication-protocol PROTOCOL=protocol.json` /
`scripts/validate_adjudication_protocol.py` can validate pre-label protocol
metadata for split, freeze, contamination check, registration, coder count,
sample target compatibility, and success criteria. `make
adjudication-protocol-preflight PROTOCOL=protocol.json SAMPLE=sample.json` /
`scripts/preflight_adjudication_protocol_sample.py` can cross-check that a
concrete sample package matches the registered protocol's project, corpus,
optional project-state/sample-file hash, target types, and planned sample size.
`make adjudication-response-preflight PROTOCOL=protocol.json
SAMPLE=sample.json RESPONSES=responses.json` /
`scripts/preflight_adjudication_responses.py` can cross-check completed
responses against the registered protocol/sample chain, exact sample item IDs,
project/corpus/project-state hashes, required target types, and completed
response validation before import.
`make
write-phase0-adjudication-package ...` /
`scripts/write_phase0_adjudication_package.py` can validate imported versioned
D3/D7 gold package files together and write a strict manifest.
`make bench-package PACKAGE=phase0_package.json` /
`scripts/run_phase0_benchmark_package.py phase0_package.json` can validate that
`schema_version=1` manifest, resolve benchmark input paths relative to it, and
invoke the canonical `make bench`/`qc_cli.py bench` scoring path. This is
repeatability and provenance infrastructure only; it is not populated held-out
evidence.

**Planned / not yet done (do not imply these exist):** any **methodological validity** evidence (blind expert ratings, gold-standard agreement from real expert labels, populated bias stratification/counterfactual audit); full **tamper-evident audit substrate** (append-only/signed log; export hash manifests, local verification, publish preflight, and hash-linked event logs are only local integrity metadata); semantic/adversarial/human-adjudicated disconfirmation with D7 validation (INV-2); populated expert adjudication runs; browser-native/full human claim-review workflow; true theoretical sampling, per-category saturation, full axial decomposition, multi-model consensus, active learning, collaborative coding, retrieval grounding.

### 13.1 Architectural invariants (the north-star — and where the build falls short)

§13 says what *is*; this says what *must be true* for the system's outputs to be trustworthy. These are the non-negotiable correctness conditions of the target architecture — and, per the Ambition section, the **committed build spec** for the public product, not an idealized measuring stick. The north-star is stricter than the current build; several invariants are **unmet today**, stated loudly so agents do not mistake the build for the target. Until an invariant is met, the outputs it governs are *provisional*, and an agent must say so. Each UNMET invariant is a ranked work item in §18.

**Met by the current build (keep them met — do not regress):**
- **INV-A — Fail-loud inter-stage contracts.** Missing upstream data raises (`ctx.require`), never silently degrades. *Met.*
- **INV-B — Structural schema validity.** Every LLM output validates against a typed schema (constrained decode where supported, else validate-and-retry). *Met* (structural only — not interpretive validity).
- **INV-C — Provenance recorded.** Every code/application is tagged LLM- vs. human- vs. system-originated. *Met.*

**Target invariants the build does NOT yet satisfy (treat governed outputs as provisional):**
- **INV-1 — Evidentiary anchoring.** Every quoted piece of evidence must resolve to a stable anchor (`doc_id`, `start_char`/`end_char`, `quote_hash`) and fail loudly if it cannot. *Status: **MOSTLY MET**.* `qc_clean/core/grounding.py` resolves each quote to exact original-document char offsets + a sha256 span hash, robust to smart quotes / whitespace / case, and now includes a conservative deterministic fuzzy fallback for long near-verbatim spans when exact matching finds zero occurrences; a quote is anchored only if it occurs **exactly once** in the corpus — **ambiguous (>1) and unresolvable (0) quotes are dropped + `data_warning`, never misattributed**. Wired into thematic, incremental, legacy-GT, and constant-comparison paths; example-quote thematic/incremental anchors now derive `speaker` from the containing char-anchored segment when available, and fall back to explicit same-line `Speaker:` source prefixes when no segment speaker exists, while exhaustive and constant-comparison paths already carry segment speakers; `verify_grounding()` / `make bench` measure the grounding rate (D1). *Remaining (why not fully MET):* (a) **`speaker` is still best-effort** when speaker labels are undetected, absent, no containing segment is available, and no explicit same-line source prefix exists; (b) matching is deterministic exact/fuzzy, **not semantic** — genuinely paraphrased quotes without near-verbatim overlap are still correctly dropped, but that is a recall cost a semantic matcher could recover; (c) constant-comparison offsets are best-effort. Quote-level evidence that *is* anchored is now verifiable; the headline misattribution risk is closed.
- **INV-2 — Source-anchored, retrieval-first disconfirmation.** Negative cases must be drawn by retrieving candidate contrary passages from the corpus *first*, then interpreting — ideally with a different model/adversarial prompt — each anchored (INV-1) and human-adjudicated **before the claim set is treated as final**. *Status: **PARTIAL (lexical/query-expanded retrieval-first + opt-in embedding-hybrid retrieval + adversarial routing + D7 scoring/export/baseline-validation/comparison/protocol-preflight/guard substrate slices).*** `qc_clean/core/disconfirmation.py` retrieves bounded char-anchored segment candidates for live claim-ledger targets before LLM interpretation using BM25-style term weighting, configurable contradiction-cue boosts, deterministic query-expansion terms, and an opt-in `embedding_hybrid` mode that combines lexical score with embedding cosine similarity when an embedding model is explicitly configured; `NegativeCaseStage` sends retrieved candidates instead of the full corpus, frames interpretation as skeptical/adversarial evidence review, and can route through `PipelineContext.disconfirmation_model_name`; `NegativeCase.candidate_id` lets returned cases attach exact candidate anchors, and invalid candidate IDs fail loud; `make bench` computes exact D7 recall/precision/F1 plus 95% Wilson intervals for recall/precision, a local exact-key F1 bootstrap interval, and local paired exact-key baseline-delta bootstrap intervals when adjudicated contrary-evidence gold anchors and baseline predictions are present; `make run-d7-retrieval` exports retrieval-mode candidates as baseline-compatible predictions with project/corpus/state/trace/budget provenance, `make validate-d7-baseline-package` validates versioned retrieval/live-baseline prediction packages, recognized versioned `BASELINES=` files validate before scoring, `make validate-d7-comparison-protocol` validates registered comparison metadata, `make d7-comparison-preflight` cross-checks versioned D7 gold and retrieval/live-baseline prediction packages against that protocol, and `make compare-d7-retrieval PROTOCOL=...` can enforce the same preflight before scoring multiple exported packages against one gold file. **Remaining gaps:** embedding-hybrid retrieval is opt-in and unvalidated; no validated default embedding/adversarial model/provider policy has been chosen; target/candidate counts are bounded; zero retrieved candidates is not evidence of no contrary evidence; candidate results are not human-adjudicated; no held-out D7 gold-set benchmark with live baselines or held-out retrieval-mode comparisons has run. The D7 baseline-package validation and comparison protocol/preflight/guard surfaces are provenance only. Disconfirmation is experimental and **not** credibility evidence.
- **INV-3 — Validity adjudication is separate from consistency.** Correctness must be estimated by human/expert adjudication on a sample of coding decisions, distinct from agreement/stability. Consistency metrics cannot detect stable error (same wrong code, high agreement). *Status: **PARTIAL (protocol + sample preflight + sample-export + response validation/preflight + guarded D3/D7 import/package substrate).*** `make validate-adjudication-protocol` validates schema_version=1 pre-label protocol metadata for split, prompt freeze, contamination check, pre-label registration, coder count, sample target compatibility, and success criteria; `make adjudication-protocol-preflight` cross-checks a concrete sample package against that protocol before labeling; `make adjudication-sample` / `qc_cli.py project adjudication-sample` now exports schema_version=1 unlabeled sample packets over applications, claims, negative cases, and relationships with project/corpus hashes, source context, and response templates; `make validate-adjudication-responses PACKAGE=sample.json` validates completed response package shape/completeness and reports missing/duplicate/invalid responses; `make adjudication-response-preflight PROTOCOL=protocol.json SAMPLE=sample.json RESPONSES=responses.json` checks completed responses against the registered protocol/sample provenance, exact item IDs, required target types, and response validation status before import; `make import-adjudication-responses ... PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json` converts valid completed code-application and negative-case responses into validator-compatible D3/D7 gold package inputs when explicitly requested, optionally running that preflight at the import boundary and excluding invalid/unclear responses; `make write-phase0-adjudication-package` writes a strict Phase 0 manifest from those versioned inputs for repeatable scoring. **Remaining gaps:** no expert labels have been collected in this repo, no correctness estimate exists, and no held-out expert adjudication run has been completed. The protocol package, preflight reports, sample packet, response validation report, generated import packages, and Phase 0 manifest are adjudication protocol/provenance artifacts, not evidence by themselves.
- **INV-4 — Stability ≠ saturation.** Codebook-stability convergence and GT category saturation (per-property/dimension adequacy) must be separate, separately-labeled outputs; codebook convergence must never be reported as theoretical adequacy. *Status: PARTIAL* (codebook stability exists; category adequacy diagnostic exists; sampling suggestions use diagnostic gaps; loaded-document candidate packages and selected-candidate result packages can be exported; pre-run theoretical-sampling protocol packages can be validated and preflighted against concrete candidate/result packages; true methodological saturation and populated theoretical sampling remain UNMET). `assess_category_saturation()` / `make bench` now report per-category property counts, dimension counts, supporting applications/documents, gaps, and diagnostic status separately from codebook stability; `suggest_next_documents()` uses non-adequate category diagnostics before falling back to low coverage; `make export-theoretical-sampling-candidates` writes schema_version=1 loaded-document candidate packages from those suggestions; `make export-theoretical-sampling-results` records explicit selected candidate IDs as schema_version=1 result packages; `make validate-theoretical-sampling-protocol` validates schema_version=1 pre-run protocol metadata for target category gaps, thresholds, candidate-source policy, collection rules, stopping rule, and success criteria; `make theoretical-sampling-preflight` checks concrete candidate/result packages against protocol IDs, project/corpus/state hashes, source policy, collection mode, target-gap coverage, and selected-candidate provenance. This is adequacy/sampling protocol guidance and provenance, **not proof of grounded-theory saturation**. *Scope note:* category saturation + theoretical sampling are mandatory **only insofar as the GT path claims theory generation**; for explicitly fixed-corpus codebook/post-positivist use, their absence is a stated scope boundary (§6), not a defect — but then the output must not be called grounded theory.
- **INV-5 — Bias surfacing.** Where respondent attributes are available and ethically permissible, stratified error diagnostics must check whether coding tracks respondent identity markers rather than textual meaning. Stratification reveals disparate error rates but cannot prove *causation*; the stronger test is **counterfactual identity-cue masking/swapping** — hold the substantive text constant, vary identity markers ("single mother", "immigrant", "manager"), and check whether code assignments change. *Status: **PARTIAL (protocol/preflight/score-time guard + local accounting substrates only).*** `make validate-d6-bias-protocol PROTOCOL=protocol.json` validates pre-run D6 protocol metadata for ethical attribute policy, frozen case-set metadata, configured D6 dimensions, held-out gates, and success criteria. `make d6-bias-preflight PROTOCOL=protocol.json STRATIFIED=... COUNTERFACTUAL=...` checks concrete D6 result files against that protocol before scoring, and `make bench D6_PROTOCOL=...` enforces the same guard before emitting scorecards or artifacts. `make bench BIAS_COUNTERFACTUAL=bias.json` scores externally supplied counterfactual identity-swap rows with code-change Wilson intervals and local mean-Jaccard bootstrap intervals. `make bench BIAS_STRATIFIED=bias_stratified.json` scores externally supplied stratified correctness/error rows with group and surface summaries, accuracy/error-rate Wilson intervals, and max error-rate gaps. **Remaining gaps:** no populated prompt_eval-backed bias suite, no generated frozen counterfactual cases, no held-out correctness labels by group, and no causal proof or bias-free evidence. Do not say the system has passed a bias audit.
- **INV-6 — Disconfirmation covers the *final* claim set.** Every output-producing stage's claims must be subject to disconfirmation — including the last one. *Status: **PARTIAL (ledger-routed + retrieval-first first slices).*** `NegativeCaseStage` now runs **last**, enumerates a bounded `ProjectState.claims` target list by claim ID, retrieves bounded source-candidate passages for those targets using default BM25-style lexical/query-expanded retrieval or opt-in embedding-hybrid retrieval, and asks an adversarially framed LLM reviewer to assess candidates. `NegativeCase.target_claim_id` and `candidate_id` let found contrary evidence attach to exact challenged claims and exact retrieved anchors, and `summarize_disconfirmation_coverage()` reports challenged vs. unchallenged claim targets on CLI/API/MCP surfaces. **Remaining gaps:** target and candidate lists are bounded/truncated for prompt size; embedding/adversarial retrieval is not validated; no validated default adversarial model/provider policy exists; not every target is guaranteed to receive a candidate or negative-case result; and the negative-case stage's own assessment is not challenged by a later stage. Do **not** say "all final claims survived disconfirmation."
- **INV-7 — Instruction/data separation (prompt injection is a *validity* failure, not only security).** Transcript text is untrusted *data*; the pipeline must treat it as data, never as instructions, or an injected instruction in a transcript can change codes/summaries so the output reflects the injection rather than the participant. *Status: **PARTIAL (first-party raw + derived prompt boundaries + strict override placeholder guards + explicit placeholder exposure policy + registry lint + scorecard/package substrate + opt-in live canary runner with protocol + prompt hashes + protocol-result preflight).*** `qc_clean/core/prompting.py` renders raw transcript/document/segment text and downstream LLM/codebook artifacts as explicit untrusted data: every data-provided line is prefixed with `DATA>`, and the boundary tells the model not to follow commands, role labels, delimiters, or formatting inside those data lines. Wired first-party raw-data paths: thematic example-quote and exhaustive coding, perspective, relationship, synthesis, negative-case, GT constant-comparison, GT axial coding, and incremental recoding. Wired derived-output paths: perspective/relationship/synthesis phase JSON, GT open/axial/core text, GT evolving codebook context, incremental existing-codebook context, and negative-case codebook/cross-case/claim-target context. `tests/test_prompt_boundaries_inv7.py` captures representative prompts with adversarial transcript and derived-output fixtures and verifies those instructions stay prefixed; `{combined_text}` and `{segment_text}` prompt-override placeholders receive already-boundaried data, and current override surfaces fail loudly if those protected placeholders are omitted, indexed, attribute-accessed, conversion-formatted, format-specified, replaced with undeclared metadata placeholders, or backed by renderer values not explicitly declared as required data, optional data, or metadata. `qc_clean/core/prompt_override_registry.py` centrally declares supported override surfaces: thematic overrides expose metadata `{num_interviews}`; GT constant-comparison overrides expose optional protected data `{codebook_context}` and metadata `{seg_idx}`, `{total_segments}`, and `{doc_name}`. `make lint-prompt-overrides` fails when source uses an unregistered `prompt_overrides` key or a registered surface disappears from source. `make bench` reports `prompt_injection_inv7`, scoring externally supplied fixture outcomes from project metadata or `PROMPT_INJECTION=inv7.json` with pass/fail rates, attack-success rates, Wilson intervals, and per-surface/per-attack-type summaries; `make run-inv7-fixtures` writes deterministic structural schema_version=1 fixture packages, `make validate-inv7-live-protocol` validates pre-run live protocol metadata, `make run-inv7-live-fixtures` writes opt-in live model canary packages with exact fixture prompt SHA-256 hashes, `make inv7-live-preflight` checks a live result package against the registered protocol before scoring, and `make validate-inv7-package` validates result package metadata including optional prompt-hash key/value consistency. **Remaining gaps:** broader custom-prompt governance can still misuse arbitrary operator-authored instructions around protected blocks, the live runner is a small canary set rather than a committed/scored adversarial benchmark, and structural boundaries, registry linting, external fixture scores, protocol/package/preflight validation, prompt hashes, and canary passes do not prove model obedience. Do **not** say prompt injection is solved.
- **INV-8 — Explicit segment universe (a defensible denominator).** The architecture must distinguish "not coded," "not examined," and "examined but judged irrelevant" — i.e., a stable registry of textual units (segment IDs) against which every coding decision (including null decisions) is recorded. *Status: **MET in exhaustive mode (opt-in); PARTIAL by default.*** Always on: `qc_clean/core/segmentation.py` builds a **char-anchored segment universe** (round-trip-verified offsets), ingest populates `ProjectState.segments`, and `compute_coverage` reports **traversal coverage** (D2). With **exhaustive coding** (`ctx.exhaustive_coding` / `project run --exhaustive`), one batched call renders a decision for *every* segment — `Segment.decision ∈ {coded, no_code, None}` — so coverage becomes **examined-and-judged** (`examined_rate`), distinguishing "not relevant" from "never examined," and `make bench` reports `coded_segment_rate` only over examined decisions. Applications anchor directly to segment spans. *Cost note:* this is **not** 5–10× (no per-segment calls) — it is one batched call with more output tokens; the default keeps the cheaper example-quote path until live-validated. Application-level *agreement* is now available too: `project irr --application-level` runs exhaustive passes and computes positive **segment × code** application agreement plus **segment-decision** agreement (§11), closing the codebook-discovery unit-of-analysis gap and explicitly counting shared no-code/not-examined decisions.
- **INV-9 — First-class claim ledger.** Every substantive analytic assertion (codes, applications, perspective claims, entity relations, code relations, synthesis findings, GT propositions, negative cases) must be an explicit typed object with: source stage, claim text, scope, supporting anchors, contrary anchors, adjudication status, and revision history. *Status: **MOSTLY MET (object layer).*** `ProjectState.claims` stores `AnalyticClaim` objects; default/thematic and GT stages derive claims or no-claims events from validated domain outputs; negative cases can link challenged code/claim targets and contrary anchors; CSV/Markdown/CLI/API/MCP expose bounded ledger summaries; `make bench` reports deterministic `claim_anchor_coverage` counts/rates/breakdowns for anchored versus unanchored claim rows. *Remaining gaps:* higher-order claims are often `needs_anchor` until explicit source-span support is added; anchor coverage is structural accounting, not truth or human review; retrieval-first disconfirmation is bounded, embedding-hybrid retrieval is opt-in/unvalidated, and no held-out D7 result exists (INV-2/6); claim review exists in `ReviewManager` but not a full browser-native workflow (INV-10); prompt schemas still emit domain objects that are adapted into claims rather than claim-native outputs. Do not say the ledger proves every claim is supported, disconfirmed, or human-retained.
- **INV-10 — Adjudication beyond code labels.** Human review must reach applications, claims, relationships, and negative cases — not only code objects. *Status: **PARTIAL**.* `ReviewManager` supports code applications, `target_type="claim"` decisions for approve/reject/modify (updating `AnalyticClaim.adjudication_status` and `revision_history`), and relationship decisions for explicit `target_type="code_relationship"` / `target_type="entity_relationship"` approve/reject/modify flows; `ReviewSummary` includes `claims_count`, `relationships_count`, and active/inactive review-decision counters; `/projects/{id}/review/claims` and MCP `qc_review_claims` expose bounded claim review rows for API/browser and agent clients; `/projects/{id}/review/negative-cases` and MCP `qc_review_negative_cases` expose bounded negative-case claim rows using the same `target_type="claim"` decision contract; `/projects/{id}/review/relationships` and MCP `qc_review_relationships` expose bounded code/entity relationship review rows; MCP `qc_review_decisions` can apply claim and relationship decisions with rationale for agent-drivable review; the browser review page now has Codes, Claims, Negative Cases, and Relationships modes that submit through the shared decision endpoint. Remaining gaps: sampled expert adjudication protocol (INV-3), held-out validity evidence, and richer sampled workflows over quote applications and downstream claims. A code label can be fine while its quote applications or downstream claims are wrong; marking the code human-reviewed must not launder unreviewed LLM inferences below it.
- **INV-11 — No stale higher-order outputs.** When the corpus changes (e.g. `project recode`), any downstream output not recomputed must be invalidated or flagged, never silently retained. *Status: **PARTIAL (explicit add-docs recode hook + hard-invalidation first slice).*** `project add-docs --recode` can now perform corpus mutation and invoke incremental recode in one opt-in command; plain `add-docs` still does not silently spend model budget. `IncrementalCodingStage` clears stale higher-order outputs it does not recompute (`synthesis`, `perspective_analysis`, `code_relationships`, `entities`, `entity_relationships`, `core_categories`, `theoretical_model`), removes matching stale phase results and claim-ledger rows for invalidated source stages, marks review decisions targeting removed claims inactive while retaining them as historical audit records, and appends a `data_warnings` entry naming what was invalidated. That warning is surfaced on the human + agent surfaces that matter: CLI human formatter, API JSON, JSON export, **Markdown export** (prominent block), MCP `qc_recode`/`qc_get_synthesis`/`qc_get_codebook`, and graph code/entity data responses. *Remaining gap (why PARTIAL, not MET):* this is explicit incremental recode-on-mutation plus invalidation, not full higher-order auto-recompute — the omitted stages still require a full pipeline rerun or future recomputation pipeline to regenerate. Locked by `tests/test_incremental_staleness_inv11.py` and `tests/test_project_commands.py`.

**Meta-invariant — INV-0:** the system and its agents must never assert an unmet invariant as met. If an output depends on an UNMET invariant, label it provisional and cite the invariant. (The architectural form of §14's claim discipline.)

## 14. Claim discipline — what agents may and may not assert

When writing commits, memos, reports, exports, or user-facing text about this system:

| You MAY say | You may NOT say |
|---|---|
| "Methodology-aware multi-stage pipeline for TA and GT-inspired coding" | "Full grounded theory" / "implements grounded theory" |
| "Structured output validated against schemas" | "Schema enforcement guarantees correct/valid coding" |
| "Measures LLM-pass agreement and stability" | "Inter-rater reliability" without the LLM-pass caveat; "kappa proves rigor" |
| "Quotes anchored to verifiable source spans where uniquely resolvable (ambiguous/unresolvable are dropped)" | "Every quote is grounded" (semantic paraphrases are dropped, not anchored; speaker best-effort) |
| "First-class claim ledger enumerates substantive assertions with support/adjudication status; Phase 0 reports structural claim-anchor coverage" | "Every claim is verified, disconfirmed, or human-adjudicated" (many higher-order claims need anchors; anchor coverage is not truth; INV-6/INV-10 remain incomplete) |
| "Experimental retrieval-first disconfirmation over bounded claim targets and source candidates, with default BM25/query-expanded retrieval, opt-in unvalidated embedding-hybrid retrieval, and configurable adversarial reviewer model" | "Negative-case analysis establishes credibility" / "all final claims were disconfirmed" (bounded candidates; no validated default embedding/adversarial model or held-out D7 evidence; INV-2/6 still partial) |
| "Cross-interview counts over LLM-surfaced example quotes" | "Consensus / prevalence across the corpus" (no segment-universe denominator; INV-8) |
| "Codebook-discovery agreement across passes" | "Codebook agreement proves coders applied the same codes to the same text" |
| "LLM-pass application-level agreement with `--application-level`: positive segment × code cells plus segment-decision agreement (`coded` / `no_code` / `not_examined`)" | "Human inter-rater reliability" / "methodological validity" / "agreement proves correctness" |
| "Confidence is an ordinal self-report signal" | "Confidence is a calibrated probability of correctness" (uncalibrated) |
| Bind claims to a stated `CorpusScope` or, when absent, to "these N transcripts" | Generalize to a population without a stated and defensible sampling frame; treat `CorpusScope` as validity proof |
| "Software is validated (tests pass)" | "The system is validated" (unqualified — implies methodological validity) |
| "Inspectable state and provenance" | "Auditable/tamper-evident" |
| "Open-source tool integrating these capabilities" | "State of the art" / "beyond SOTA" / "first to do X" |

When unsure which column a claim is in, default to the conservative phrasing and cite the relevant §13 status or invariant.

## 15. Methodological honesty (the things most likely to bite)

- **Consistency ≠ validity.** Agreement and stability detect *inconsistency*; they cannot detect a *consistent* shared bias across passes/models. LLM coding bias can be **systematic** w.r.t. respondent characteristics (Ashwin, Chhabra & Rao, 2025), not just random — the metrics we have will not catch it. (INV-3, INV-5.)
- **Quote anchoring is mostly met now** (INV-1). Quotes resolve to verifiable char spans + hash, and the "three people said 'I felt ignored'" case is handled (ambiguous → dropped, never guessed). Example-quote anchors can now derive `speaker` from a containing segment when available, or from an explicit same-line `Speaker:` source prefix when no segment speaker exists. *Residual weaknesses:* matching is deterministic exact/fuzzy, so a genuinely **semantic paraphrase** is dropped (recall cost, not a misattribution); and `speaker` remains best-effort when no speaker-labeled segment or explicit source prefix contains the span. A semantic matcher is the main follow-up.
- **Disconfirmation can still launder confirmation** (INV-2). The current pass is retrieval-first over bounded source candidates and can attach exact candidate anchors, which is materially better than asking the model to search the whole prompt from memory. Default retrieval is deterministic BM25-style lexical/query-expanded; opt-in embedding-hybrid retrieval can add embedding cosine similarity when explicitly configured. It now has an adversarial prompt stance and a configurable disconfirmation model override. But retrieval remains bounded and unvalidated, no validated embedding/reviewer default exists, and candidate results are not human-adjudicated. The real hardened version needs retrieval/model/provider policy backed by D7 evaluation, human adjudication, and adversarial retrieval tests. *Absence of a found negative case is not evidence none exists.*
- **Pseudo-replication.** Repeated LLM passes — even across model families trained on overlapping corpora — are not independent raters; panels reduce but don't remove the shared-dependency risk.
- **The denominator problem** (INV-8, addressed in exhaustive mode). There is a char-anchored **segment universe** and a **coverage** metric. In the default example-quote mode this is *traversal* coverage (and cross-interview consensus/prevalence still counts over example quotes → salience, not prevalence). In **exhaustive mode** every segment gets a recorded decision, so coverage is *examined-and-judged* and `coded_segment_rate` is computed over examined decisions rather than inferred from untouched text. Prefer exhaustive mode when you need to report prevalence/coverage as corpus facts.
- **Claim ledger existence ≠ claim validity** (INV-9 mostly met; INV-6/10 still partial). Substantive assertions now become typed claim objects, and Phase 0 can quantify which rows have supporting/contrary anchors, but many higher-order claims still need source anchors, hardened disconfirmation, and human/expert adjudication. A polished or anchored ledger row can still be unsupported, wrong, or provisional.
- **Confidence is not calibrated.** `confidence`/`discovery_confidence`/`confidence_assessment` are ordinal self-reports, not empirical correctness probabilities. Do not rank or weight claims as if they were calibrated.
- **Corpus boundary is recordable, not validated.** `ProjectState.corpus_scope` can now state phenomenon, population, sampling frame, inclusion/exclusion criteria, and caveats; CLI/API surfaces can read/update it, and CLI/MCP project creation can set it at creation time; Markdown export surfaces it before analytic claims, CSV/Markdown claim rows include compact claim-scope and corpus-boundary context, JSON/CSV exports emit machine-readable warnings when claim-bearing exports have no recorded scope, an empty scope record, or a population without a sampling frame, `make lint-scope-phrasing` can scan arbitrary text for risky population-generalizing phrases under missing/under-specified scope, and `make bench` reports `corpus_scope_adequacy` status and field completeness. That helps report discipline; it does **not** prove the sampling frame is adequate or make population generalization safe. If scope is absent or under-specified, fall back to "these N transcripts," not population language.
- **Schema constraint is not validity** (§10).

## 16. Security & deployment posture

The system is a **local research tool**, loopback-bound and unauthenticated; hardened against arbitrary-write (MCP export sandbox) and stored XSS, but not a multi-tenant deployment. Transcripts often contain sensitive/PII data. **Before running on anything real:** prefer local models (Ollama/vLLM) so data never leaves the machine; treat transcripts as *untrusted input* (prompt-injection risk — also a **validity** invariant, INV-7, because an injected instruction corrupts the analysis itself, not just the system); know that PII de-identification, log redaction, local-only enforcement, and right-to-delete cascades are **not yet implemented**. Don't run on regulated/clinical/protected data as-is without those controls and an IRB/DPIA assessment.

| Deployment class | Acceptability (as described) |
|---|---|
| Synthetic / demo transcripts | Acceptable |
| Public-domain text | Acceptable |
| De-identified low-risk interviews | Conditionally acceptable (local model; manual PII review) |
| Clinical / educational / workplace transcripts | Not yet acceptable without local-only enforcement, redaction, threat model |
| Regulated / protected data | Not acceptable as described |

## 17. Limitations (the short list)

LLM bias may be systematic not random (INV-3/5); reliability ≠ validity; pseudo-replication; the denominator problem (INV-8 default path); claim ledger rows can be provisional/unanchored/unadjudicated (INV-9/10); GT fidelity partial ("GT-inspired," not "full GT"); disconfirmation is retrieval-first/adversarially framed now but still bounded, defaults to BM25-style lexical/query-expanded retrieval, has only opt-in unvalidated embedding-hybrid retrieval, is not held-out D7-validated, and remains experimental even with optional baseline point-comparison wiring (INV-2/6); prompt-injection scoring can ingest structural or opt-in live canary fixture files but no committed/scored live adversarial benchmark result exists (INV-7); D10 wall-clock timing is last-local-run metadata and can be packaged as a local timing artifact with runtime environment metadata, but it is not public benchmark timing evidence; confidence uncalibrated; corpus scope is recordable/exported but not sampling-frame validation; incremental staleness is hard-invalidated but not auto-refreshed (INV-11); export hash manifests, verification, publish preflight, and hash-linked event logs are local integrity metadata, not a full tamper-evident audit substrate; methodological validity unmeasured; non-determinism inherent (we measure and report it).

## 18. Roadmap (priority order — toward the public SOTA product)

Sequencing rule: **the evaluation harness is the keystone** (it proves the SOTA claim *and* drives improvement), then the *objects* that make the guarantees true (segment universe, claim ledger), then the rigor edges — not features. Full harness design: `docs/EVALUATION_HARNESS.md`.

1. **Evaluation harness (KEYSTONE)** — *Phase 0 DONE* (`make bench`: grounding rate D1, coverage D2, externally fed D4 codebook-quality rubric outcome scoring, pre-evaluation D4 protocol validation via `make validate-d4-codebook-quality-protocol`, D4 protocol/result preflight via `make d4-codebook-quality-preflight`, D4 score-time preflight guard via `make bench D4_PROTOCOL=...`, gold-dependent exact code/source-anchor D3 application-validity scoring with raw or versioned validated D3 gold files plus surfaced package provenance, local F1 bootstrap intervals, local same-code/doc span-IoU diagnostics, local Modified Hausdorff diagnostics, exact-key binary system-vs-gold κ/AC1 metadata, human-ceiling exact-metric comparison, and human-human κ/α/AC1 metadata when package metrics are present, externally fed D6 counterfactual identity-swap outcome scoring with code-change Wilson intervals and local mean-Jaccard bootstrap intervals, externally fed D6 stratified correctness/error scoring with accuracy/error-rate Wilson intervals, per-attribute/per-group summaries, per-surface summaries, and max group error-rate gaps, pre-run D6 bias protocol validation via `make validate-d6-bias-protocol`, D6 protocol/result preflight via `make d6-bias-preflight`, D6 score-time preflight guard via `make bench D6_PROTOCOL=...`, reliability/stability D5 with Gwet's AC1, prevalence tables, and local row-bootstrap intervals surfaced when IRR results exist, gold-dependent exact-anchor D7 disconfirmation scoring with recall/precision Wilson intervals, local F1 bootstrap intervals, exact-key binary system-vs-gold κ/AC1 metadata, optional baseline comparisons with local paired delta bootstrap intervals, human-ceiling exact-metric comparison, human-human κ/α/AC1 metadata when package metrics are present, and surfaced package provenance, D3/D7 gold-package validation through Make and top-level `qc_cli.py validate-d3-gold` / `qc_cli.py validate-d7-gold`, `make run-d7-retrieval` export of retrieval-mode candidates for that D7 baseline path, externally fed INV-7 prompt-injection fixture outcome scoring with per-surface/per-attack-type summaries, externally fed D8 GT-fidelity rubric outcome scoring, pre-evaluation D8 GT-fidelity protocol validation via `make validate-d8-gt-fidelity-protocol`, D8 protocol/result preflight via `make d8-gt-fidelity-preflight`, D8 score-time preflight guard via `make bench D8_PROTOCOL=...`, externally fed D9 forced-choice interpretive-preference outcome scoring, pre-evaluation D9 interpretive-preference protocol validation via `make validate-d9-interpretive-preference-protocol`, D9 protocol/result preflight via `make d9-interpretive-preference-preflight`, D9 score-time preflight guard via `make bench D9_PROTOCOL=...`, externally fed confidence-calibration scoring, pre-evaluation confidence-calibration protocol validation via `make validate-confidence-calibration-protocol`, confidence-calibration protocol/result preflight via `make confidence-calibration-preflight`, confidence-calibration score-time preflight guard via `make bench CONFIDENCE_PROTOCOL=...`, D10 cost/latency from real `llm_calls` rows plus optional matching `tool_calls` rows, D10 last-local-run wall-clock metadata, D10 timing artifact packaging with runtime environment metadata, Phase 0 input/configuration hashes with prompt hashes marked `not_run`, pre-label adjudication protocol validation via `make validate-adjudication-protocol`, protocol/sample package preflight via `make adjudication-protocol-preflight`, unlabeled adjudication sample export via `make adjudication-sample`, completed-response shape validation via `make validate-adjudication-responses`, completed-response protocol/sample preflight via `make adjudication-response-preflight`, D3/D7 gold package import from valid completed responses with optional import-time preflight guard inputs via `make import-adjudication-responses`, and strict Phase 0 manifest assembly for imported D3/D7 package inputs via `make write-phase0-adjudication-package`; deterministic except opt-in embedding export cost and separately generated live INV-7 canary files; `qc_clean/core/bench.py`, `qc_clean/core/d4_codebook_quality_protocol.py`, `qc_clean/core/d4_codebook_quality_preflight.py`, `qc_clean/core/d6_bias_protocol.py`, `qc_clean/core/d6_bias_preflight.py`, `qc_clean/core/d8_gt_fidelity_protocol.py`, `qc_clean/core/d8_gt_fidelity_preflight.py`, `qc_clean/core/d9_interpretive_preference_protocol.py`, `qc_clean/core/d9_interpretive_preference_preflight.py`, `qc_clean/core/confidence_calibration_protocol.py`, `qc_clean/core/confidence_calibration_preflight.py`, `qc_clean/core/adjudication_protocol.py`, `qc_clean/core/adjudication_preflight.py`, `qc_clean/core/adjudication_response_preflight.py`, `qc_clean/core/adjudication_sample.py`, `qc_clean/core/adjudication_import.py`). Remaining: gold-standard corpora, blind expert ratings, populated D4 LLM-judge/blind-expert evaluations, full D3 Krippendorff's α/semantic agreement and populated human-ceiling comparison data, populated prompt_eval-backed bias stratification + counterfactual identity-cue tests, populated D8 expert GT-fidelity rubric outcomes under a pre-registered protocol, populated blind expert D9 preference outcomes under a pre-registered non-inferiority margin, held-out D7 runs with live baselines, committed/scored live adversarial prompt-injection runs, public benchmark timing evidence with controlled environment/baseline context, populated confidence-calibration benchmark — built on `prompt_eval`. *Narrows INV-3 infrastructure but does not close INV-3 until expert labels are collected and scored*, operationalizes INV-5.
   Phase 0 can also run through `make bench-package PACKAGE=...`, a strict
   manifest wrapper for the same canonical scorecard path; this improves
   package repeatability and provenance, not the evidentiary status of any
   unpopulated benchmark.
   D3 now also has an externally fed baseline-comparison substrate through
   `D3_BASELINES=...`, but actual/live baseline runs on held-out data remain
   future benchmark work.
   D3/D7 exact-key system-gold agreement now includes Krippendorff's α metadata;
   full semantic/multi-label α remains future benchmark work.
   D9 protocol metadata can now be validated before outcome collection, D9
   result files can now be preflighted against those protocols, and `make bench
   D9_PROTOCOL=...` enforces that guard at score time while computing a local
   non-inferiority margin assessment from protocol metadata, but populated
   blind expert preference outcomes remain future benchmark work.
   D9 tie rates now also report Wilson intervals, but this is local uncertainty
   metadata only.
   Confidence calibration now reports Wilson accuracy intervals plus local
   Brier/ECE bootstrap intervals, pre-evaluation confidence-calibration
   protocol packages can now be validated, and calibration result files can be
   preflighted against those protocols, while `make bench
   CONFIDENCE_PROTOCOL=...` enforces that guard at score time; populated
   held-out calibration labels remain future benchmark work.
   D6 counterfactual-bias scorecards now report Wilson intervals for
   code-change rates and local bootstrap intervals for mean Jaccard distance;
   D6 stratified-bias scorecards now report Wilson intervals, per-group and
   per-surface summaries, and max error-rate gaps for externally supplied
   correctness rows. D6 bias protocols can now be validated before rows are
   generated/scored, D6 result files can be preflighted against those
   protocols, and `make bench D6_PROTOCOL=...` enforces that guard at score
   time. Populated prompt_eval-backed bias audits remain future benchmark work.
   D4 codebook-quality scorecards now report local bootstrap intervals for
   rubric means, D4 codebook-quality protocol packages can now be validated,
   and D4 result files can now be preflighted against those protocols before
   rows are generated/scored, while `make bench D4_PROTOCOL=...` enforces that
   preflight guard at score time; populated LLM-judge/blind-expert-panel
   evidence remains future benchmark work.
   D8 GT-fidelity scorecards now report local bootstrap intervals for rubric
   means, D8 GT-fidelity protocol packages can now be validated, D8 result
   files can now be preflighted against those protocols, and `make bench
   D8_PROTOCOL=...` enforces that guard at score time; populated expert-rubric
   GT-fidelity evidence remains future benchmark work.
2. **Span-anchored grounding** — *MOSTLY DONE* (`qc_clean/core/grounding.py`: offsets + hash + verify + unique-resolution, deterministic fuzzy recovery for long near-verbatim spans, ambiguous/unresolvable dropped; speaker derived from containing segments or explicit same-line source prefixes when available). Remaining for full INV-1: semantic matcher for genuinely paraphrased quotes and stronger speaker attribution when speaker labels/source prefixes are absent or undetected.
3. **Segment universe** — *DONE* (`segmentation.py` registry + `ProjectState.segments` + `compute_coverage`; **exhaustive per-segment coding** via `project run --exhaustive` gives examined-and-judged coverage and segment-anchored applications — INV-8 met in that mode; `project irr --application-level` now reports positive segment × code application agreement and segment-decision agreement). Remaining: decide whether exhaustive becomes the default after live validation.
4. **First-class claim ledger** — *MOSTLY DONE object layer* (`ProjectState.claims`, deterministic stage builders, no-claims events, negative-case target refs, CSV/Markdown/CLI/API/MCP surfaces, API/MCP/browser claim-review first slices, API/MCP/browser negative-case review first slices, and API/MCP/browser/manager relationship-review first slices). Remaining for full INV-9/10: stronger source anchoring for higher-order claims and deciding whether future LLM schemas emit claim-native outputs.
5. **Disconfirmation + adjudication over the ledger** — *FIRST SLICES DONE*: negative-case prompts include bounded claim targets by ID, BM25-style lexical/query-expanded retrieval-first source candidates, opt-in embedding-hybrid retrieval, exact `candidate_id` anchors, configurable disconfirmation model routing, adversarial evidence-bound prompt stance, coverage summaries report challenged/unchallenged targets, `make bench` can score D7 against supplied adjudicated gold anchors with recall/precision Wilson intervals, local F1 bootstrap intervals, and optional baseline comparisons with local paired delta bootstrap intervals, `make run-d7-retrieval` exports retrieval-mode candidates with project/corpus/state/trace/budget provenance for that D7 baseline path, `make validate-d7-baseline-package` validates versioned retrieval/live-baseline prediction packages and recognized versioned `BASELINES=` files validate before scoring, `make validate-d7-comparison-protocol` and `make d7-comparison-preflight` validate/cross-check D7 retrieval comparison protocols, versioned gold, and predictions before scoring, `make compare-d7-retrieval PROTOCOL=...` can enforce that preflight guard before emitting exact-span local comparison reports for exported packages, `ReviewManager` plus API/MCP/browser first slices can adjudicate claim objects including negative-case claim rows, `ReviewManager` plus API/MCP/browser first slices can adjudicate code/entity relationships, `make validate-adjudication-protocol` can validate pre-label protocol metadata, `make adjudication-protocol-preflight` can cross-check protocol/sample package matching before labeling, `make adjudication-sample` can export unlabeled sample packets for human/expert review inputs, `make validate-adjudication-responses` can validate completed response package shape/completeness, `make adjudication-response-preflight` can check completed responses against protocol/sample provenance before import, `make import-adjudication-responses ... PREFLIGHT_PROTOCOL=protocol.json PREFLIGHT_SAMPLE=sample.json` can convert valid completed code-application/negative-case responses into D3/D7 gold package inputs with an optional import-time preflight guard, and `make write-phase0-adjudication-package` can assemble a strict Phase 0 manifest from those versioned package inputs. Remaining for full INV-2/INV-3/INV-6/INV-10: validated embedding/adversarial retrieval policy, held-out D7 gold-set evaluation with live baselines, held-out retrieval-mode comparisons, and actual expert adjudication runs.
6. **Instruction/data separation + prompt-injection tests** — *FIRST SLICES DONE*: first-party raw transcript/segment prompt data and downstream LLM/codebook artifacts are line-prefixed as untrusted, current prompt override surfaces require bare protected data placeholders, reject undeclared metadata placeholders, require renderer values to be declared as required data, optional data, or metadata, and are checked against a central source/registry lint, deterministic prompt-capture regressions exist, `make bench` can score externally supplied prompt-injection fixture outcomes, `make run-inv7-fixtures` and `make run-inv7-live-fixtures` write schema_version=1 INV-7 packages, live fixture runner output carries exact prompt SHA-256 hashes, `make validate-inv7-live-protocol` validates pre-run protocol metadata, `make inv7-live-preflight` checks live result packages against registered protocol metadata and prompt hashes before scoring, and `make validate-inv7-package` validates result package metadata and optional prompt-hash consistency. Remaining for full INV-7: broader custom-prompt threat-model tightening and a committed/scored live adversarial injection benchmark run.
7. **True theoretical sampling + per-category saturation** — *PARTIAL*: category adequacy diagnostics are surfaced separately from codebook stability, existing document suggestions consume those diagnostic gaps, loaded-document candidate packages can be exported from those suggestions, selected-candidate result packages can be recorded, pre-run theoretical-sampling protocol packages can be validated, and concrete candidate/result packages can be preflighted against those protocols. Remaining work is collecting/selecting new data beyond already-loaded uncoded docs, populated sampling-result evidence from real sampling cycles, and expert/held-out GT-fidelity evaluation before any true saturation claim (only if the GT path claims theory generation).
8. **Corpus-boundary / scope-condition contract** — *FIRST SLICES DONE*: optional `ProjectState.corpus_scope` records phenomenon, population, sampling frame, inclusion/exclusion criteria, and caveats; CLI/API read/update surfaces are available; CLI/MCP project creation can set scope at creation time; Markdown export surfaces scope before analytic claims, CSV/Markdown claim rows carry compact claim-scope and corpus-boundary context, Markdown/JSON/CSV exports warn when claim-bearing exports have no recorded scope, an empty scope record, or a population without a sampling frame, `make lint-scope-phrasing` scans arbitrary text for risky population-generalizing phrases under missing/under-specified scope, and `make bench` reports deterministic scope-record adequacy status/field completeness. Remaining: any actual sampling-frame adequacy evaluation beyond record completeness.
9. **Stale-output handling** — *INV-11 explicit add-docs recode hook + hard-invalidation first slices DONE*; remaining: full higher-order auto-recompute on corpus mutation.
10. **Features:** multi-model consensus; active learning from review; collaborative coding; retrieval grounding.
11. **Tamper-evident audit substrate** — *FIRST HASH-MANIFEST + LOCAL VERIFY + PREFLIGHT + EVENT-LOG SLICES DONE*: `make export-audit-manifest` writes schema_version=1 hash manifests for existing JSON/CSV/Markdown/QDPX export artifacts with project-state and per-file SHA-256 hashes; `make verify-export-audit-manifest` verifies manifest self-hash, artifact sizes/hashes, and optional current project-state hash; `make export-publish-preflight` is a strict local publish/handoff gate that requires an existing verified export-audit manifest and can include the current project-state hash when `ID=<project_id>` is supplied; local audit scripts and `qc_cli.py project export --audit-manifest ... --audit-log ...` can append hash-linked JSONL events, MCP JSON/Markdown export tools can append confined event-log sidecars with `audit_event_log=True`, and `make verify-export-audit-log` verifies event self-hashes and previous-event links. Remaining: signed/external or append-only storage semantics, default export/event-log policy decisions, and optional DB-backed audit events. Do not call the current manifest/verification/preflight/event-log set a full tamper-evident audit log.

## 19. Prior art worth learning from

Systems an agent researching improvements should read — relevant landscape, not competitors to beat. **GT automation:** AcademiaOS (arXiv:2403.08844); LOGOS (arXiv:2509.24294 — ~80.4% schema alignment across 5 corpora). **Inductive/thematic with LLMs:** MindCoder / "Efficiency with Rigor!" (arXiv:2501.00775); HICode (EMNLP 2025); TAMA (arXiv:2503.20666); Auto-TA (arXiv:2506.23998); Thematic-LM (ACM Web Conf. 2025). **Human–AI coding & evaluation:** PaTAT (CHI 2023); LLMCode (arXiv:2504.16671 — IoU/Hausdorff researcher-AI alignment metrics worth borrowing for INV-3 evaluation). **Local-first OSS QDA with QDPX export:** AQDA (github.com/tseidl/aqda) — closest comparator on the local+export axis. **Methods caution:** Ashwin, Chhabra & Rao (2025, *Sociological Methods & Research*) on systematic LLM coding bias; a 2026 PLOS Digital Health blinded comparison (LLM ≈ human on *deductive* code application, more variable on *inductive* theme generation, with modest chance-corrected agreement). **Reporting/reliability theory to target:** COREQ, SRQR; Krippendorff's alpha; Landis & Koch.
