# Step 5 — Declare this repo's post-install checks

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` only.
> Run pylint, mypy and the fast unit pytest set (see CLAUDE.md). All must pass. Run
> the formatter, then make one commit.

## WHERE
- `pyproject.toml`: the existing `[tool.mcp-coder.install]` section (around line 407)

## WHAT
```toml
[tool.mcp-coder.install]
# Extras `mcp-coder install` passes to `uv` when provisioning this repo.
extras = "dev"
# Run by `mcp-coder install` after provisioning; any failure fails the install.
post_install_checks = [
    ["mcp-coder", "--version"],
    ["mcp-workspace", "--version"],
    ["mcp-tools-py", "--version"],
]
```

## HOW
- `mcp-config` is deliberately left out: it is not a dependency of this repo.
- Sanity check: `get_post_install_checks(Path("."), strict=True)` returns the three
  tuples. A unit test is not needed; any existing test that reads this repo's
  pyproject must still pass.

## ALGORITHM / DATA
None.
