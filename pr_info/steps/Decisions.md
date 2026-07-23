# Decisions

Decisions from the plan-update discussion for the `mcp-coder rebase` command.

## 1. Settings become an in-code constant (was a shipped JSON resource)
The old plan shipped `resources/claude/settings/rebase_settings.json`, but that
path is gitignored AND wiped+rebuilt by `setup.py` on every build, so it would
vanish at install time (critical build bug). Decision: define the permissions as
a module-level `REBASE_LLM_PERMISSIONS` dict in
`src/mcp_coder/workflows/rebase_permissions.py`; the CLI materializes a temp
settings file from it at runtime (via `tempfile`) and passes that path to
`prompt_llm` as `settings_file`. The `--settings` override is preserved (user
file wins; otherwise materialize from the constant). A code comment notes this is
intended to fold into the configurable-permissions system from EPIC #1038
(sub-issue #1054) once that lands. (Affects Step 1, Step 7, summary.)

## 2. Drop lockfile / `uv lock` handling entirely (YAGNI)
This repo has no tracked lockfile (`uv.lock` is gitignored; `git ls-files` for
`*.lock`/`*lock.json` is empty), so a rebase can never produce a lockfile
conflict. The issue's `uv lock` regeneration scope is inapplicable here.
Decision: remove `uv lock` from `REBASE_LLM_PERMISSIONS` (git-write ops only; the
constant mirrors SKILL.md's git ops + MCP check/file tools, minus push, minus
`uv lock`); Step 1's test asserts `uv lock` and `push` are absent and the
git-write ops are present. Remove all lockfile-regeneration instructions from the
`## Automated Rebase` prompt; a hypothetical lockfile conflict falls under the
generic abort-with-reason rule. Drift-test reconciliation: keep a matching plain
lockfile row (accept `--theirs`, notify to regenerate) in the prompt so the
`issubset` drift test stays green (simplest option). Documented as a deviation
from the issue in the summary, alongside the existing Python-owns-the-force-push
deviation.

## 3. Step 6 no-op short-circuit uses the resolved base branch
Changed `needs_rebase(project_dir)` to `needs_rebase(project_dir, base)` so the
no-op check uses the base resolved in Step 5 instead of re-auto-detecting the
default (which could check the wrong branch).

## 4. Step 2 prompt body must be a fenced code block
`get_prompt` extracts the code block after the header and raises if the body is
prose, so the `## Automated Rebase` prompt body must be enclosed in a ``` fenced
code block. Noted in Step 2 WHAT and the loader test.

## 5. Step 6 drop redundant exception
Changed `except (LLMTimeoutError, Exception)` to `except Exception`
(`LLMTimeoutError` is a subclass, so the tuple is redundant and pylint may warn).

## 6. Step 2 canonical SKILL path note
Noted that the canonical SKILL lives at `.claude/skills/rebase/SKILL.md` and the
packaged copy under `resources/claude/skills/rebase/SKILL.md` (read by the drift
test via `find_data_file`) is a build-time artifact — the established convention.
