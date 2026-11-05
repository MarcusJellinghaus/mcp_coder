# Step 2: Subprocess rule, tests and docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, then implement this step. Write the test first and see it fail, then add the rule, update the stale text and docs, and verify `src/` is clean with the `.scratch/` probe. This step produces exactly one commit. Write the commit message to `pr_info/.commit_message.txt`. Do not commit yourself.

## WHERE

- `tests/tools/test_check_forbidden_calls.py`
- `tools/check_forbidden_calls.py`
- `tools/forbidden_calls_check.sh`, `tools/forbidden_calls_check.bat`
- `docs/repository-setup/quality-and-security-checks.md`
- `docs/architecture/enforcement.md`
- Create, then delete in this step: `.scratch/test_probe.py`

## WHAT

### Test (write first)

Add after `test_git_argv_multi_line_reports_bracket_line`, with the two constants next to the other module-level names. Write the tool list out here. Do not import it from the script, because only an independent list catches a typo in the rule.

```python
_QUALITY_TOOLS = (
    "pytest",
    "pylint",
    "mypy",
    "ruff",
    "vulture",
    "bandit",
    "lint-imports",
    "tach",
    "deptry",
)

# (argv template, line reported): a multi-line match starts at "-m" or "run",
# not at the bracket.
_QUALITY_TOOL_ARGVS = (
    ('cmd = ["{tool}", "-q"]\n', 1),
    ('cmd = [\n    "{tool}",\n    "-q",\n]\n', 1),
    ('cmd = [sys.executable, "-m", "{tool}"]\n', 1),
    ('cmd = [\n    sys.executable,\n    "-m",\n    "{tool}",\n]\n', 3),
    ('cmd = ["uv", "run", "{tool}"]\n', 1),
    ('cmd = [\n    "uv",\n    "run",\n    "{tool}",\n]\n', 3),
)


@pytest.mark.parametrize("tool", _QUALITY_TOOLS)
@pytest.mark.parametrize(("template", "line"), _QUALITY_TOOL_ARGVS)
def test_quality_tool_argv_is_hit(tool: str, template: str, line: int) -> None:
    hits = find_violations("src/mcp_coder/x.py", template.format(tool=tool))
    assert len(hits) == 1
    assert hits[0].startswith(f"src/mcp_coder/x.py:{line}: [quality-tools]")
```

### Rule

In `tools/check_forbidden_calls.py`, add the constant above `RULES` and the entry after the `git` rule:

```python
_QUALITY_TOOLS = "pytest|pylint|mypy|ruff|vulture|bandit|lint-imports|tach|deptry"
```

```python
    Rule(
        "quality-tools",
        (re.compile(rf'(?:\[\s*|"-m",\s*|"run",\s*)"(?:{_QUALITY_TOOLS})"'),),
        ("src",),
        (),
        "use the quality-tool boundary, not a subprocess",
    ),
```

### Module docstring

Summary line:

```
Fail if ``src/`` runs git or quality tools, or imports mcp_workspace internals.
```

Add this rule after the `git` bullet:

```
- ``quality-tools``: an argv with a Python quality tool (pytest, pylint, mypy,
  ruff, vulture, bandit, lint-imports, tach, deptry) as ``["<tool>"``,
  ``"-m", "<tool>"`` or ``"run", "<tool>"``, also split across lines. Use the
  quality-tool boundary instead.
```

Add this paragraph after the "text scan" paragraph:

```
``quality-tools`` also misses ``[exe, "pytest"]``, ``("pytest", "-q")``, flags
between ``run`` and the tool, ``["uvx", "ruff"]`` and shell strings. It can hit
non-argv text such as ``x = ["mypy", "pylint"]``, ``cfg["mypy"]`` or
``Literal["pytest", "mypy"]``. Nothing in ``src/`` does today; narrow the
pattern if later work needs such text.
```

### Script comments

In both `tools/forbidden_calls_check.sh` and `tools/forbidden_calls_check.bat`, keep the `#` / `REM` prefix and change the first comment line to:

```
Check src for git and quality-tool subprocess argv and direct mcp_workspace imports
```

### Docs

`docs/repository-setup/quality-and-security-checks.md`, `forbidden-calls` entry:

```markdown
- `forbidden-calls` ([`check_forbidden_calls.py`](../../tools/check_forbidden_calls.py)):
  text scan of `src/` for literal `["git", …]` argv lists, literal argv lists that run a
  Python quality tool (`["pytest", …]`, `"-m", "pytest"`, `"run", "pytest"`), and direct
  `mcp_workspace.git_operations` / `github_operations` imports outside their shims. Why:
  [`enforcement.md`](../architecture/enforcement.md#shim-boundary).
```

`docs/architecture/enforcement.md`, new paragraph at the end of "Shim boundary":

```markdown
Python quality tools (pytest, pylint, mypy, ruff, vulture, bandit, import-linter, tach, deptry) are reached only through the quality-tool boundary, today the `mcp_coder.mcp_tools_py` shim. The `quality_tools_isolation` contract in [`.importlinter`](../../.importlinter) forbids importing them. import-linter cannot see subprocess calls, so the `quality-tools` rule in `RULES` guards literal argv lists.
```

## HOW

`find_violations()` and `scan()` are unchanged and pick the new rule up from `RULES`. `paths=("src",)` keeps `tests/` and `tools/` out of scope, and no file is excluded.

Probe for the done-when check, `.scratch/test_probe.py`:

```python
"""One-off: the real src/ tree has no forbidden calls."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_src_is_clean() -> None:
    spec = importlib.util.spec_from_file_location(
        "check_forbidden_calls", ROOT / "tools" / "check_forbidden_calls.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.scan(ROOT) == []
```

Run it with `run_pytest_check(extra_args=["-p", "no:cacheprovider", ".scratch/test_probe.py"])`, then `delete_directory(".scratch", recursive=True)`.

## ALGORITHM

```
add the test                -> run it, the 54 new cases fail
add _QUALITY_TOOLS and the Rule entry
run the test file           -> all pass, including the existing git tests
update docstring, script comments and docs
run the probe, delete .scratch/
```

If the probe reports violations, delete `.scratch/`, write one line to `pr_info/.blocked.txt` naming the first hit, and stop. Do not widen, narrow or exclude to make it pass.

## DATA

Each hit keeps the existing format, for example:

```
src/mcp_coder/x.py:3: [quality-tools] use the quality-tool boundary, not a subprocess
```

`pr_info/.commit_message.txt`:

```
feat(tools): forbid running quality tools as subprocesses

Add a quality-tools rule to check_forbidden_calls.py for literal argv lists,
with tests for all nine tools, three patterns and both line forms.
```

## Checks

- `.scratch/` no longer exists.
- Run pylint, mypy, ruff and pytest with the fast-unit-test markers.
- `run_format_code` runs before the commit, as usual.
