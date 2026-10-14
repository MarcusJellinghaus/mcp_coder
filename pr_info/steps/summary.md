# Summary: Enable ruff `E` — exclude `E501` (Issue #1167)

## Goal

Add ruff's `E` (pycodestyle error) rule group to the project's lint selection,
except `E501` (line-too-long), which stays excluded permanently because black
already owns line length and deliberately leaves some lines long. Fix the 70
real findings this uncovers (`E741`, `E402`, `E721`) before turning the rule
on, so every commit keeps `ruff check` green under its own config.

## Architectural / design changes

There is no architectural change — this is a lint-configuration change plus
small, targeted fixes to satisfy it. Two precedents worth recording:

- **`E501` is excluded on principle, not temporarily.** Black and ruff agree
  on line length by construction only sometimes (long string literals, URLs,
  dense f-strings are exceptions black leaves alone). Enabling `E501` would
  make ruff fail on output black considers final. This exclusion is not
  revisited when the formatter changes.
- **A single file-level `# ruff: noqa: E402` is the sanctioned pattern** for
  `src/mcp_coder/cli/main.py`'s intentional import-after-bootstrap ordering
  (`faulthandler.enable()` must run before the heavy imports below it). This
  replaces 24 per-line suppressions and documents the one place in the repo
  the rule is deliberately overridden.
- **`E741` ambiguous-name fixes use three different replacement names**
  (`label`, `line`, `entry`) depending on what the variable actually holds,
  rather than one blanket rename — readability over mechanical uniformity.

## Files to create / modify

- `pyproject.toml` — modify `[tool.ruff.lint]`: add `"E"` to `select`, add
  `"E501"` to `ignore` with an explanatory comment.
- `src/mcp_coder/cli/commands/define_labels.py` — modify: rename `l` → `label`
  in `execute_define_labels` (line ~582).
- `src/mcp_coder/cli/main.py` — modify: add a file-level `# ruff: noqa: E402`
  suppression with a comment.
- `tests/llm/test_types.py` — modify: 4 type comparisons `==` → `is`.
- `tests/cli/commands/test_prompt_streaming.py` — modify: rename `l` → `line`
  (4 sites).
- `tests/cli/commands/test_set_status.py` — modify: rename `l` → `line`
  (4 sites).
- `tests/cli/commands/test_verify.py` — modify: rename `l` → `line`
  (7 sites).
- `tests/cli/commands/test_verify_format_mcp_section.py` — modify: rename
  `l` → `line` (5 sites).
- `tests/cli/commands/test_verify_format_section_basic.py` — modify: rename
  `l` → `line` (6 sites).
- `tests/cli/commands/test_verify_mcp_orchestration.py` — modify: rename
  `l` → `line` (2 sites).
- `tests/cli/commands/test_verify_sections_config.py` — modify: rename
  `l` → `line` (2 sites).
- `tests/cli/commands/test_verify_sections_orchestration.py` — modify:
  rename `l` → `line` (4 sites).
- `tests/utils/test_user_config_create_default.py` — modify: rename `l` →
  `line` (1 site, line ~187).
- `tests/config/test_label_config.py` — modify: rename inner `l` → `entry`
  (6 sites; outer `label` binding is unchanged).

No new source or test modules are created. `pr_info/steps/*.md` are the plan
files for this implementation.

## Step sequence and rationale

Code fixes land **before** the config change, so `ruff check` stays green at
every commit under whatever config is active at that point, and the final
step's config change finds nothing left to flag:

1. `E741` in `src/mcp_coder/cli/commands/define_labels.py` → `label`
2. `E741` in 8 test files → `line` (35 sites)
3. `E741` in `tests/config/test_label_config.py` → `entry` (6 sites)
4. `E721` in `tests/llm/test_types.py` → `is` (4 sites)
5. `E402` in `src/mcp_coder/cli/main.py` → file-level noqa
6. Enable `E` / exclude `E501` in `pyproject.toml`; confirm `ruff check` is
   clean

## Reference

Issue #1167. Depends on #1164 (closed). Part of epic #1163.
