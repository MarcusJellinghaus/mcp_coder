# Step 1 — Add `setup_commands_macos` to `RepoVSCodeClaudeConfig`

**Reference:** [summary.md](./summary.md) — issue #963.

## Goal

Extend the per-repo vscodeclaude config schema with a new optional key `setup_commands_macos`. Parse it the same way as `setup_commands_windows` / `setup_commands_linux`. Step 4 will wire it into resolution order; this step is purely the schema + parser + tests.

## WHERE

- **Modify:** `src/mcp_coder/workflows/vscodeclaude/types.py`
- **Modify:** `src/mcp_coder/workflows/vscodeclaude/config.py` — function `load_repo_vscodeclaude_config`
- **Modify:** `tests/workflows/vscodeclaude/test_types.py`
- **Modify:** `tests/workflows/vscodeclaude/test_config.py`

## WHAT

### `types.py` — `RepoVSCodeClaudeConfig`

Add a third optional field, mirroring the existing two:

```python
class RepoVSCodeClaudeConfig(TypedDict, total=False):
    setup_commands_windows: list[str]
    setup_commands_linux: list[str]
    setup_commands_macos: list[str]   # new
```

### `config.py` — `load_repo_vscodeclaude_config(repo_name: str) -> RepoVSCodeClaudeConfig`

Add a third batch-fetch entry and a third parsing block, structurally identical to the existing two.

## HOW

- No new imports.
- The existing parsing pattern (list → use directly; str → try `json.loads`, else wrap as single-item list) is duplicated for the new key. **Do not** factor a helper — the issue does not ask for it and three near-identical blocks remain easier to read than one parameterized helper.

## ALGORITHM (parsing block to add)

```
fetch (section, "setup_commands_macos") into config dict
if value is list      → result["setup_commands_macos"] = [str(c) for c in value]
elif value is str     → try json.loads
                          if list → result["setup_commands_macos"] = parsed
                          else (JSONDecodeError) → result["setup_commands_macos"] = [value]
else                  → key omitted from result
```

## DATA

- `RepoVSCodeClaudeConfig` is a `TypedDict(total=False)` — missing keys are valid, no default needed.
- `load_repo_vscodeclaude_config` continues to return `RepoVSCodeClaudeConfig`. New key appears only when configured.

## Tests (write first)

### `tests/workflows/vscodeclaude/test_types.py`

Add a test that constructs `RepoVSCodeClaudeConfig(setup_commands_macos=["brew install foo"])` and asserts the field round-trips. Mirror existing pattern for the other two keys.

### `tests/workflows/vscodeclaude/test_config.py`

Add four test cases for `load_repo_vscodeclaude_config`, paralleling the existing coverage for `setup_commands_linux`:

1. **List form**: TOML config has `setup_commands_macos = ["brew install x", "uv sync"]` → result has the same list.
2. **JSON-string form**: config returns the value as a JSON-string `'["a", "b"]'` → parsed to `["a", "b"]`.
3. **Plain-string form**: config returns a single command string `"brew install x"` → wrapped as `["brew install x"]`.
4. **Missing key**: config has no entry → key absent from result (no crash, no default).

Use the same mocking style already used for `setup_commands_linux` cases.

## Acceptance

- New tests pass.
- Existing tests still pass.
- pylint, mypy, pytest (with the standard exclusion marker set) all clean.

## LLM prompt

> Implement Step 1 from `pr_info/steps/step_1.md`, using `pr_info/steps/summary.md` for context.
>
> Add `setup_commands_macos: list[str]` to `RepoVSCodeClaudeConfig` in `src/mcp_coder/workflows/vscodeclaude/types.py`. In `src/mcp_coder/workflows/vscodeclaude/config.py`, extend `load_repo_vscodeclaude_config` to parse the new key with the same list / JSON-string / plain-string handling as the existing two keys.
>
> Write the tests **first**, in `tests/workflows/vscodeclaude/test_types.py` and `tests/workflows/vscodeclaude/test_config.py`, mirroring the existing `setup_commands_linux` cases. Then implement until they pass.
>
> Finish by running the three required quality checks per `.claude/CLAUDE.md`. Commit when all pass. One commit, message: `Add setup_commands_macos to RepoVSCodeClaudeConfig (#963)`.
