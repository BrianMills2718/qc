# Qualitative Coding System — Theory, Goals, and Honest State

**An orientation document for coding agents working on this project.**

*Version 2.0 — 2026-06-19*

> **Purpose & audience.** This is the single canonical statement of *why this
> project exists, the theory it implements, and the honest state of what is
> built*. It is written for the coding agents (and humans) who work on this
> repository, not for external publication. It complements `CLAUDE.md` (which is
> operational — commands, file map, architecture detail) and `AGENTS.md` (its
> mirror). When the two disagree about *current capability*, trust the code and
> `CLAUDE.md`; this document is for *intent, theory, and the proven-vs-planned
> ledger*.
>
> **How to use it.** Read §6 (state ledger) and §7 (claim discipline) before you
> describe the system in any commit message, memo, report, or user-facing text.
> Those two sections exist specifically to stop agents from overclaiming.

---

## 1. What this project is, in one paragraph

LLM-powered qualitative coding of interview transcripts. It treats the LLM as the **engine of a methodology-aware pipeline** — not as a chat sidebar bolted onto manual coding — with the human as reviewer and director. It runs two methodologies (thematic analysis and a grounded-theory-inspired pipeline) as ordered, inspectable stages over a single typed state object, produces structured output validated against Pydantic schemas, keeps a human-in-the-loop review loop, measures its own coding consistency, and exports to the standard QDA interchange format (QDPX). The bet is that good qualitative analysis is neither pure-human (slow, inconsistently documented) nor pure-LLM (fast but unfalsifiable), but a disciplined collaboration: **programmatic code guarantees *processing* coverage (every segment is traversed and submitted — not that every relevant meaning is captured), the LLM supplies semantic judgment, the human supplies direction and final authority.** (The distinction matters: mechanical traversal is not analytic coverage; the code cannot know it captured all meanings.)

*This paragraph states intent and design, not demonstrated maturity. "Measures its own consistency" is not "is correct"; the present build does not yet meet several of its own correctness conditions. See §6 (what is proven vs. measured vs. planned) and §6.1 (the architectural invariants and where the build falls short) before describing the system as methodologically validated.*

## 2. Why it exists (the gap it targets)

Three things separate "an LLM can suggest codes" from "an LLM can do defensible qualitative analysis", and the project is organized around all three:

1. **Methodology is a process, not a prompt.** Grounded theory is constant comparison → axial → selective → integration, with theoretical sampling and saturation. Thematic analysis is hierarchy + cross-case synthesis + disconfirmation. A one-shot "find the themes" call is autocoding, not method. We encode the *stages*.
2. **Rigor needs machinery.** Reviewers of qualitative work expect agreement evidence, audit trails, disconfirmation, and saturation. LLM output is non-deterministic and can be *systematically* biased. So we build the consistency/stability/provenance/memo machinery — the **scaffold** rigor requires. (Building the scaffold is not the same as having *demonstrated* rigor; see §6.)
3. **Trust must be engineered.** A research instrument must fail loudly, log provenance, and let a human intervene — otherwise fluent-but-wrong output is camouflaged. This is the fail-loud, observability, and review design.

## 3. The methodology model (theory the code implements)

Two pipelines, each a fixed ordered sequence of stages over `ProjectState`.

**Thematic / default (7 stages):** Ingest → Thematic Coding → Perspective Analysis → Relationship Mapping → Synthesis → Negative Case *(experimental — see §6.1/§8)* → Cross-Interview. Produces a hierarchical codebook (codes with definitions, semantic criteria, quotes, mention counts, confidence), per-speaker perspective maps, an entity/relationship graph, a synthesis, an (experimental) disconfirmation pass, and automatic cross-document analysis for multi-interview corpora. Note: the codebook's quotes are *currently* attached by brittle substring matching (INV-1, §6.1) — treat quote-level evidence as provisional until span anchoring lands.

**Grounded-theory-*inspired* (7 stages):** Ingest → Constant Comparison Coding → Axial Coding → Selective Coding → Theory Integration → Negative Case *(experimental)* → Cross-Interview. Constant comparison codes each segment against an evolving codebook with a **codebook-stability** saturation check per pass — this is *codebook convergence*, **not** grounded-theory *category saturation* (per-property/dimension adequacy), which is unmet (INV-4, §6.1). Do not report codebook stability as theoretical adequacy. Axial finds category relationships; selective finds the core category; integration builds a theoretical model.

**Why "GT-*inspired*", not "full GT" — agents must respect this distinction.** The pipeline performs the *visible procedural steps* of GT (procedural mimicry) but does **not** yet implement GT's core epistemic logic (methodological fidelity). Specifically missing: *theoretical sampling* (collecting new data to develop weak categories), *category-level saturation* (per-property/dimension, not just codebook stability), *analytic memoing* that builds conceptual relations (current memos lean toward summary logging), full *axial decomposition* (causal vs. context vs. intervening conditions), and *reflexivity*. **Do not describe the system as doing "full grounded theory."**

**Which qualitative tradition it fits.** The emphasis on agreement metrics, structured output, and codebook stability fits **codebook / post-positivist** qualitative analysis (codebook thematic analysis, framework analysis). It is a poor fit for **reflexive thematic analysis** (Braun & Clarke — treats coder subjectivity as a resource, rejects inter-coder agreement as a quality criterion) and **constructivist grounded theory** (Charmaz — foregrounds the researcher's standpoint), *unless* a human fully drives interpretation and the LLM is used only as an assistant. Don't apply the automated agreement machinery to a reflexive study and call it appropriate.

## 4. Design principles (operating constraints — follow these when you build)

- **LLM-first, schema-constrained.** Every semantic step returns a Pydantic model with a description on every field. Schema constraint buys *regularity, parseability, and failure detection* — **not** interpretive validity. It guarantees a `confidence` field exists; it does not guarantee the quote is real, the code is useful, or the score is calibrated. All LLM-facing list/dict fields must default to empty (LLMs omit fields); this is locked by `tests/test_schema_robustness.py`.
- **Fail loud, never silently degrade.** Inter-stage dependencies use `ctx.require(...)`, which raises naming the missing field and stage. No `except: pass`. This is the most valuable property in the codebase — preserve it.
- **Single typed state.** All state is one `ProjectState` JSON model. Good for reproducibility/portability; *not* yet a tamper-evident audit substrate (no immutable log/hashes — roadmap).
- **Human-in-the-loop.** `ReviewManager` does approve/reject/modify/merge/split; every code carries provenance (LLM vs. human).
- **Maximum observability.** Every LLM call logs model/schema/prompt/tokens/latency/cost via `llm_client`. Query the observability DB for real costs; never estimate.

## 5. Architecture in brief

Stage-based pipeline (`AnalysisPipeline`) over `ProjectState`, assembled by `create_pipeline(methodology)`, configured by a typed `PipelineContext` (`extra="forbid"`). `LLMHandler` is a thin adapter over the shared `llm_client`. LLM-output schemas → domain model via the single tested seam in `adapters.py`. Surfaces: CLI, FastAPI server, MCP server, browser review UI, Cytoscape graph views. **Full detail lives in `CLAUDE.md` — don't duplicate it here.**

**Schema enforcement is provider-dependent — state it accurately.** `llm_client` uses three tiers: (1) GPT-5-class → Responses API native structured output (constrained decoding); (2) providers with native `response_format` json_schema → decode-time structural enforcement; (3) everything else (incl. many local models) → **instructor** post-hoc: parse, validate, re-ask on failure. Plus `litellm.enable_json_schema_validation` for post-generation validation. So: "structural validity is enforced — by constrained decoding where supported, otherwise validate-and-retry." Value-level constraints (ranges, non-empty, patterns) are never decode-time enforced anywhere.

## 6. Honest state ledger — proven / measured / planned

This is the section that keeps agents accurate. Categorize any capability before relying on or describing it.

**Proven (software works; verified by tests + live E2E):**
- Both pipelines run end-to-end against real transcripts; stages compose; schemas validate; failures are caught and localized.
- Human review (CLI + browser), IRR/stability commands, incremental recode, graph views, and JSON/CSV/Markdown/QDPX export all function.
- 527 deterministic tests + 6 live-LLM E2E tests pass; ruff + docs gates green.
- This is **software/integration validation**, i.e., "the program does what it's built to do." It is *not* evidence the analysis is correct.

**Measured (we quantify it, but it is not validity):**
- **LLM-pass agreement** (`project irr`): percent agreement, Cohen's/Fleiss' kappa across passes/models. This is *computational consistency*, not human inter-rater reliability — repeated LLM passes are not independent raters (pseudo-replication). Report it as consistency, never as proof of correctness.
- **Stability** (`project stability`): per-code stable/moderate/unstable across identical runs — quantifies the model's own non-determinism.

**Planned / not yet done (do not imply these exist):**
- Any **methodological validity** evidence (grounding rate, blind expert ratings, gold-standard agreement, bias stratification). None measured yet.
- **Span-anchored quote grounding** (see §8). Current attribution is brittle substring matching.
- **Tamper-evident audit substrate** (immutable event log, content/prompt/model hashes, replay).
- **Hardened disconfirmation** (the current negative-case pass is experimental; see §8).
- True theoretical sampling, per-category saturation, full axial decomposition, multi-model consensus, active learning, collaborative coding, retrieval grounding.

### 6.1 Architectural invariants (the north-star — and where the build falls short)

The §6 ledger says what *is*; this says what *must be true* for the system's outputs to be trustworthy. These are the non-negotiable correctness conditions of the target architecture — the north-star is stricter than the current build. Several are **unmet today**; that is stated loudly so agents do not mistake the build for the target. The point of listing them as invariants (not roadmap) is that until an invariant is met, the outputs it governs are *provisional*, and an agent must say so.

**Met by the current build (keep them met — do not regress):**
- **INV-A — Fail-loud inter-stage contracts.** Missing upstream data raises (`ctx.require`), never silently degrades. *Met.*
- **INV-B — Structural schema validity.** Every LLM output validates against a typed schema (constrained decode where supported, else validate-and-retry). *Met* (structural only — not interpretive validity).
- **INV-C — Provenance recorded.** Every code is tagged LLM- vs. human-originated. *Met.*

**Target invariants the build does NOT yet satisfy (treat governed outputs as provisional):**
- **INV-1 — Evidentiary anchoring.** Every quoted piece of evidence must resolve to a stable anchor: `{document id, speaker id, turn/char offsets, quote hash}`, and must fail loudly if it cannot. *Status: UNMET* (substring matching). **Until met, all quote-level evidence — in codebooks, negative cases, synthesis, and QDPX export — may be misattributed to the wrong speaker/interview/context and must be labeled provisional.** This is the foundational invariant; most others depend on it.
- **INV-2 — Source-anchored, retrieval-first disconfirmation.** Negative cases must be drawn by retrieving candidate contradictory passages from the corpus *first*, then interpreting them — ideally with a different model/adversarial prompt — each anchored (INV-1) and human-adjudicated before synthesis. *Status: UNMET* (same-model, memory-first pass that can launder confirmation). Until met, disconfirmation is experimental and is **not** credibility evidence.
- **INV-3 — Validity adjudication is separate from consistency.** Correctness must be estimated by human/expert adjudication on a sample of coding decisions, as a distinct layer from agreement/stability. Consistency metrics cannot detect stable error (same wrong code, high agreement). *Status: UNMET* (only consistency is measured).
- **INV-4 — Stability ≠ saturation.** Codebook-stability convergence and grounded-theory category saturation (per-property/dimension adequacy) must be separate, separately-labeled outputs; codebook convergence must never be reported as theoretical adequacy. *Status: PARTIAL* (codebook stability exists; category saturation UNMET). *Scope note:* category saturation + theoretical sampling are mandatory **only insofar as the GT path claims theory generation**; for explicitly fixed-corpus codebook/post-positivist use, their absence is a stated scope boundary (§3), not a defect — but then the output must not be called grounded theory.
- **INV-5 — Bias surfacing.** Where respondent attributes are available and ethically permissible, stratified error diagnostics must check whether coding tracks respondent identity markers rather than textual meaning. *Status: UNMET.*
- **INV-6 — Disconfirmation covers the *final* claim set.** Every output-producing stage's claims must be subject to disconfirmation — including the last one. *Status: UNMET, verified in `pipeline_factory.py`:* all pipelines run `NegativeCaseStage` *before* `CrossInterviewStage`, so cross-interview consensus/divergence claims are generated *after* the disconfirmation pass and are never disconfirmed. Closing this is a code change (move/duplicate disconfirmation after cross-interview, or run a final disconfirmation over the whole claim set), not just a doc edit — flagged for the build.
- **INV-7 — Instruction/data separation (prompt injection is a *validity* failure, not only a security one).** Transcript text is untrusted *data*; the pipeline must treat it as data, never as instructions, or an injected instruction in a transcript can change codes/summaries so the output reflects the injection rather than the participant. *Status: UNMET* (no instruction/data isolation or injection tests yet). This is why §9's prompt-injection item is also an inferential-validity item, not just security.

**Meta-invariant — INV-0:** the system and its agents must never assert an unmet invariant as met. If an output depends on an UNMET invariant, label it provisional and cite the invariant. (This is the architectural form of §7's claim discipline.)

## 7. Claim discipline — what agents may and may not assert

When writing commits, memos, reports, exports, or user-facing text about this system:

| You MAY say | You may NOT say |
|---|---|
| "Methodology-aware multi-stage pipeline for TA and GT-inspired coding" | "Full grounded theory" / "implements grounded theory" |
| "Structured output validated against schemas" | "Schema enforcement guarantees correct/valid coding" |
| "Measures LLM-pass agreement and stability" | "Inter-rater reliability" without the LLM-pass caveat; "kappa proves rigor" |
| "Quotes attributed to source (currently substring-based, brittle)" | "Quotes are reliably grounded to exact source spans" |
| "Includes an experimental disconfirmation pass" | "Negative-case analysis establishes credibility" |
| "Software is validated (tests pass)" | "The system is validated" (unqualified — implies methodological validity) |
| "Inspectable state and provenance" | "Auditable/tamper-evident" |
| "Open-source tool integrating these capabilities" | "State of the art" / "beyond SOTA" / "first to do X" |

When unsure which column a claim is in, default to the conservative phrasing and link the relevant §6 status.

## 8. Methodological honesty (the things most likely to bite)

- **Consistency ≠ validity.** Agreement and stability detect *inconsistency*; they cannot detect a *consistent* shared bias across passes/models. LLM coding bias can be **systematic** with respect to respondent characteristics (Ashwin, Chhabra & Rao, 2025), not just random — the metrics we have will not catch it.
- **Quote attribution is the highest-priority technical weakness.** Substring matching proves a phrase exists *somewhere*, not which speaker/interview/turn produced it. If three participants say "I felt ignored," the evidentiary chain breaks. This undermines confirmability, disconfirmation evidence, and QDPX integrity. Span anchoring (doc + speaker + char/turn offsets + quote hash, every quote required to resolve) is the top roadmap item.
- **Disconfirmation can launder confirmation.** Asking the same model+prompt lineage to refute its own codes risks "appearing to challenge itself while staying inside its own assumptions." Treat the current pass as experimental; the real version needs a different model/adversarial prompt, retrieval-first search, mandatory anchored spans, and human adjudication.
- **Schema constraint is not validity** (see §4).

## 9. Security & deployment posture

The system is a **local research tool**, loopback-bound and unauthenticated; hardened against arbitrary-write (MCP export sandbox) and stored XSS, but not a multi-tenant deployment. Transcripts often contain sensitive/PII data. **Before running on anything real:** prefer local models (Ollama/vLLM) so data never leaves the machine; treat transcripts as *untrusted input* (prompt-injection risk — this is also a **validity** invariant, INV-7 §6.1, because an injected instruction corrupts the analysis itself, not just the system); know that PII de-identification, log redaction, local-only enforcement, and right-to-delete cascades are **not yet implemented**. Don't run it on regulated/clinical/protected data as-is without those controls and an IRB/DPIA assessment. Safe today: synthetic, demo, public-domain, or de-identified low-risk text.

## 10. Roadmap (priority order)

Ordered to close the unmet invariants in §6.1 first (an invariant outranks a feature).

1. Span-anchored grounding — **closes INV-1**, the precondition for trustworthy evidence and the grounding metric.
2. Methodological evaluation — **closes INV-3/INV-5**: grounding rate, blind expert ratings, gold-standard comparison, stability CIs, bias stratification, and a human-in-the-loop anchoring-bias study (LLM-first vs blind-human-first). Moves the system from "software works" to "analysis is trustworthy."
3. Hardened, retrieval-first disconfirmation — **closes INV-2** (depends on INV-1); while here, also reorder so disconfirmation covers cross-interview output — **closes INV-6** (cheap: move/duplicate the stage).
4. Instruction/data separation + prompt-injection tests — **closes INV-7** (validity safeguard, not just security).
5. True theoretical sampling + per-category saturation — **closes INV-4** (GT fidelity; only if the GT path claims theory generation).
6. Multi-model consensus; active learning from review; collaborative coding; retrieval grounding (features, not invariants).
7. Tamper-evident audit substrate (append-only log + export hashes + optional DB).

## 11. Prior art worth learning from

Systems an agent researching improvements should read — not competitors to beat, just the relevant landscape. Grounded-theory automation: AcademiaOS (arXiv:2403.08844), LOGOS (arXiv:2509.24294, ~80% schema alignment across 5 corpora). Inductive/thematic with LLMs: MindCoder / "Efficiency with Rigor!" (arXiv:2501.00775), HICode (EMNLP 2025), TAMA (arXiv:2503.20666), Auto-TA (arXiv:2506.23998), Thematic-LM (ACM Web Conf. 2025). Human-AI coding & evaluation: PaTAT (CHI 2023), LLMCode (arXiv:2504.16671 — IoU/Hausdorff researcher-AI alignment metrics worth borrowing). Local-first OSS QDA with QDPX export: AQDA (github.com/tseidl/aqda). Methods caution: Ashwin, Chhabra & Rao (2025, *Sociological Methods & Research*) on systematic LLM coding bias; a 2026 PLOS Digital Health blinded comparison found LLM≈human on *deductive* code application but more variable on *inductive* theme generation. Reporting standards to target for the eventual methods appendix: COREQ, SRQR; reliability theory: Krippendorff's alpha, Landis & Koch.
