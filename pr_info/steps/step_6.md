# Step 6: Add `[tool.mcp-coder.from-github]` to pyproject.toml

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step adds the GitHub package override configuration to this repo's
> `pyproject.toml`, declaring which MCP packages can be installed from GitHub.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 6.

Add the `[tool.mcp-coder.from-github]` section to `pyproject.toml` with the
package specs from the issue. No tests needed for this step (it's declarative
config). Run all three code quality checks to ensure nothing breaks.
```

## Files to Modify

### Implementation

**`pyproject.toml`**

- WHERE: After existing `[tool.*]` sections (e.g., after `[tool.ruff.lint.pydocstyle]`)
- WHAT: Add `[tool.mcp-coder.from-github]` section
- HOW: Append TOML section

```toml
[tool.mcp-coder.from-github]
# Installed WITH deps (leaves — picks up new external deps)
packages = [
    "mcp-config-tool @ git+https://github.com/MarcusJellinghaus/mcp-config.git",
    "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git",
]
# Installed WITHOUT deps (depend on siblings — avoid downgrading)
packages-no-deps = [
    "mcp-tools-py @ git+https://github.com/MarcusJellinghaus/mcp-tools-py.git",
]
```

## Data

- `packages`: list of PEP 440 direct-reference specs with `git+https://` URLs
  - `mcp-config-tool`: MCP config server (leaf — no sibling deps)
  - `mcp-workspace`: MCP workspace server (leaf — no sibling deps)
- `packages-no-deps`: list of specs installed with `--no-deps`
  - `mcp-tools-py`: depends on siblings, `--no-deps` prevents downgrading them

## Verification

- `pyproject.toml` is valid TOML (parseable by `tomllib`)
- All existing tests still pass
- pylint, mypy, pytest all green
