# Step 3: Prompted check — VS Code gpuAcceleration detection

## References
- [Summary](summary.md) for architecture overview
- [Step 1](step_1.md) for the skeleton and warning checks
- [Step 2](step_2.md) for the silent fix this builds on
- Issue #780 for full requirements

## Goal
Add the VS Code gpuAcceleration check: Windows-only, reads `%APPDATA%\Code\User\settings.json`, regex search for `gpuAcceleration.*off`, prompts user with Instructions/Abort (both abort).

## WHERE
- **Modify**: `src/mcp_coder/utils/tui_preparation.py`
- **Modify**: `tests/utils/test_tui_preparation.py`

## WHAT — New method on `TuiChecker`

### `_check_vscode_gpu_acceleration(self) -> None`
```python
def _check_vscode_gpu_acceleration(self) -> None: ...
```

## ALGORITHM
```
1. if sys.platform != "win32": return
2. if os.environ.get("SSH_CONNECTION"): return   (remote session — settings.json not relevant)
3. if os.environ.get("TERM_PROGRAM") != "vscode": return
4. settings_path = Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "settings.json"
5. if not settings_path.is_file(): return
6. content = settings_path.read_text(encoding="utf-8", errors="ignore")
7. if re.search(r'"terminal\.integrated\.gpuAcceleration"\s*:\s*"off"', content):
       self._prompts.append((PROMPT_TEXT, INSTRUCTION_TEXT))
```

## DATA — Constants
```python
_VSCODE_GPU_PROMPT = (
    "VS Code terminal gpuAcceleration is set to 'off', which breaks TUI mouse/rendering."
)
_VSCODE_GPU_INSTRUCTIONS = (
    "To fix: Open VS Code Settings → search 'gpuAcceleration' "
    "→ change to 'auto' or remove the setting → restart the terminal."
)
```

## HOW — Integration
Add call in `run_all_checks()`:
```python
self._check_vscode_gpu_acceleration()
```

## Tests
Use `tmp_path` to create fake settings.json files. Mock `sys.platform`, env vars, and the settings path.

1. `test_vscode_gpu_detected` — `win32`, `TERM_PROGRAM=vscode`, settings.json contains `"terminal.integrated.gpuAcceleration": "off"`, verify `_prompts` has one entry
2. `test_vscode_gpu_not_off` — settings.json contains `"terminal.integrated.gpuAcceleration": "auto"`, verify `_prompts` is empty
3. `test_vscode_gpu_no_setting` — settings.json exists but no gpuAcceleration, verify `_prompts` is empty
4. `test_vscode_gpu_no_settings_file` — settings path doesn't exist, verify `_prompts` is empty
5. `test_vscode_gpu_wrong_platform` — `sys.platform="linux"`, verify `_prompts` is empty (skipped)
6. `test_vscode_gpu_ssh_connection_skips` — `SSH_CONNECTION` set, verify `_prompts` is empty
7. `test_vscode_gpu_not_vscode_terminal` — `TERM_PROGRAM=xterm`, verify `_prompts` is empty
8. `test_vscode_gpu_prompt_instructions_flow` — run `run_all_checks()` with mock `input()` returning "i", verify `TuiPreflightAbort` raised and instruction text was logged
9. `test_vscode_gpu_prompt_abort_flow` — run `run_all_checks()` with mock `input()` returning "a", verify `TuiPreflightAbort` raised

### Mocking the settings path
Patch the `Path` construction or use `monkeypatch.setenv("APPDATA", str(tmp_path))` so the settings path resolves to `tmp_path / "Code" / "User" / "settings.json"`.

## LLM Prompt
```
Implement Step 3 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_3.md for this step's spec.

Add _check_vscode_gpu_acceleration() to TuiChecker in src/mcp_coder/utils/tui_preparation.py.
Windows-only, skips if SSH_CONNECTION is set, checks TERM_PROGRAM=vscode,
reads %APPDATA%\Code\User\settings.json with regex for gpuAcceleration off.
Appends to _prompts list. Wire into run_all_checks().
Add tests to tests/utils/test_tui_preparation.py using tmp_path for fake settings files.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
