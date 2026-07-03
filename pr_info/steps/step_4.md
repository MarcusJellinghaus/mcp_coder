# Step 4 — Thin launcher templates + gitignore entry (additive)

Read `pr_info/steps/summary.md` first. This step adds the two launcher constants,
the `INTERVENTION_WARNING` constant, and the new gitignore line. It is **purely
additive** — the old orchestration constants remain (still used by
`workspace.py`) so all existing tests stay green. They are removed later in
Step 6.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/templates.py` (add constants; extend one)
- `tests/workflows/vscodeclaude/test_templates.py` (add launcher tests)

## WHAT
```python
LAUNCHER_WINDOWS = (
    "@echo off\n"
    '"{mcp_coder_install_path}\\.venv\\Scripts\\python.exe" '
    "-m mcp_coder.workflows.vscodeclaude.session_setup \"%CD%\" || pause\n"
)

LAUNCHER_POSIX = (
    "#!/usr/bin/env bash\n"
    '"{mcp_coder_install_path}/.venv/bin/python" '
    "-m mcp_coder.workflows.vscodeclaude.session_setup \"$PWD\" "
    '|| read -r -p "Session failed (Enter to close)..."\n'
)

# Intervention warning, printed at runtime by session_setup.render_banner
# (see Step 2). Extracted verbatim from the deleted INTERVENTION_SCRIPT_*
# templates so the terminal warning survives the launcher refactor.
INTERVENTION_WARNING = (
    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
    "!! INTERVENTION MODE - Automation may be running elsewhere\n"
    "!! Investigate manually. No automated analysis will run.\n"
    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
)
```

## HOW
- The launchers' only placeholder is `{mcp_coder_install_path}`; keep the strings
  as raw/plain constants next to the surviving `*_TEMPLATE` strings.
- `INTERVENTION_WARNING` is a plain (no-placeholder) constant, added alongside
  the launchers. It is consumed by `render_banner` (Step 2) and survives the
  Step-6 deletion of the `INTERVENTION_SCRIPT_*` templates. Added here (rather
  than Step 2) so all template constants live in `templates.py`.
- Extend `GITIGNORE_ENTRY` to also ignore `.vscodeclaude_session.json` (keep the
  existing `.vscodeclaude_start.bat`/`.sh` lines for now; remove in Step 6 if
  desired, but the session json line is required by the issue here).

## ALGORITHM
None (declarative constants).

## DATA
- Three module-level `str` constants (`LAUNCHER_WINDOWS`, `LAUNCHER_POSIX`,
  `INTERVENTION_WARNING`) + an updated `GITIGNORE_ENTRY` string.

## TESTS (write first)
- `LAUNCHER_WINDOWS.format(mcp_coder_install_path="C:\\tool")` contains
  `python.exe`, `-m mcp_coder.workflows.vscodeclaude.session_setup`, `"%CD%"`,
  `|| pause`, and no leftover `{` placeholder.
- `LAUNCHER_POSIX.format(...)` starts with `#!/usr/bin/env bash`, contains
  `/.venv/bin/python`, `"$PWD"`, and `read -r -p`.
- `INTERVENTION_WARNING` contains `INTERVENTION MODE - Automation may be running
  elsewhere` and `No automated analysis will run.` (no `{` placeholder).
- `GITIGNORE_ENTRY` contains `.vscodeclaude_session.json`.

## LLM PROMPT
> Implement Step 4 from `pr_info/steps/step_4.md` (context in
> `pr_info/steps/summary.md`). Add `LAUNCHER_WINDOWS`, `LAUNCHER_POSIX`, and the
> `INTERVENTION_WARNING` constant to
> `src/mcp_coder/workflows/vscodeclaude/templates.py` and add
> `.vscodeclaude_session.json` to `GITIGNORE_ENTRY`. This step is additive — do
> not remove any existing constants. Add tests to
> `tests/workflows/vscodeclaude/test_templates.py` (launcher format substitution,
> `INTERVENTION_WARNING` text, gitignore line). Use MCP workspace tools. Run
> pylint, pytest (`-n auto` + standard exclusions), mypy; fix all. One commit.
