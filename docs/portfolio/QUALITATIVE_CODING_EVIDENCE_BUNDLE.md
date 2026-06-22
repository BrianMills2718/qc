# Qualitative Coding Evidence Bundle

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Position

Qualitative Coding is the analyst-methods counterpart to the AI-engineering
projects. It is best presented as a methodology-aware research instrument for
LLM-assisted qualitative coding, not as a generic text-labeling tool and not as
proof that an LLM can replace a qualitative researcher.

The portfolio claim is that qualitative analysis can be made more auditable by
wrapping LLM judgment in typed project state, span anchoring, explicit
coverage denominators, claim ledgers, human review surfaces, benchmark
scorecards, and strict claim discipline.

## What Is Actually Built

| Evidence area | Current artifact | Reviewer meaning |
|---------------|------------------|------------------|
| Methodology-aware pipeline | `README.md`, `CLAUDE.md`, `docs/PROJECT_THEORY_AND_GOALS.md` | The system supports thematic analysis and a grounded-theory-inspired path as ordered stages over one typed `ProjectState`. |
| Span anchoring | `docs/plans/completed/INV1_OVERNIGHT_SPRINT.md` | Quote evidence resolves to source character offsets and hashes when uniquely resolvable; ambiguous or unresolvable quotes are dropped and warned, not misattributed. |
| Segment denominator | `docs/plans/completed/INV8_SEGMENT_UNIVERSE.md` | The system has a char-anchored segment universe; exhaustive mode can record examined-and-judged coverage instead of only LLM-surfaced example quotes. |
| Claim ledger | `docs/plans/completed/INV9_CLAIM_LEDGER.md` | Substantive analytic assertions are represented as typed claim objects with support/adjudication status instead of remaining only in prose. |
| Disconfirmation scoring substrate | `docs/plans/completed/INV2_D7_DISCONFIRMATION_SCORECARD.md` | Negative-case analysis can be scored against externally supplied gold contrary-evidence anchors, but no held-out D7 benchmark has been run yet. |
| Instruction/data separation | `docs/plans/completed/INV7_INSTRUCTION_DATA_SEPARATION.md` | Transcript text is rendered as untrusted data in first-party prompt paths, with deterministic prompt-boundary tests. |
| Application-level agreement | `docs/plans/completed/IRR_APPLICATION_LEVEL.md` | Agreement can be measured over segment x code decisions in exhaustive mode, not only over discovered code names. |
| Phase 0 benchmark artifacts | `docs/plans/completed/PHASE0_BENCHMARK_ARTIFACTS.md` | `make bench` can produce versioned local scorecard packages with hashes and explicit caveats. |

## What This Advances Beyond RAND-Style Tooling

The strong story is not "the model labels qualitative data." The stronger story
is the shift from LLM-assisted coding as output generation to qualitative
analysis as a governed workflow:

| Weak framing | Stronger portfolio framing |
|--------------|----------------------------|
| LLM generates themes | LLM proposes structured claims and code applications that can be reviewed. |
| Quotes appear in summaries | Evidence is span-anchored, hashable, and dropped when not uniquely resolvable. |
| Coding is spot-checked manually | Coverage, grounding, agreement, disconfirmation, and benchmark artifacts have explicit measurement surfaces. |
| Negative cases are prompted for | Disconfirmation is routed through claim IDs and can be scored against gold anchors when supplied. |
| The tool is evaluated by vibes | The public target is a prompt_eval-backed, held-out, human-adjudicated benchmark suite. |

## Honest Claim Discipline

This project is software-validated and architecturally serious. It is not yet
methodologically validated as a public qualitative-research instrument.

Safe claims:

- methodology-aware qualitative coding pipeline;
- structured state, export, review, and audit surfaces;
- span-anchored evidence where uniquely resolvable;
- segment-universe and exhaustive-mode coverage substrate;
- claim-ledger and disconfirmation-scoring substrates;
- benchmark plan and Phase 0 scorecard packaging.

Do not claim:

- full grounded theory;
- state of the art;
- human/expert parity;
- validated social-science findings;
- negative-case analysis establishes credibility;
- prompt injection is solved;
- IRR proves methodological validity.

## Reviewer Path

1. Read `docs/PORTFOLIO_REVIEWER_GUIDE.md` for the short public framing.
2. Read this bundle to understand the evidence map and caveats.
3. Read `docs/PROJECT_THEORY_AND_GOALS.md` sections on state ledger,
   invariants, and claim discipline before repeating any capability claim.
4. Read `docs/EVALUATION_HARNESS.md` to see how methodological validity would
   be demonstrated.
5. Inspect the selected completed plan artifacts for concrete engineering
   evidence.

## Current Gaps

- No sanitized reviewer corpus is published yet.
- No held-out, human-adjudicated gold set has been run through the full
  evaluation harness.
- D7 disconfirmation scoring exists as a substrate, but no public gold-anchor
  benchmark result is counted.
- Prompt-injection checks currently include deterministic structural fixtures
  and one committed built-in live canary artifact
  (`docs/benchmarks/inv7_live_canary_2026_06_22/`); broader held-out live
  adversarial evaluation is still future work.
- GT remains grounded-theory-inspired unless a theoretical sampling and
  category-saturation protocol is completed and evaluated.

## Next High-Value Work

1. Add one sanitized corpus and a reviewer walkthrough from raw transcript to
   coded spans, claim ledger, benchmark scorecard, and Markdown/QDPX export.
2. Populate a small human-adjudicated gold set for application validity and D7
   contrary-evidence recall.
3. Run `make bench` with versioned artifact output and publish a sanitized
   scorecard package.
4. Keep every public-facing claim tied to the claim-discipline table in
   `docs/PROJECT_THEORY_AND_GOALS.md`.
