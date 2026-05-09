# Step 4 — Setup-commands resolution per platform with Darwin → Linux fallback

**Reference:** [summary.md](./summary.md) — issue #963. Depends on Step 1 (`setup_commands_macos` field).

## Goal

`prepare_and_launch_session` currently picks setup commands by `is_windows ? "setup_commands_windows" : "setup_commands_linux"`. Replace with a three-way platform branch:

- **Windows** → `setup_commands_windows`
- **Linux** → `setup_commands_linux`
- **Darwin** → `setup_commands_macos`, falling back to `setup_commands_linux` if absent. If both absent, run no commands (silent — matches current Linux behavior when key is missing).

## WHERE

- **Modify:** `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — function `prepare_and_launch_session`
- **Modify:** `tests/workflows/vscodeclaude/test_session_launch.py`

## WHAT

### `session_launch.py` — inside `prepare_and_launch_session`

Replace the existing block:

```python
is_windows = platform.system() == "Windows"
if is_windows:
    setup_commands = repo_vscodeclaude_config.get("setup_commands_windows", [])
else:
    setup_commands = repo_vscodeclaude_config.get("setup_commands_linux", [])
```

with a key-list lookup keyed by `platform.system()`:

```python
_SETUP_COMMAND_KEYS: dict[str, tuple[str, ...]] = {
    "Windows": ("setup_commands_windows",),
    "Linux":   ("setup_commands_linux",),
    "Darwin":  ("setup_commands_macos", "setup_commands_linux"),
}
candidate_keys = _SETUP_COMMAND_KEYS.get(platform.system(), ())
setup_commands: list[str] = []
for key in candidate_keys:
    value = repo_vscodeclaude_config.get(key)
    if value:
        setup_commands = value
        break
```

`_SETUP_COMMAND_KEYS` is a module-level constant in `session_launch.py`.

## HOW

- "First non-empty wins" semantics: an explicit empty list `[]` is treated like a missing key (skipped) so the Darwin fallback to `linux` is reachable when `setup_commands_macos = []`. This matches user intent — `[]` says "I don't want any commands here".
- No other behavior in the function changes.

## ALGORITHM

```
keys = _SETUP_COMMAND_KEYS.get(platform.system(), ())
for k in keys:
    v = repo_vscodeclaude_config.get(k)
    if v:                 # non-empty list
        commands = v
        break
else:
    commands = []
if commands: validate_setup_commands(commands); run_setup_commands(folder_path, commands)
```

## DATA

- `_SETUP_COMMAND_KEYS: dict[str, tuple[str, ...]]` — module-level.
- `setup_commands: list[str]` — local; behavior unchanged downstream.

## Tests (write first)

Add to `tests/workflows/vscodeclaude/test_session_launch.py` a focused class that tests *only* the resolution decision. The cleanest path is to mock `validate_setup_commands` and `run_setup_commands` (and the upstream git/folder/script side-effects already mocked in existing tests) and assert `run_setup_commands` was called with the expected list.

Cases:

| Platform | `setup_commands_windows` | `setup_commands_linux` | `setup_commands_macos` | Expected `run_setup_commands` arg |
|---|---|---|---|---|
| Windows | `["choco install foo"]` | `["apt install bar"]` | `["brew install baz"]` | `["choco install foo"]` |
| Linux   | `["choco install foo"]` | `["apt install bar"]` | `["brew install baz"]` | `["apt install bar"]` |
| Darwin  | `["choco install foo"]` | `["apt install bar"]` | `["brew install baz"]` | `["brew install baz"]` |
| Darwin  | (n/a) | `["apt install bar"]` | (absent) | `["apt install bar"]` (fallback) |
| Darwin  | (n/a) | `[]`                 | (absent) | not called (both empty) |
| Darwin  | (n/a) | (absent) | (absent) | not called |

The "not called" assertions verify `run_setup_commands.assert_not_called()`.

Use existing mocking patterns from `test_session_launch.py` to suppress the git clone, gitignore, workspace file creation, etc.

## Acceptance

- New tests pass.
- Existing `prepare_and_launch_session` tests still pass.
- pylint, mypy, pytest clean.

## LLM prompt

> Implement Step 4 from `pr_info/steps/step_4.md`, using `pr_info/steps/summary.md` for context.
>
> In `src/mcp_coder/workflows/vscodeclaude/session_launch.py`, replace the binary `is_windows`-based setup-commands selection in `prepare_and_launch_session` with a `_SETUP_COMMAND_KEYS` module-level mapping. On Darwin, prefer `setup_commands_macos`; if absent or empty, fall back to `setup_commands_linux`; if both absent or empty, run no commands.
>
> Write the parametrized resolution-order tests in `tests/workflows/vscodeclaude/test_session_launch.py` **first**, mocking `validate_setup_commands` and `run_setup_commands` so the test focuses purely on which list (if any) gets passed downstream. Cover the table in the step doc.
>
> Run the three required quality checks per `.claude/CLAUDE.md`. One commit, message: `Resolve setup commands per platform with Darwin→Linux fallback (#963)`.
