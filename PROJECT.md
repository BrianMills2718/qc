# Qualitative Coding Project Dossier

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Role

Qualitative Coding is a core analyst-methods project. It turns qualitative
interview analysis into an auditable AI-assisted workflow: transcripts become a
typed project state with codebooks, span-anchored code applications, claim
ledger rows, review decisions, exports, and evaluation packages.

The strongest portfolio claim is not that an LLM can label text. The stronger
claim is that qualitative analysis can be made more inspectable by wrapping LLM
judgment in methodology-aware stages, structured state, human review, grounding
checks, coverage denominators, disconfirmation surfaces, and explicit claim
discipline.

## Current Status

This repo is active and substantial. The software and evaluation substrates are
built enough to demonstrate serious AI engineering, but the project is not yet
methodologically validated as a public qualitative-research instrument.

Safe current claims:

- thematic and grounded-theory-inspired coding pipelines over a typed
  `ProjectState`;
- span-anchored evidence where source quotes resolve uniquely;
- segment-universe and exhaustive-mode coverage surfaces;
- first-class analytic claim ledger with review and export surfaces;
- Phase 0 scorecard and protocol/preflight substrate for future D3/D7/D8/D9
  validity work;
- prompt-boundary and instruction/data-separation checks for repo-owned prompt
  paths;
- QDPX, Markdown, CSV, and JSON export paths.

Do not claim:

- full grounded theory;
- state of the art;
- human/expert parity;
- validated social-science findings;
- validated negative-case/disconfirmation performance;
- prompt-injection robustness beyond the specific fixture/canary evidence;
- methodological validity without a sanitized corpus and adjudicated benchmark.

## Reviewer Path

1. Read [README.md](README.md) for the operational overview and capability list.
2. Read [docs/PORTFOLIO_REVIEWER_GUIDE.md](docs/PORTFOLIO_REVIEWER_GUIDE.md)
   for the compact public framing.
3. Read [docs/portfolio/QUALITATIVE_CODING_EVIDENCE_BUNDLE.md](docs/portfolio/QUALITATIVE_CODING_EVIDENCE_BUNDLE.md)
   for the evidence map and caveats.
4. Read [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the project methodology
   spine.
5. Read [docs/VALIDATION.md](docs/VALIDATION.md) before using any claim about
   rigor, validity, or evaluation.
6. Read [docs/ARTIFACTS.md](docs/ARTIFACTS.md) to find the main inspectable
   artifacts.
7. Read [docs/CONCERNS.md](docs/CONCERNS.md) for unresolved risks and the next
   evidence to create.

## Why It Matters For An AI Engineer / Analyst Portfolio

This is evidence of method translation: taking a qualitative research workflow
and turning it into a governed computational system. It shows typed domain
modeling, structured LLM output, data provenance, human review, export
interoperability, evaluation design, and claim discipline around an
analyst-facing task.

It should be presented beside `process_tracing` as part of the analyst-methods
portfolio: `process_tracing` focuses on causal inference over historical
evidence, while `qualitative_coding` focuses on auditable coding and
interpretive workflow over interview-style corpora.

## Next Evidence To Create

The highest-value next portfolio work is not more generic tooling. It is
stronger evidence:

1. A sanitized reviewer corpus with a walkthrough from raw transcript to coded
   spans, claim ledger, export, and scorecard.
2. A small human-adjudicated gold package for code-application validity and D7
   contrary-evidence recall.
3. A versioned Phase 0 benchmark artifact package from that corpus.
4. A short public reviewer report that says exactly which claims are licensed
   and which remain planned.

