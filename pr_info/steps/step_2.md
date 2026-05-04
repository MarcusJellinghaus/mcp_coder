# Step 2 — Wire GIT section into `mcp-coder verify`

> **Reference:** [`pr_info/steps/summary.md`](./summary.md) — Architecture & file overview.
> **Depends on:** Step 1 (shim re-export must already be merged).

## Goal

Add a `=== GIT ===` section to `mcp-coder verify` between PROJECT and GITHUB, route its `overall_ok` into the exit code (provider-independent), and cover the wiring with a unit smoke test plus an integration test.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | Import `verify_git`; extend `_LABEL_MAP` (13 entries); extend `_compute_exit_code` signature; insert `0d` GIT section in `execute_verify`; renumber GitHub comment `0d`→`0e` |
| `tests/cli/commands/test_verify_orchestration.py` | Add `_mock_git` autouse fixture |
| `tests/cli/commands/test_verify_format_section_basic.py` | Add `TestGitLabelMappings` class |
| `tests/cli/commands/test_verify_integration.py` | Add `git_integration`-marked test for gpgsign-without-key |

## WHAT

### 1. Import (verify.py, near `verify_github` import ~line 18)

```python
from ...mcp_workspace_git import verify_git
```

### 2. `_LABEL_MAP` extension (verify.py, after the GitHub keys block)

```python
# Git section
"git_binary": "Git binary",
"git_repo": "Repository",
"user_identity": "Git identity",
"signing_intent": "Signing enabled",
"signing_consistency": "Signing config consistent",
"signing_format": "Signing format",
"signing_key": "Signing key",
"signing_binary": "Signing binary",
"signing_key_accessible": "Signing key accessible",
"agent_reachable": "GPG agent",
"allowed_signers": "Allowed signers file",
"verify_head": "HEAD signature",
"actual_signature": "End-to-end sign test",
```

### 3. `_compute_exit_code` signature

```python
def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
    test_prompt_ok: bool = True,
    mcp_result: dict[str, Any] | None = None,
    config_has_error: bool = False,
    claude_mcp_ok: bool | None = None,
    github_result: dict[str, Any] | None = None,
    git_result: dict[str, Any] | None = None,   # NEW
) -> int:
```

Add a new early-reject block (provider-independent), placed adjacent to the existing `github_result` check:

```python
# Git failure always means exit 1 (provider-independent)
if git_result is not None and not git_result.get("overall_ok"):
    return 1
```

Update the docstring's `Args:` block with `git_result`.

### 4. Section wiring in `execute_verify` (between PROJECT and GITHUB)

```python
# 0d. Git verification section
git_result = verify_git(project_dir, actually_sign=True)
print(_format_section("GIT", git_result, symbols))

# 0e. GitHub verification section   <-- renumbered comment
github_result = verify_github(project_dir)
...
```

Update the existing `_compute_exit_code(...)` call at the bottom of `execute_verify` to pass `git_result=git_result`.

### 5. Orchestration test fixture (`test_verify_orchestration.py`)

Add an autouse fixture parallel to the existing `_mock_github`:

```python
@pytest.fixture(autouse=True)
def _mock_git(self) -> Any:
    """Default: verify_git returns neutral ok result."""
    with patch(f"{_VERIFY}.verify_git", return_value={"overall_ok": True}):
        yield
```

### 6. Unit smoke test (`test_verify_format_section_basic.py`, append a new class)

```python
class TestGitLabelMappings:
    """Tests for GIT section label mappings and rendering."""

    _GIT_KEYS = (
        "git_binary", "git_repo", "user_identity",
        "signing_intent", "signing_consistency", "signing_format",
        "signing_key", "signing_binary", "signing_key_accessible",
        "agent_reachable", "allowed_signers", "verify_head",
        "actual_signature",
    )

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_all_git_keys_in_label_map(self) -> None:
        from mcp_coder.cli.commands.verify import _LABEL_MAP
        for key in self._GIT_KEYS:
            assert key in _LABEL_MAP, f"Missing key: {key}"

    def test_format_section_renders_git_section(self) -> None:
        result: dict[str, Any] = {
            "git_binary": {"ok": True, "value": "git 2.45.0"},
            "signing_intent": {"ok": True, "value": "not configured"},
            "signing_key": {
                "ok": False,
                "value": "missing",
                "error": "user.signingkey unset",
            },
            "overall_ok": False,
        }
        output = _format_section("GIT", result, self._symbols())
        assert "=== GIT " in output
        assert "Git binary" in output
        assert "Signing enabled" in output
        assert "Signing key" in output
        assert "[OK]" in output
        assert "[ERR]" in output
        assert "user.signingkey unset" in output
```

### 7. Integration test (`test_verify_integration.py`, append)

```python
@pytest.mark.git_integration
def test_verify_flags_gpgsign_without_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repo with commit.gpgsign=true and no user.signingkey → exit non-zero."""
    import subprocess
    import argparse

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "true"], cwd=repo, check=True,
    )

    # Mock everything except verify_git so we exercise the real upstream check.
    args = argparse.Namespace(
        check_models=False, mcp_config=None, llm_method=None,
        project_dir=str(repo),
    )
    with (
        patch(f"{_VERIFY}.verify_github", return_value={"overall_ok": True}),
        patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
        patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
        patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
        patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
        patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
    ):
        exit_code = execute_verify(args)

    output = capsys.readouterr().out
    assert "=== GIT " in output
    assert "Signing key" in output or "signing_key" in output
    assert exit_code != 0
```

(Reuse the existing helper imports / `_VERIFY` constant pattern from the file. If those helpers aren't already in `test_verify_integration.py`, copy the minimal needed ones from `test_verify_orchestration.py`, or place this test in `test_verify_orchestration.py` instead — pick whichever produces the smaller diff.)

## HOW

- The new section uses the existing `_format_section` — **no formatter changes**. The 13 git keys flow through the generic top-level rendering branch (`_BRANCH_PROTECTION_CHILDREN` does not contain any git key, so the special-case path is skipped).
- The exit-code change is provider-independent: place the `git_result` check next to the existing `github_result` check, before the provider-specific branches.
- The `_mock_git` fixture is autouse + class-scoped, parallel to the existing `_mock_github` fixture (same file, ~4 lines).
- Per Decision #11, do not add `logger.info` / `logger.debug` calls around `verify_git`.

## ALGORITHM (exit code)

```
if config_has_error:                       return 1
if not test_prompt_ok:                     return 1
if github_result and not overall_ok:       return 1
if git_result and not overall_ok:          return 1   # NEW
if active_provider == "claude" and not claude.overall_ok: return 1
... (rest unchanged)
```

## DATA

`verify_git(project_dir, actually_sign=True)` returns a `CheckResult` TypedDict (same shape as `verify_github`):

```python
{
    "overall_ok": bool,
    "git_binary":    {"ok": bool, "value": str, "error"?: str, ...},
    "git_repo":      {...},
    "signing_intent": {...},
    # ... up to 13 keys (only emitted when relevant)
}
```

`_format_section` iterates entries, skips `overall_ok`, looks each key up in `_LABEL_MAP` (falling back to the raw key if missing), and renders a row with `[OK]`/`[ERR]`/`[WARN]` based on `entry["ok"]`.

## TDD Order

1. Add the unit smoke test class (`TestGitLabelMappings`) — run pytest → **fails** (keys missing from `_LABEL_MAP`).
2. Add the 13 entries to `_LABEL_MAP` → unit smoke test still fails (rendering test needs section wired).
3. Add the import, `_compute_exit_code` parameter + check, and the `0d` section in `execute_verify`. Pass `git_result` into the call.
4. Add the `_mock_git` autouse fixture in `test_verify_orchestration.py` (otherwise existing orchestration tests break by hitting real git).
5. Run unit tests with the integration-marker exclusion → **all green**.
6. Add the `git_integration`-marked test.
7. Run integration test with `markers=["git_integration"]` → **green** (exits non-zero, output mentions signing).
8. Run all three quality checks.

## Acceptance

- `mcp-coder verify` includes a `=== GIT ===` section between PROJECT and GITHUB.
- When no signing flags are set: section reports `Signing enabled  [OK]  not configured`; exit code unaffected.
- When `commit.gpgsign=true` is set with a broken setup: section shows a clear error row and verify exits non-zero.
- All existing `test_verify*.py` tests still pass (the `_mock_git` fixture protects them).
- pylint, pytest, mypy all green.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Step 1 (shim re-export of verify_git) is already merged on this branch — verify
that `from mcp_coder.mcp_workspace_git import verify_git` succeeds before starting.

Implement Step 2 exactly as specified, in this order (TDD):

1. Append the TestGitLabelMappings class to
   tests/cli/commands/test_verify_format_section_basic.py (use the code in the
   step's "Unit smoke test" section verbatim, adjusting only the imports if
   the file already provides them). Run pytest on that file — confirm failure.

2. Edit src/mcp_coder/cli/commands/verify.py:
   a. Add `from ...mcp_workspace_git import verify_git` near the existing
      `verify_github` import.
   b. Append the 13 git keys to _LABEL_MAP under a "# Git section" comment.
   c. Add `git_result: dict[str, Any] | None = None` parameter to
      `_compute_exit_code` (last keyword arg) and add the early-reject check
      next to the existing github_result check. Update the docstring.
   d. Insert the `0d. Git verification section` block in `execute_verify`
      between `_print_project_section(...)` and the existing GitHub block.
      Renumber the GitHub comment from `0d` to `0e`.
   e. Pass `git_result=git_result` in the `_compute_exit_code(...)` call at
      the bottom of `execute_verify`.

3. Add the `_mock_git` autouse fixture inside the TestVerifyOrchestration
   class in tests/cli/commands/test_verify_orchestration.py, parallel to the
   existing `_mock_github` fixture.

4. Run quality checks per .claude/CLAUDE.md:
   - mcp__tools-py__run_pylint_check
   - mcp__tools-py__run_pytest_check with extra_args=["-n", "auto",
     "-m", "not git_integration and not claude_cli_integration and not
     claude_api_integration and not formatter_integration and not
     github_integration and not langchain_integration"]
   - mcp__tools-py__run_mypy_check
   Fix any failures.

5. Append the `test_verify_flags_gpgsign_without_key` test (marked
   `git_integration`) to tests/cli/commands/test_verify_integration.py.
   If the helpers `_VERIFY`, `_claude_ok`, `_mlflow_not_installed`,
   `_minimal_llm_response` are not in scope there, either import them from
   test_verify_orchestration.py (if exposed) or place this test in
   test_verify_orchestration.py instead — choose the smaller diff.

6. Run integration test:
   - mcp__tools-py__run_pytest_check with extra_args=["-n", "auto"],
     markers=["git_integration"]
   Fix any failures.

7. Re-run all three quality checks; confirm green.

8. Run ./tools/format_all.sh before committing.

9. Commit with message such as:
   "Wire verify_git into mcp-coder verify (#937)"

CONSTRAINTS:
- Do NOT add any logger.info / logger.debug calls around verify_git
  (Decision #11 — no signing-key logging in the wiring layer).
- Do NOT modify _format_section.
- Do NOT add a --sign-test flag — Tier 3 always runs (actually_sign=True).
- Do NOT introduce a wrapper function around verify_git in the shim.
```
