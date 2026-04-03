# Step 1: Config layer — add `find_repo_section_by_url()`

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/utils/user_config.py` — new function
- `tests/utils/test_user_config.py` — new test class

## WHAT

### New function in `user_config.py`

```python
def find_repo_section_by_url(repo_url: str) -> str | None:
    """Scan all [coordinator.repos.*] sections for matching repo_url.

    Normalizes URLs before comparison (strips trailing .git and slash).
    
    Args:
        repo_url: Repository URL to match (e.g., "https://github.com/org/repo")

    Returns:
        Section name like "coordinator.repos.mcp_coder", or None if no match.
    """
```

## HOW
- Import `load_config` (already available in-module)
- No new imports needed
- Function is standalone, no decorators

## ALGORITHM (pseudocode)
```
def find_repo_section_by_url(repo_url):
    normalized_input = strip_trailing_git_and_slash(repo_url)
    config = load_config()
    repos = config.get("coordinator", {}).get("repos", {})
    for repo_name, repo_data in repos.items():
        config_url = repo_data.get("repo_url", "")
        if strip_trailing_git_and_slash(config_url) == normalized_input:
            return f"coordinator.repos.{repo_name}"
    return None
```

## DATA
- **Input:** `repo_url: str` — a GitHub URL in any format (with/without `.git`, trailing slash)
- **Output:** `str | None` — the dot-notation section name, or `None`
- **URL normalization:** strip trailing `.git` then trailing `/` (covers `https://github.com/org/repo.git`, `https://github.com/org/repo/`, `https://github.com/org/repo`)

## TESTS (TDD — write first)

New class `TestFindRepoSectionByUrl` in `tests/utils/test_user_config.py`:

1. **`test_find_repo_section_exact_match`** — config has `repo_url = "https://github.com/org/repo.git"`, input is same → returns `"coordinator.repos.repo_name"`
2. **`test_find_repo_section_normalizes_git_suffix`** — config URL has `.git`, input doesn't (and vice versa) → match
3. **`test_find_repo_section_normalizes_trailing_slash`** — config URL has trailing `/`, input doesn't → match
4. **`test_find_repo_section_no_match`** — input URL not in config → returns `None`
5. **`test_find_repo_section_empty_config`** — no `[coordinator]` section → returns `None`
6. **`test_find_repo_section_multiple_repos_returns_correct`** — two repos in config, matches the right one

All tests use `tmp_path` + `monkeypatch` to mock `get_config_file_path` (same pattern as existing tests).

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1: add find_repo_section_by_url() to user_config.py.

1. Write tests FIRST in tests/utils/test_user_config.py (new TestFindRepoSectionByUrl class)
2. Implement find_repo_section_by_url() in src/mcp_coder/utils/user_config.py
3. Add it to the module's imports if needed
4. Run all code quality checks (pylint, pytest, mypy)
5. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: add find_repo_section_by_url to user_config (#661)

Add helper that scans [coordinator.repos.*] sections in config.toml
to find a repo section matching a given URL. Normalizes URLs by
stripping trailing .git and slash before comparison.
```
