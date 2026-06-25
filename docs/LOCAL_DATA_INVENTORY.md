# Local Data Inventory

**Status:** Metadata-only local inventory
**Last updated:** 2026-06-25

This document records locally present, git-ignored data assets that matter for
planning and reproducibility. It intentionally does **not** expose transcript
contents or full participant-level file listings.

## Policy

- Raw interview/transcript files under `data/interviews/` are local restricted
  materials unless a later manifest says otherwise.
- Do not commit raw transcript contents.
- This file is only a discovery/provenance aid. It does not sanitize or clear
  the materials for publication.
- Sanitization/de-identification tooling is deferred. Use a separate future
  corpus manifest for any sanitized/evidence-ready subset.

## Candidate Africa Corpus

Likely source for Plan #234.

| Path | Files | Size | Git status | Notes |
|---|---:|---:|---|---|
| `data/interviews/africa_interviews/` | 85 `.docx` | ~2.4 MB | ignored by `.gitignore` via `**/interviews/` | Larger local corpus. Contains a subfolder named `For Brian_cleaned notes`, but this inventory does not verify sanitization or publication safety. |
| `data/interviews/africa_3_interviews_for_test/` | 3 `.docx` | ~84 KB | ignored by `.gitignore` via `**/interviews/` | Small candidate subset for Plan #234 local work. |
| `data/samples/temp_test_interviews/africa/` | 3 `.txt` | ~44 KB | ignored by `.gitignore` via `temp*` | Small text extracts. Treat as local restricted material until reviewed. |

Metadata-only discovery commands run on 2026-06-25:

```bash
find data/interviews/africa_interviews data/interviews/africa_3_interviews_for_test data/samples/temp_test_interviews/africa -maxdepth 4 -type f -printf '%p\t%s bytes\t%TY-%Tm-%Td %TH:%TM\n'
git check-ignore -v data/interviews/africa_interviews/africa_interveiws_alll_2025.0728/'For Brian_cleaned notes'/AF\ PDPA.docx data/samples/temp_test_interviews/africa/africa_1_CA\ team\ Abidjan.txt
git status --short -- data/interviews/africa_interviews data/interviews/africa_3_interviews_for_test data/samples/temp_test_interviews/africa
```

Result summary:

- Candidate Africa materials exist locally in this repo.
- They are not tracked by git.
- The raw files should not be committed.
- The next safe action is to use the 3-file subset for local Plan #234 corpus
  work without committing raw contents. Sanitization is deferred.

## RAND-Related Check

`/home/brian/projects/rand_ai_analysis` exists and contains RAND AI analysis
materials. A metadata-only search did not find Africa/interview transcript
files there on 2026-06-25. The Africa transcript candidate set appears to live
under this repo's ignored `data/interviews/` tree.

## Cleanup Note

This inventory exists because important local project inputs were discoverable
by filesystem search but not by tracked docs. If more ignored local corpora are
used, add metadata-only rows here and keep raw data out of git.
