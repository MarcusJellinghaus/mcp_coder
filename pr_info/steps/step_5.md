# Step 5 — `alwaysLoad: true` in `.mcp.json` and `.mcp.macos.json`

> Read `pr_info/steps/summary.md` first, then this step.

## Goal

Add `"alwaysLoad": true` to the `mcp-tools-py` and `mcp-workspace` server configs in **both** `.mcp.json` and `.mcp.macos.json`. Both files define exactly these two MCP servers — there is no third server to consider. (`obsidian-dev-wiki` is **not** an MCP server in either file; it appears only as a `--reference-project` path argument inside the `mcp-workspace` server config in `.mcp.macos.json`. It's a path, not a server entry.)

Effective once Claude CLI ≥ 2.1.121 lands on runners; silently ignored on older versions.

This step satisfies AC #5.

## TDD

No automated test for static JSON config. Verification = JSON parses + the new key is on the right two servers.

## WHERE

| Path | Action |
|---|---|
| `.mcp.json` | Modify (2 server entries — the only servers in the file) |
| `.mcp.macos.json` | Modify (2 server entries — the only servers in the file) |

## WHAT

In each file, for each of the two named servers, add a top-level `"alwaysLoad": true` member alongside `"command"`, `"args"`, `"env"`, etc.

Conventional placement: at the **end** of the server block (after `"env"`), to minimize diff churn:

```jsonc
"mcp-tools-py": {
  "type": "stdio",
  "command": "...",
  "args": [...],
  "env": {...},
  "alwaysLoad": true
}
```

Same pattern for `mcp-workspace` in both files.

> **Trailing-comma note (JSON syntax):** when inserting `"alwaysLoad": true` after the existing `"env": {...}` block, the closing `}` line of `"env"` must gain a trailing comma (it currently has none, since `"env"` is presently the last key). The new `"alwaysLoad": true` line itself does **not** get a trailing comma — it becomes the new last key in the server block. Forgetting either rule will break JSON parse.

## HOW (integration points)

- Read directly by Claude Code CLI when launching MCP servers. Not consumed by any mcp-coder Python code.
- No JSON-validity tooling in the repo to satisfy — but ensure trailing comma rules are kept (`alwaysLoad: true` is the **last** key in each block, no trailing comma).
- Verify both files still parse as valid JSON after the edit (e.g., `python -c "import json; json.load(open('.mcp.json'))"` and same for the macos file). The Python tests don't load these JSONs, so a manual parse check is enough.

## ALGORITHM

n/a — JSON property addition.

## DATA

```jsonc
// Two new key-value pairs per file:
"alwaysLoad": true
```

## Quality gates before committing

1. Manually verify both JSON files parse: `python -c "import json; json.load(open('.mcp.json'))"` and same for `.mcp.macos.json`. Both must succeed.
2. `./tools/format_all.sh` (no-op on JSON, but harmless).
3. `mcp__tools-py__run_pylint_check`
4. `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
5. `mcp__tools-py__run_mypy_check`

All must pass.

## Commit message

```
chore(mcp): add alwaysLoad: true to mcp-tools-py and mcp-workspace

Adds "alwaysLoad": true to mcp-tools-py and mcp-workspace in both
.mcp.json and .mcp.macos.json. These are the only MCP servers
defined in either file. Effective on Claude CLI v2.1.121+, silently
ignored on older versions.

Refs #944
```

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement Step 5 only — add `"alwaysLoad": true` as the last key inside each of the `mcp-tools-py` and `mcp-workspace` server blocks in **both** `.mcp.json` and `.mcp.macos.json`. These are the only MCP servers in either file (`obsidian-dev-wiki` is a `--reference-project` argument, not a server, so there is nothing to leave alone). Mind the trailing-comma note in step_5.md — the previous last key (`"env"`) needs a trailing comma added; `"alwaysLoad"` itself takes none. Verify both files parse as valid JSON. Run the quality gates (format, pylint, pytest with standard exclusions, mypy) — all must pass. Make exactly one commit using the message in step_5.md. Do not touch any other files in this step.
