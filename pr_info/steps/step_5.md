# Step 5: Create `read_github_deps.py` + improve `reinstall_local.bat`

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Create the bootstrap helper that prints `uv pip install` commands from `pyproject.toml`, then update `reinstall_local.bat` to use it instead of hardcoded GitHub URLs.

## Changes

### CREATE: `tools/read_github_deps.py`

**WHERE:** `tools/read_github_deps.py`

**WHAT:** Bootstrap script that imports `pyproject_config` via `sys.path` and prints pip install commands.

```python
"""Print uv pip install commands for GitHub dependency overrides.

Bootstrap helper for reinstall_local.bat. Uses sys.path to import
pyproject_config without requiring an installed package.

Output format (one command per line):
    uv pip install "pkg1" "pkg2"
    uv pip install --no-deps "pkg3"
"""
import sys
from pathlib import Path

def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_dir / "src"))
    from mcp_coder.utils.pyproject_config import get_github_install_config
    
    config = get_github_install_config(project_dir)
    if config.packages:
        quoted = " ".join(f'"{p}"' for p in config.packages)
        print(f"uv pip install {quoted}")
    if config.packages_no_deps:
        quoted = " ".join(f'"{p}"' for p in config.packages_no_deps)
        print(f"uv pip install --no-deps {quoted}")

if __name__ == "__main__":
    main()
```

**ALGORITHM:**
```
1. project_dir = parent of tools/
2. sys.path.insert(0, project_dir / "src")
3. import get_github_install_config
4. config = get_github_install_config(project_dir)
5. print "uv pip install ..." for packages
6. print "uv pip install --no-deps ..." for packages_no_deps
```

### MODIFY: `tools/reinstall_local.bat`

**Changes:**

1. **Add silent deactivate** near the top (after environment checks):
```batch
REM Silently deactivate any active venv
call deactivate 2>nul
```

2. **Create .venv if missing** (already exists in current script — keep it)

3. **Replace hardcoded GitHub URLs** (step 3/7) with dynamic reading:

**BEFORE (step 3/7):**
```batch
echo [3/7] Overriding dependencies with GitHub versions...
uv pip install "mcp-config-tool @ git+https://github.com/MarcusJellinghaus/mcp-config.git" "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git" --python "!VENV_SCRIPTS!\python.exe"
...
uv pip install --no-deps "mcp-tools-py @ git+https://github.com/MarcusJellinghaus/mcp-tools-py.git" --python "!VENV_SCRIPTS!\python.exe"
```

**AFTER:**
```batch
echo [3/7] Overriding dependencies with GitHub versions...
REM Read GitHub dependency overrides from pyproject.toml
for /f "delims=" %%C in ('python tools\read_github_deps.py') do (
    echo   %%C
    %%C --python "!VENV_SCRIPTS!\python.exe"
    if !ERRORLEVEL! NEQ 0 (
        echo [FAIL] GitHub dependency override failed!
        exit /b 1
    )
)
echo [OK] GitHub dependencies overridden from pyproject.toml
```

**KEY DESIGN DECISION:** The batch file stays in control of pip execution. `read_github_deps.py` only prints commands — it never runs them. The `--python` flag is appended by the batch file since it knows the venv path.

4. **Remove the wrong-venv guard** at the top and replace with silent deactivate. The current script errors out if the wrong venv is active — instead, just deactivate whatever is active and proceed.

## Verification

- Run `python tools/read_github_deps.py` manually and verify output matches expected format
- Verify `reinstall_local.bat` structure is correct (manual review — can't easily run it in test)
- pylint, mypy, pytest all clean

## Commit

```
feat: dynamic GitHub deps in reinstall_local.bat (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Create tools/read_github_deps.py as specified. Then modify tools/reinstall_local.bat:
add silent deactivate, replace hardcoded GitHub URLs with read_github_deps.py output,
replace the wrong-venv guard with silent deactivate. Keep the rest of the script 
structure (uninstall, editable install, LangChain/MLflow, verify, activate).
Run all quality checks.
```
