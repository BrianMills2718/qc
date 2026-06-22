# Portfolio Dossier Spine

**Status:** Complete
**Type:** documentation
**Priority:** High
**Blocked By:** None
**Blocks:** Portfolio wiki navigation and project evidence review

---

## Outcome

Completed 2026-06-22. Added the standardized project dossier spine:

- `PROJECT.md`
- `docs/METHODOLOGY.md`
- `docs/ARTIFACTS.md`
- `docs/VALIDATION.md`
- `docs/CONCERNS.md`
- `docs/adr/0001_qualitative_coding_methodology_spine.md`

Updated `docs/wiki_manifest.yaml` so the wiki can publish those surfaces, and
updated the completed-plan index so the record is not orphaned.

This is portfolio documentation and navigation. It does not change code, run a
new benchmark, create a sanitized corpus, populate D3/D7 gold packages, prove
methodological validity, or support SOTA claims.

## Gap

Before this plan, the repo had strong evidence documents but lacked the
standard dossier filenames expected by the cross-project wiki coverage checker.
That made the project harder to navigate in portfolio surfaces even though it
already had a reviewer guide, evidence bundle, theory document, evaluation
harness, and many completed plan records.

## Target

Create a concise wiki-style dossier that:

- frames the repo as an analyst-methods project;
- separates software/workflow validation from methodological validation;
- points reviewers to the key artifacts;
- lists concerns and next evidence;
- preserves claim discipline around GT, SOTA, D3/D7, D8/D9, and INV-7.

## References Reviewed

- `README.md`
- `CLAUDE.md`
- `docs/PORTFOLIO_REVIEWER_GUIDE.md`
- `docs/portfolio/QUALITATIVE_CODING_EVIDENCE_BUNDLE.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `docs/EVALUATION_HARNESS.md`
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`
- `docs/wiki_manifest.yaml`
- Memory recall for `qualitative_coding` active decisions, which returned only
  old completed sessions and no active architectural decision.
- Coordination claims, which showed only an unrelated `llm_client` claim.

## Files Affected

- `PROJECT.md` (add)
- `docs/METHODOLOGY.md` (add)
- `docs/ARTIFACTS.md` (add)
- `docs/VALIDATION.md` (add)
- `docs/CONCERNS.md` (add)
- `docs/adr/0001_qualitative_coding_methodology_spine.md` (add)
- `docs/wiki_manifest.yaml` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/completed/PORTFOLIO_DOSSIER_SPINE.md` (add)

## Acceptance Criteria

| Criterion | Status |
|---|---|
| Dossier entrypoint exists at `PROJECT.md`. | Complete |
| Methodology, artifact, validation, and concern registers exist under `docs/`. | Complete |
| ADR exists under `docs/adr/`. | Complete |
| Wiki manifest publishes the new pages. | Complete |
| Completed-plan index references this record. | Complete |
| Documentation checks pass. | Complete after verification below. |

## Verification

Passed on 2026-06-22:

```bash
python scripts/check_markdown_links.py PROJECT.md docs/METHODOLOGY.md docs/ARTIFACTS.md docs/VALIDATION.md docs/CONCERNS.md docs/adr/0001_qualitative_coding_methodology_spine.md docs/plans/completed/PORTFOLIO_DOSSIER_SPINE.md docs/wiki_manifest.yaml docs/plans/CLAUDE.md
python scripts/sync_plan_status.py --check
python - <<'PY'
from pathlib import Path
import yaml
manifest = yaml.safe_load(Path('docs/wiki_manifest.yaml').read_text())
print(f"publish entries={len(manifest.get('publish', []))}")
PY
git diff --check
make docs-check
```

Full `make check` is not required for this docs-only slice because there are
pre-existing active implementation edits in `qc_clean/plugins/api/api_server.py`
and `tests/test_review_api.py` that are outside this dossier change.
