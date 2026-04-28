# Step 6 — Render `token_source` in verify command

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement Step 6
> exactly as specified. Use TDD: write the two render tests in
> `tests/cli/commands/test_verify.py` first, see them fail, then add the
> 4-line special case to `_format_section()` in
> `src/mcp_coder/cli/commands/verify.py`. Run pylint, pytest (fast unit
> pattern), mypy, and lint-imports. All must pass. This is one commit.

## WHERE

- Modified: `src/mcp_coder/cli/commands/verify.py`
- Modified: `tests/cli/commands/test_verify.py`

## WHAT

### `verify.py` — `_format_section()` special case

Inside `_format_section()`, after the existing labeled-row append for
non-branch-protection keys (i.e. after the line
`lines.append(_format_row(label, symbol, row_value, indent=2))`), add a
4-line special case that emits a second indented line at the value column
when the entry has a `token_source`:

```python
if key == "token_configured" and entry.get("token_source"):
    src = entry["token_source"]
    suffix = "GITHUB_TOKEN env var" if src == "env" else "~/.mcp_coder/config.toml"
    lines.append(f"{' ' * _VALUE_COLUMN_INDENT}from {suffix}")
```

This renders, for example:

```
  Token configured     [OK] configured (scopes: repo, workflow)
                            from GITHUB_TOKEN env var
```

The literal tilde (`~`) is intentional — do **not** expand it via
`Path.expanduser()`.

### `tests/cli/commands/test_verify.py` — two new tests

Add two tests in a new test class (e.g. `TestVerifyGithubTokenSource`) that
patch `verify_github` to return a payload with a `token_configured` entry
containing `token_source`, then assert the rendered output:

1. `test_token_source_env_renders_second_line`: `token_source="env"` →
   output contains the line `from GITHUB_TOKEN env var`, indented at the
   value column.
2. `test_token_source_config_renders_second_line`: `token_source="config"` →
   output contains the line `from ~/.mcp_coder/config.toml`, with the literal
   tilde.

Both tests assert that the upstream `value` (e.g.
`configured (scopes: repo, workflow)`) is preserved on the main line.

Use the existing `_make_args()` / `_minimal_llm_response()` / `_claude_ok()`
test helpers in the file. Pattern after `TestVerifyShowsPromptSection` for the
patching style.

## HOW

- Reuse `_VALUE_COLUMN_INDENT` (already defined at module scope in
  `verify.py`) for the second-line indentation.
- The patch target for `verify_github` is `mcp_coder.cli.commands.verify.
  verify_github` (the name imported into the module).
- Patch `prompt_llm`, `verify_mlflow`, `verify_claude`, `find_claude_executable`,
  `verify_config`, `resolve_llm_method`, `load_prompts` to return minimal
  successful values so `execute_verify` runs end-to-end without external
  dependencies.

## ALGORITHM

```
for each (key, entry) in result.items():
    ... existing rendering ...
    if key == "token_configured" and entry.get("token_source"):
        suffix = "GITHUB_TOKEN env var" if source == "env" else "~/.mcp_coder/config.toml"
        append second line at _VALUE_COLUMN_INDENT prefixed with "from "
```

## DATA

- Input: `verify_github()` result dict where
  `result["token_configured"]["token_source"]` is `"env"` or `"config"`.
- Output: same multi-line section string as before, with one extra line
  inserted directly after the `Token configured` row.
- The upstream `value` (`configured (scopes: ...)`) is **not** modified — it
  stays on the main line.

## TDD note

The two tests should fail before the special case is added (the second-line
text is absent from output). After the implementation, both pass.

## Edge cases

- `token_source` absent: the special case's `entry.get("token_source")`
  short-circuits to falsy → no second line. Backward-compatible with any
  upstream payload that doesn't yet emit `token_source`.
- `token_source` is some unexpected value (e.g. `"unknown"`): the conditional
  uses `if src == "env" else <config string>` — anything other than `"env"`
  falls back to `~/.mcp_coder/config.toml`. The issue lists only `"env"` and
  `"config"` as valid values; unknown values shouldn't occur. If we later see
  a third source, this branch needs revisiting — for now, two states is the
  full domain.
- No token configured at all (no `token_configured` entry, or `ok is False`):
  `entry.get("token_source")` is missing → no second line. Correct behaviour.

## Acceptance for this step

- The two new tests pass.
- `mcp-coder verify` (locally, when token is set) shows the second line.
- The upstream `value` (`configured (scopes: ...)`) is preserved on the main
  line.
- `pylint`, `pytest` (fast unit pattern), `mypy`, `lint-imports` all green.
