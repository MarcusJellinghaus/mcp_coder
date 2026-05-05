# Step 2 — Wire GIT section into `mcp-coder verify`

> **Reference:** [`pr_info/steps/summary.md`](./summary.md) — Architecture & file overview.
> **Depends on:** Step 1 (shim re-export must already be merged).

## Goal

Add a `=== GIT ===` section to `mcp-coder verify` between PROJECT and GITHUB, route its `overall_ok` into the exit code (provider-independent), and cover the wiring with a unit smoke test plus an integration test.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | Import `verify_git`; extend `_LABEL_MAP` (13 entries); extend `_compute_exit_code` signature; insert `0d` GIT section in `execute_verify`; renumber GitHub comment `0d`→`0e` |
| `tests/cli/commands/conftest.py` | Add `_mock_verify_git` autouse fixture (parallel to `_mock_verify_github`) |
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

Add a new early-reject block (provider-independent), placed adjacent to the existing `github_result` check. Match the existing `github_result` comment style exactly, replacing only "GitHub" with "Git":

```python
# Git failure always means exit 1 (provider-independent)
if git_result is not None and not git_result.get("overall_ok"):
    return 1
```

Update the docstring:
- Add `git_result` entry to the `Args:` block (mirror the existing `github_result` line).
- Update the failure-conditions summary line at the top of the docstring (the "Exit 1 when ..." sentence). Insert "when git verification failed" between the existing "when GitHub verification failed" item and the next condition. Read `verify.py` first to copy the exact phrasing/style.

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

### 5. Conftest autouse fixture (`tests/cli/commands/conftest.py`)

`verify_git` runs unmocked across at least 6 test files/classes that exercise `execute_verify` — a per-class fixture is not enough. Add a new module-level autouse fixture parallel to the existing `_mock_verify_github` (around lines 104–123 of `conftest.py`). Mirror that fixture's structure exactly:

```python
@pytest.fixture(autouse=True)
def _mock_verify_git() -> Generator[MagicMock, None, None]:
    """Auto-mock verify_git to return a default OK result.

    Tests that need a specific git result can override by patching
    verify_git explicitly inside the test body.
    """
    default = {"overall_ok": True}
    with patch(
        "mcp_coder.cli.commands.verify.verify_git", return_value=default
    ) as mock:
        yield mock
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

    def test_git_section_appears_between_project_and_github(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIT section is rendered between PROJECT and GITHUB (Decision #2)."""
        # Relies on the autouse mocks (verify_config, verify_github, verify_git)
        # in tests/cli/commands/conftest.py to keep this hermetic.
        execute_verify(_make_args())
        output = capsys.readouterr().out
        assert output.find("=== PROJECT") < output.find("=== GIT") < output.find("=== GITHUB")

    def test_verify_git_called_with_actually_sign_true(self) -> None:
        """Decision #3: Tier 3 always runs (actually_sign=True, no flag)."""
        with patch(f"{_VERIFY}.verify_git", return_value={"overall_ok": True}) as mock:
            execute_verify(_make_args())
        mock.assert_called_once_with(project_dir, actually_sign=True)
        # NOTE: the test must pass `project_dir` matching the resolved Path
        # used by execute_verify (use the same _make_args() helper as elsewhere
        # so the project_dir argument is consistent).
```

(The two new tests reuse `_make_args()` and `_VERIFY` constants already present in the test file/module — wire imports as the existing tests do. The `actually_sign=True` assertion pins Decision #3 in code.)

### 7. Integration test (`tests/cli/commands/test_verify_integration.py`, append)

Pin the test to `test_verify_integration.py`. The helpers actually present in that file are `_make_claude_result`, `_make_mlflow_result`, and the module-level constant `_MOCK_LLM_RESPONSE` — use those, do NOT reference `_claude_ok` / `_mlflow_not_installed` / `_minimal_llm_response` (those names live in `test_verify_orchestration.py`).

```python
@pytest.mark.git_integration
def test_verify_flags_gpgsign_without_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Repo with commit.gpgsign=true and no user.signingkey → exit non-zero.

    Note: this test is environment-sensitive — gpg may or may not be installed
    on the runner. Assertions are intentionally minimal (header present + non-zero
    exit) so the test stays robust across both environments.
    """
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
        patch(f"{_VERIFY}.verify_claude", return_value=_make_claude_result(ok=True)),
        patch(f"{_VERIFY}.verify_mlflow", return_value=_make_mlflow_result(installed=False)),
        patch(f"{_VERIFY}.prompt_llm", return_value=_MOCK_LLM_RESPONSE),
        patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
        patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
    ):
        exit_code = execute_verify(args)

    output = capsys.readouterr().out
    # Environment-sensitive: gpg may or may not be installed. Keep assertions minimal.
    assert "=== GIT" in output
    assert exit_code != 0
```

## HOW

- The new section uses the existing `_format_section` — **no formatter changes**. The 13 git keys flow through the generic top-level rendering branch (`_BRANCH_PROTECTION_CHILDREN` does not contain any git key, so the special-case path is skipped).
- The exit-code change is provider-independent: place the `git_result` check next to the existing `github_result` check, before the provider-specific branches.
- The `_mock_verify_git` fixture is autouse + module-level in `tests/cli/commands/conftest.py`, parallel to the existing `_mock_verify_github` fixture (mirror its structure exactly).
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
1.5. Add focused unit tests for the new `_compute_exit_code(git_result=...)` branch, mirroring the existing `test_github_failure_causes_exit_1` pattern in `test_verify_orchestration.py` (the test that asserts "exit code is 1 when verify_github returns overall_ok=False"). Two tests:
   - `test_exit_1_when_git_overall_ok_false` — `git_result={"overall_ok": False}` → return 1.
   - `test_exit_0_when_git_result_none` — `git_result=None` → not the failing path (other inputs ok → return 0).

   These can either go in `test_verify_orchestration.py` next to the GitHub equivalents, or in a focused unit-test class for `_compute_exit_code` if one already exists. They will fail until step 3 lands.
2. Add the 13 entries to `_LABEL_MAP` → unit smoke test still fails (rendering test needs section wired).
3. Add the import, `_compute_exit_code` parameter + check (with updated docstring summary line + Args), and the `0d` section in `execute_verify`. Pass `git_result` into the call.
4. Add the `_mock_verify_git` autouse fixture to `tests/cli/commands/conftest.py` (otherwise tests across multiple files break by hitting real git).
5. Run unit tests with the integration-marker exclusion → **all green**.
6. Add the `git_integration`-marked test.
7. Run integration test with `markers=["git_integration"]` → **green** (exits non-zero, GIT header present).
8. Run all three quality checks.

## Acceptance

- `mcp-coder verify` includes a `=== GIT ===` section between PROJECT and GITHUB.
- When no signing flags are set: section reports `Signing enabled  [OK]  not configured`; exit code unaffected.
- When `commit.gpgsign=true` is set with a broken setup: section shows a clear error row and verify exits non-zero.
- All existing `test_verify*.py` tests still pass (the conftest-level `_mock_verify_git` autouse fixture protects them).
- New `_compute_exit_code` unit tests pass: `test_exit_1_when_git_overall_ok_false` and `test_exit_0_when_git_result_none`.
- New ordering test passes: `test_git_section_appears_between_project_and_github` — pins Decision #2.
- New invocation test passes: `test_verify_git_called_with_actually_sign_true` — pins Decision #3.
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
      next to the existing github_result check (match its comment style:
      "# Git failure always means exit 1 (provider-independent)"). Update
      the docstring's Args block AND the failure-conditions summary line at
      the top of the docstring (insert "when git verification failed" between
      "when GitHub verification failed" and the next condition — read the
      current text in verify.py and copy its phrasing exactly).
   d. Insert the `0d. Git verification section` block in `execute_verify`
      between `_print_project_section(...)` and the existing GitHub block.
      Renumber the GitHub comment from `0d` to `0e`.
   e. Pass `git_result=git_result` in the `_compute_exit_code(...)` call at
      the bottom of `execute_verify`.

3. Add the `_mock_verify_git` autouse fixture to
   tests/cli/commands/conftest.py, parallel to the existing
   `_mock_verify_github` fixture (around lines 104-123 of conftest.py).
   Mirror that fixture's structure exactly: module-level (not class-scoped),
   patches `mcp_coder.cli.commands.verify.verify_git`, default returns
   `{"overall_ok": True}`.

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
   Use the helpers ALREADY present in that file: `_VERIFY`,
   `_make_claude_result`, `_make_mlflow_result`, and the module-level
   `_MOCK_LLM_RESPONSE` constant. Do NOT use the names from
   test_verify_orchestration.py (`_claude_ok` etc.) — those are different
   helpers and don't exist in test_verify_integration.py. Keep assertions
   minimal (header `=== GIT` present + non-zero exit) since gpg may or
   may not be installed on the runner.

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
