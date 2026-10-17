# Step 1 — Local check: Dependabot config

Part of mcp_coder#1180. Read `pr_info/steps/summary.md` first for the overall design.

No dependency on mcp-workspace#314 — proceeds unconditionally.

## LLM prompt

> Implement Step 1 of mcp_coder#1180 exactly as specified in `pr_info/steps/step_1.md`,
> using the architecture in `pr_info/steps/summary.md`. Write the tests first, then the
> implementation, until they pass. Run `mcp__mcp-tools-py__run_pylint_check`,
> `mcp__mcp-tools-py__run_pytest_check`, and `mcp__mcp-tools-py__run_mypy_check`; all
> must pass. Then make exactly one commit for this step.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py` — add the function.
- `tests/cli/commands/test_verify_sections_security.py` — **new file**, test class
  `TestCheckDependabotConfig`.

## WHAT

```python
def _check_dependabot_config(project_dir: Path) -> CheckResult:
    """Check .github/dependabot.yml for configured ecosystems and schedules."""
```

## HOW

- Add imports to `verify_sections.py`:
  - `import yaml` (PyYAML — already a transitive dependency via `python-frontmatter`;
    no `pyproject.toml` change needed).
  - `from ...mcp_workspace_github import CheckResult`.
- No wiring into `verify.py` yet — that happens in Step 3. This step only adds the
  function and its tests.
- Three-state convention is **not** used here: this is a deterministic local-file
  read with no permission barrier, so the row is always `ok=True` or `ok=False`,
  never `None`. `severity` is always `"warning"` (the section is exit-neutral
  regardless — see summary.md).
- Missing/invalid `.github/dependabot.yml` renders `ok=False` → `[ERR]`, not `[WARN]`,
  deliberately — this mirrors the sibling local-file row from Step 2 (`CodeQL
  workflow`), where the issue's own rendered example shows an absent workflow as
  `[ERR]`, not `[WARN]`: `CodeQL workflow [ERR] no workflow step uses
  github/codeql-action`. Both rows answer "is this local config present and
  parseable", with no permission barrier to justify a softer `[WARN]`. The issue's
  Problem section calling `dependabot.yml` "optional in the setup matrix" explains
  why checking for it is useful (it's easy to skip when propagating configs by
  hand), not that its absence should render at a lower severity than the other
  local-file row — that's unlike the *API-backed* `dependabot_security_updates`
  row, which the issue deliberately renders at `[WARN]` for a different reason
  (an already-configured-but-weaker state, not "nothing set up"). The symbol
  carries no exit-code weight either way (the section stays exit-neutral), so
  this is a display-consistency choice, not a correctness one.

## ALGORITHM

```
path = project_dir / ".github" / "dependabot.yml"
if path does not exist: return ok=False, value="not present"
parse YAML; on parse error: return ok=False, value="invalid YAML (<error>)"
updates = data["updates"] if a dict with a list there, else None
if not updates: return ok=False, value="no ecosystems configured"
collect (ecosystem, interval) pairs from each dict entry in updates
if every interval is identical: value = ".github/dependabot.yml (<eco1, eco2>: <interval>)"
else: value = ".github/dependabot.yml (<eco1>: <interval1>, <eco2>: <interval2>, ...)"
return ok=True, value=value
```

Ecosystem/interval come from `package-ecosystem` and `schedule.interval` on each
`updates[]` entry; entries missing either key fall back to `"?"` rather than raising.

## DATA

Returns a `CheckResult` (`TypedDict` from `mcp_workspace_github`):

```python
CheckResult(ok=True, value=".github/dependabot.yml (pip: weekly)", severity="warning")
```

## Tests (write first)

In `tests/cli/commands/test_verify_sections_security.py`, using `tmp_path` to build a
fake `project_dir`:

- `test_missing_file_returns_false` — no `.github` dir at all. Pin down both the
  wording and the severity: assert `ok is False` (renders `[ERR]`, matching the
  `CodeQL workflow` row's own missing-case severity — see HOW) and
  `value == "not present"` exactly.
- `test_invalid_yaml_returns_false` — file contains unparsable YAML.
- `test_no_updates_key_returns_false` — valid YAML, no `updates` key.
- `test_empty_updates_list_returns_false` — `updates: []`.
- `test_single_ecosystem` — one `pip`/`weekly` entry → `ok=True`, value contains
  `"pip: weekly"`.
- `test_multi_ecosystem_uniform_schedule` — `pip` and `npm`, both `weekly` → value
  contains `"pip, npm: weekly"` (collapsed).
- `test_multi_ecosystem_mixed_schedule` — `pip: weekly`, `npm: daily` → value contains
  `"pip: weekly, npm: daily"` (not collapsed).
