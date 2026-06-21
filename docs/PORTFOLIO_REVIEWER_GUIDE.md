# Qualitative Coding Portfolio Reviewer Guide

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Claim

This project should be presented as computational social-science infrastructure for rigorous qualitative coding, not as an older RAND-style labeling tool. The strongest claim is that LLM assistance can be wrapped in review, span anchoring, stability checks, IRR-style evaluation, and explicit claim discipline.

## What Makes It Different

| Older qualitative-analysis tooling | Portfolio framing for this project |
|-----------------------------------|------------------------------------|
| Produces codes or summaries | Produces reviewable coded spans with project state |
| Treats LLM output as the result | Treats LLM output as a candidate requiring evaluation |
| Relies on manual spot checks | Plans stability, IRR, and benchmark harnesses |
| Optimizes throughput | Optimizes interpretive discipline and traceability |

## Reviewer Path

1. Read `README.md` for the capability list and honest status.
2. Read `docs/PROJECT_THEORY_AND_GOALS.md` for the methodological claim discipline.
3. Read `docs/EVALUATION_HARNESS.md` for the SOTA evaluation plan.

## Current Use In The Portfolio

This is analyst-facing evidence of method translation: turning qualitative research practice into structured artifacts that an agent can assist with and a human can audit. It is not ready to stand alone as proof of methodological validity without a sanitized corpus and reviewer walkthrough.

## Caveat

Do not overclaim that the system has validated social-science findings. The validated claim is software and workflow design; methodological validity still depends on corpus selection, human review, and evaluation evidence.
