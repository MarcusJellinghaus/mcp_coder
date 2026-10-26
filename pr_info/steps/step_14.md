# Step 14 — Enforcement: `tools/check_forbidden_calls.py` + CI + wrappers

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_14.md`. Implement step 14 only,
> tests first. Run the tool (`python tools/check_forbidden_calls.py` via the wrapper or
> pytest-invoked `main`), pylint, pytest (fast unit set, `-n auto`), mypy and lint-imports
> until all pass, run the formatter, and make one commit:
> `ci: add forbidden-calls check (git argv, direct mcp_workspace imports)`.

## Precondition

Steps 1–13 are committed. The tool must report zero hits on `src/`. A hit means a missed
migration: migrate it in this step. If a hit cannot be migrated with an existing shim
function, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Create `tools/check_forbidden_calls.py`
- Create `tools/forbidden_calls_check.sh`, `tools/forbidden_calls_check.bat`
- Create `tests/tools/test_check_forbidden_calls.py`
- Modify `.github/workflows/ci.yml` (matrix, next to `no-url-deps`, ~line 107)
- Modify `.importlinter` (~73–86 TODO blocks; comment next to `[importlinter:contract:subprocess_isolation]` ~498)

## WHAT — tool (pattern of `tools/check_no_url_deps.py`: stdlib only, `main() -> int`)

```python
@dataclass(frozen=True)
class Rule:
    id: str
    patterns: tuple[re.Pattern[str], ...]
    paths: tuple[str, ...]      # scanned roots, repo-relative POSIX
    exclude: tuple[str, ...]    # repo-relative POSIX file paths
    message: str

RULES: tuple[Rule, ...] = (
    Rule("git", (re.compile(r'\[\s*"git"'),), ("src",), (),
         "use `mcp_coder.mcp_workspace_git`"),
    Rule("workspace-git-direct-import", (re.compile(r"mcp_workspace\.git_operations"),),
         ("src",), ("src/mcp_coder/mcp_workspace_git.py",),
         "import from `mcp_coder.mcp_workspace_git`"),
    Rule("workspace-github-direct-import", (re.compile(r"mcp_workspace\.github_operations"),),
         ("src",), ("src/mcp_coder/mcp_workspace_github.py",),
         "import from `mcp_coder.mcp_workspace_github`"),
)

def find_violations(rel_path: str, text: str, rules: Sequence[Rule] = RULES) -> list[str]:
    """Return "<path>:<line>: [<rule id>] <message>" for every hit in one file."""

def main() -> int:
    """Scan every *.py under each rule's paths; print hits; 1 if any, else 0."""
```

## ALGORITHM

```
find_violations: for rule in rules:
    skip if rel_path not under any rule.paths or rel_path in rule.exclude
    for pattern in rule.patterns: for m in pattern.finditer(text):
        line = text.count("\n", 0, m.start()) + 1 -> append f"{rel_path}:{line}: [{rule.id}] {rule.message}"
main: root = Path(__file__).resolve().parent.parent; for py in sorted(root/"src").rglob("*.py"):
    hits += find_violations(py.relative_to(root).as_posix(), py.read_text(encoding="utf-8"))
print hits + "ERROR: ..." and return 1, else print "OK: no forbidden calls" and return 0
```

Text scan, no AST: `\s*` matches newlines, so a multi-line list `[\n    "git",` is caught.
Module docstring states the known limit: an argv that never spells `"git"` literally
(`[GIT_BIN, ...]`, `shlex.split`) is not caught — this guards accidents, not bypass; and
lists what is out of scope (tests, `command_templates.py` shell text, `gh`, tools scripts).

## WHAT — wrappers (style of `tools/ruff_check.sh/.bat`)

- `.sh`: header comment + `python tools/check_forbidden_calls.py "$@"`
- `.bat`: `@echo off`, header `REM`, `python tools\check_forbidden_calls.py %*`, `exit /b %ERRORLEVEL%`

## WHAT — CI / config

- `ci.yml`: `- {name: "forbidden-calls", cmd: "python tools/check_forbidden_calls.py"}` (no `install:` key).
- `.importlinter`: replace both TODO blocks with "Enforced by `tools/check_forbidden_calls.py`
  (rules `workspace-git-direct-import` / `workspace-github-direct-import`) — import-linter cannot
  resolve external subpackages." Next to `subprocess_isolation`: "Running git through the
  allowed runner is caught by `tools/check_forbidden_calls.py` (rule `git`)."

## Tests (write first) — `tests/tools/test_check_forbidden_calls.py`

Load the tool with `importlib.util.spec_from_file_location` (as `test_ci_coverage_summary.py` does).
Fixture strings only; the test does not scan the repo.

- `execute_command(["git", "status"])` in `src/mcp_coder/x.py` → one hit, rule `git`, line 1.
- multi-line `[\n    "git",\n    "fetch",\n]` → one hit with the line of `[`.
- `from mcp_workspace.git_operations.core import X` in `src/mcp_coder/mcp_workspace_git.py` → no hit (excluded); same text in `src/mcp_coder/other.py` → hit `workspace-git-direct-import`.
- same for `mcp_workspace.github_operations` / `mcp_workspace_github.py`.
- path outside `src/` (e.g. `tests/test_x.py` with `["git", "init"]`) → no hit.
- clean file → `[]`.
- `main()` returns 0 when patched to scan an empty temp `src` tree and 1 with one offending file
  (monkeypatch the root, or factor `scan(root: Path) -> list[str]` and test that).

## DATA

- `find_violations` → `list[str]`; `main` → exit code `0 | 1`.
