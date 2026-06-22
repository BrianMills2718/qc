# Plan #152: Explicit Export Overwrite Policy

## Mission

Resolve the documented exporter overwrite technical debt. Current exports
overwrite existing output paths implicitly. Keep that behavior as the default
for backward compatibility, but make the policy explicit and add an
agent-drivable no-clobber guard for durable artifacts.

## Scope

- Add an `overwrite: bool = True` option to `ProjectExporter` JSON, CSV,
  Markdown, and QDPX export methods.
- Add a CLI `project export --no-overwrite` flag that passes
  `overwrite=False`.
- Fail loud before writing if `--no-overwrite` is used and the target artifact
  already exists.
- For CSV exports, check the full output set before writing any file so the
  no-overwrite path cannot leave partial exports.
- Document default behavior: overwrite is allowed unless `--no-overwrite` is
  supplied.

## Non-Goals

- Do not change default export behavior.
- Do not add timestamped automatic filenames.
- Do not change audit-manifest or audit-log semantics.
- Do not implement append-only external storage or signing.

## Acceptance Criteria

Passes when:

- Existing exporter calls still overwrite by default.
- `ProjectExporter(..., overwrite=False)` equivalents raise `FileExistsError`
  before writing existing JSON, Markdown, QDPX, or CSV artifacts.
- `project export --no-overwrite` is parsed and returns nonzero with a clear
  error when the target exists.
- CSV no-overwrite checks all target files before writing.
- Focused exporter and parser tests pass.
- `make docs-check` and `make check` pass before closeout.

Fails when:

- Existing callers break because overwrite defaults changed.
- CSV no-overwrite writes some files before discovering another target exists.
- Errors are silent or ambiguous.
- Docs imply a full tamper-evident audit log exists.

## Failure Modes And Diagnostics

| Failure mode | Diagnosis | Response |
|---|---|---|
| Backward compatibility breaks | Existing export tests fail | Keep `overwrite=True` as the default |
| Partial CSV output under no-overwrite | Fixture pre-creates one CSV target and sees another target modified | Precompute and validate all CSV paths first |
| CLI flag parsed but ignored | CLI test exits 0 while target exists | Thread `overwrite=not args.no_overwrite` into exporter calls |
| Audit overclaim | Docs say no-overwrite is tamper-evidence | Reframe as local clobber prevention only |

## Verification

- `python -m pytest tests/test_project_commands.py -k "export"`
- `python -m pytest tests/test_claim_ledger_exports.py -q`
- `python -m pytest tests/test_qdpx_export.py -q`
- `make docs-check`
- `make check`

## Closeout Notes

Completed 2026-06-22.

Outcome: Project exports now have an explicit overwrite policy. Default export
behavior remains backward-compatible (`overwrite=True`), while
`overwrite=False` and `project export --no-overwrite` fail loudly before
clobbering existing JSON, Markdown, QDPX, or any planned CSV artifact. CSV
exports preflight the full artifact set before writing so no-overwrite failures
do not leave partial output.

Checkpoints:

- Plan checkpoint: `55ea954`
- Implementation checkpoint: `0765829`

Verification:

- `python -m pytest tests/test_project_commands.py -k "export" -q` (`26 passed,
  23 deselected`)
- `python -m pytest tests/test_qdpx_export.py -q` (`14 passed`)
- `python -m pytest tests/test_claim_ledger_exports.py -q` (`18 passed`)
- `ruff check qc_clean/core/export/data_exporter.py qc_clean/core/cli/commands/project.py qc_cli.py tests/test_project_commands.py tests/test_qdpx_export.py`
- `make docs-check`
- `make check` (`1097 passed, 1 skipped, 8 deselected`)

Caveat: this is local clobber prevention only. It is not append-only storage,
tamper-evidence, external signing, or a durable audit substrate.
