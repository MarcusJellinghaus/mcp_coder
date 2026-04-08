# Step 4: Deploy logic and integration into execute_init

**Summary reference:** See `pr_info/steps/summary.md` for overall architecture.

## Goal

Add `_deploy_skills()` to `init.py` and integrate it into `execute_init()` so that `mcp-coder init` deploys skills by default, and `--just-skills` skips config creation.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4: add `_deploy_skills()` in `init.py` with never-overwrite copy logic, integrate into `execute_init()` (default: config + skills, --just-skills: skills only), resolve --project-dir. Write tests first (TDD), then implement, then run all three code quality checks.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/init.py` | **Edit** — add `_deploy_skills()`, update `execute_init()` |
| `tests/cli/commands/test_init.py` | **Edit** — add deploy tests, update existing tests |

## WHAT

### `init.py` — `_deploy_skills()`

```python
def _deploy_skills(source_dir: Path, project_dir: Path) -> tuple[int, int]:
    """Deploy Claude skills, knowledge_base, and agents to a project.

    Copies files from source_dir into project_dir/.claude/. Never overwrites
    existing files — skips them with a warning.

    Args:
        source_dir: Path containing skills/, knowledge_base/, agents/ subdirs.
        project_dir: Target project root.

    Returns:
        Tuple of (files_added, files_skipped).
    """
```

### `init.py` — Updated `execute_init()`

```python
def execute_init(args: argparse.Namespace) -> int:
    # 1. Validate --project-dir EARLY (before deploy or config creation)
    if args.project_dir is not None:
        project_dir = Path(args.project_dir)
        if not project_dir.exists():
            logger.error("Project directory does not exist: %s", project_dir)
            return 1
    else:
        project_dir = Path.cwd()

    # 2. Resolve source and detect self-deploy (running inside mcp-coder source repo)
    source_dir = _find_claude_source_dir()  # from step 3
    target_base = project_dir / ".claude"
    if source_dir.resolve() == target_base.resolve():
        logger.info("Skipping deploy: running inside mcp-coder source repo")
    else:
        added, skipped = _deploy_skills(source_dir, project_dir)
        logger.log(OUTPUT, "Skills: %d added, %d skipped", added, skipped)

    # 3. Config creation (skip if --just-skills)
    if not args.just_skills:
        # ... existing config creation logic ...

    return 0
```

**Behavior notes:**

- **Missing --project-dir:** If `args.project_dir` is set but the path does not exist, exit 1 with a clear error. Checked first so we fail fast before any side effects.
- **Self-deploy detection:** Compare `source_dir.resolve()` with `target_base.resolve()`. When equal (the user is running `mcp-coder init` inside the mcp-coder source tree itself, where source and target are the same `.claude/`), skip deploy silently with a single info log line. This prevents the warning spam of skipping every file against itself.
- Both checks live at the top of `execute_init()` so the order is: validate args → resolve source → self-deploy check → deploy → config.

## HOW

- `_deploy_skills` uses `shutil.copy2` for individual files (not `copytree`) to enable per-file skip logic.
- Walks source subdirs recursively using `Path.rglob("*")`.
- For each file, computes relative path and checks if target exists before copying.
- Creates intermediate directories with `Path.mkdir(parents=True, exist_ok=True)`.

## ALGORITHM — `_deploy_skills()`

```python
def _deploy_skills(source_dir: Path, project_dir: Path) -> tuple[int, int]:
    added, skipped = 0, 0
    target_base = project_dir / ".claude"
    for subdir_name in DEPLOY_SUBDIRS:
        src_sub = source_dir / subdir_name
        if not src_sub.is_dir():
            continue
        for src_file in src_sub.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(source_dir)
            dest = target_base / rel
            if dest.exists():
                logger.warning("Skipped (exists): %s", rel)
                skipped += 1
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
                added += 1
    return added, skipped
```

## DATA

- **Input:** `source_dir: Path` (from `_find_claude_source_dir()`), `project_dir: Path` (from `--project-dir` or CWD)
- **Returns:** `tuple[int, int]` — `(files_added, files_skipped)`
- **Output logging:** Summary line `"Skills: N added, M skipped"` at OUTPUT level. Per-file `WARNING` for each skipped file.

## TESTS

```python
class TestDeploySkills:
    def test_deploy_to_empty_project(self, tmp_path):
        """All files deployed when target .claude/ doesn't exist."""

    def test_never_overwrites_existing_files(self, tmp_path):
        """Existing files are skipped, not overwritten."""

    def test_returns_correct_counts(self, tmp_path):
        """Returns (added, skipped) counts matching actual operations."""

    def test_skipped_files_emit_warning(self, tmp_path, caplog):
        """Each skipped file produces a warning log message."""

    def test_creates_intermediate_directories(self, tmp_path):
        """Creates nested dirs (e.g., skills/plan_review/) as needed."""

    def test_handles_missing_source_subdir(self, tmp_path):
        """Gracefully handles source dir missing a subdir (e.g., no agents/)."""


class TestExecuteInitWithDeploy:
    def test_default_creates_config_and_deploys(self, tmp_path, monkeypatch):
        """Default init creates config AND deploys skills."""

    def test_just_skills_skips_config(self, tmp_path, monkeypatch):
        """--just-skills deploys skills but does NOT create config."""

    def test_project_dir_flag(self, tmp_path, monkeypatch):
        """--project-dir targets the specified directory."""

    def test_deploy_failure_exits_1(self, monkeypatch):
        """Exit 1 when source cannot be found (from _find_claude_source_dir).

        Integration smoke test complementing step 3's unit tests for
        _find_claude_source_dir — verifies the sys.exit(1) actually propagates
        through execute_init().
        """

    def test_missing_project_dir_exits_1(self, tmp_path):
        """--project-dir pointing at a non-existent path exits 1 with a clear error."""

    def test_self_deploy_is_skipped(self, tmp_path, monkeypatch, caplog):
        """When source_dir.resolve() == target_base.resolve(), skip deploy silently.

        - Asserts _deploy_skills is NOT called.
        - Asserts an info log line like 'Skipping deploy: running inside mcp-coder source repo'.
        - Config creation still runs (unless --just-skills).
        """
```

## Integration with existing tests

Existing tests in `TestInitCommand` mock `create_default_config` and `get_config_file_path`. They need to be updated to:
1. Include `just_skills=False, project_dir=None` in `argparse.Namespace`.
2. Mock `_find_claude_source_dir` and `_deploy_skills` to isolate config-creation tests from deploy logic.
