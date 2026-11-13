# review-implementation review log 1

## Round 1 — 2026-11-13
**Findings**:
Still reviewing: core setup modules read; now checking the `install` built-in delegation, session launcher and templates.Checking bin-dir helper consistency and the remaining tests.`src/mcp_coder/workflows/vscodeclaude/session_launch.py:111` — low — If `pyproject.toml` can't be parsed, `load_setup_config` raises, and the launch warning blames an "invalid [tool.mcp-coder.setup]" table. Before this change the warning just said the file couldn't be read, which matched the "unreadable pyproject.toml" case the issue mentions. The parse error text is still included, so the existing test passes.
**Decisions**:
Verdict(decision='tasks', tasks=["In src/mcp_coder/workflows/vscodeclaude/session_launch.py:111, separate the 'pyproject.toml cannot be read/parsed' case from the 'invalid [tool.mcp-coder.setup] table' case. Either catch the TOML read/parse error on its own, or have load_setup_config raise a distinct exception type for it. An unreadable or unparseable pyproject.toml should give a warning saying the file couldn't be read (as before this change), and only a real schema/validation error should blame the [tool.mcp-coder.setup] table. Keep the underlying error text in both messages. Add or adjust a test that gives a malformed pyproject.toml and checks that the warning says the file couldn't be read and does not name the setup table."], escalate_reason=None)
**Changes**:
applied
