# Step 1 — Resolve SIM findings ahead of enabling the rule

Reference: `pr_info/steps/summary.md` (issue #1168).

## Precondition check (do this first)

Run `ruff check --select SIM102,SIM105,SIM108,SIM113,SIM114,SIM300,SIM905`
over `src/` and `tests/`. Compare to the "Locations" list below.

- If the total count differs, or any location differs from what's listed
  (new file, a line far from the named one, or a different code at a named
  location), **write one line to `pr_info/.blocked.txt` describing the
  mismatch and stop.**
- Minor line-number drift at the *same* site (±a few lines from an
  unrelated edit) is expected and not a block.

## WHERE

No new files. Modifies:

- `tests/conftest.py`
- `tests/llm/providers/langchain/test_langchain_integration.py`
- `tests/utils/test_git_encoding_stress.py`
- `tests/icoder/test_app_pilot.py`
- `tests/integration/test_mlflow_integration.py`
- `tests/llm/test_types.py`
- `tests/workflows/vscodeclaude/test_status_display.py`
- `src/mcp_coder/checks/file_sizes.py`
- `src/mcp_coder/cli/commands/verify_exit_code.py`
- `src/mcp_coder/icoder/ui/app.py`
- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`
- `src/mcp_coder/utils/user_config.py`
- `src/mcp_coder/workflow_utils/commit_operations.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `src/mcp_coder/icoder/core/event_log.py`
- `src/mcp_coder/install/_env.py`
- `src/mcp_coder/llm/providers/langchain/_errors_404.py`
- `src/mcp_coder/utils/tui_preparation.py`
- `src/mcp_coder/workflow_utils/failure_handling.py`
- `src/mcp_coder/llm/providers/copilot/copilot_cli.py`
- `src/mcp_coder/llm/storage/session_storage.py`
- `src/mcp_coder/utils/folder_deletion.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py`
- `src/mcp_coder/workflows/utils.py`

## WHAT

No new functions or signatures. Every site keeps its existing function
signature; only a control-flow body changes. Two sites get a
`# noqa: <rule>` comment and no code change.

## Locations (measured 2026-10-14 — re-verify per precondition above)

### Noqa exceptions — add comment only, no rewrite. Do these FIRST, before auto-fixing.

- `tests/conftest.py:311` — the `try:` line of the inner
  `try: repo.git.checkout("master") except Exception: pass  # Use current branch`
  block. Add `# noqa: SIM105` to the `try:` line:
  ```python
  try:  # noqa: SIM105 -- pass holds the "Use current branch" comment; suppress() has nowhere to put it
      repo.git.checkout("master")
  except Exception:  # pylint: disable=broad-exception-caught  # test helper
      pass  # Use current branch
  ```
- `tests/llm/providers/langchain/test_langchain_integration.py:57` — the
  `elif backend == "anthropic":` line. Add `# noqa: SIM102`:
  ```python
  elif backend == "anthropic":  # noqa: SIM102 -- collapsing overflows line length and breaks symmetry with the openai/gemini branches above
      if not os.getenv("ANTHROPIC_API_KEY") and not cfg.get("api_key"):
  ```

### Auto-fixable (apply via tool, see ALGORITHM) — SIM102, SIM105, SIM108, SIM114, SIM300, SIM905

- **SIM102** (collapsible-if, merge nested `if`s into one `if ... and ...`):
  `src/mcp_coder/checks/file_sizes.py:137`,
  `src/mcp_coder/cli/commands/verify_exit_code.py:90`, `:113`,
  `src/mcp_coder/icoder/ui/app.py:376`,
  `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py:301`,
  `src/mcp_coder/utils/user_config.py:238`, `:499`,
  `src/mcp_coder/workflow_utils/commit_operations.py:282`,
  `src/mcp_coder/workflows/implement/task_processing.py:550`,
  `src/mcp_coder/workflows/vscodeclaude/sessions.py:456`, `:502`,
  `tests/conftest.py:141`
- **SIM105** (`try/except/pass` → `contextlib.suppress(...)`):
  `src/mcp_coder/icoder/core/event_log.py:164`,
  `src/mcp_coder/install/_env.py:230`,
  `src/mcp_coder/llm/providers/langchain/_errors_404.py:90`,
  `src/mcp_coder/utils/tui_preparation.py:77`,
  `src/mcp_coder/workflow_utils/failure_handling.py:339`,
  `tests/conftest.py:144`,
  `tests/icoder/test_app_pilot.py:2285`,
  `tests/integration/test_mlflow_integration.py:409`, `:415`
- **SIM108** (if/else assignment → ternary):
  `src/mcp_coder/llm/providers/copilot/copilot_cli.py:236`,
  `src/mcp_coder/llm/storage/session_storage.py:58`,
  `src/mcp_coder/utils/folder_deletion.py:315`,
  `src/mcp_coder/workflows/create_plan/prerequisites.py:221`,
  `src/mcp_coder/workflows/utils.py:27`
- **SIM114** (merge identical `elif` bodies with `or`):
  `src/mcp_coder/llm/providers/copilot/copilot_cli.py:150`
- **SIM300** (reverse yoda condition): `tests/llm/test_types.py:380`, `:542`
- **SIM905** (`str.split()` on a literal → list literal):
  `tests/workflows/vscodeclaude/test_status_display.py:415`

### Manual only — no autofix exists

- **SIM113** (`tests/utils/test_git_encoding_stress.py:98`): the loop keeps
  a hand-rolled `char_index` that always equals the `for i in
  range(target_length)` loop variable. Fix:
  ```python
  # before
  test_content_chars = []
  char_index = 0
  for i in range(target_length):
      test_content_chars.append(special_chars[char_index % len(special_chars)])
      char_index += 1
      if i > 0 and i % 100 == 0:
          test_content_chars.append("\n")

  # after
  test_content_chars = []
  for i in range(target_length):
      test_content_chars.append(special_chars[i % len(special_chars)])
      if i > 0 and i % 100 == 0:
          test_content_chars.append("\n")
  ```

## HOW

1. Add the two `# noqa` comments by hand first (`edit_file`), so the fixer
   below leaves them untouched.
2. Run
   `mcp__mcp-tools-py__run_ruff_fix(select=["SIM102","SIM105","SIM108","SIM114","SIM300","SIM905"], target_directories=["src","tests"], extra_args=["--unsafe-fixes"])`.
   `SIM102`'s fix is classified unsafe by ruff (it merges nested
   conditions); the rest are safe. `--unsafe-fixes` is required to pick up
   `SIM102` as well.
3. `SIM105`'s fix adds `import contextlib` automatically where needed — do
   not add it by hand.
4. Apply the `SIM113` rewrite above by hand (`edit_file`).
5. Re-run
   `ruff check --select SIM102,SIM105,SIM108,SIM113,SIM114,SIM300,SIM905`
   over `src/` and `tests/` — expect zero remaining findings (the two
   noqa'd lines are suppressed, not reported).

## ALGORITHM

```
add noqa comments to the 2 exception lines
run ruff --fix --unsafe-fixes for [SIM102, SIM105, SIM108, SIM114, SIM300, SIM905] on src/ + tests/
manually rewrite the SIM113 site (drop char_index, reuse loop var i)
re-run ruff check for the same rule set -> must report 0
```

## DATA

No data structures or return values change. Every rewrite preserves the
exact runtime behavior of the branch it replaces (verified by the existing
test suite, not new tests).

## Verification before commit

- `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_format_code`

All must pass clean.

## Commit

One commit:

```
fix: resolve SIM lint findings ahead of enabling ruff SIM rule

Mechanical rewrites (contextlib.suppress, ternaries, merged
conditionals, enumerate-equivalent cleanup, list literals) plus two
noqa exceptions documented inline. Prepares for enabling SIM in
pyproject.toml with no new findings.
```

## LLM prompt for this step

"Implement Step 1 from `pr_info/steps/step_1.md`, following the
architecture described in `pr_info/steps/summary.md` for issue #1168.
Follow the precondition check first. Do not modify `pyproject.toml` in
this step — that is Step 2. Make exactly one commit containing the noqa
additions, the ruff-fix-driven rewrites, and the manual SIM113 rewrite,
with all checks (pytest, pylint, mypy, format) passing."
