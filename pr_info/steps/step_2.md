# Step 2 — Copilot: collapse `execution_dir` into `cwd`

**Context:** [summary.md](./summary.md), section "Provider layer: the honest name at each layer".

`prompt_llm` passes the *identical* value to Copilot's `cwd` and `execution_dir`
(`interface.py:223`/`:227` and `:393`/`:397`). Two parameters, one value, distinguished only by
which side effect they enable. Collapse them into `cwd`. Independent of every other step.

## WHERE

| File | Symbols |
|---|---|
| `src/mcp_coder/llm/providers/copilot/copilot_cli.py` | `_read_settings_allow` (`:230`), `ask_copilot_cli` (`:271`, docstring `:284`, use `:317`) |
| `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` | `ask_copilot_cli_stream` (`:110`, docstring `:126`, use `:154`) |
| `src/mcp_coder/llm/interface.py` | copilot branches only (`:227`, `:397`) |
| `tests/llm/test_interface.py` | copilot kwarg assertions only: `execution_dir=None` at `:1989` and `:2012`, both in `TestPromptLlmCopilotRouting` (class at `:1963`) |
| `tests/llm/providers/copilot/` | `test_copilot_integration.py:69` and any unit test passing `execution_dir=` |

## WHAT

```python
# copilot_cli.py
def _read_settings_allow(cwd: str | None) -> list[str] | None: ...

def ask_copilot_cli(question, session_id=None, timeout=..., env_vars=None,
                    cwd=None, logs_dir=None, branch_name=None,
                    system_prompt=None) -> LLMResponseDict: ...
```

The second parameter is deleted; the body's `_read_settings_allow(execution_dir)` becomes
`_read_settings_allow(cwd)`. Same change in `ask_copilot_cli_stream`. Merge the two docstring
lines into one on `cwd`, e.g.:

```
cwd: Working directory for the Copilot subprocess; also the directory
    .claude/settings.local.json is read from.
```

## HOW — integration points

- `interface.py`: delete `execution_dir=execution_dir,` from both copilot call sites. `cwd=`
  already carries the value, so no other edit is needed there.
- `prompt_llm` / `prompt_llm_stream` signatures are **untouched** in this step.
- Keep the existing behaviour note in the summary's Constraints: Copilot still ignores the
  resolved `settings_file` and re-derives `<dir>/.claude/settings.local.json`. **Do not fix
  that here** — it is explicitly out of scope for #1132.

## ALGORITHM

No logic change. The only semantic statement being made is
`execution_dir == cwd` at this layer, which the two call sites already guaranteed.

## DATA

No return values or data structures change.

## TDD

1. **Tests first.** Drop `execution_dir=` from Copilot call sites and expected-kwargs dicts in
   `tests/llm/test_interface.py` (copilot assertions only) and the copilot provider tests. If a
   test asserts `_read_settings_allow` was called with the execution dir, retarget it to `cwd`.
2. Run the suite — expect failures only in the tests just edited.
3. **Implementation.** Delete the parameter from the two public functions, rename
   `_read_settings_allow`'s parameter, and remove the two `interface.py` lines.
4. Quality gate (all three MCP checks). `copilot_cli_integration`-marked tests are excluded
   from the fast run; grep them for `execution_dir` and fix in this step if present.

## Commit

```
Collapse copilot execution_dir into cwd

prompt_llm passed the identical value to both parameters. Part of #1132.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`, then implement step 2 only.
>
> In `src/mcp_coder/llm/providers/copilot/copilot_cli.py` and `copilot_cli_streaming.py`,
> delete the `execution_dir` parameter from `ask_copilot_cli` and `ask_copilot_cli_stream` and
> rename `_read_settings_allow`'s parameter to `cwd`, so the single existing `cwd` parameter
> serves both purposes. Merge the two docstring lines into one. In
> `src/mcp_coder/llm/interface.py`, stop passing `execution_dir=` in the two copilot branches
> **only** — do not change `prompt_llm`'s or `prompt_llm_stream`'s own signature (step 4).
> Do not touch Copilot's handling of `settings_file`; that is out of scope for #1132.
>
> Follow TDD: update the copilot assertions in `tests/llm/test_interface.py` and the tests
> under `tests/llm/providers/copilot/` first, then make the source change.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass. One commit for this step.

## Implementation note (2026-08-29)

Change applied as specified: `execution_dir` deleted from `ask_copilot_cli` /
`ask_copilot_cli_stream`, `_read_settings_allow`'s parameter renamed to `cwd`, docstring lines
merged, and the two `execution_dir=` keywords removed from the copilot branches in
`interface.py`. Tests updated first (`tests/llm/test_interface.py` copilot kwarg assertions,
`tests/llm/providers/copilot/test_copilot_integration.py:69`). No other caller passed the
parameter.

**Quality gate caveat — pre-existing environment breakage, not caused by this step.** The
installed `mcp-workspace` package is older than what `main` requires:
`src/mcp_coder/checks/branch_status.py:17` imports
`mcp_workspace.checks.branch_status_rendering`, which does not exist in the installed copy.
Because `mcp_coder/__init__.py:37` imports that module, **every** test module fails at
collection, so pytest cannot run at all until the dependency is reinstalled
(`mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git`). The same
breakage produces the pylint `E0401` / mypy `import-not-found` entries, plus the
`fail_on_reviews` / `pr_feedback_undeterminable` `E1123` / `call-arg` errors in
`cli/commands/check_branch_status.py`, `workflows/create_pr/core.py` and
`workflows/review/core.py`. Pylint and mypy report **no** issues in
`src/mcp_coder/llm/` — i.e. none attributable to this step.
