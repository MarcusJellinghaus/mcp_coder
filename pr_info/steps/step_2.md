# Step 2 — Tests that call the real probe

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only.
> This step adds tests only; no `src/` change is expected. Run pylint, mypy, and the
> fast pytest suite (`-n auto`, unit markers excluded) and fix until all pass. Format
> with `run_format_code`, then make exactly one commit.

## Precondition

If these tests fail because the installed mcp-workspace lacks `code_scanning_alerts`
or uses different value strings, do not weaken or skip them: write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

New file `tests/cli/commands/test_verify_github_security_probe.py`.

## WHAT

```python
_SECTIONS = "mcp_coder.cli.commands.verify_sections"
_PROBES = "mcp_workspace.github_operations._security_probes"  # string patch target, tests only

def _render(project_dir: Path, repo: MagicMock | None) -> str:
    """Run the GITHUB SECURITY section through the real probe; return stdout lines."""

def _row(output: str, label: str) -> str:
    """Return the single output line containing `label`."""

class TestRealProbeCodeScanning:
    @pytest.mark.parametrize(...)
    def test_code_scanning_row(...) -> None: ...

class TestRealProbeRepoUnresolvable:
    def test_all_api_rows_not_accessible(...) -> None: ...
```

## HOW

- Imports: `GithubException` and `verify_github_security` from the shim
  `mcp_coder.mcp_workspace_github` (never `import github`);
  `_print_github_security_section` from `verify_sections`; `STATUS_SYMBOLS` from
  `verify_formatting`.
- Re-patch the autouse mock: `patch(f"{_SECTIONS}.verify_github_security", verify_github_security)`.
- Patch `f"{_PROBES}.BaseGitHubManager"`:
  - repo case: `mock_cls.return_value._get_repository.return_value = repo`
  - unresolvable case: `side_effect=ValueError("no token")`
- No live calls.

## ALGORITHM

```
repo = MagicMock(); repo.url = "https://api.github.com/repos/o/r"
repo.requester.requestJson.return_value = (204, {}, None)      # Dependabot alerts probe
repo.security_and_analysis = None                               # other three probes
repo.requester.requestJsonAndCheck.side_effect = <case>         # code-scanning probe
output = _render(tmp_path, repo); line = _row(output, "Code scanning alerts")
assert expected marker and expected value in line
```

## DATA — parametrized cases (`side_effect`, marker, value text)

| Case | `requestJsonAndCheck.side_effect` | Marker | Value in line |
|---|---|---|---|
| 200 | `None` | `[OK]` | `scope present` |
| 403 | `GithubException(403, {"message": "x"}, None)` | `[ERR]` | `scope missing or Advanced Security not enabled` |
| 404 | `GithubException(404, {"message": "x"}, None)` | `[WARN]` | `scope missing or not configured` |
| error | `ConnectionError("boom")` | `[WARN]` | `not accessible (network error: boom)` |

Assert on the code-scanning row only (the other four rows are fed by the mock too).

Repo-unresolvable test: `BaseGitHubManager` raises `ValueError`; for each of the five
labels (Dependabot alerts, Dependabot security, Secret scanning, Secret push
protection, Code scanning alerts) the line contains `[WARN]` and
`not accessible (repository not accessible)`. To tell `Secret scanning` from
`Secret push protection`, match the row prefix (line starts with `"  " + label`
padded) or check `Secret push protection` first and exclude it.
