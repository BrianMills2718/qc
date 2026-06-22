# Plan #156: Line Ending Normalization

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** The maintenance backlog calls out mixed CRLF/LF line endings.
Repository inspection found 80 tracked files with CRLF or mixed CRLF/LF line
terminators and no `.gitattributes` line-ending policy.

**Target:** Tracked text files are normalized to LF line endings in one
mechanical commit, and a narrow repository policy keeps text checkouts on LF.

**Why:** Mixed line endings create noisy diffs, make surgical patches harder to
review, and have already caused unrelated line-ending churn in small code
changes.

---

## References Reviewed

- `CLAUDE.md` - maintenance follow-up requiring line-ending normalization in one
  mechanical commit with `make check`.
- `git ls-files | xargs file | rg 'CRLF|with CRLF'` - found 80 tracked files
  with CRLF or mixed CRLF/LF line terminators.
- `.gitattributes` - absent before this plan.
- Memory context:
  `agent-memory recall 'line endings CRLF normalization qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this is mechanical repository hygiene and does not create or modify a
callable capability.

---

## Files Affected

- `.gitattributes` - add LF text normalization policy.
- All tracked text files currently containing CRLF or mixed line endings,
  identified by `git ls-files | xargs file | rg 'CRLF|with CRLF'`.
- `CLAUDE.md` - remove the completed maintenance follow-up.
- `AGENTS.md` - regenerated if `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add `.gitattributes` with text normalization to LF.
2. Mechanically convert tracked text files containing CRLF to LF.
3. Re-run CRLF scans to verify no tracked text files still report CRLF.
4. Remove the completed maintenance follow-up and regenerate `AGENTS.md`.
5. Run `make docs-check` and `make check`.

---

## Required Tests

### New Tests (TDD)

No new tests: this is a mechanical line-ending normalization.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `git ls-files | xargs file | rg 'CRLF|with CRLF'` exits nonzero | Proves tracked files no longer report CRLF line terminators |
| `rg -Il $'\r' $(git ls-files ...)` returns no tracked text files | Proves no carriage returns remain in tracked text content |
| `make docs-check` | AGENTS sync and plan docs remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] Tracked text files are LF-normalized.
- [ ] `.gitattributes` records the LF text policy.
- [ ] The change is mechanical: no intentional source behavior changes.
- [ ] The maintenance follow-up is removed only after verification.

Process criteria:

- [ ] Required scans pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

This commit will be broad by file count. Keep it mechanical and avoid combining
semantic edits with line-ending normalization.

## Closeout Notes

Completed 2026-06-22.

Outcome: Tracked text files were normalized from CRLF/mixed line endings to LF,
and `.gitattributes` now records an LF text normalization policy. The final
tracked-content scan reported no carriage returns in tracked text files. The
change is intentionally mechanical; no semantic source edits were made.

Checkpoints:

- Plan checkpoint: `939acb3`
- Implementation checkpoint: `78c4aae`

Verification:

- `git ls-files | xargs file | rg 'CRLF|with CRLF'` produced no matches.
- `git ls-files -z | xargs -0 rg -Il $'\r'` produced no tracked text paths.
- `make docs-check`
- `make check` (`1103 passed, 1 skipped, 8 deselected`)

Caveat: `git diff --check` surfaced pre-existing trailing whitespace after the
line-ending rewrite made whole lines appear changed. That whitespace was not
stripped in this lane because removing trailing spaces inside broad source and
template files can alter literal multi-line string content. A future whitespace
cleanup should be planned separately if desired.
