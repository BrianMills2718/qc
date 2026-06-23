# Plan #206: Reviewer Demo Run Packet

**Status:** Active
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Brian review handoff, portfolio reviewer walkthrough

---

## Gap

The repo has many verified implementation slices, but the portfolio reviewer
guide still says the project lacks a sanitized corpus and reviewer walkthrough.
That means Brian cannot yet review a concrete run/output packet without either
using private data, trusting prior conversation, or manually assembling state.

Current runnable surfaces also default to the user-level project store
(`~/.qc_projects`), which is inconvenient for an isolated review demo. A review
packet should be generated into a local output directory, then viewed through
the same CLI/API/browser surfaces without mutating normal project state.

## Target

Add a deterministic reviewer-demo runner that creates an isolated, sanitized
project packet and writes reviewable artifacts:

- fixture transcripts and project state in an output-local project store;
- Markdown and JSON exports;
- claim-ledger, review, and graph/API snapshots;
- a Phase 0 structural scorecard artifact package;
- a README/walkthrough with exact commands for local review;
- a self-review note that states what the packet proves and does not prove.

This is a software/demo readiness slice. It must not claim live LLM semantic
validity, expert adjudication, held-out D3/D7 validity, methodological
validity, or SOTA evidence.

## References Reviewed

- `docs/PORTFOLIO_REVIEWER_GUIDE.md` - current reviewer path and caveat that a
  sanitized corpus/walkthrough is missing.
- `README.md` - local run, export, review UI, and graph UI commands.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and invariant caveats.
- `docs/EVALUATION_HARNESS.md` - Phase 0 scorecard framing and non-evidentiary
  limits when no adjudicated gold is supplied.
- `qc_clean/core/persistence/project_store.py` - default project-store
  behavior.
- `qc_clean/plugins/api/api_server.py` - API/browser review and graph surfaces.
- `scripts/bench_phase0.py` - existing structural scorecard entrypoint.
- `qc_clean/core/export/data_exporter.py` - existing export implementation.
- Memory context:
  `agent-memory recall 'active decisions qualitative_coding reviewable demo output plans' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only an
  unrelated `llm_client` write claim.

## Research Basis For This Slice

No external research is needed. This is deterministic packaging and review
workflow work over existing local surfaces.

## Capabilities

This plan creates a project-local demo/walkthrough capability:

| Capability | Input | Output | Consumers | Cost |
|------------|-------|--------|-----------|------|
| Reviewer demo packet generation | optional output directory | isolated project store, exports, API snapshots, scorecard artifact, README | Brian, future reviewers, agents | free / no LLM calls |

## Files Affected

- `qc_clean/core/persistence/project_store.py` (modify)
- `scripts/build_reviewer_demo.py` (add)
- `tests/test_project_store.py` (modify)
- `tests/test_reviewer_demo.py` (add)
- `Makefile` (modify)
- `README.md` or `docs/PORTFOLIO_REVIEWER_GUIDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/REVIEWER_DEMO_RUN_PACKET.md` (create, then move to completed)

## Plan

1. Add focused tests for a `QC_PROJECTS_DIR` environment override on
   `ProjectStore()` while preserving explicit `projects_dir` precedence.
2. Add focused tests for the reviewer-demo runner:
   - it writes an isolated project store and state file;
   - it writes Markdown/JSON exports;
   - it writes claim/review/API snapshots;
   - it writes a Phase 0 scorecard artifact and README;
   - all artifacts contain honest caveats and no live-LLM/evidence overclaims.
3. Implement the `QC_PROJECTS_DIR` override in `ProjectStore`.
4. Implement `scripts/build_reviewer_demo.py` with deterministic synthetic
   transcripts and hand-authored domain objects that exercise span anchors,
   segment decisions, claim ledger, contrary evidence, review rows, graph rows,
   export, and scorecard surfaces.
5. Add `make reviewer-demo OUTPUT=...` as the agent/human entrypoint.
6. Update docs so the reviewer path points to the demo packet, with caveats.
7. Run the demo locally and inspect the generated output before declaring it
   ready for Brian review.

## Required Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_project_store.py` | `test_default_store_uses_qc_projects_dir_env` | `ProjectStore()` honors an isolated project-store environment override. |
| `tests/test_project_store.py` | `test_explicit_projects_dir_overrides_env` | Explicit `projects_dir` still wins over the environment. |
| `tests/test_reviewer_demo.py` | `test_build_reviewer_demo_writes_packet` | The demo runner writes the expected packet artifacts and caveats. |
| `tests/test_reviewer_demo.py` | `test_reviewer_demo_project_loads_from_env_store` | The generated project can be loaded by normal `ProjectStore()` when `QC_PROJECTS_DIR` points at the packet store. |

## Existing Tests (Must Pass)

| Command | Why |
|---------|-----|
| `python -m pytest tests/test_project_store.py tests/test_reviewer_demo.py -q` | Focused store/demo coverage. |
| `python -m ruff check qc_clean/core/persistence/project_store.py scripts/build_reviewer_demo.py tests/test_project_store.py tests/test_reviewer_demo.py` | Focused lint. |
| `make reviewer-demo OUTPUT=test_output/reviewer_demo` | Prove the actual packet generator runs. |
| `make docs-check` | Plan/docs consistency and generated-agent sync. |
| `git diff --check` | Whitespace safety. |
| `make check` | Full deterministic gate if practical. |

## Acceptance Criteria

Feature-level criteria:

- [x] A reviewer can run one command to generate the local demo packet.
- [x] The packet is written under an isolated output directory and does not
  mutate the default project store unless the user explicitly points the
  environment there.
- [x] The packet includes fixture transcripts, project JSON, Markdown and JSON
  exports, claim-ledger snapshots, review/API snapshots, and a Phase 0
  structural scorecard artifact.
- [x] The packet README includes exact commands for CLI inspection and browser
  review using `QC_PROJECTS_DIR=<packet>/projects`.
- [x] The packet self-review explicitly states this is deterministic software
  demonstration output, not live LLM semantic validity, expert adjudication,
  held-out benchmark evidence, methodological validity, or SOTA evidence.
- [x] I have run the packet generator myself and inspected representative
  generated outputs before asking Brian to review.

Process criteria:

- [x] Required focused tests pass.
- [x] Focused Ruff passes.
- [x] `make reviewer-demo OUTPUT=test_output/reviewer_demo` passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes or any failure is documented with evidence.
- [ ] Verified work is committed and pushed.

## Implementation Notes

- `ProjectStore()` now honors `QC_PROJECTS_DIR` when no explicit
  `projects_dir` is supplied; explicit constructor paths still take precedence.
- `scripts/build_reviewer_demo.py` builds a deterministic, synthetic,
  LLM-free packet with fixture transcripts, an isolated project store, exports,
  API/review/graph snapshots, a Phase 0 scorecard, a versioned scorecard
  artifact, and README/self-review files.
- `make reviewer-demo OUTPUT=test_output/reviewer_demo` is the canonical
  local entrypoint. The generated packet includes exact `QC_PROJECTS_DIR=...`
  CLI and browser commands.
- Self-run inspection covered generated README, self-review, Markdown export,
  CLI project show/claims, API snapshots, Phase 0 scorecard caveats, export
  rerun, HTTP review/graph page loads, JSON claim/negative-case routes, and a
  headless browser render of `/review/reviewer-demo`.

## Verification

- TDD red:
  `python -m pytest tests/test_project_store.py tests/test_reviewer_demo.py -q`
  initially failed because `scripts/build_reviewer_demo.py` did not exist and
  `ProjectStore()` did not honor the planned env override.
- Focused tests:
  `python -m pytest tests/test_project_store.py tests/test_reviewer_demo.py -q`
  (`16 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/core/persistence/project_store.py scripts/build_reviewer_demo.py tests/test_project_store.py tests/test_reviewer_demo.py`.
- Demo run:
  `make reviewer-demo OUTPUT=test_output/reviewer_demo`.
- CLI self-check:
  `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py project show reviewer-demo`
  and
  `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py project claims reviewer-demo --show-scope --show-anchors --limit 2`.
- Export self-check:
  `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py project export reviewer-demo --format markdown --output-file test_output/reviewer_demo/exports/rerun-report.md`.
- Browser/API self-check:
  `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python start_server.py`;
  `curl` returned `200` for `/review/reviewer-demo` and
  `/graph/reviewer-demo`; JSON claim and negative-case routes returned expected
  anchored payloads; headless browser render reported title `Code Review` and
  heading `Reviewer Demo: Shift Coordination`.
- Docs gate: `make docs-check`.
- Whitespace gate: `git diff --check`.
- Full gate: `make check` (`1286 passed, 1 skipped, 8 deselected`; Ruff/docs
  passed; type check not configured).

## Open Questions

- [ ] Should the final Brian review include a live LLM run after this packet? —
  Status: DEFERRED | Reason: the deterministic packet is the first readiness
  gate; live runs require API credentials, cost awareness, and separate
  evaluation framing.

## Notes

The demo runner may construct deterministic domain objects directly. That is
acceptable for this slice because the goal is reviewable software surface
readiness, not proving the LLM pipeline produces valid interpretations.
