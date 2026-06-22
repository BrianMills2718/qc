# Qualitative Coding Validation Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Validation Position

This repo has meaningful software and workflow validation. It does not yet have
the public methodological-validation evidence needed for SOTA, expert-parity, or
full-grounded-theory claims.

The right distinction is:

- **software validation:** the code, schemas, commands, and artifacts behave as
  designed;
- **workflow validation:** the system preserves reviewability, provenance,
  grounding, coverage accounting, and export boundaries;
- **methodological validation:** expert- or gold-set-backed evidence shows the
  outputs are substantively valid for a defined corpus and task.

The first two have substantial substrate. The third is the key remaining
portfolio gap.

## Current Evidence

| Evidence area | Current status | Claim licensed |
|---|---|---|
| Deterministic tests | `make test`, `make test-quick`, and focused pytest suites exist. | The implementation can be regression-tested. |
| Documentation gates | `make docs-check`, markdown link checks, and plan-index checks exist. | The repo has enforceable documentation consistency. |
| Span anchoring | INV-1 plan and code resolve quote evidence to source spans where uniquely resolvable. | Evidence can be anchored where resolution succeeds. |
| Segment universe | INV-8 provides a denominator and exhaustive-mode coverage accounting. | Coverage can be measured over segments in exhaustive mode. |
| Claim ledger | INV-9 stores analytic assertions as first-class claim objects. | Claims are inspectable and reviewable as objects. |
| D3/D7/D8/D9 protocols | Protocol, preflight, and scorecard substrates exist. | Evaluation can be run when populated evidence exists. |
| INV-7 fixtures/canaries | Built-in structural/live canary artifacts exist. | Specific boundary fixtures have evidence, not general robustness. |
| Export/audit substrates | Export manifests, preflight, event logs, and SQLite mirrors exist. | Local provenance and handoff checks are supported. |

## Evidence Not Yet Present

The following claims are not licensed yet:

- state of the art;
- expert parity;
- full grounded theory;
- validated social-science findings;
- validated application correctness against a held-out gold set;
- validated D7 contrary-evidence recall;
- broad prompt-injection robustness;
- sampling-frame adequacy or population generalization.

## Commands

Core deterministic verification:

```bash
make test
make docs-check
make check
```

Focused documentation verification:

```bash
python scripts/check_markdown_links.py
python scripts/sync_plan_status.py --check
python scripts/meta/check_agents_sync.py --check
```

Phase 0 scorecard path, when a local project exists:

```bash
make bench ID=<project_id> ARTIFACT_DIR=benchmark_results
make verify-phase0-benchmark-artifact ARTIFACT=benchmark_results/<run_dir>
```

Gold/preflight surfaces, when adjudicated packages exist:

```bash
make validate-d3-gold GOLD=d3_gold.json
make validate-d7-gold GOLD=d7_gold.json
make validate-d3-comparison-protocol PROTOCOL=d3_protocol.json
make validate-d7-comparison-protocol PROTOCOL=d7_protocol.json
```

## Portfolio Readiness Gate

The project becomes much stronger for a portfolio when it has all of the
following:

1. A sanitized corpus with clear scope.
2. A repeatable walkthrough that starts from raw transcript files.
3. Human-adjudicated D3 and D7 labels for a small but real case set.
4. A Phase 0 artifact package with hashes and caveats.
5. A public report that avoids every unlicensed claim listed above.

Until then, present this as strong analyst-methods engineering and evaluation
infrastructure, not as completed methodological proof.

