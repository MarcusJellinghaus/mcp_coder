# Deploy Claude Skills via `mcp-coder init` — Implementation Summary

**Issue:** #725
**Goal:** Extend `mcp-coder init` to automatically deploy `.claude/skills/`, `.claude/knowledge_base/`, and `.claude/agents/` into downstream projects.

## Architectural / Design Changes

### 1. Build-time packaging (new `setup.py`)

Skills live at repo root (`.claude/`) and are **not shipped in the wheel** today. A new `setup.py` adds a custom `build_py` command that copies `.claude/{skills,knowledge_base,agents}/` → `src/mcp_coder/resources/claude/` before the standard build runs. This ensures `python -m build` and `pip install .` both bundle the skill files as package data.

- `src/mcp_coder/resources/claude/` is a **build artifact** (gitignored), not a source-of-truth.
- Canonical editing stays at repo-root `.claude/`.

### 2. Runtime dual-lookup (in `init.py`)

A private function `_find_claude_source_dir()` resolves the skill source at runtime:

1. **Wheel path:** `importlib.resources.files("mcp_coder") / "resources" / "claude"` — works for `pip install mcp-coder`.
2. **Editable fallback:** Walk up from `mcp_coder.__file__` to find the repo-root `.claude/` — works for `pip install -e .` where the build-time copy is skipped.
3. **Both fail:** exit 1 with terse error (broken packaging).

### 3. Deploy logic (in `init.py`)

A private function `_deploy_skills()` copies the three directories into `<project-dir>/.claude/`. Policy:

- **Never overwrite** existing files — skip with a warning per file.
- Summary output: `"N added, M skipped"`.
- Exit code 0 even with skips.

### 4. CLI surface extension

`mcp-coder init` gets two new flags via a dedicated parser function:

```
mcp-coder init                              # default: config + skills
mcp-coder init --just-skills                # deploy skills only
mcp-coder init --project-dir <path>         # target project (default: CWD)
```

The `init` subparser in `main.py` changes from a bare `add_parser("init")` to using `add_init_parser(subparsers)` from `parsers.py`.

### 5. What is NOT deployed

- `.claude/CLAUDE.md` — project-specific
- `.claude/settings.local.json` — gitignored, security-sensitive
- `.mcp.json` — marked "Copy as-is: No"

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/init.py` | Add `_find_claude_source_dir()`, `_deploy_skills()`, update `execute_init()` |
| `src/mcp_coder/cli/parsers.py` | Add `add_init_parser()` |
| `src/mcp_coder/cli/main.py` | Replace bare `add_parser("init")` with `add_init_parser(subparsers)` + import |
| `pyproject.toml` | Add `"resources/claude/**/*"` to `[tool.setuptools.package-data]` |
| `.gitignore` | Add `src/mcp_coder/resources/claude/` |
| `tests/cli/commands/test_init.py` | Add tests for deploy logic, source resolver, CLI flags, update existing tests |
| `docs/repository-setup/claude-code.md` | Replace hand-copy instructions with `mcp-coder init` reference |
| `docs/repository-setup/README.md` | Update compatibility table note |

## Files Created

| File | Purpose |
|------|---------|
| `setup.py` | Custom `build_py` to copy `.claude/` → `src/mcp_coder/resources/claude/` at build time |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Build-time packaging: `setup.py` + `pyproject.toml` package-data + `.gitignore` | Packaging infrastructure |
| 2 | CLI parser: `add_init_parser()` with `--just-skills` and `--project-dir` + wire into `main.py` | CLI surface for init |
| 3 | Source resolver: `_find_claude_source_dir()` with dual-lookup logic | Runtime skill source resolution |
| 4 | Deploy logic: `_deploy_skills()` + integrate into `execute_init()` | Skill deployment |
| 5 | Documentation: update `claude-code.md` and `README.md` | Docs update |
