# Step 2 — Wire the gitignore block into `mcp-coder init`

**Depends on:** step 1 (needs the `list[str]` return value).

`mcp-coder init` ensures the VSCodeClaude entries are present in
`<project_dir>/.gitignore` — a working copy where they will actually be
committed — reports what it did, and exits 1 if the write failed without
aborting the rest of the run.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/init.py` | New import, new `_write_gitignore_entries()`, 2 edits in `execute_init` |
| `tests/cli/commands/test_init.py` | 3 new tests in `TestExecuteInitWithDeploy`; 3 existing `TestInitCommand` tests get a real `project_dir` |

Do not modify `main.py`, the argument parser, `tach.toml`, or `.importlinter` —
`mcp_coder.cli -> mcp_coder.workflows` is already an allowed dependency in both.

## WHAT

```python
def _write_gitignore_entries(project_dir: Path) -> bool:
```

Module-private helper. Returns `True` on success (including "nothing to do"),
`False` when the write failed.

## HOW

**Import** — add to the existing relative-import block at the top of `init.py`,
after the `...utils.user_config` line (isort order: `utils` before `workflows`):

```python
from ...workflows.vscodeclaude.workspace import update_gitignore
```

Import the **module**, not the `vscodeclaude` package, per the issue note. Be
aware this does not actually avoid executing
`workflows/vscodeclaude/__init__.py`: Python runs every parent package
`__init__` on submodule import, and `workflows/__init__.py` eagerly imports
`vscodeclaude` anyway. There is no startup cost either way — `cli/main.py`
already loads that package for every invocation — so this is a style/graph
choice, not a lazy-loading one. The module-level import is also what makes
`mcp_coder.cli.commands.init.update_gitignore` a patchable target in tests.

**Placement** — define `_write_gitignore_entries` after `_deploy_skills`.

**Call site** — in `execute_init`, between the deploy block (step 2 comment) and
the config block, so the `Gitignore:` output line sits next to `Skills:` rather
than after the closing "Next steps:" text. Renumber the config comment to `# 4.`:

```python
    # 3. Gitignore entries (both modes: project-scoped, like the .claude/ deploy)
    gitignore_ok = _write_gitignore_entries(project_dir)

    # 4. Config creation (skip if --just-skills)
    if not args.just_skills:
        ...

    return 0 if gitignore_ok else 1
```

The final `return 0` becomes `return 0 if gitignore_ok else 1`. The existing
early `return 1` on config `OSError` is unchanged.

## ALGORITHM

```
try: added = update_gitignore(project_dir)
except OSError as e: log warning, return False       # never abort init
log OUTPUT "Gitignore: N entries added"              # N == 0 means up to date
if added and no .git/ in project_dir: log warning    # init before git init is legal
return True
```

The `added and` conjunction is the whole "no warning when nothing was written"
rule. `(project_dir / ".git").exists()` covers both a real directory and the
`.git` *file* used by worktrees.

```python
def _write_gitignore_entries(project_dir: Path) -> bool:
    """Ensure the VSCodeClaude entries are present in the project .gitignore.

    Args:
        project_dir: Target project root.

    Returns:
        True on success (including "already up to date"), False if the write
        failed. A failure is logged and never aborts init.
    """
    try:
        added = update_gitignore(project_dir)
    except OSError as e:
        logger.warning("Failed to update .gitignore in %s: %s", project_dir, e)
        return False

    logger.log(OUTPUT, "Gitignore: %d entries added", len(added))
    if added and not (project_dir / ".git").exists():
        logger.warning(
            "Wrote .gitignore entries but %s has no .git/ directory", project_dir
        )
    return True
```

## DATA

- `_write_gitignore_entries` → `bool`.
- `execute_init` → `int`, unchanged contract: `0` success, `1` failure. New
  failure source: gitignore write, reported only after the rest of the run.
- Output line at the `OUTPUT` level, matching the existing
  `Skills: %d added, %d skipped` style. `Gitignore: 0 entries added` is the
  already-up-to-date case — a single format string, same as `Skills:` printing
  zeros.

## Tests (write first)

### Fix 3 existing tests first

`TestInitCommand::test_init_creates_config_success`,
`test_init_config_already_exists`, and `test_init_write_failure` build
`argparse.Namespace(..., project_dir=None)`, which resolves to `Path.cwd()` —
the mcp-coder repo itself. Harmless today because deploy is mocked, but once
init writes `.gitignore` these tests would touch the real repo file. All three
already receive `tmp_path`; change `project_dir=None` to
`project_dir=str(tmp_path)`. No new mocks.

### 3 new tests in `TestExecuteInitWithDeploy`

**A — block appears, second run is a no-op, `.git` warning rules.** Patch
`create_default_config` / `get_config_file_path` and `_find_claude_source_dir`
as the neighbouring tests do; `just_skills=False`; project is a bare `tmp_path`
subdir with no `.git/`.

```
run execute_init -> assert 0
    assert ".vscodeclaude_session.json" in .gitignore
    assert "no .git/" in caplog.text
record content; caplog.clear()
run execute_init again -> assert 0
    assert .gitignore content is byte-identical
    assert "no .git/" not in caplog.text        # nothing written -> no warning
```

**B — `--just-skills` writes it.** `just_skills=True`, `create_default_config`
patched and asserted not called; assert the block is in `.gitignore`.

**C — write failure exits 1 but finishes the run.** `just_skills=False`;
monkeypatch `mcp_coder.cli.commands.init.update_gitignore` to raise
`PermissionError("read-only")`.

```
result == 1
"Failed to update .gitignore" in caplog.text
skills deployed        (step before gitignore ran)
create_default_config called once   (step after gitignore still ran)
```

Use `caplog.at_level(logging.WARNING, logger="mcp_coder.cli.commands.init")`,
consistent with `test_self_deploy_is_skipped`.

All other tests in the file must keep passing unchanged.

## Checks

Run all three MCP checks; all must pass before commit. Watch for other tests
anywhere in the suite that invoke `execute_init` with `project_dir=None`.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Step 1 is
> already committed, so `update_gitignore` returns `list[str]`.
>
> Implement step 2 only: wire the gitignore step into
> `src/mcp_coder/cli/commands/init.py` via a `_write_gitignore_entries` helper,
> exactly as specified in the step. Follow TDD: first change the three
> `TestInitCommand` namespaces from `project_dir=None` to
> `project_dir=str(tmp_path)`, then add the three new tests in
> `TestExecuteInitWithDeploy`, watch them fail, then implement.
>
> Keep it minimal: one helper, one import, one local `gitignore_ok` flag, one
> changed return. Do not touch `main.py`, the parser, `tach.toml`,
> `.importlinter`, or `session_launch.py`. Docs come in step 3.
>
> Use MCP tools for all file operations. After the change run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
> Fix any issue before finishing. This step is one commit.
