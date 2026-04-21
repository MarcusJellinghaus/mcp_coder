# Step 1 — Replace Shared Libraries section in CLAUDE.md

## Context

See `pr_info/steps/summary.md` for issue context.
This is the only step — a single documentation edit.

## TDD Applicability

**Not applicable.** This is a markdown content change with no code or testable logic.

## WHERE

- `.claude/CLAUDE.md` — lines 103–105 (the `## Shared Libraries` heading and its single paragraph)

## WHAT

Replace the current section:

```markdown
## Shared Libraries

`subprocess_runner`, `subprocess_streaming`, and `log_utils` in `src/mcp_coder/utils/` are thin shims over `mcp-coder-utils`. Always import through the local shims (`from mcp_coder.utils.<module> import ...`), not from `mcp_coder_utils` directly. Enforced by import-linter (`mcp_coder_utils_isolation` contract).
```

With the expanded version from issue #887:

```markdown
## Shared Libraries

This repo uses `mcp-coder-utils` for subprocess execution, logging, and redaction. Three shim modules in `src/mcp_coder/utils/` re-export the upstream API:

| Shim module | Upstream module | Key imports |
|-------------|-----------------|-------------|
| `mcp_coder.utils.subprocess_runner` | `mcp_coder_utils.subprocess_runner` | `execute_command`, `execute_subprocess`, `CommandResult`, `CommandOptions`, `launch_process`, `prepare_env` |
| `mcp_coder.utils.subprocess_streaming` | `mcp_coder_utils.subprocess_streaming` | `stream_subprocess`, `StreamResult` |
| `mcp_coder.utils.log_utils` | `mcp_coder_utils.log_utils` + `redaction` | `setup_logging`, `log_function_call`, `OUTPUT`, `REDACTED_VALUE`, `RedactableDict` |

**Rules:**
- Always import through the local shims (`from mcp_coder.utils.<module> import ...`), never from `mcp_coder_utils` directly. Enforced by import-linter (`mcp_coder_utils_isolation` contract).
- Do not reimplement utilities that exist in mcp-coder-utils. When in doubt, check the source first.
- Full source: reference project `p_coder-utils` — use `mcp__workspace__read_reference_file`.
```

## HOW

Single `edit_file` call replacing old text with new text.

## Verification

Run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`, `mcp__tools-py__run_mypy_check` to confirm no regressions (expected: no impact from a markdown-only change).

## Commit

```
docs: expand CLAUDE.md shared libraries section (#887)
```

## LLM Prompt

```
Implement step 1 from pr_info/steps/step_1.md (see pr_info/steps/summary.md for context).

Edit .claude/CLAUDE.md: replace the current ## Shared Libraries section (single paragraph on line 105) with the expanded version specified in step_1.md. Use mcp__workspace__edit_file. Then run all three quality checks.
```
