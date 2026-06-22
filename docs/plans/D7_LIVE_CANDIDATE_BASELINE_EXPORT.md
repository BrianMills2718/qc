# Plan #134: D7 Live Candidate Baseline Export

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Existing D7 retrieval export, scorecard baseline loader, and LLM handler
**Blocks:** First opt-in live D7 baseline package generation for later held-out comparison runs

---

## Gap

**Current:** D7 can score gold-dependent system disconfirmation results and
externally supplied baseline packages. The repo can export deterministic
retrieval candidate baselines and compare packages against D7 gold. It still
has no opt-in live model baseline package generator.

**Target:** Add a small live baseline exporter that:

- retrieves bounded D7 candidate passages with the existing deterministic
  retrieval helper;
- asks a configured live model, through structured output, to select candidate
  IDs that directly contradict, qualify, or complicate each target claim;
- fails loudly on hallucinated/unknown candidate IDs;
- writes a scorecard-compatible object containing `disconfirmation_baselines`;
- records model, prompt hashes, trace ID, budget, project/corpus hashes, and
  retrieval configuration;
- is reachable through script, Make, and canonical `qc_cli.py` surfaces.

**Why:** The roadmap names held-out D7 runs with live baselines as a remaining
keystone harness gap. This slice creates the first runnable live baseline
package generator without claiming held-out evidence and without requiring a
live API call for deterministic tests.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - remaining D7 live-baseline gap.
- `docs/EVALUATION_HARNESS.md` - D7 baseline and live-baseline caveats.
- `qc_clean/core/d7_retrieval.py` - retrieval package shape and scorecard
  compatibility.
- `scripts/run_d7_retrieval.py` - existing export script pattern.
- `qc_clean/core/llm/llm_handler.py` - structured LLM wrapper with
  `task`, `trace_id`, and `max_budget`.
- `qc_clean/core/disconfirmation.py` - deterministic candidate retrieval and
  exact candidate anchors.
- `scripts/bench_phase0.py` - D7 baseline package loader accepts any object
  with `disconfirmation_baselines`.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Scope And Non-Goals

This is an opt-in live **candidate-selection** baseline over bounded retrieved
source candidates. It is not an unbounded whole-corpus ChatGPT baseline, not a
held-out D7 run, not a superiority test, and not methodological-validity
evidence.

Existing D7 comparison protocol preflight currently validates retrieval
prediction packages. This plan does not generalize that preflight to the new
live-baseline package type; that can be a later lane after the package shape is
available.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `d7_live_candidate_baseline_export` | `ProjectState`, model/budget/retrieval config | scorecard-compatible `disconfirmation_baselines` package with live metadata | qualitative_coding | `make bench BASELINES=...`, `compare-d7-retrieval` without live preflight | paid LLM |
| `qc_cli_run_d7_live_baseline` | `qc_cli.py run-d7-live-baseline` argv | script exit code/stdout and optional JSON file | qualitative_coding | agents/operators using canonical CLI | paid LLM |

### Capability Validation

- [ ] Core live baseline exporter builds a package with model/trace/budget,
  prompt hashes, retrieval metadata, and `disconfirmation_baselines`.
- [ ] Core exporter fails loudly when the model returns an unknown candidate ID.
- [ ] Core exporter does not mutate `ProjectState`.
- [ ] Script writes the same JSON to stdout and `--output`.
- [ ] Make and `qc_cli.py` surfaces forward current script flags.

---

## Files Affected

- `qc_clean/core/d7_live_baseline.py` (new)
- `qc_clean/prompts/d7_live_candidate_selection.txt` (new prompt template)
- `qc_clean/prompts/__init__.py` (new)
- `scripts/run_d7_live_baseline.py` (new)
- `tests/test_d7_live_baseline.py` (new)
- `tests/test_run_d7_live_baseline_script.py` (new)
- `tests/test_qc_cli_d7_live_baseline.py` (new)
- `qc_cli.py` (modify)
- `Makefile` (modify)
- `CLAUDE.md` and `AGENTS.md` (docs/update)
- `docs/EVALUATION_HARNESS.md` (docs/update)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for the core fake-caller path, unknown-ID failure, no state
   mutation, script stdout/output parity, and CLI forwarding.
3. Implement the core live candidate-selection exporter with an injectable
   async caller and a prompt template loaded from `qc_clean/prompts`.
4. Add `scripts/run_d7_live_baseline.py`, `make run-d7-live-baseline`, and
   `qc_cli.py run-d7-live-baseline`.
5. Update docs with the new command surfaces and caveats.
6. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New/Updated Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_live_baseline.py` | `test_live_candidate_baseline_exports_selected_candidate_package` | Fake live selector produces a scorecard-compatible baseline package with selected exact anchors and metadata. |
| `tests/test_d7_live_baseline.py` | `test_live_candidate_baseline_rejects_unknown_candidate_id` | Unknown candidate IDs from the model fail loudly before output. |
| `tests/test_d7_live_baseline.py` | `test_live_candidate_baseline_does_not_mutate_project_state` | Exporting does not persist baselines or mutate source state. |
| `tests/test_run_d7_live_baseline_script.py` | `test_run_d7_live_baseline_writes_output_and_stdout` | Script boundary writes identical JSON to stdout and `--output` using a fake exporter. |
| `tests/test_run_d7_live_baseline_script.py` | `test_run_d7_live_baseline_forwards_options_to_exporter` | Script forwards model, retrieval, trace, and budget flags. |
| `tests/test_qc_cli_d7_live_baseline.py` | `test_qc_cli_run_d7_live_baseline_forwards_flags` | Canonical CLI forwards flags to the script unchanged. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py -q` | New live baseline slice. |
| `python -m pytest tests/test_d7_retrieval.py tests/test_run_d7_retrieval_script.py tests/test_qc_cli_d7_retrieval.py -q` | Existing D7 retrieval surfaces remain compatible. |
| `python -m ruff check qc_clean/core/d7_live_baseline.py scripts/run_d7_live_baseline.py tests/test_d7_live_baseline.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py qc_cli.py` | Focused lint on changed/new Python files. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `make run-d7-live-baseline` and
  `qc_cli.py run-d7-live-baseline` exist and delegate to the script.
- [ ] The exporter produces a `disconfirmation_baselines` package accepted by
  the existing Phase 0 baseline loader.
- [ ] Model-selected candidates are converted to exact D7 anchors from the
  existing retrieval candidates, not model-invented spans.
- [ ] Unknown candidate IDs fail loudly.
- [ ] Package metadata includes model, trace ID, budget, prompt hashes,
  project/corpus hashes, retrieval configuration, selected candidate count,
  and a claim-discipline note.
- [ ] Docs preserve that this is a live baseline package generator, not a
  held-out D7 result or superiority claim.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] Focused Ruff check passes.
- [ ] `make docs-check` passes.
- [ ] Full `make check` passes or any failure is documented with evidence.
- [ ] Type-check status is reported.
- [ ] Verified work is committed and pushed.

---

## Notes

This lane advances the D7 live-baseline substrate only. It intentionally avoids
running a paid live benchmark in deterministic CI and does not change the claim
discipline in `docs/PROJECT_THEORY_AND_GOALS.md`.
