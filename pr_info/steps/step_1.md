# Step 1 — Bump `mcp-coder-utils` dependency

## Goal

Pull in the upstream `stream_subprocess` stdin fix
(MarcusJellinghaus/mcp-coder-utils#26) so that `ask_claude_code_cli_stream()`
actually pipes the prompt to the Claude CLI subprocess.

## WHERE

- File: `pyproject.toml`
- Section: `[project] → dependencies`

## WHAT

Single-line edit. Change:

```toml
"mcp-coder-utils>=0.1.3",
```

to the released version containing PR #26, e.g.:

```toml
"mcp-coder-utils>={FIXED_VERSION}",
```

> **Operator action required**: replace `{FIXED_VERSION}` with the actual
> release tag from `mcp-coder-utils` that contains PR #26. Confirm via
> the upstream changelog or `pip index versions mcp-coder-utils` before
> committing.

## HOW

No code changes, no imports, no new tests. The bump is purely a constraint
update; existing unit tests already cover `stream_subprocess` behavior with
mocks, and Step 3 will add real-CLI coverage.

## ALGORITHM

Not applicable — single-line dependency edit.

## DATA

Not applicable — no data structures change.

## Validation

After editing `pyproject.toml`:
1. Reinstall the dev environment so the new version is resolved
   (e.g. `pip install -e .[dev]` or `uv sync`).
2. Run all three quality checks:
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__tools-py__run_mypy_check`
3. All checks must pass before committing.

## Commit

One commit titled e.g.:
`Bump mcp-coder-utils to {FIXED_VERSION} for stream_subprocess stdin fix (#916)`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement
> Step 1 only: bump the `mcp-coder-utils` dependency in `pyproject.toml` to
> the version containing upstream PR #26. Ask the user for the exact version
> if unknown. Run pylint, pytest (with the unit-test exclusion marker
> pattern), and mypy via the MCP quality-check tools. All three must pass
> before producing one commit for this step. Do not modify anything outside
> `pyproject.toml`.
