# Step 2 — `resolve_execution_dir`: `project_dir` parameter + deprecation warning

**Depends on:** the pre-flight marker probe only. **Step 1 is independent of this step** —
either may be committed first; the numbering is presentational, and summary.md's ordering note
says the same. Step 3 is the first step that needs both.

**Goal:** teach the resolver the new default and emit the deprecation notice.
**Backwards compatible on purpose** — all nine call sites still pass one argument after this
step, so every existing test stays green. Step 4 flips the actual behaviour.

---

## WHERE

- `src/mcp_coder/cli/utils.py` — `resolve_execution_dir` (currently `:347-390`)
- `tests/cli/test_utils.py` — extend `class TestResolveExecutionDir` (`:220`)

## WHAT

```python
def resolve_execution_dir(
    execution_dir: str | None,
    project_dir: str | Path | None = None,
) -> Path:
```

Mirrors `resolve_mcp_config_path` (`:161`) and `resolve_claude_settings_path` (`:248`), which
took this same fix in #977 and #981.

`project_dir` is **optional, not required.** The guarantee rests on all nine call sites passing
it (Step 4), not on the type checker — a required parameter was considered and rejected as
needless churn given #1132 deletes the `execution_dir` parameter entirely.

## HOW

- `import warnings` at the top of `cli/utils.py`.
- No change to `__all__` (already lists `resolve_execution_dir`).
- Update the docstring at `:352` and the doctest example at `:363-364` — both currently state
  the old default.

## ALGORITHM

```
if execution_dir is None:
    if project_dir is None: return Path.cwd()          # no anchor available
    return Path(project_dir).resolve()                 # RESOLVE, do not validate

warnings.warn("--execution-dir is deprecated ... removal tracked in #1132",
              DeprecationWarning, stacklevel=2)
logger.warning("--execution-dir is deprecated ... see #1132")
<existing body unchanged: relative -> Path.cwd()/path, exists() check, return path.resolve()>
```

### Three things that must not change

1. **Do not existence-validate the `project_dir` default.** `commit.py:80` builds
   `Path(args.project_dir)` without `.resolve()`, so the default must be resolved or a relative
   `--project-dir sub` reaches the subprocess as a relative cwd. But *validating* it would
   break `commit.py`'s error ordering, where `validate_git_repository` (`:83`) owns the message
   for a bad `project_dir`. `project_dir` is already validated by each command's own path.
2. **Relative `--execution-dir` still resolves against `Path.cwd()`**, not `project_dir`. The
   issue does not ask to change this and `test_existing_relative_path`
   (`tests/cli/test_utils.py:237`) pins it.
3. **Both warning channels are required.** Python ignores `DeprecationWarning` by default
   unless raised from `__main__`, and this is raised inside `cli/utils.py` — so the log line is
   what the operator actually sees. The `DeprecationWarning` is what tooling and `-W error` runs
   see. Neither alone is sufficient. Both messages must contain the string `#1132`.

## DATA

Returns `Path`, always absolute. Never `None`, never relative.

| `execution_dir` | `project_dir` | result | warns |
|---|---|---|---|
| `None` | `None` | `Path.cwd()` | no |
| `None` | `X` | `Path(X).resolve()`, not validated | no |
| `"/abs"` | anything | `Path("/abs").resolve()`, validated | **yes** |
| `"rel"` | anything | `(Path.cwd() / "rel").resolve()`, validated | **yes** |

## TESTS (write first)

Add to `TestResolveExecutionDir` in `tests/cli/test_utils.py`:

1. `test_none_with_project_dir_returns_project_dir` — `resolve_execution_dir(None, project_dir=tmp_path)` → `tmp_path.resolve()`.
2. `test_project_dir_accepts_str_and_path` — both forms give the same result.
3. `test_relative_project_dir_is_resolved` — `monkeypatch.chdir(tmp_path)`; `resolve_execution_dir(None, project_dir="sub")` → `(tmp_path / "sub").resolve()`, absolute. **Pins the `commit.py` case.**
4. `test_nonexistent_project_dir_is_not_validated` — `resolve_execution_dir(None, project_dir="/no/such/dir")` returns without raising. **Pins the deliberate non-validation.**
5. `test_explicit_execution_dir_wins_over_project_dir` — `resolve_execution_dir(str(tmp_path/"a"), project_dir=tmp_path/"b")` → the `a` path.
6. `test_explicit_execution_dir_warns_deprecation` — `pytest.warns(DeprecationWarning, match="1132")`.
7. `test_explicit_execution_dir_logs_deprecation` — `caplog` at `WARNING` contains `1132`.
8. `test_default_does_not_warn` — `warnings.catch_warnings(record=True)` around
   `resolve_execution_dir(None, project_dir=tmp_path)` records no `DeprecationWarning`.

**Update, do not delete:**

- `tests/cli/test_utils.py:223-228` `test_none_returns_cwd` — still passes (one positional arg
  ⇒ `project_dir=None`). Change its docstring to say it documents the *no-`project_dir`*
  fallback, not the default.
- `tests/integration/test_execution_dir_integration.py:154-166` `test_resolve_none_returns_cwd`
  — same treatment.

## Expected new warnings in the pytest summary

Three existing test groups execute the `execution_dir is not None` branch and will now emit
`DeprecationWarning`: `tests/cli/test_utils.py:230-272`,
`tests/integration/test_execution_dir_integration.py:168-220`, and `:234-281`. `pyproject.toml`
sets no `filterwarnings` and none of these assert on warning output, so pytest lists them
without failing. **This is expected — do not add `filterwarnings` to silence them.**

Five other groups pass the flag only through `parse_args` and never reach the warning
(`tests/cli/test_main.py:449-515`, `:687`, `:709`;
`tests/icoder/test_cli_icoder_parser.py:41-44`;
`tests/integration/test_execution_dir_integration.py:50-146`).

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Add project_dir parameter and deprecation warning to resolve_execution_dir (#1113)

Optional project_dir becomes the default execution directory when no
--execution-dir is given, mirroring resolve_mcp_config_path (#977) and
resolve_claude_settings_path (#981). The default is resolved but not
existence-validated, preserving commit.py's error ordering.

Explicit --execution-dir now warns via both DeprecationWarning and
logger.warning, naming #1132. Call sites still pass one argument; the
default flips in a later step.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially "1. The anchor moves from the shell to the
> project" and "2. Deliberate non-validation of the default") and `pr_info/steps/step_2.md`,
> then implement Step 2.
>
> Change `resolve_execution_dir` in `src/mcp_coder/cli/utils.py:347` to
> `resolve_execution_dir(execution_dir: str | None, project_dir: str | Path | None = None) -> Path`.
> When `execution_dir` is None and `project_dir` is given, return `Path(project_dir).resolve()`
> — **resolved but NOT existence-validated**; when both are None, keep returning `Path.cwd()`.
> When `execution_dir` is given, emit the deprecation notice **both** as
> `warnings.warn(..., DeprecationWarning, stacklevel=2)` and `logger.warning`, each naming
> `#1132`, then run the existing body unchanged.
>
> Do not change how a relative `--execution-dir` resolves (still against `Path.cwd()`). Update
> the docstring and the doctest example at `:363-364`.
>
> Follow TDD: write the eight tests listed under TESTS in `tests/cli/test_utils.py` first
> (extend the existing `TestResolveExecutionDir` class at `:220`), watch them fail, then
> implement.
>
> Do not change any call site in this step — every existing call still passes one argument, so
> the whole suite must stay green. Three existing test groups will newly emit
> `DeprecationWarning` in the pytest summary; that is expected — do not add `filterwarnings`.
> Update the docstrings of `test_none_returns_cwd` in `tests/cli/test_utils.py:223` and
> `test_resolve_none_returns_cwd` in `tests/integration/test_execution_dir_integration.py:154`
> to say they document the no-`project_dir` fallback.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md) and `run_mypy_check`. Fix
> everything before finishing. One commit.
