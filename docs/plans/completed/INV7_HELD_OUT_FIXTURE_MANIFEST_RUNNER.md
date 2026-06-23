# Plan #209: INV-7 Held-Out Fixture Manifest Runner

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** broader held-out/adversarial live INV-7 evaluation beyond built-in canaries

---

## Outcome

The INV-7 live fixture runner now accepts external schema_version=1 fixture
manifests through script, Make, and `qc_cli.py` surfaces:

- `scripts/run_inv7_live_fixtures.py --fixtures manifest.json`
- `make run-inv7-live-fixtures FIXTURES=manifest.json ...`
- `qc_cli.py run-inv7-live-fixtures --fixtures manifest.json ...`

The manifest contract carries result package ID, split, fixture-set ID/version,
prompt-frozen status, contamination-check status, pre-run registration status,
optional note, and live fixtures. Held-out manifests fail loudly unless
`prompt_frozen`, `contamination_checked`, and `registered_before_run` are all
true. Runner output preserves manifest metadata in the strict INV-7 result
package and records exact SHA-256 hashes for every fixture prompt.

Implementation commit: `7d066035`
(`[Plan: INV7_HELDOUT] Add live fixture manifest runner`).

Verification:

- `python -m pytest tests/test_inv7_fixture_runner.py tests/test_qc_cli_inv7_fixtures.py -q`
  -> 18 passed.
- `python -m pytest tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q`
  -> 23 passed, 42 deselected.
- `python -m ruff check qc_clean/core/inv7_fixtures.py scripts/run_inv7_live_fixtures.py qc_cli.py tests/test_inv7_fixture_runner.py tests/test_qc_cli_inv7_fixtures.py`
  -> passed.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> 1293 passed, 1 skipped, 8 deselected; Ruff and docs gates
  passed.

This is execution/provenance infrastructure only. It does not create held-out
results, prompt-injection robustness evidence, model-obedience proof,
methodological-validity evidence, or SOTA evidence.

---

## Gap

**Current:** `run_inv7_live_fixtures_async()` can run custom fixture objects
internally, but the agent-facing CLI/Make surfaces can only run the built-in
canary set. A broader held-out/adversarial INV-7 evaluation therefore still
requires code edits or ad hoc Python to inject fixtures, which is not an
agent-drivable benchmark workflow.

**Target:** Add a versioned external INV-7 live fixture manifest contract and
wire it through `scripts/run_inv7_live_fixtures.py`, `make
run-inv7-live-fixtures`, and `qc_cli.py run-inv7-live-fixtures`. The runner
must preserve strict package output, exact prompt hashes, model/trace/budget
metadata, and split/provenance fields from the manifest so `held_out` fixture
sets can be pre-registered and then scored through the existing
`INV7_PROTOCOL` preflight guard.

**Why:** This is the next prerequisite for real INV-7 held-out evaluation. It
does not create held-out results by itself; it makes such runs executable,
repeatable, and governable without changing code for each fixture set.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - ranked roadmap names broader
  held-out live injection evaluation as the remaining INV-7 gap.
- `docs/EVALUATION_HARNESS.md` - INV-7 package/scorecard/protocol caveats and
  current canary status.
- `docs/plans/ACTIVE_SPRINT.md` - current sprint mission and no active plan.
- `docs/plans/completed/INV7_CUSTOM_PROMPT_OVERRIDE_FIXTURES.md` - fixture-set
  expansion to built-in version `2`.
- `docs/plans/completed/INV7_COMMITTED_LIVE_CANARY_V2.md` - committed canary
  artifact workflow and claim limits.
- `qc_clean/core/inv7_fixtures.py` - live fixture models, built-in fixture set,
  custom fixture hook, and output package fields.
- `qc_clean/core/inv7_live_protocol.py` - held-out protocol requirements:
  prompt frozen, contamination checked, and registered before run.
- `qc_clean/core/inv7_live_preflight.py` - protocol/result package cross-checks.
- `scripts/run_inv7_live_fixtures.py`, `Makefile`, and `qc_cli.py` - current
  live runner entrypoints.
- `tests/test_inv7_fixture_runner.py`, `tests/test_qc_cli_inv7_fixtures.py`,
  `tests/test_inv7_live_protocol.py`, and `tests/test_inv7_live_preflight.py`
  - current INV-7 runner/CLI/protocol coverage.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` - no
  relevant in-flight decision found.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local
workflow gap over existing INV-7 protocol and package contracts.

---

## Capabilities

Internal project capability only; no cross-project tool or boundary registry
entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_inv7_live_fixtures` with external manifest | INV-7 live fixture manifest JSON | schema_version=1 INV-7 prompt-injection package JSON | qualitative_coding | `make bench`, `qc_cli.py bench`, benchmark artifact workflows | paid LLM |

### Capability Validation

Skipped for cross-project registry purposes: this extends an existing
project-local fixture runner surface.

---

## Files Affected

- `docs/plans/INV7_HELD_OUT_FIXTURE_MANIFEST_RUNNER.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `qc_clean/core/inv7_fixtures.py` - manifest contract/load helper and
  metadata-aware live runner output.
- `scripts/run_inv7_live_fixtures.py` - `--fixtures` manifest argument.
- `Makefile` - optional `FIXTURES=` forwarding for `run-inv7-live-fixtures`.
- `qc_cli.py` - optional `--fixtures` forwarding for `run-inv7-live-fixtures`.
- `tests/test_inv7_fixture_runner.py` - manifest loading and runner metadata
  tests.
- `tests/test_qc_cli_inv7_fixtures.py` - CLI forwarding regression.
- Docs after implementation, if behavior lands:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/PROJECT_THEORY_AND_GOALS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add Pydantic models for a versioned INV-7 live fixture manifest with:
   `schema_version=1`, `package_type="inv7_live_fixture_manifest"`, package
   metadata, split, fixture-set ID/version, prompt-frozen and contamination
   flags, optional note, and a non-empty fixture list.
2. Enforce held-out manifest invariants consistent with protocol packages:
   `split="held_out"` requires `prompt_frozen=true`,
   `contamination_checked=true`, and `registered_before_run=true`.
3. Add a loader that converts manifest fixture rows into `Inv7LiveFixture`
   objects and returns the run metadata needed for the output package.
4. Extend `run_inv7_live_fixtures_async()` to accept optional run metadata for
   split, package ID, fixture-set ID/version, prompt-frozen,
   contamination-checked, and note while preserving the built-in canary
   defaults.
5. Add `--fixtures` to script/Make/`qc_cli.py` surfaces, forwarding the loaded
   manifest to the runner.
6. Add tests proving manifest validation, held-out invariant failures, runner
   output metadata/hash preservation, and CLI forwarding.
7. Update docs conservatively: external held-out fixture manifests are now
   runnable, but no held-out result or robustness evidence exists until a
   protocol-registered live run is executed and scored.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_inv7_fixture_runner.py` | `test_load_inv7_live_fixture_manifest_returns_fixtures_and_metadata` | Valid manifest rows become live fixtures and carry run metadata. |
| `tests/test_inv7_fixture_runner.py` | `test_held_out_inv7_manifest_requires_frozen_registered_contamination_checked` | Held-out manifests fail loudly when provenance flags are missing. |
| `tests/test_inv7_fixture_runner.py` | `test_run_inv7_live_fixtures_uses_manifest_metadata` | Custom manifest metadata appears in strict output package and prompt hashes match. |
| `tests/test_inv7_fixture_runner.py` | `test_run_inv7_live_fixture_script_accepts_fixture_manifest` | Script accepts `--fixtures` and writes package output from the manifest. |
| `tests/test_qc_cli_inv7_fixtures.py` | `test_qc_cli_run_inv7_live_fixtures_forwards_fixture_manifest` | Canonical CLI forwards optional manifest path. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_inv7_fixture_runner.py tests/test_qc_cli_inv7_fixtures.py -q` | Focused runner and CLI regressions. |
| `python -m pytest tests/test_inv7_prompt_injection_package.py tests/test_inv7_live_protocol.py tests/test_inv7_live_preflight.py tests/test_bench_phase0_script.py -k "inv7 or prompt_injection" -q` | Existing package/protocol/preflight/scorecard behavior remains compatible. |
| `python -m ruff check qc_clean/core/inv7_fixtures.py scripts/run_inv7_live_fixtures.py qc_cli.py tests/test_inv7_fixture_runner.py tests/test_qc_cli_inv7_fixtures.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync remain valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] A schema_version=1 external INV-7 live fixture manifest can be loaded.
- [x] Held-out manifests require frozen prompts, contamination checking, and
  pre-run registration.
- [x] `run-inv7-live-fixtures --fixtures manifest.json` writes a strict
  package whose split, fixture-set metadata, prompt-frozen flag,
  contamination flag, note, and exact prompt hashes come from the manifest.
- [x] Make and `qc_cli.py` expose the same optional fixture-manifest path.
- [x] Existing built-in canary behavior remains backward-compatible when no
  manifest is supplied.
- [x] Docs preserve claim discipline: this enables held-out runs but does not
  create held-out evidence, prompt-injection robustness evidence, model
  obedience proof, methodological-validity evidence, or SOTA evidence.

Process criteria:

- [x] Focused new tests pass.
- [x] Existing INV-7 package/protocol/preflight/scorecard tests pass.
- [x] Touched Python Ruff gate passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Open Questions

- [x] Should this plan run a real held-out live benchmark?
  Status: RESOLVED. No. This slice creates the governed manifest runner. A
  subsequent plan can create and execute a held-out protocol package using this
  surface, with its own budget/provenance gates.

---

## Notes

The manifest runner must fail loud on malformed manifests. It must not invent
or estimate cost, and it must not weaken the current strict result package
validator.
