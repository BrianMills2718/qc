# Qualitative Coding Concern Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Open Concerns

| ID | Concern | Severity | Current mitigation | Next evidence/action |
|---|---|---:|---|---|
| QC-PORT-001 | No sanitized reviewer corpus is published. | High | Existing docs clearly state that public methodological evidence is missing. | Create a small corpus with scope, run outputs, and export artifacts. |
| QC-PORT-002 | D3/D7 gold packages are substrates, not populated held-out results. | High | `docs/EVALUATION_HARNESS.md` distinguishes protocol/preflight from evidence. | Adjudicate a small code-application and contrary-evidence set. |
| QC-PORT-003 | Grounded-theory language can overclaim methodological fidelity. | High | Docs use "grounded-theory-inspired" and warn against "full GT". | Create D8 GT-fidelity protocol results before any stronger GT claim. |
| QC-PORT-004 | Prompt-boundary evidence can be mistaken for broad prompt-injection robustness. | Medium | INV-7 docs and canary READMEs caveat fixture/canary scope. | Run broader held-out adversarial fixtures under a committed protocol. |
| QC-PORT-005 | Historical note: prior API/review active work could have made dossier surfaces stale. | Low | Plans through #230 were completed, checked, committed, and pushed; active sprint now points to the current checkpoint. | Keep this closed at the next concern cleanup unless new active review-surface drift appears. |
| QC-PORT-006 | Competitor landscape changes quickly. | Medium | Theory doc records the need to re-audit field claims. | Re-audit MAXQDA/NVivo/ATLAS.ti and recent research before public SOTA language. |
| QC-PORT-007 | The system is extensive enough that reviewers may miss the main story. | Medium | The dossier, artifact register, and synthetic reviewer-demo packet create a short reviewer path. | Add a sanitized or shareable walkthrough with screenshots or export snippets after the next review workflow stabilizes. |
| QC-ABD-001 | Abductive candidates are provisional hypotheses but do not yet have first-class review decisions. | High | Docs and surfaces label them as provisional, not causal proof. | Plan #232 should add CLI/API/manager review semantics before process-tracing handoff. |
| QC-ABD-002 | Abductive candidate quality thresholds are exploratory and should not be frozen prematurely. | Medium | `docs/LONG_TERM_EXECUTION_PLAN.md` treats candidate quality as a readout/rubric dependency, not a fixed proof threshold. | Use reviewer packets and later adjudication rubrics to discover stable quality dimensions. |
| QC-WB-001 | Future `mixed_methods_workbench` / `process_tracing` alignment can drift if QC exports untyped JSON. | High | `CLAUDE.md` and the long-term plan keep process-tracing inference outside this repo. | Plan #233 should create a versioned typed handoff package and request process-tracing consumer review. |

## Portfolio Judgment

This is valuable portfolio work if framed correctly. The high-signal story is
not "LLM does coding." It is "analyst qualitative workflow made inspectable,
reviewable, exportable, and benchmark-ready."

The repo will become much more persuasive once one corpus and one scorecard
package turn the current infrastructure into visible evidence.
