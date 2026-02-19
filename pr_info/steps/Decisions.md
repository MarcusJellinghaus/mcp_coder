# Decisions

Decisions made during plan review discussion for issue #469.

---

## D1: `ansi=True` injects both `--color=always` and `--color-moved=dimmed-zebra`

**Decision:** When `ansi=True`, `get_branch_diff()` prepends both
`--color=always` and `--color-moved=dimmed-zebra` to diff args.

**Rationale:** Both flags are required together for Pass 1 move detection.
`--color=always` alone does not mark moved lines with dim SGR codes; only
`--color-moved=dimmed-zebra` does that.

---

## D2: 100% moved threshold in `render_hunk()` (no ratio constant)

**Decision:** A block is suppressed only when **all** significant lines in it
are confirmed moved. The original 80% threshold is dropped entirely, along with
any `MIN_MOVED_RATIO` constant.

**Rationale:** At 80%, genuine changes (the 20% non-moved lines) could be
silently hidden behind `# [moved: N lines not shown]`. At 100%, no real changes
can be lost.

---

## D3: Remove `find_first_nonblank_line()`

**Decision:** `find_first_nonblank_line()` is not implemented.

**Rationale:** The function did not appear in the `render_hunk()` or
`render_compact_diff()` algorithms. Removing it follows YAGNI.

---

## D4: Windows ANSI compatibility — no special setup needed

**Decision:** No extra environment variables (e.g. `FORCE_COLOR`) are needed.
Document in docstring only.

**Rationale:** Tested live on Windows — `git diff --color=always
--color-moved=dimmed-zebra` produces correct ANSI dim codes (`\x1b[2m`) without
any additional configuration.

---

## D5: `tach` compliance confirmed — no changes needed

**Decision:** No `tach.toml` changes required for `git_tool.py`.

**Rationale:** `mcp_coder.cli` already lists `mcp_coder.workflow_utils` and
`mcp_coder.utils` in its `depends_on`. `git_tool.py` uses the same imports as
the existing `gh_tool.py`.

---

## D6: Add `test_render_compact_diff_empty_input`

**Decision:** `TestRenderCompactDiff` includes a test asserting that
`render_compact_diff("", "")` returns `""`.

**Rationale:** Explicit safety net for the empty-input edge case (e.g. running
on main branch or on error).

---

## D7: New Step 5 for documentation updates

**Decision:** Documentation updates are a separate Step 5 (not folded into
Step 4).

**Rationale:** Keeps Step 4 (non-code slash command + deletions) focused.
Step 5 covers concise updates to `docs/cli-reference.md`,
`docs/architecture/architecture.md`, and `README.md`.
