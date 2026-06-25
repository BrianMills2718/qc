# Qualitative Coding Artifact Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Primary Reviewer Artifacts

| Artifact | Role | Portfolio meaning |
|---|---|---|
| [PROJECT.md](../PROJECT.md) | Dossier entrypoint | Explains the project as an analyst-methods portfolio item. |
| [README.md](../README.md) | Operational overview | Shows what the system does and how to run it. |
| [docs/PORTFOLIO_REVIEWER_GUIDE.md](PORTFOLIO_REVIEWER_GUIDE.md) | Short portfolio guide | Gives the public framing and reviewer path. |
| [docs/portfolio/QUALITATIVE_CODING_EVIDENCE_BUNDLE.md](portfolio/QUALITATIVE_CODING_EVIDENCE_BUNDLE.md) | Evidence bundle | Maps built features to caveats and next evidence. |
| [docs/PROJECT_THEORY_AND_GOALS.md](PROJECT_THEORY_AND_GOALS.md) | Canonical theory and claim discipline | Prevents overclaiming and defines the long-term target. |
| [docs/EVALUATION_HARNESS.md](EVALUATION_HARNESS.md) | Evaluation design | Defines how SOTA, parity, and methodological-validity claims would be earned. |

## Methodology And Governance Artifacts

| Artifact | Role | Notes |
|---|---|---|
| [docs/METHODOLOGY.md](METHODOLOGY.md) | Methodology spine | Summarizes goals, modality, evidence-promotion rules, and failure modes. |
| [docs/LONG_TERM_EXECUTION_PLAN.md](LONG_TERM_EXECUTION_PLAN.md) | Long-term execution spine | Maps the design-plan protocol to current roadmap slices, next actions, dependency subplans, and stop conditions. |
| [docs/CAPABILITY_DEPENDENCY_GRAPH.md](CAPABILITY_DEPENDENCY_GRAPH.md) | Capability dependency graph | Orders QC, grounded-research, abductive, process-tracing, and mixed-methods workbench capabilities by dependency and success criteria. |
| [docs/VALIDATION.md](VALIDATION.md) | Validation register | Separates software evidence from methodological evidence. |
| [docs/CONCERNS.md](CONCERNS.md) | Concern register | Tracks the remaining blockers to a stronger public portfolio page. |
| [docs/adr/0001_qualitative_coding_methodology_spine.md](adr/0001_qualitative_coding_methodology_spine.md) | ADR | Records the dossier framing decision. |
| [docs/plans/ACTIVE_SPRINT.md](plans/ACTIVE_SPRINT.md) | Active sprint tracker | Shows ongoing implementation work and stop conditions. |
| [docs/plans/CLAUDE.md](plans/CLAUDE.md) | Plan index | Lists active and completed implementation records. |

## Evaluation And Evidence Artifacts

| Artifact | Evidence area | What it does and does not prove |
|---|---|---|
| [docs/plans/completed/INV1_OVERNIGHT_SPRINT.md](plans/completed/INV1_OVERNIGHT_SPRINT.md) | Span anchoring | Shows the grounding substrate. It does not prove interpretive validity. |
| [docs/plans/completed/INV8_SEGMENT_UNIVERSE.md](plans/completed/INV8_SEGMENT_UNIVERSE.md) | Segment denominator | Shows coverage accounting in exhaustive mode. It does not prove code usefulness. |
| [docs/plans/completed/INV9_CLAIM_LEDGER.md](plans/completed/INV9_CLAIM_LEDGER.md) | Claim ledger | Shows typed analytic claims and read surfaces. It does not prove claims are true. |
| [docs/plans/completed/INV2_D7_DISCONFIRMATION_SCORECARD.md](plans/completed/INV2_D7_DISCONFIRMATION_SCORECARD.md) | Disconfirmation scoring substrate | Shows how D7 can be scored when gold anchors exist. It is not a held-out D7 result. |
| [docs/plans/completed/INV7_INSTRUCTION_DATA_SEPARATION.md](plans/completed/INV7_INSTRUCTION_DATA_SEPARATION.md) | Prompt/data boundary | Shows first-party prompt-boundary controls. It does not prove prompt-injection robustness. |
| [docs/plans/completed/IRR_APPLICATION_LEVEL.md](plans/completed/IRR_APPLICATION_LEVEL.md) | Application-level agreement | Shows segment x code agreement machinery. It is consistency evidence, not validity evidence. |
| [docs/plans/completed/PHASE0_BENCHMARK_ARTIFACTS.md](plans/completed/PHASE0_BENCHMARK_ARTIFACTS.md) | Benchmark packaging | Shows reproducible scorecard packaging. It is local provenance unless populated with adjudicated evidence. |
| [docs/benchmarks/inv7_live_canary_2026_06_22/README.md](benchmarks/inv7_live_canary_2026_06_22/README.md) | INV-7 canary artifact | Shows a committed live canary. It is not broad adversarial proof. |
| [docs/benchmarks/inv7_live_canary_v2_2026_06_22/README.md](benchmarks/inv7_live_canary_v2_2026_06_22/README.md) | INV-7 v2 canary artifact | Shows broader canary coverage including prompt override surfaces. It is still not held-out robustness evidence. |

## Software Surfaces

| Surface | Main files | Reviewer meaning |
|---|---|---|
| CLI | `qc_cli.py`, `qc_clean/core/cli/` | Agent-drivable local project creation, running, review, export, and benchmark commands. |
| API | `qc_clean/plugins/api/` | Browser and JSON surfaces for review, graph inspection, and project data. |
| MCP | `qc_mcp_server.py` | Agent-facing operations over qualitative-coding projects. |
| Domain model | `qc_clean/schemas/domain.py` | The typed state contract for documents, segments, codes, claims, review decisions, and exports. |
| Evaluation core | `qc_clean/core/bench.py` and scripts under `scripts/` | Phase 0 scorecards, package validation, preflight, and artifact verification. |
| Export | `qc_clean/core/export/data_exporter.py` | JSON, CSV, Markdown, and QDPX handoff surfaces. |
| Process-tracing handoff | `qc_clean/core/process_tracing_handoff.py`, `scripts/export_process_tracing_handoff.py`, `scripts/validate_process_tracing_handoff.py` | Strict QC-side package of qualitative evidence objects. Process-tracing consumer review accepted it as a QC-side fixture/adaptor input on 2026-06-25; it is still not a runnable PT input, causal proof, or PT result. |

## Missing Portfolio Artifacts

The main missing artifacts are not more documentation. They are evidence:

- a sanitized corpus that can be published or privately shown;
- a reviewer walkthrough from transcript to claim ledger and export;
- human-adjudicated D3/D7 gold packages;
- a benchmark artifact package created from that corpus;
- a concise portfolio report that licenses only the claims supported by the
  artifact package.
