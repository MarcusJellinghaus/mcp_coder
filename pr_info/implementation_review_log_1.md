# Implementation Review Log — Issue #963

**Branch:** `963-vscodeclaude-implement-macos-linux-launch-support`
**Goal:** vscodeclaude: macOS/Linux launch support
**Started:** 2026-05-10

---

## Round 1 — 2026-05-10

**Findings** (from engineer subagent invoking `/implementation_review`):

1. Banner fields other than `{title}` (`{repo}`, `{status}`, `{issue_url}`, `{emoji}`) are interpolated raw inside single-quoted shell echo lines in `STARTUP_SCRIPT_POSIX` / `INTERVENTION_SCRIPT_POSIX` — defensive escaping suggested.
2. Path interpolation in venv exports (`templates.py:232-234, 241, 261`) uses `"…"` quoting; could harden with `shlex.quote()` at script-creation time.
3. `cast(list[str] | None, repo_vscodeclaude_config.get(key))` at `session_launch.py:171` could be removed with a literal-key mapping.
4. `templates.py` module docstring (lines 1-32) describes only Windows backslash paths — no mention of POSIX.
5. Possible test gap: `test_intervention_mode_posix` does not assert the surrounding banner border lines.
6. Quality-check noise: pylint/mypy/some pytest collectors fail on `mcp_coder_utils.user_app_data` import — pre-existing on `main` (commit `a41e40e`), not branch-related.

**Decisions**:

- **Skip #1** — Issue's Decisions table explicitly states "Inline `value.replace("'", "'\\''")` + single-quote wrapping. No helper function." Implies only `title` needs escaping. Other fields (GitHub URL, status label, emoji) are project-controlled or URL-encoded; defensive escape is speculative per knowledge base.
- **Skip #2** — YAGNI; design didn't require this. macOS user paths in practice don't contain `"`, `\`, `$`, `` ` ``. Pre-existing pattern (Windows uses `"…"` similarly).
- **Skip #3** — Cast is correct and self-documenting. Removing it would require introducing a `Literal` overload, which adds typing complexity for negligible gain. "If a change only matters when someone makes a future mistake, it's speculative — skip it."
- **Accept #4** — Boy Scout fix. Module docstring should reflect the new POSIX support.
- **Skip #5** — Existing `"INTERVENTION MODE"` assertion suffices; banner border is incidental rendering. Coverage is good.
- **Note #6** — Pre-existing breakage on `main`, out of scope per knowledge base ("Pre-existing issues are out of scope. Note them if important, but don't block the review."). Verified: installed `mcp_coder_utils` package and upstream GitHub repo both lack `user_app_data.py`. Worth a separate issue, not this PR.

**Changes**:

- `src/mcp_coder/workflows/vscodeclaude/templates.py` — module docstring updated: forward-slash paths, both Windows and POSIX activation forms, new "PLATFORM TEMPLATES" section explaining the per-platform variants and the no-`case $(uname)` rule.

**Quality checks** (scoped to vscodeclaude module):
- pylint: clean
- mypy: clean
- pytest (`tests/workflows/vscodeclaude/`): 460 passed, 8 skipped, 0 failed

**Status**: code change ready to commit.

---
