# Step 4 — FILE ACCESS section (workspace + reference projects)

Read [summary.md](summary.md) first. Requires steps 1–3. One commit.

## LLM prompt

> Implement step 4 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_4.md`.
> Write `tests/cli/commands/test_verify_file_access_section.py` and the conftest autouse
> mocks first, then add the shim names, `_load_mcp_json`, `_lookup_reference_projects`,
> `_print_file_access_section`, the `file_access_ok` exit-code input, remove the PROJECT
> `.mcp-file-access` row and update the docs. Rows must match `mcp-workspace verify`.
> Run pylint, pytest (`-n auto`, fast unit markers), mypy, ruff, lint-imports, tach,
> vulture, deptry; format; commit.

## Precondition

`mcp_workspace.file_tools` exports `verify_file_access` and `FileAccessVerification`;
`mcp_workspace.main._check_reference_projects(reference_args, project_dir)` returns
`(dict[str, ReferenceProject], list[tuple[str, str]])`. If not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace.py` — new re-exports
- `src/mcp_coder/cli/commands/verify_sections.py` — `_load_mcp_json`, `_lookup_reference_projects`; `_validate_mcp_config` uses the loader; delete `_file_access_row`
- `src/mcp_coder/cli/commands/verify.py` — `_print_file_access_section`, call order, smoke-test text
- `src/mcp_coder/cli/commands/verify_exit_code.py` — `file_access_ok`
- `tests/cli/commands/conftest.py` — two autouse mocks
- `tests/cli/commands/test_verify_file_access_section.py` — new
- `tests/cli/commands/test_verify_project_section.py`, `test_verify_mcp_edit_smoke.py`, `test_verify_exit_codes.py`
- `docs/cli-reference.md`, `docs/repository-setup/repo.md`

## WHAT

### Shim `src/mcp_coder/mcp_workspace.py` (add to imports and `__all__`)

```python
from mcp_workspace.cli.verify_formatting import format_file_access_section  # next to the step-2 names
from mcp_workspace.file_tools import FileAccessVerification, verify_file_access
# Private upstream name: the only API that also returns the rejected references.
from mcp_workspace.main import _check_reference_projects
```

### `verify_sections.py`

```python
def _load_mcp_json(mcp_json_path: str) -> Any:
    """Parse ``.mcp.json``. Raises OSError / json.JSONDecodeError (ValueError)."""
    return json.loads(Path(mcp_json_path).read_text(encoding="utf-8"))
```

`_validate_mcp_config` calls `_load_mcp_json` inside its existing `try`; its
`(ok, message, warnings)` return and messages are unchanged.

```python
def _lookup_reference_projects(
    project_dir: Path, mcp_json_path: str | None, env_vars: Mapping[str, str] | None
) -> tuple[list[tuple[str, Path]], list[tuple[str, str]]]:
    """Validate the mcp-workspace server's ``--reference-project`` args.

    Returns accepted ``(final name, path)`` in argument order and rejected
    ``(label, reason)`` pairs. Never returns ``ReferenceProject``: its ``url``
    keeps raw credentials. Raises whatever ``_check_reference_projects`` raises.
    """
```

Imports: `WORKSPACE_SERVER` from `...utils.toolkit_runner`; `_check_reference_projects` from
`...mcp_workspace`; `resolve_placeholders` (already imported).

Delete `_file_access_row`; `_print_project_section` no longer calls it and returns
`ok` (docstring: drop `.mcp-file-access`). Drop the `validate_access_rules` import if unused.

### `verify.py`

```python
from ...mcp_workspace import FileAccess, format_file_access_section, get_file_access, validate_access_rules, verify_file_access
from .verify_sections import _lookup_reference_projects  # bound here so tests patch verify.<name>

def _print_file_access_section(
    project_dir: Path,
    mcp_config_path: str | None,
    env_vars: dict[str, str],
    symbols: dict[str, str],
    out: SectionBuilder,
) -> bool:
    """Print FILE ACCESS: workspace, accepted references, rejected references.

    Same rows as ``mcp-workspace verify``. Returns False when any row is [ERR].
    """
```

In `_run_verify`, directly after `project_ok = _print_project_section(...)`:

```python
mcp_config_resolved = resolve_mcp_config_path(args.mcp_config, project_dir=args.project_dir)
env_vars = prepare_llm_environment(project_dir)
file_access_ok = _print_file_access_section(project_dir, mcp_config_resolved, env_vars, symbols, out)
```

Remove the two later calls (keep `settings_file = resolve_claude_settings_path(...)` where it
is; move their comments with them). Pass `file_access_ok=file_access_ok` to
`_compute_exit_code`. `_smoke_test_skip_reason` text →
`"skipped: invalid .mcp-file-access (see FILE ACCESS)"`.

### `verify_exit_code.py`

New keyword `file_access_ok: bool = True` (last parameter); `if not file_access_ok: return 1`
right after the `project_ok` check. Docstring: add the arg ("any [ERR] row in FILE ACCESS:
invalid rules file of the workspace or a reference, rejected reference, lookup error"),
drop `.mcp-file-access` from `project_ok`, add FILE ACCESS to the summary sentence.

## ALGORITHM

`_lookup_reference_projects`:

```
if mcp_json_path is None: return [], []
try: data = _load_mcp_json(mcp_json_path) except (OSError, ValueError): return [], []
server = data.get("mcpServers", {}).get(WORKSPACE_SERVER) if dicts else None; args = server.get("args") if list else []
it = iter(args); raw = [next(it, None) if a == "--reference-project" else a.split("=", 1)[1] for a in it if a == "--reference-project" or a.startswith("--reference-project=")]  # str items only, drop None
accepted, rejected = _check_reference_projects([resolve_placeholders(r, env_vars)[0] for r in raw], project_dir)
return [(name, ref.path) for name, ref in accepted.items()], rejected
```

(Write the arg scan as a plain loop over an iterator; the one-liner is shorthand. The
server's `--project-dir` arg is ignored; verify's own `project_dir` is passed.)

`_print_file_access_section`:

```
out.open("FILE ACCESS"); workspace = verify_file_access(project_dir); ok = workspace["overall_ok"]
out.add(*format_file_access_section(workspace, symbols, label="workspace"))
try: accepted, rejected = _lookup_reference_projects(project_dir, mcp_config_path, env_vars)
except Exception as exc: out.add(Row("reference projects", symbols["failure"], str(exc), wrap=True)); out.close(); return False
for name, path in accepted: path missing → Row(name, warning, "path not found"); else r = verify_file_access(path); ok &= r["overall_ok"]; out.add(*format_file_access_section(r, symbols, label=name))
for label, reason in rejected: out.add(Row(label, failure, f"rejected: {reason}")); ok = False
out.close(); return ok
```

(`except Exception` with `# pylint: disable=broad-except`: verify must not crash; the
upstream message is already credential-scrubbed.)

## DATA

- `verify_file_access(path) -> FileAccessVerification = {"rules_file": CheckResult, "overall_ok": bool}`;
  values `absent - gitignore only`, `N rules`, `invalid` + `error`.
- Lookup: `([(name, Path)], [(label, reason)])`.
- Rows: `workspace [OK] absent - gitignore only`, `<name> [WARN] path not found`,
  `<label> [ERR] rejected: <reason>`, `reference projects [ERR] <message>`.

## Tests (write first)

### `tests/cli/commands/conftest.py` — autouse

```python
@pytest.fixture(autouse=True)
def _mock_verify_file_access() -> Generator[MagicMock, None, None]:
    """Keep execute_verify off the repo's own .mcp-file-access."""
    default = {"rules_file": {"ok": True, "value": "absent - gitignore only", "severity": "error"}, "overall_ok": True}
    with patch(f"{_VERIFY}.verify_file_access", return_value=default) as mock: yield mock

@pytest.fixture(autouse=True)
def _mock_lookup_reference_projects() -> Generator[MagicMock, None, None]:
    """Keep execute_verify off the real .mcp.json and reference repos (no GitPython)."""
    with patch(f"{_VERIFY}._lookup_reference_projects", return_value=([], [])) as mock: yield mock
```

Add both names to `vulture_whitelist.py` next to the other fixtures if vulture reports them.

### `tests/cli/commands/test_verify_file_access_section.py` (new)

`TestLookupReferenceProjects` — calls `verify_sections._lookup_reference_projects` (not the
patched binding); writes a tmp `.mcp.json`; references are tmp dirs **without** `url=` (no git):
- `None` path, missing file, malformed JSON, no `mcp-workspace` server, `args` not a list → `([], [])`
- `["--reference-project", "name=a,path=<dir>"]` → `([("a", <dir resolved>)], [])`
- `"--reference-project=name=a,path=<dir>"` form accepted; order kept across both forms
- `path=${REF_DIR}` resolved from `env_vars={"REF_DIR": ...}`
- other args (`--project-dir X`, `--log-level`) ignored
- missing path without url → `([], [("a", "path not found")])`
- path == project_dir → rejected `"same directory as workspace"`

`TestPrintFileAccessSection` — calls `verify._print_file_access_section` with a
`SectionBuilder`, capturing stdout; patch `verify.verify_file_access` with the real
`mcp_coder.mcp_workspace.verify_file_access` and use tmp dirs; set the lookup return per case:
- workspace without rules file → `workspace [OK] absent - gitignore only`, returns True
- workspace `read-write /.scratch/\n` → `[OK] 1 rules`
- workspace `writable /x\n` → `[ERR] invalid (` …, returns False
- accepted ref with valid rules → row labelled with its name, True
- accepted ref with invalid rules → False
- accepted ref whose path doesn't exist → `[WARN] path not found`, True
- rejected `("bad", "missing path")` → `bad [ERR] rejected: missing path`, False
- lookup raises `ValueError("URL mismatch")` → exactly one row after workspace:
  `reference projects [ERR] URL mismatch`, False
- order: workspace, accepted (argument order), rejected; all rows share one value column
  (`_assert_section_aligned` from `.conftest`)

`TestExecuteVerifyFileAccess` — through `execute_verify` with `_make_verify_mocks()`:
- section order: `=== PROJECT` < `=== FILE ACCESS` < `=== GIT`
- lookup returns a rejected entry → exit 1; accepted entry with missing path → exit 0
- lookup is called with `(project_dir, "/fake/.mcp.json", {"K": "V"})`

### Other test updates

- `test_verify_exit_codes.py`: `_compute_exit_code(..., file_access_ok=False) == 1`, default stays 0.
- `test_verify_project_section.py`: delete `TestFileAccessRow` and its constants; remove
  `".mcp-file-access"` from `TestProjectLayout` labels; module docstring without
  `.mcp-file-access`.
- `test_verify_mcp_edit_smoke.py`: expected text `skipped: invalid .mcp-file-access (see FILE ACCESS)`.
- Any test asserting the PROJECT `.mcp-file-access` row or `not present (gitignore defaults)` /
  `[OK] valid`: search `tests/` and fix.

## HOW — docs

- `docs/cli-reference.md` verify paragraph: replace "project configuration (including the
  `.mcp-file-access` rules file; an invalid file exits 1)" with "project configuration,
  `FILE ACCESS` (the `.mcp-file-access` rules file of the workspace and of each reference
  project passed to the mcp-workspace server in `.mcp.json`; an invalid file or a rejected
  reference exits 1, a reference whose path does not exist is `[WARN] path not found` when it
  has `url=` and `[ERR] rejected: path not found` without)"; "listed in the project section"
  → "listed in FILE ACCESS".
- `docs/repository-setup/repo.md` "An invalid file" bullet: "`mcp-coder verify` shows it as
  `[ERR]` in the FILE ACCESS section (workspace and reference projects) and exits 1."
