# Step 6 — Rebase: `fix_text`, toolkit-filled prompt, fix-turn grants

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 9 (no-grants
slot), 11, and the binding-level "Done when". Depends on Steps 1–5.

## LLM prompt

> Implement Step 6 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_6.md`: make `_run_all_checks` return the `fix_text` per
> action, render the Rebase Regression Fix prompt from the toolkit's
> permissions, pass Bash grants on fix turns only, and add the npm-style
> binding-level test (TDD — tests first). Run the code-quality checks from
> CLAUDE.md and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase_checks.py` — `_run_all_checks`.
- `src/mcp_coder/workflows/rebase.py` — `_prompt_in_session`,
  `_marker_filter_text`, `_build_regression_fix_prompt`, `run_rebase_workflow`.
- `src/mcp_coder/prompts/prompts.md` — section "Rebase Regression Fix".
- `src/mcp_coder/workflows/rebase_permissions.py` — module docstring only.
- Tests: `tests/workflows/rebase/test_prompt.py` and the existing rebase
  workflow/check tests (update for the new return type); new
  `tests/workflows/rebase/test_command_toolkit_binding.py`.

## WHAT

```python
FixTexts = dict[str, str]  # action -> fix_text (joined by blank line)

def _run_all_checks(project_dir: Path, automated: bool = False) -> tuple[set[FailureKey], FixTexts]
def _prompt_in_session(prompt, session_id, *, ..., step_name: str,
                       bash_grants: Sequence[str] | None = None) -> tuple[str, str | None]
def _marker_filter_text(project_dir: Path, automated: bool, permissions: Sequence[str]) -> str
def _check_tool_texts(permissions: Sequence[str]) -> tuple[str, str]   # (check sentence, shell ban)
def _build_regression_fix_prompt(replacements: dict[str, str]) -> str
```

## Prompt template (`prompts.md`)

Replace the hardcoded sentences with placeholders; keep the fixed text:
```
The list contains failure keys only. The check output after the rebase follows
below; it may also show pre-existing failures — fix only the listed regressions.
[check_tools]
[pytest_marker_filter]

Regressions (new failures versus the pre-rebase baseline):
[regression_output]

Check output after the rebase:
[fix_text]
...
**Tools:** (unchanged file/git tool list) ... nothing else.

**Prohibited:** [shell_ban]no staging, committing, or pushing — ...; no outcome markers ...
```
Update the section's "Placeholders:" line.

## ALGORITHM

`_check_tool_texts(perms)`:
```
bash = bash_grants_of(perms); mcp = [p for p in perms if p not in bash]
parts = []
if mcp: parts.append("Before editing anything, re-run the granted MCP check tools (`a`, `b`) to get the full failure detail.")
if bash: parts.append("Before editing anything, re-run the granted check commands, exactly as written: `npm run lint`, ...")
if not parts: parts.append("You cannot re-run the checks; use the output below.")
ban = "" if bash else "no shell commands of any kind; "
return " ".join(parts), ban
```
`run_rebase_workflow`:
```
entry = "rebase_automated" if automated else "rebase"
perms = llm_permissions(project_dir, provider, entry)    # computed once, before the fix loop
baseline, _ = _run_all_checks(...); after: keys, fix_texts = _run_all_checks(...); regressions = keys - baseline
fix_text = "\n\n".join(fix_texts[a] for a in sorted({k.split(": ", 1)[0] for k in regressions}) if fix_texts.get(a))
prompt = _build_regression_fix_prompt({...})
_prompt_in_session(prompt, ..., bash_grants=bash_grants_of(perms))      # conflict turns: no bash_grants
```
`_marker_filter_text`: `""` when not automated; `""` when the toolkit declares
`Bash(` grants for the binding but `perms` has none (provider dropped them —
compare with `llm_permissions(project_dir, "claude", entry)`); else the fragment.
`_run_all_checks`: `fix_texts[action]` = join of `result.fix_text or result.summary`
for results with `findings`.

## DATA

`_run_all_checks` → `({"check: npm run lint"}, {"check": "npm run lint\n..."})`.

## Docstring (`rebase_permissions.py`)

Replace the "no `Bash(...)` grants" bullet: Bash grants are not in this dict;
fix turns get the toolkit's exact `Bash(...)` grants via `--allowedTools`
(`llm_permissions`), which also applies with a `--settings` override; conflict
turns get none. `REBASE_LLM_PERMISSIONS` itself is unchanged (#1197).

## Tests

`test_prompt.py`: keep template-load tests (assert the new placeholders); turn
`test_regression_fix_prompt_rerequests_check_detail` and
`test_regression_fix_prompt_has_no_shell_or_markers` into rendered-prompt tests:
- `PythonToolkit` perms → pytest/pylint/mypy tool names present, "no shell commands" present, no "Bash";
- `command` perms with Bash under Claude → grant commands present, no shell ban,
  no `mcp__mcp-tools-py__` names;
- empty perms (`"none"` or non-Claude) → "use the output below" and the shell ban;
- `[fix_text]` is inlined; no `REBASE_OUTCOME`, no `git rebase`.

Rebase workflow tests: fix turns get `bash_grants`, conflict and marker-retry
turns don't; `_marker_filter_text` returns `""` for copilot when grants were dropped.

`test_command_toolkit_binding.py` (Done when): temp project with only
`mcp-coder.toml` (`toolkit = "command"`, `format.apply`, `check.quick`,
`check.standard`, `test.standard` running small Python scripts that act like
npm, forward-slash script paths), `_toolkit_class` patched to `CommandToolkit`,
a mock asserting nothing from `mcp_coder.mcp_tools_py` is called:
- `run_formatters(project)` → `True`;
- `run_binding(load_toolkit(p), p, "implement_final")` runs `check@quick`;
- `_run_all_checks(p)` → keys and fix texts for `check@standard` / `test@standard`
  (one script exits 1 → a key `check: <name>`).
