# Theoretical Sampling Smoke Artifact - 2026-06-23

This directory is a synthetic INV-4 workflow/provenance smoke artifact. It
demonstrates that theoretical-sampling protocol validation, explicit
repo-local candidate export, selected-candidate result export, and protocol
preflight can run end to end without using the default user project store.

It is not theoretical sampling execution, not new data collection, not
sampling-frame adequacy evidence, not category-saturation evidence, not
GT-fidelity evidence, not methodological-validity evidence, and not SOTA
evidence.

Claim-boundary checklist:

- not theoretical sampling execution
- not sampling-frame adequacy evidence
- not category-saturation evidence
- not SOTA evidence

## Files

| File | Purpose |
|------|---------|
| `projects/theoretical-sampling-smoke.json` | Synthetic repo-local `ProjectState` with one coded document and one loaded uncoded candidate document. |
| `protocol.json` | Pre-registered schema_version=1 theoretical-sampling protocol with hashes for the synthetic project/corpus. |
| `validated_protocol.json` | Normalized validator output from `qc_cli.py validate-theoretical-sampling-protocol`. |
| `candidates.json` | Loaded-document candidate package exported with explicit `PROJECTS_DIR`. |
| `results.json` | Selected-candidate result package. |
| `preflight.json` | Passing candidate/result preflight report. |

## Commands

Validate the protocol:

```bash
python qc_cli.py validate-theoretical-sampling-protocol \
  docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json \
  > docs/benchmarks/theoretical_sampling_smoke_2026_06_23/validated_protocol.json
```

Export candidates from the repo-local project store:

```bash
make export-theoretical-sampling-candidates \
  ID=theoretical-sampling-smoke \
  PROJECTS_DIR=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/projects \
  PROTOCOL=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json \
  OUTPUT=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/candidates.json \
  MAX=1
```

Export selected-candidate results:

```bash
python qc_cli.py export-theoretical-sampling-results \
  docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json \
  --candidates-file docs/benchmarks/theoretical_sampling_smoke_2026_06_23/candidates.json \
  --selected-candidate-id loaded-doc-2 \
  --success-criterion-met "Every targeted gap has an explicit sampling decision." \
  --output docs/benchmarks/theoretical_sampling_smoke_2026_06_23/results.json
```

Preflight the candidate/result packages:

```bash
make -s theoretical-sampling-preflight \
  PROTOCOL=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json \
  CANDIDATES=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/candidates.json \
  RESULTS=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/results.json \
  > docs/benchmarks/theoretical_sampling_smoke_2026_06_23/preflight.json
```

`make -s` is used for the saved preflight artifact so the Make command itself
is not echoed into the JSON file.

## Result Summary

- Protocol validation: passed
- Candidate export: 1 loaded-document candidate
- Selected result: `loaded-doc-2`
- Preflight status: `pass`
- Preflight candidate count: 1
- Preflight selected count: 1

## Caveat

This artifact proves only that the package workflow and provenance checks are
agent-drivable over a repo-local synthetic store. It does not show that a real
researcher selected new cases, that any category is saturated, that the sample
supports a population claim, or that the GT path has methodological validity.
