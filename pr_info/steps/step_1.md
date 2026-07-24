# Step 1 — `utils/repo_config.py`: `get_repo_flag` primitive

**Read `pr_info/steps/summary.md` first** (§1 New utils-level config primitive). This step creates
the single shared primitive that steps 2, 3, and 6 consume. TDD: write the tests first, then the
implementation.

## WHERE
- Create `src/mcp_coder/utils/repo_config.py`
- Create `tests/utils/test_repo_config.py`

## WHAT
```python
# src/mcp_coder/utils/repo_config.py
def get_repo_flag(project_dir: Path, key: str, default: bool = False) -> bool:
    """Resolve a boolean [coordinator.repos.*] flag for a project's git remote.

    Maps project_dir -> git remote https URL -> matching repo config section ->
    typed bool flag value. Returns `default` when the repo has no remote, no
    matching section, or the flag is unset / non-boolean.
    """
```

## HOW (imports / layering)
- `from pathlib import Path`
- `from mcp_coder.mcp_workspace_git import get_repository_identifier` (one layer below `utils` — legal)
- `from .user_config import find_repo_section_by_url, get_config_values` (same layer)
- This mirrors the existing pattern in `cli/utils.py:resolve_issue_interaction_flags`.
- **Do NOT** modify `resolve_issue_interaction_flags` (intentionally left as-is — see summary §1).
- Add a module logger; no logging required beyond optional debug.

## ALGORITHM
```
identifier = get_repository_identifier(project_dir)
repo_url = identifier.https_url if identifier else None
if not repo_url: return default
section = find_repo_section_by_url(repo_url)
if not section: return default
value = get_config_values([(section, key, None)])[(section, key)]
return value if isinstance(value, bool) else default
```

## DATA
- Returns `bool`.

## TESTS (`tests/utils/test_repo_config.py`)
Mock `get_repository_identifier`, `find_repo_section_by_url`, `get_config_values` at
`mcp_coder.utils.repo_config.*`. Cover:
1. Flag set `True` in section → returns `True`.
2. Flag set `False` in section → returns `False`.
3. Flag unset (`None`) → returns `default` (test both default=False and default=True).
4. No matching section (`find_repo_section_by_url` returns `None`) → returns `default`.
5. No git remote (`get_repository_identifier` returns `None`) → returns `default`.
6. Non-boolean value → returns `default`. Note: in production `get_config_values` validates
   values against the FieldDef schema and **raises `ValueError`** on a type mismatch, so a real
   non-bool never reaches `get_repo_flag`'s `isinstance` guard. This test still stands because it
   mocks `get_config_values` to return a non-bool directly, and the `isinstance(value, bool)` guard
   remains sound defensive code — just don't describe it as a real-world code path.

## Commit
One commit: new module + tests. Run pylint, pytest (`-n auto` unit exclusion pattern), mypy,
`lint-imports`.
