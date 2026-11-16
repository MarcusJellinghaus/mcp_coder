# Step 1: `tools/check_sensitive_files.py` with unit tests

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> TDD: write `tests/tools/test_check_sensitive_files.py` first, then the script.
> Run ruff check and format with `target_directories=["src", "tests", "tools"]`, then
> pylint, mypy and pytest (`-n auto`, fast unit-test markers). All must pass. One commit.

## Precondition

`mcp_workspace.file_tools.access_rules` must provide `AccessRules`, `READ_ONLY` and
`load_access_rules(project_dir: Path) -> AccessRules` (check with `get_library_source`).
If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Create `tools/check_sensitive_files.py`
- Create `tests/tools/test_check_sensitive_files.py`

## WHAT (script)

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = ".mcp-file-access"
WATCH_LIST = (
    "/pyproject.toml",
    "/.claude/agents/",
    "/.claude/skills/",
    "/.github/workflows/",
    "/tools/check_sensitive_files.py",
)
_REGULAR_MODES = (b"100644", b"100755")

@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: bytes
    stderr: str

def run_git(args: Sequence[str]) -> GitResult            # tests replace this via monkeypatch
def _git(*args: str) -> bytes                            # raises SystemExit on non-zero exit
def _load(data: bytes) -> AccessRules                    # temp dir + load_access_rules
def _base_rules(base: str) -> tuple[AccessRules | None, dict[int, str]]
def _reasons(path: str, rules: AccessRules | None, patterns: dict[int, str],
             watch: AccessRules) -> list[str]
def _escape_data(text: str) -> str                       # % CR LF
def _escape_property(text: str) -> str                   # _escape_data + : ,
def _escape_cell(text: str) -> str                       # | → \|, CR/LF → space
def _summary(flagged: dict[str, list[str]]) -> str
def main(argv: Sequence[str] | None = None) -> int
```

## HOW

- Imports: stdlib (`argparse`, `logging`, `os`, `re`, `subprocess`, `sys`, `tempfile`,
  `dataclasses`, `pathlib`, `collections.abc`) and
  `from mcp_workspace.file_tools.access_rules import READ_ONLY, AccessRules, load_access_rules`.
  No `mcp_coder` import.
- `run_git`: `cmd = ["git", *args]`, then
  `subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, check=False)`. Pass the variable,
  not a literal list, to avoid `S607` (as `tools/tach_docs.py` does). Decode stderr with
  `errors="replace"`.
- `_git` and `_load` look up `run_git` / `load_access_rules` as module globals at call
  time, so the tests can `monkeypatch.setattr(module, "run_git", fake)`.
- `__main__` block: `logging.getLogger(load_access_rules.__module__).disabled = True`, then
  `sys.exit(main())`.
- Ruff rules apply to `tools/`: docstrings (`D`, Google style), annotations (`ANN`), a
  `Raises:` section on `_git` (`DOC501`), `check=False` (`PLW1510`), no `/tmp` literals.
  `DOC201` (Returns) is ignored for `tools/**`.

## ALGORITHM

`_base_rules(base)`:
```
listing = _git("ls-tree", "-z", base, "--", RULES_FILE)
if not listing: print(f"No {RULES_FILE} on {base}: read-only rule check skipped."); return None, {}
if listing.split(b" ", 1)[0] not in _REGULAR_MODES: problems = ["not a regular file"]
else: raw = _git("show", f"{base}:{RULES_FILE}")
      try: original = _load(raw); problems = list(original.problems)
           if not problems: lowered = _load(raw.decode("utf-8-sig").lower().encode("utf-8")); problems = list(lowered.problems)
      except (re.error, ValueError) as exc: problems = [f"pattern error: {exc}"]
if problems: print("::warning::" + _escape_data(<invalid message>)); return None, {}
return lowered, {r.line: r.pattern for r in original.rules}
```
The invalid message names the base ref, joins the problems with `"; "`, says the MCP server
treats every committed file as read-only while the rules file is invalid, and that
read-only rule matching is skipped.

`_reasons(path, rules, patterns, watch)`:
```
lowered = path.lower(); reasons = []
if rules and (r := rules.match(lowered)) and r.level == READ_ONLY: reasons.append(f"read-only rule {patterns[r.line]}")
if lowered == RULES_FILE: reasons.append("rules file")
if (w := watch.match(lowered)): reasons.append(f"watch list {w.pattern}")
return reasons
```

`main(argv)`:
```
args = argparse (--base, --head; both required)
merge_base = _git("merge-base", args.base, args.head).decode().strip()
paths = [p.decode("utf-8", errors="replace") for p in _git("diff", "--name-only", "--no-renames", "-z", merge_base, args.head).split(b"\0") if p]
rules, patterns = _base_rules(args.base); watch = _load("".join(f"read-only {p}\n" for p in WATCH_LIST).encode())
flagged = {p: r for p in paths if (r := _reasons(p, rules, patterns, watch))}
print one "::warning file={_escape_property(p)}::{_escape_data('; '.join(r))}" per flagged file
append _summary(flagged) to $GITHUB_STEP_SUMMARY (utf-8) if set, else print it; return 0
```

## DATA

- `GitResult(returncode, stdout: bytes, stderr: str)`.
- `flagged: dict[str, list[str]]`: path as git reports it → reasons in the order read-only
  rule, rules file, watch list.
- `_summary`: if empty → `"No sensitive files changed.\n"`; else
  ```
  ## Sensitive files changed

  | File | Reasons |
  |---|---|
  | <_escape_cell(path)> | <_escape_cell("; ".join(reasons))> |
  ```
- Exit code: `0` after a completed check (also when files are flagged); `SystemExit(message)`
  → `1` when git fails.

## Tests (`tests/tools/test_check_sensitive_files.py`)

Load the script via `importlib.util.spec_from_file_location` (pattern:
`tests/tools/test_check_forbidden_calls.py`). Do **not** import `subprocess`
(`subprocess_isolation` contract). Test docstrings are not required.

Fake git (a small dataclass, used as a fixture), installed with
`monkeypatch.setattr(module, "run_git", fake)`:
- fields: `changed: list[str]`, `rules: bytes | None` (default: synthetic test rules
  `read-only /.mcp.json`, `read-only /.claude/`, `read-write /.claude/skills/` — not the
  repo's real `.mcp-file-access`; the `/.claude/` and `/.claude/skills/` rules are
  deliberately synthetic and tests 9 and 10 depend on them, so don't copy the real file),
  `mode: str = "100644"`, `fail: bool = False`, `calls: list[tuple[str, ...]]`.
- answers by `args[0]`: `merge-base` → `b"MB\n"`; `diff` → NUL-joined `changed`;
  `ls-tree` → `b""` if `rules is None` else `f"{mode} blob 0123\t.mcp-file-access\0"`;
  `show` → `rules`. With `fail=True` every call returns `GitResult(128, b"", "fatal: bad revision")`.
- helper `_run(module, monkeypatch, capsys, fake) -> tuple[int, str]`: delete
  `GITHUB_STEP_SUMMARY` from the env, call `main(["--base", "B", "--head", "H"])`, return
  the exit code and stdout.

Test cases (one test each, unless noted):
1. no rules file on the base → info line; `pyproject.toml` still flagged `watch list /pyproject.toml`.
2. invalid rules file (`read-only` with no pattern) → one `::warning::` with the problem text; watch list still applies; `.mcp.json` not flagged.
3. non-UTF-8 rules file (`b"read-only /\xff\n"`) → invalid, no crash.
4. `Read-Only /.mcp.json` → invalid; `.mcp.json` not flagged.
5. `read-only /[Z-a]x` with `sys.platform` patched to `"linux"` → the lower-cased load raises `re.error` → invalid, no crash.
6. same rule, `sys.platform` patched to `"linux"` (on win32 the original load already raises, so the lower-cased load would never be reached), and `load_access_rules` wrapped via monkeypatch so the load whose file contains `[z-a]` returns `AccessRules(problems=("line 1: invalid pattern '/[z-a]x'",))` → invalid.
7. ls-tree mode `040000` and `120000` (parametrize) → invalid.
8. `.mcp.json` → `read-only rule /.mcp.json`.
9. `.claude/settings.json` under directory rule `/.claude/` → flagged.
10. `.claude/skills/x/SKILL.md` overridden by `read-write /.claude/skills/` → no read-only reason (only `watch list /.claude/skills/`).
11. `.mcp-file-access` → `rules file`.
12. `pyproject.toml` → `watch list /pyproject.toml` only.
13. `.claude/agents/a.md` → `watch list /.claude/agents/`.
14. rename: changed `["x.json", ".mcp.json"]` → old path `.mcp.json` flagged; diff call contains `--no-renames`.
15. deleted read-only file listed by diff → flagged.
16. `.MCP.json` with `sys.platform` patched to `"linux"` → `read-only rule /.mcp.json`; output keeps `.MCP.json`.
17. base rules used though the PR changes `.mcp-file-access`: `show` call is `("show", "B:.mcp-file-access")`.
18. several reasons: `.mcp-file-access` with a base rule `read-only /.mcp-file-access` → both `read-only rule` and `rules file`.
19. nothing flagged → summary is exactly `No sensitive files changed.`
20. calls include `("merge-base", "B", "H")` and the diff starts from `MB`, not `B`.
21. escaping: `_escape_property("a%b:c,d\r\ne") == "a%25b%3Ac%2Cd%0D%0Ae"`; `_escape_data` leaves `:` and `,`; a flagged `.claude/agents/a|b.md` appears as `a\|b.md` in the table.
    End-to-end (separate test): changed path `.claude/agents/a%:,\nb.md` through `main` → stdout contains `::warning file=.claude/agents/a%25%3A%2C%0Ab.md::watch list /.claude/agents/` and no raw line starting with `b.md`.
22. `GITHUB_STEP_SUMMARY` set to a `tmp_path` file with existing content → the table is appended there, not printed; unset → printed (covered by the other tests).
23. exit code 0 when files are flagged.
24. `fail=True` → `pytest.raises(SystemExit)`, and the code is neither `0` nor `None`.

## Commit

`feat(tools): add check_sensitive_files.py for PR sensitive-file warnings (#1431)`
