# Step 2 — Remove the `tests/install` `_env` bypass; document remaining `subprocess` exceptions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> This is a test-only refactor plus `.importlinter` changes; the existing `tests/install`
> tests are the safety net and must keep passing unchanged in behaviour.
> Run lint-imports, pylint, mypy, the fast pytest suite and `tests/install`; all must pass.
> Run the formatter, then make exactly one commit.

## WHERE

- `tests/install/conftest.py`
- `tests/install/test_install_integration.py`
- `tests/install/test_install_phases.py`
- `.importlinter` — contract `[importlinter:contract:subprocess_isolation]`

## Precondition

Step 1 is committed: `.importlinter` no longer contains `mcp_coder.utils.mcp_verification -> subprocess`.
If it still does, write one line to `pr_info/.blocked.txt` and stop.

## WHAT

No new functions. `namespace(**overrides) -> argparse.Namespace` in `conftest.py` is unchanged.

### `tests/install/conftest.py`

- Delete `from mcp_coder.install import _env`, the 5-line comment, and
  `subprocess = _env.subprocess  # type: ignore[attr-defined]`.
- Module docstring: delete the "Subprocess note: ..." paragraph. In the first paragraph, drop the
  mention of the `subprocess` shim so it describes only `namespace`, e.g.:
  > Not a fixture module in the pytest-DI sense: ``namespace`` is a plain function the test
  > modules call directly with varying keyword overrides, and is imported explicitly where needed.

### `tests/install/test_install_integration.py`

- Replace `from .conftest import subprocess as _subprocess` with a plain stdlib `import subprocess`.
- `_subprocess.run(` → `subprocess.run(`.
- Delete the "Subprocess note: ..." docstring paragraph.
- Keep `_env` (still used for `venv_bin` / `exe`) and the existing `import shutil`.

### `tests/install/test_install_phases.py`

- Replace `from .conftest import subprocess as _subprocess` with plain stdlib `import shutil` and
  `import subprocess`.
- Delete the 5-line comment and `_shutil = _env.shutil  # type: ignore[attr-defined]`.
- Rename every `_shutil` → `shutil` and `_subprocess` → `subprocess` (`monkeypatch.setattr(...)`
  targets and `_subprocess.CalledProcessError`).
- Delete the "Subprocess note: ..." docstring paragraph; keep the "Shell-quoting note".
- Keep `_env` (still used for `ensure_system_uv` etc.).

## HOW

- `monkeypatch.setattr(shutil, "which", ...)` / `monkeypatch.setattr(subprocess, "run", ...)`
  still affect `_env`, because `_env` does `import shutil` / `import subprocess` and calls
  `shutil.which` / `subprocess.run` through the module object. `_env.shutil` is the same module
  object as `shutil`, so behaviour is unchanged.
- Removing the attribute access also removes both `# type: ignore[attr-defined]` comments.

## ALGORITHM

None (mechanical import/rename refactor).

### `.importlinter`

1. Append to `subprocess_isolation` → `ignore_imports`:

```
    tests.install.** -> subprocess
```

2. Extend the comment block above `[importlinter:contract:subprocess_isolation]` (after the
   existing `tools/check_forbidden_calls.py` lines, before the closing dashed line) with:

```
#
# Permanent exceptions (need inherited TTY/stdio and no timeout, which
# subprocess_runner cannot provide):
#   - workflows.vscodeclaude.session_setup (+ its flow test): interactive
#     `claude` / `mcp-coder install` sessions
#   - install.** : uv/pip with live progress output
#   - tests.install.** : patch/call subprocess to exercise install._env
# tools/ is outside root_packages and unchecked: safe_delete_folder.py must
# run standalone without importing mcp_coder; tach_docs.py is dev-only.
```

Keep reasons in the comment block only, not inline in the `ignore_imports` value.

## DATA

Final `subprocess_isolation` → `ignore_imports`:

```
    mcp_coder.workflows.vscodeclaude.session_setup -> subprocess
    tests.workflows.vscodeclaude.test_session_setup_flow -> subprocess
    mcp_coder.install.** -> subprocess
    tests.install.** -> subprocess
```

## Checks

- `mcp__mcp-workspace__search_files` with pattern `_env\.(subprocess|shutil)` over `tests/**` → no matches.
- `mcp__mcp-tools-py__run_lint_imports_check` — passes.
- `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `-n auto` and the fast-unit marker filter from CLAUDE.md
- `mcp__mcp-tools-py__run_pytest_check` with `-n auto` and `markers=["install_integration"]`. It needs `uv`.
  If `uv` is missing, the tests skip themselves; that's acceptable.
- `mcp__mcp-tools-py__run_format_code`, then commit, e.g.
  `test(install): import subprocess/shutil directly; document subprocess exceptions`
