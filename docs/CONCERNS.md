# Qualitative Coding Concern Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Open Concerns

| ID | Concern | Severity | Current mitigation | Next evidence/action |
|---|---|---:|---|---|
| QC-PORT-001 | No sanitized reviewer corpus is published. | High | Existing docs clearly state that public methodological evidence is missing. | Create a small corpus with scope, run outputs, and export artifacts. |
| QC-PORT-002 | D3/D7 gold packages are substrates, not populated held-out results. | High | `docs/EVALUATION_HARNESS.md` distinguishes protocol/preflight from evidence. | Adjudicate a small code-application and contrary-evidence set. |
| QC-PORT-003 | Grounded-theory language can overclaim methodological fidelity. | High | Docs use "grounded-theory-inspired" and warn against "full GT". | Create D8 GT-fidelity protocol results before any stronger GT claim. |
| QC-PORT-004 | Prompt-boundary evidence can be mistaken for broad prompt-injection robustness. | Medium | INV-7 docs and canary READMEs caveat fixture/canary scope. | Run broader held-out adversarial fixtures under a committed protocol. |
| QC-PORT-005 | Active implementation work is in progress in API/review surfaces. | Medium | Dossier work avoids dirty active files and documents current status separately. | Let Plan #202 finish, then regenerate wiki/report surfaces. |
| QC-PORT-006 | Competitor landscape changes quickly. | Medium | Theory doc records the need to re-audit field claims. | Re-audit MAXQDA/NVivo/ATLAS.ti and recent research before public SOTA language. |
| QC-PORT-007 | The system is extensive enough that reviewers may miss the main story. | Medium | This dossier creates a short reviewer path and artifact register. | Add a single sanitized walkthrough with screenshots or export snippets. |

## Portfolio Judgment

This is valuable portfolio work if framed correctly. The high-signal story is
not "LLM does coding." It is "analyst qualitative workflow made inspectable,
reviewable, exportable, and benchmark-ready."

The repo will become much more persuasive once one corpus and one scorecard
package turn the current infrastructure into visible evidence.

