# Decisions Log

Decisions made during plan review discussion (2026-03-04).

---

## D1: Where to document the existing-test fix

**Question**: When Step 3 adds `args.committed_only` access, all 9 existing tests fail with `AttributeError`. Where should the fix be documented?

**Decision**: Document it in **Step 3** as an explicit sub-task — update all existing `argparse.Namespace` calls in `test_git_tool.py` to add `committed_only=False`.

---

## D2: Import placement for `fnmatch`

**Question**: Should `import fnmatch` be at the top of `git_tool.py` or inside the helper function body?

**Decision**: Move to **top-of-file imports** (conventional Python style, avoids repeated import lookups).

---

## D3: Remove unused `from pathlib import Path` from helper

**Question**: The plan included `from pathlib import Path` inside the helper function, but `Path` is never used there. Remove it?

**Decision**: **Yes, remove it** — avoids a pylint/mypy warning and keeps the function clean.

---

## D4: Note on `fnmatch` path separator behaviour

**Question**: `fnmatch`'s `*` matches `/` (unlike shell globbing), so `pr_info/**` correctly matches `pr_info/notes.md`. Should this be documented?

**Decision**: Add a **note in Step 5 file only** (not as a code comment). The note is now in the helper function implementation section of Step 5.

---

## D5: "No committed changes" message

**Question**: When there are no committed changes but there are uncommitted changes, should the output show "No committed changes" before the uncommitted section, or skip straight to the uncommitted section?

**Decision**: **Keep the "No committed changes" message** — makes it explicit to the user that the committed section is not missing.
