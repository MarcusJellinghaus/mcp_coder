# Step 4 — Layer discovery (`_discover_layers`)

See [summary.md](./summary.md). Locate the three settings files in precedence
order; skip absent layers silently; never touch `.claude/*`.

## WHERE
- `src/mcp_coder/icoder/permissions/loader.py` (extend)
- `tests/icoder/test_permissions_loader.py` (extend)

Add `from pathlib import Path` and
`from mcp_coder.utils.user_app_data import get_user_app_data_dir`.

## WHAT
```python
def _discover_layers(project_dir: Path) -> list[tuple[str, Path]]:
    """Return (layer_tag, path) for each existing settings file, ordered
    lowest -> highest precedence: user, project, local. Absent files omitted."""
```

## HOW
- `user`  → `get_user_app_data_dir("mcp_coder") / ".icoder" / "settings.json"`
- `project` → `project_dir / ".icoder" / "settings.json"`
- `local` → `project_dir / ".icoder" / "settings.local.json"`
- Include a tuple only when `path.is_file()`.
- **Resolve each candidate path to absolute** (`.resolve()`) so the stored
  `Rule.source_path` provenance is absolute (issue #1042 Decisions + Loop-A
  refinement); `get_user_app_data_dir` is already absolute, but a relative
  `project_dir` would otherwise yield relative project/local paths.

## ALGORITHM
```
candidates = [
    ("user",    get_user_app_data_dir("mcp_coder")/".icoder"/"settings.json"),
    ("project", project_dir/".icoder"/"settings.json"),
    ("local",   project_dir/".icoder"/"settings.local.json"),
]
# .resolve() so provenance (Rule.source_path) is absolute (issue #1042 Decisions).
return [(tag, p.resolve()) for tag, p in candidates if p.is_file()]
```

## DATA
`list[tuple[str, Path]]` — layer tag paired with its absolute path, ordered
lowest → highest precedence.

## TESTS (write first)
- All three present → three tuples in exactly `user, project, local` order.
- Only `project` present → single `("project", ...)` tuple (no error).
- None present → empty list.
- User layer resolves under `get_user_app_data_dir` (monkeypatch the helper to a
  tmp dir and assert the returned path sits under it).
- A `.claude/settings.json` in the project dir is **never** returned (assert no
  discovered path contains `.claude`).
- Passing a **relative** `project_dir` still yields absolute discovered paths
  (assert every returned `path.is_absolute()`).

## VERIFICATION
All four MCP checks pass.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement Step 4
> with TDD: add discovery tests (three-layer order, partial presence, empty,
> user-layer under `get_user_app_data_dir`, `.claude` never read) first, then add
> `_discover_layers` to `loader.py` per the algorithm. Use MCP workspace file
> tools. Run all four MCP checks; fix until green. Single commit.
