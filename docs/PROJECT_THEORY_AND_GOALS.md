# Qualitative Coding System — Theory, Goals, and Honest State

**A detailed orientation and theory reference for coding agents working on this project.**

*Version 3.0 — 2026-06-19*

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

- **Target SOTA on the structural rigor dimensions** — coverage/exhaustiveness (INV-8), evidentiary grounding (INV-1), auditability/reproducibility (INV-9 + audit log), disconfirmation rigor (INV-2/6), reliability, scale, and cost. The defensible claim is about the **integrated bundle**, not any single dimension: several research prototypes already do parts well (HICode reports human-evaluated P/R on hierarchical coding; LOGOS a 5-dim GT metric; LLMCode IoU/Hausdorff alignment; Auto-TA end-to-end TA). What no widely-adopted tool *or* prototype combines is *all* of {exhaustive coverage + span-anchored grounding + first-class claim ledger + auditable provenance + systematic disconfirmation + QDA-format interop} in one system — and that combined claim must still be earned per dimension on a shared benchmark, not asserted.
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
- **`codebook: Codebook`** — `version`, `methodology`, `created_by`, and `codes: List[Code]`. A **`Code`** has `id`, `name`, `description`, `definition`, `parent_id` (hierarchy), `level`, `properties`, `dimensions`, `provenance`, `version`, `example_quotes`, `mention_count`, `confidence`, `reasoning` (why this code was created — the per-code audit trail).
- **`code_applications: List[CodeApplication]`** — the evidence links. A **`CodeApplication`** has `code_id`, `doc_id`, `quote_text`, `speaker`, `start_char`, `end_char`, `confidence`, `applied_by`, `codebook_version`. **Note for INV-1:** the anchor fields (`doc_id`, `speaker`, `start_char`, `end_char`) already exist in the schema; the unmet invariant is that `start_char`/`end_char` are not reliably populated (attribution is substring-derived), so the anchors cannot yet be trusted to identify the exact source instance.
- **`segments: List[Segment]`** — the **segment universe** (INV-8): every document split into char-anchored units (`doc_id`, `index`, `start_char`/`end_char`, `speaker`, `text`), populated by ingest. The denominator for coverage and (eventually) application-level agreement.
- **`code_relationships: List[CodeRelationship]`** — typed relations between codes (axial output): `relationship_type`, `strength`, `evidence`, `conditions`, `consequences`.
- **`entities` / `entity_relationships`** — entity map (relationship stage): people, orgs, concepts, tools and their typed relations, with `supporting_evidence`.
- **`perspective_analysis: Optional[PerspectiveAnalysis]`** — per-participant viewpoints, consensus/divergent themes, `perspective_mapping` (participant → emphasized codes).
- **`synthesis: Optional[Synthesis]`** — `executive_summary`, `key_findings`, `cross_cutting_patterns`, `recommendations`, `confidence_assessment`.
- **`core_categories` / `theoretical_model`** — GT selective + integration outputs.
- **`irr_result` / `stability_result`** — reliability outputs (§11).
- **`memos: List[AnalysisMemo]`** — every stage's analytic memo. `memo_type ∈ {theoretical, methodological, pattern, cross_case, coding, negative_case, ...}`, with `code_refs`, `doc_refs`, `created_by`. The `cross_case` memo is the cross-interview claim set (now ingested by negative-case analysis; INV-6).
- **`review_decisions: List[HumanReviewDecision]`** — the human audit trail (action, target, rationale, new value).
- **`phase_results`, `current_phase`, `pipeline_status`** — execution bookkeeping; each `AnalysisPhaseResult` records status, timing, input/output summaries, error message.
- **`iteration`, `codebook_history`** — support incremental re-coding and saturation comparison across iterations.
- **`data_warnings`** — surfaced non-fatal issues.

**Why one typed object:** reproducibility (the whole analytic record is one inspectable file), and fail-loud composition (a stage that needs `codebook` calls `ctx.require("codebook", ...)` and raises if it is absent). The cost: it is *inspectable*, not tamper-evidently *auditable* (INV — append-only log/hashes are roadmap).

---

## Part III — Methodology and stages

## 6. The methodology model (theory the code implements)

Two pipelines, each a fixed ordered sequence of stages over `ProjectState`. **Disconfirmation runs last in both** so it covers the final claim set (INV-6).

**Thematic / default (7 stages):** Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Cross-Interview → Negative Case.

**Grounded-theory-*inspired* (7 stages):** Ingest → Constant Comparison Coding → Axial Coding → Selective Coding → Theory Integration → Cross-Interview → Negative Case.

**Why "GT-*inspired*", not "full GT" — agents must respect this.** The pipeline performs the *visible procedural steps* of GT (**procedural mimicry**) but does **not** yet instantiate GT's core epistemic logic (**methodological fidelity**). Missing: *theoretical sampling* (collecting new data to develop weak categories), *category-level saturation* (per-property/dimension, not just codebook stability), *analytic memoing* that builds conceptual relations (current memos lean toward summary logging), full *axial decomposition* (causal vs. context vs. intervening conditions), and *reflexivity*. **Do not describe the system as doing "full grounded theory."**

**Which qualitative tradition it fits.** The emphasis on agreement metrics, structured output, and codebook stability fits **codebook / post-positivist** qualitative analysis (codebook thematic analysis, framework analysis). It is a poor fit for **reflexive thematic analysis** (Braun & Clarke — coder subjectivity is a resource; rejects inter-coder agreement as a quality criterion) and **constructivist grounded theory** (Charmaz — foregrounds the researcher's standpoint), *unless* a human fully drives interpretation and the LLM is only an assistant. Don't apply the automated agreement machinery to a reflexive study and call it appropriate.

## 7. Stage reference

Each stage implements `PipelineStage` (`can_execute(state) -> bool`, `execute(state, ctx) -> state`, `name()`). LLM stages return a Pydantic schema (`analysis_schemas.py` / `gt_schemas.py`) converted to the domain model via `adapters.py`. Every stage emits a memo.

**Shared / thematic:**

- **Ingest** (`ingest.py`) — parses `.txt/.docx/.pdf/.rtf`, detects speakers (handles `Name:` and `Name 0:03` timestamp formats), populates `corpus.documents`. *Reads:* loaded docs. *Writes:* `corpus` (content, `detected_speakers`). *Runs:* always.
- **Thematic Coding** (`thematic_coding.py`) — LLM discovers a hierarchical codebook. *Schema:* `CodeHierarchy` (codes with id/name/description/semantic_definition/level/example_quotes/mention_count/discovery_confidence/reasoning). *Writes:* `codebook.codes`, and `code_applications` (one per `example_quote` that resolves to a **unique** span via `grounding.resolve_against_docs` — anchored with `start_char`/`end_char`/`quote_hash`; ambiguous/unresolvable quotes are dropped + warned, INV-1). *Prompt is overridable* via `ctx.prompt_overrides["thematic_coding"]`. *Runs:* always (the foundational stage).
- **Perspective Analysis** (`perspective.py`) — maps participants to emphasized codes; single-speaker (introspection: strongest positions / internal tensions) vs. multi-speaker (consensus / divergence) mode chosen from detected speaker count. *Schema:* `SpeakerAnalysis`. *Writes:* `perspective_analysis`. *Requires:* codebook (`ctx.require`).
- **Relationship Mapping** (`relationship.py`) — extracts entities and typed relationships (powers the graph views). *Schema:* `EntityMapping`. *Writes:* `entities`, `entity_relationships`. *Requires:* codebook.
- **Synthesis** (`synthesis.py`) — executive summary, key findings, cross-cutting patterns, prioritized recommendations. *Schema:* `AnalysisSynthesis`. *Writes:* `synthesis`. *Requires:* upstream coding/perspective.
- **Cross-Interview** (`cross_interview.py`) — **programmatic, not LLM** (`analyze_cross_interview_patterns`): shared codes, consensus themes (code present in ≥60% of interviews), divergent themes, top code co-occurrences. *Writes:* a `cross_case` memo. *Runs:* only when `corpus.num_documents > 1`. **Denominator caveat (important):** these counts are computed over `code_applications`, and in the thematic path applications are LLM-surfaced *example quotes*, **not** all occurrences. So "consensus / prevalence / co-occurrence" here measure *salience-in-generation*, not *prevalence-in-corpus* — the denominator is "examples the LLM chose to surface," not "all coded segments." Do not report these as corpus prevalence until a segment universe exists (INV-8).
- **Negative Case** (`negative_case.py`) — LLM searches for disconfirming evidence against the codebook **and** the cross-interview claims (INV-6). *Schema:* `NegativeCaseResponse` (negative_cases + overall_assessment + analytical_memo). *Writes:* `negative_case` + `methodological` memos. *Runs:* when codebook has codes. **Status: experimental** (INV-2 — same-model/prompt lineage; can launder confirmation).

**Grounded-theory-specific:**

- **Constant Comparison Coding** (`gt_constant_comparison.py`) — segments documents (speaker turn or paragraph), iteratively codes each segment against the *evolving* codebook, checks codebook-stability saturation per pass (this is codebook convergence, **not** GT category saturation; INV-4). *Schema:* `OpenCode` (per segment). *Writes:* `codebook.codes`, `code_applications`. *Prompt overridable.* Replaces the legacy batch `gt_open_coding.py`.
- **Axial Coding** (`gt_axial_coding.py`) — relates categories (partial Strauss & Corbin paradigm: conditions, consequences). *Schema:* `AxialRelationship`. *Writes:* `code_relationships`. *Requires:* codebook.
- **Selective Coding** (`gt_selective_coding.py`) — identifies the core category. *Schema:* `CoreCategory`. *Writes:* `core_categories`. *Requires:* axial output.
- **Theory Integration** (`gt_theory_integration.py`) — assembles a theoretical model (framework, propositions, conceptual relationships, scope conditions, implications). *Schema:* `TheoreticalModel`. *Writes:* `theoretical_model`. *Requires:* core categories.

**Incremental** (`incremental_coding.py`) — `project recode`: codes only *uncoded* documents against the existing codebook, merges, then re-runs downstream state-driven stages (Cross-Interview → Negative Case). Deliberately omits stages that depend on ctx fields from a coding stage that is not re-run (Perspective/Relationship/Synthesis, Axial/Selective/Theory). **Staleness handling (INV-11, now flagged):** because those stages do not re-run, after a recode the state can hold *fresh* `code_applications` alongside *stale* `synthesis`, `perspective_analysis`, `entities`, `core_categories`, and `theoretical_model` that reflect the old corpus. The stage now appends a `data_warnings` entry naming any populated stale outputs (non-destructive — they are retained, not cleared); consumers must honor that warning. Full re-computation/invalidation is still future work.

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
4. **Negative Case** (runs last) ingests that memo and challenges it: *"Sam at 12:30 says 'I actually asked for more check-ins' — partially contradicts the 'oversight = imposed' framing."* — a disconfirming case against a **cross-interview** claim (INV-6 in action). Marked experimental (INV-2): the same model produced both, so absence of a found negative case is not proof none exists.

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

`ReviewManager` (`review.py`) implements the five operations a qualitative reviewer needs, over CLI (`project review`) and a browser UI (`/review/<id>`):

- **approve** — accept a code as-is.
- **reject** — remove a code (and its applications).
- **modify** — edit name/definition/etc. (bumps the code `version`).
- **merge** — combine codes (e.g. two near-duplicates into one).
- **split** — divide an over-broad code into finer codes.

Every decision is recorded as a `HumanReviewDecision` (action, target, rationale, new value) — the human audit trail — and updates code `provenance` to `HUMAN`. Review raises `ValueError` on unknown target types (fail loud). The pipeline can pause at review checkpoints when `enable_human_review=True`.

## 11. Reliability: IRR and stability (`irr.py`)

Two distinct measures, both **consistency, not validity** (§15):

- **Inter-rater reliability** (`project irr`) — runs coding N times with prompt variation (and optionally across multiple models), normalizes/aligns code names, builds a binary matrix (code × pass: 1 if that pass *discovered* the code), and computes **percent agreement**, **Cohen's kappa** (exactly 2 passes), and **Fleiss' kappa** (2+ passes), interpreted on the **Landis & Koch (1977)** scale. **Unit-of-analysis caveat:** this measures **codebook-discovery agreement** (do independent passes surface the same codes?), *not* application-level coding agreement (do raters assign the same code to the *same segment*?). True coding-reliability kappa needs a shared unit of analysis (the same segments) and a shared decision space — which needs the segment universe (INV-8). It is a legitimate reproducibility measure, but do not present it as inter-rater agreement on code *application*. See also the pseudo-replication caveat (§15, INV-3).
- **Multi-run stability** (`project stability`) — runs identical coding N times (no prompt variation) to quantify the model's *own* non-determinism; produces per-code stability scores classified stable / moderate / unstable, plus overall stability.

The distinction is the point: IRR ≈ "does the method agree with itself under variation"; stability ≈ "is the model deterministic." Neither says the codes are *correct*.

## 12. Export and interoperability (`data_exporter.py`)

`ProjectExporter` renders `ProjectState` to:
- **JSON** — full state.
- **CSV** — codes, applications, memos (`memos.csv`), reasoning column (audit trail), stability.
- **Markdown** — human-readable report incl. audit-trail and memo sections.
- **QDPX** — the REFI-QDA interchange ZIP (`project.qde` XML + source files) for ATLAS.ti / NVivo. Filenames are sanitized against path traversal. Exported applications now carry verifiable span anchors (INV-1 mostly met); paraphrased quotes that couldn't be anchored were dropped upstream, so exported segments are trustworthy-where-present.

MCP export tools (`qc_export_json/markdown`) confine the `output_file` to a sandboxed exports directory; the CLI exporter keeps full path freedom for the trusted local user.

---

## Part V — Honest state, invariants, and discipline

## 13. Honest state ledger — proven / measured / planned

Categorize any capability before relying on or describing it.

**Proven (software works; verified by tests + live E2E):** both pipelines run end-to-end; stages compose; schemas validate; failures are caught and localized; **span-anchored grounding** (char offsets + hash + verification, ambiguous/unresolvable dropped — INV-1 mostly met); a **char-anchored segment universe** + **coverage** denominator (INV-8 partial); review (CLI + browser), IRR/stability, incremental recode, graph views, and JSON/CSV/Markdown/QDPX export function; 559 deterministic tests + 6 live-LLM E2E pass; ruff + docs gates green. This is **software/integration validation** — "the program does what it's built to do." It is *not* evidence the analysis is correct.

**Measured (quantified, but not validity):** **grounding rate** (D1) and **coverage** (D2 — segments with anchored evidence / total) via `verify_grounding`/`compute_coverage`/`make bench`; **LLM-pass agreement** (`project irr`) and **stability** (`project stability`) — computational consistency, not human inter-rater reliability and not correctness.

**Planned / not yet done (do not imply these exist):** any **methodological validity** evidence (blind expert ratings, gold-standard agreement, bias stratification); **tamper-evident audit substrate**; **hardened disconfirmation** (INV-2); segment universe (INV-8); claim ledger (INV-9); true theoretical sampling, per-category saturation, full axial decomposition, multi-model consensus, active learning, collaborative coding, retrieval grounding.

### 13.1 Architectural invariants (the north-star — and where the build falls short)

§13 says what *is*; this says what *must be true* for the system's outputs to be trustworthy. These are the non-negotiable correctness conditions of the target architecture — and, per the Ambition section, the **committed build spec** for the public product, not an idealized measuring stick. The north-star is stricter than the current build; several invariants are **unmet today**, stated loudly so agents do not mistake the build for the target. Until an invariant is met, the outputs it governs are *provisional*, and an agent must say so. Each UNMET invariant is a ranked work item in §18.

**Met by the current build (keep them met — do not regress):**
- **INV-A — Fail-loud inter-stage contracts.** Missing upstream data raises (`ctx.require`), never silently degrades. *Met.*
- **INV-B — Structural schema validity.** Every LLM output validates against a typed schema (constrained decode where supported, else validate-and-retry). *Met* (structural only — not interpretive validity).
- **INV-C — Provenance recorded.** Every code/application is tagged LLM- vs. human- vs. system-originated. *Met.*

**Target invariants the build does NOT yet satisfy (treat governed outputs as provisional):**
- **INV-1 — Evidentiary anchoring.** Every quoted piece of evidence must resolve to a stable anchor (`doc_id`, `start_char`/`end_char`, `quote_hash`) and fail loudly if it cannot. *Status: **MOSTLY MET**.* `qc_clean/core/grounding.py` resolves each quote to exact original-document char offsets + a sha256 span hash, robust to smart quotes / whitespace / case; a quote is anchored only if it occurs **exactly once** in the corpus — **ambiguous (>1) and unresolvable (0) quotes are dropped + `data_warning`, never misattributed**. Wired into thematic, incremental, legacy-GT, and constant-comparison paths; `verify_grounding()` / `make bench` measure the grounding rate (D1). *Remaining (why not fully MET):* (a) **`speaker` is best-effort** (constant-comparison segments only); (b) matching is **exact-normalized, not fuzzy/semantic** — a genuinely paraphrased "quote" is correctly dropped, but that is a recall cost a semantic matcher could recover; (c) constant-comparison offsets are best-effort. Quote-level evidence that *is* anchored is now verifiable; the headline misattribution risk is closed.
- **INV-2 — Source-anchored, retrieval-first disconfirmation.** Negative cases must be drawn by retrieving candidate contrary passages from the corpus *first*, then interpreting — ideally with a different model/adversarial prompt — each anchored (INV-1) and human-adjudicated **before the claim set is treated as final** (note: not "before `SynthesisStage`," which currently runs *early*, before disconfirmation — meaning synthesis claims are produced and never disconfirmed; this is the same gap as INV-6). *Status: UNMET* (same-model, memory-first pass that can launder confirmation). Disconfirmation is experimental and **not** credibility evidence.
- **INV-3 — Validity adjudication is separate from consistency.** Correctness must be estimated by human/expert adjudication on a sample of coding decisions, distinct from agreement/stability. Consistency metrics cannot detect stable error (same wrong code, high agreement). *Status: UNMET.*
- **INV-4 — Stability ≠ saturation.** Codebook-stability convergence and GT category saturation (per-property/dimension adequacy) must be separate, separately-labeled outputs; codebook convergence must never be reported as theoretical adequacy. *Status: PARTIAL* (codebook stability exists; category saturation UNMET). *Scope note:* category saturation + theoretical sampling are mandatory **only insofar as the GT path claims theory generation**; for explicitly fixed-corpus codebook/post-positivist use, their absence is a stated scope boundary (§6), not a defect — but then the output must not be called grounded theory.
- **INV-5 — Bias surfacing.** Where respondent attributes are available and ethically permissible, stratified error diagnostics must check whether coding tracks respondent identity markers rather than textual meaning. Stratification reveals disparate error rates but cannot prove *causation*; the stronger test is **counterfactual identity-cue masking/swapping** — hold the substantive text constant, vary identity markers ("single mother", "immigrant", "manager"), and check whether code assignments change. *Status: UNMET.*
- **INV-6 — Disconfirmation covers the *final* claim set.** Every output-producing stage's claims must be subject to disconfirmation — including the last one. *Status: **PARTIAL** (was over-marked MET in v3.0 — corrected here per INV-0).* `NegativeCaseStage` now runs **last** and ingests the codebook **and** the cross-interview `cross_case` memo (locked by `tests/test_pipeline_engine.py` + `tests/test_negative_case_inv6.py`). **But it does NOT challenge the other substantive outputs** — `synthesis`, `perspective_analysis`, `entities`/`entity_relationships`, `core_categories`/`theoretical_model` — nor its own `overall_assessment` (nothing runs after it). So only codebook + cross-interview claims are disconfirmed today. Fully closing this needs every final claim to be a disconfirmation target, which in turn needs a first-class claim ledger (INV-9): until then, do **not** say "all final claims survived disconfirmation."
- **INV-7 — Instruction/data separation (prompt injection is a *validity* failure, not only security).** Transcript text is untrusted *data*; the pipeline must treat it as data, never as instructions, or an injected instruction in a transcript can change codes/summaries so the output reflects the injection rather than the participant. *Status: UNMET* (no instruction/data isolation or injection tests yet).
- **INV-8 — Explicit segment universe (a defensible denominator).** The architecture must distinguish "not coded," "not examined," and "examined but judged irrelevant" — i.e., a stable registry of textual units (segment IDs) against which every coding decision (including null decisions) is recorded. *Status: **PARTIAL**.* `qc_clean/core/segmentation.py` builds a **char-anchored segment universe** (`segment_corpus`, round-trip-verified offsets, speaker-turn or paragraph), ingest populates `ProjectState.segments`, and `compute_coverage` gives a real **denominator**: coverage = segments overlapped by ≥1 anchored application / total segments (surfaced in `make bench` / `qc_grounding_report` as D2). *Remaining (the deferred fork):* this is **corpus-traversal** coverage, not exhaustive **examined-and-judged** coverage — distinguishing "examined-but-irrelevant" from "not examined" requires forcing an LLM decision on *every* segment (incl. nulls), which ~5–10×'s cost and changes the thematic method's character. That is a deliberate product decision left to the user, not a default. Application-level agreement (vs. codebook-discovery, §11) also still needs coding decisions recorded *per segment*, which the exhaustive half would provide.
- **INV-9 — First-class claim ledger.** Every substantive analytic assertion (codes, applications, perspective claims, entity relations, code relations, synthesis findings, GT propositions, negative cases) must be an explicit typed object with: source stage, claim text, scope, supporting anchors, contrary anchors, adjudication status, and revision history. *Status: UNMET* — today claims live as prose in memos and free-text fields, so the system cannot prove each final assertion has support, has faced contrary evidence, and was retained/narrowed/withdrawn. This is the object INV-6 needs to be truly closed, and the place disconfirmation and adjudication should operate.
- **INV-10 — Adjudication beyond code labels.** Human review must reach applications, claims, relationships, and negative cases — not only code objects. *Status: UNMET* (review covers approve/reject/modify/merge/split on *codes*; §10.1). A code label can be fine while its quote applications or downstream claims are wrong; marking the code human-reviewed must not launder unreviewed LLM inferences below it.
- **INV-11 — No stale higher-order outputs.** When the corpus changes (e.g. `project recode`), any downstream output not recomputed must be invalidated or flagged, never silently retained. *Status: **PARTIAL**.* `IncrementalCodingStage` appends a `data_warnings` entry naming the populated outputs it did not recompute, and that warning is now surfaced on the human + agent surfaces that matter: CLI human formatter, API JSON, JSON export, **Markdown export** (prominent block), and MCP `qc_recode`/`qc_get_synthesis`. *Remaining gaps (why PARTIAL, not MET):* (a) it is *flag*, not invalidation/auto-recompute — consumers must honor the warning; (b) some narrower surfaces (e.g. `qc_get_codebook`, graph UI) don't echo it. Locked by `tests/test_incremental_staleness_inv11.py`.

**Meta-invariant — INV-0:** the system and its agents must never assert an unmet invariant as met. If an output depends on an UNMET invariant, label it provisional and cite the invariant. (The architectural form of §14's claim discipline.)

## 14. Claim discipline — what agents may and may not assert

When writing commits, memos, reports, exports, or user-facing text about this system:

| You MAY say | You may NOT say |
|---|---|
| "Methodology-aware multi-stage pipeline for TA and GT-inspired coding" | "Full grounded theory" / "implements grounded theory" |
| "Structured output validated against schemas" | "Schema enforcement guarantees correct/valid coding" |
| "Measures LLM-pass agreement and stability" | "Inter-rater reliability" without the LLM-pass caveat; "kappa proves rigor" |
| "Quotes anchored to verifiable source spans where uniquely resolvable (ambiguous/unresolvable are dropped)" | "Every quote is grounded" (exact-match only — paraphrased quotes are dropped, not anchored; speaker best-effort) |
| "Experimental disconfirmation over the codebook + cross-interview claims" | "Negative-case analysis establishes credibility" / "all final claims were disconfirmed" (synthesis/perspective/entity/GT claims are not; INV-6) |
| "Cross-interview counts over LLM-surfaced example quotes" | "Consensus / prevalence across the corpus" (no segment-universe denominator; INV-8) |
| "Codebook-discovery agreement across passes" | "Inter-rater reliability on code application" (wrong unit; INV-8) |
| "Confidence is an ordinal self-report signal" | "Confidence is a calibrated probability of correctness" (uncalibrated) |
| Bind claims to "these N transcripts" | Generalize to a population without a stated sampling frame (corpus-boundary unstated) |
| "Software is validated (tests pass)" | "The system is validated" (unqualified — implies methodological validity) |
| "Inspectable state and provenance" | "Auditable/tamper-evident" |
| "Open-source tool integrating these capabilities" | "State of the art" / "beyond SOTA" / "first to do X" |

When unsure which column a claim is in, default to the conservative phrasing and cite the relevant §13 status or invariant.

## 15. Methodological honesty (the things most likely to bite)

- **Consistency ≠ validity.** Agreement and stability detect *inconsistency*; they cannot detect a *consistent* shared bias across passes/models. LLM coding bias can be **systematic** w.r.t. respondent characteristics (Ashwin, Chhabra & Rao, 2025), not just random — the metrics we have will not catch it. (INV-3, INV-5.)
- **Quote anchoring is mostly met now** (INV-1). Quotes resolve to verifiable char spans + hash, and the "three people said 'I felt ignored'" case is handled (ambiguous → dropped, never guessed). *Residual weaknesses:* matching is exact-normalized, so a genuinely **paraphrased** "quote" is dropped (recall cost, not a misattribution); and `speaker` is best-effort. A fuzzy/semantic matcher and segment-derived speaker are the follow-ups.
- **Disconfirmation can launder confirmation** (INV-2). Same model+prompt lineage refuting its own codes may stay inside its own assumptions. The real version needs a different model/adversarial prompt, retrieval-first search, anchored spans, and human adjudication. *Absence of a found negative case is not evidence none exists.*
- **Pseudo-replication.** Repeated LLM passes — even across model families trained on overlapping corpora — are not independent raters; panels reduce but don't remove the shared-dependency risk.
- **The denominator problem** (INV-8, now partially addressed). There is now a char-anchored **segment universe** and a **coverage** metric (segments with anchored evidence / total). But this is *traversal* coverage, not *examined-and-judged*; and cross-interview consensus/prevalence still counts over example-quote applications, so those specific counts remain salience-not-prevalence until coding decisions are recorded per segment (the exhaustive-coding fork).
- **Claims aren't first-class** (INV-9). Substantive assertions live as prose in memos/fields, so the system can't certify each one has support, faced contrary evidence, and was retained/narrowed/withdrawn. Polished prose can hide an unsupported claim.
- **Confidence is not calibrated.** `confidence`/`discovery_confidence`/`confidence_assessment` are ordinal self-reports, not empirical correctness probabilities. Do not rank or weight claims as if they were calibrated.
- **Corpus boundary is unstated.** The state model has documents but no analytic scope (who is in the corpus, why, what population/phenomenon, what exclusions). Don't let "these two transcripts say X" slide into "the population values X."
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

LLM bias may be systematic not random (INV-3/5); reliability ≠ validity; pseudo-replication; the denominator problem (INV-8); claims not first-class (INV-9); GT fidelity partial ("GT-inspired," not "full GT"); quote anchoring mostly met (INV-1; residual: exact-match recall + best-effort speaker); disconfirmation experimental and partial-coverage (INV-2/6); confidence uncalibrated; corpus boundary unstated; incremental staleness now flagged but outputs not auto-refreshed (INV-11); audit substrate not tamper-evident; methodological validity unmeasured; non-determinism inherent (we measure and report it).

## 18. Roadmap (priority order — toward the public SOTA product)

Sequencing rule: **the evaluation harness is the keystone** (it proves the SOTA claim *and* drives improvement), then the *objects* that make the guarantees true (segment universe, claim ledger), then the rigor edges — not features. Full harness design: `docs/EVALUATION_HARNESS.md`.

1. **Evaluation harness (KEYSTONE)** — *Phase 0 DONE* (`make bench`: grounding rate D1 + reliability/stability, deterministic; `qc_clean/core/bench.py`). Remaining: gold-standard corpora, blind expert ratings, agreement-vs-gold (κ/α/AC1, IoU/Hausdorff), coverage, bias stratification + counterfactual identity-cue tests, disconfirmation recall/precision, confidence calibration, baselines — built on `prompt_eval`. *Closes INV-3*, operationalizes INV-5.
2. **Span-anchored grounding** — *MOSTLY DONE* (`qc_clean/core/grounding.py`: offsets + hash + verify + unique-resolution, ambiguous/unresolvable dropped). Remaining for full INV-1: fuzzy/semantic matcher (recover paraphrased quotes) + segment-derived `speaker`.
3. **Segment universe** — *foundational half DONE* (`segmentation.py`: char-anchored registry + `ProjectState.segments` + `compute_coverage` D2). Remaining to *fully* close INV-8: **exhaustive per-segment coding decisions** (incl. nulls) so coverage becomes examined-and-judged and application-level agreement gets a real unit of analysis — this is a **cost/method fork (~5–10× LLM cost), a user decision**, not a default.
4. **First-class claim ledger** — make every substantive assertion a typed object (source, scope, supporting/contrary anchors, adjudication, revision). *Closes INV-9*; the object that lets disconfirmation (INV-6) and adjudication (INV-10) operate over *all* final claims, not selected memos.
5. **Disconfirmation + adjudication over the ledger** — extend negative-case search and human review to applications/claims/relations/negative-cases. *Closes INV-6 fully and INV-10*; hardened retrieval-first, different-model disconfirmation *closes INV-2*.
6. **Instruction/data separation + prompt-injection tests** — *closes INV-7*.
7. **True theoretical sampling + per-category saturation** — *closes INV-4* (only if the GT path claims theory generation).
8. **Corpus-boundary / scope-condition contract** — bind final claims to the actual sampling frame.
9. **Stale-output handling** — *INV-11 flagging DONE*; remaining: auto-recompute/hard invalidation on corpus mutation.
10. **Features:** multi-model consensus; active learning from review; collaborative coding; retrieval grounding.
11. **Tamper-evident audit substrate** (append-only log + export hashes + optional DB).

## 19. Prior art worth learning from

Systems an agent researching improvements should read — relevant landscape, not competitors to beat. **GT automation:** AcademiaOS (arXiv:2403.08844); LOGOS (arXiv:2509.24294 — ~80.4% schema alignment across 5 corpora). **Inductive/thematic with LLMs:** MindCoder / "Efficiency with Rigor!" (arXiv:2501.00775); HICode (EMNLP 2025); TAMA (arXiv:2503.20666); Auto-TA (arXiv:2506.23998); Thematic-LM (ACM Web Conf. 2025). **Human–AI coding & evaluation:** PaTAT (CHI 2023); LLMCode (arXiv:2504.16671 — IoU/Hausdorff researcher-AI alignment metrics worth borrowing for INV-3 evaluation). **Local-first OSS QDA with QDPX export:** AQDA (github.com/tseidl/aqda) — closest comparator on the local+export axis. **Methods caution:** Ashwin, Chhabra & Rao (2025, *Sociological Methods & Research*) on systematic LLM coding bias; a 2026 PLOS Digital Health blinded comparison (LLM ≈ human on *deductive* code application, more variable on *inductive* theme generation, with modest chance-corrected agreement). **Reporting/reliability theory to target:** COREQ, SRQR; Krippendorff's alpha; Landis & Koch.
