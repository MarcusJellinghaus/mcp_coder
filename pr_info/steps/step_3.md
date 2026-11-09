# Step 3 — `verify`, `prompt_fragments` and registration

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 2, 8, 9.
Depends on Steps 1–2.

## LLM prompt

> Implement Step 3 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_3.md`: add `CommandToolkit.verify` and
> `CommandToolkit.prompt_fragments`, register the toolkit as entry point
> `command`, and add the import-linter contracts (TDD — tests first). Run the
> code-quality checks from CLAUDE.md, including `run_lint_imports_check`,
> `run_tach_check` and `run_vulture_check`, and make exactly one commit.

## WHERE

- `src/mcp_coder/toolkits/command/toolkit.py` — add the two methods.
- `pyproject.toml` — new table after `[project.scripts]`:
  ```toml
  [project.entry-points."mcp_coder.toolkits"]
  command = "mcp_coder.toolkits.command:CommandToolkit"
  ```
- `.importlinter` — two forbidden contracts:
  - `toolkits_isolation`: `source_modules` = every core top-level package
    (`mcp_coder.cli`, `icoder`, `workflows`, `workflow_steps`, `services`,
    `checks`, `workflow_utils`, `llm`, `prompt_manager`, `prompt_sources`,
    `prompt_parsing`, `prompts`, `install`, `utils`, `mcp_tools_py`,
    `mcp_workspace`, `mcp_workspace_git`, `mcp_workspace_github`, `config`,
    `constants`), `forbidden_modules = mcp_coder.toolkits`. Comment: new core
    packages must be added here; the source must not cover `mcp_coder.toolkits`.
  - `toolkits_isolation_root`: `as_packages = False`, `source_modules = mcp_coder`,
    `forbidden_modules = mcp_coder.toolkits, mcp_coder.toolkits.command`
    (covers `mcp_coder/__init__.py`; `as_packages = False` also applies to the
    forbidden side, so the package alone would not cover its submodules).
  Check each listed module exists (`list_directory src/mcp_coder`); drop names
  that are not packages/modules.
- `vulture_whitelist.py` — add `CommandToolkit` only if vulture reports it.
- Create `tests/toolkits/command/test_toolkit_describe.py` (verify + fragments)
  and `tests/toolkits/command/test_registration.py`.

## WHAT

```python
def verify(self, project_dir: Path, action: str | None = None) -> list[VerifyItem]: ...
def prompt_fragments(self) -> dict[str, str]: ...
def _steps_text(steps: list[Step]) -> str: ...   # shared by both check_instructions fragments
```

## HOW / ALGORITHM

`verify`:
```
parsed = parse_config(self.config); items = global problems as VerifyItems
if action and action not in parsed.steps: items.append(error "<action>: not declared")
for problem with scope: include if action is None or scope[0] == action
for each well-formed step in scope: _resolve_exe(argv0, project_dir) is None -> error "'<argv0>' not found"
return items or [VerifyItem("command", "ok")]
```
`VerifyItem(name=problem.name, status=problem.status, message=problem.message)`.

`prompt_fragments`:
- `parsed = parse_config(self.config)`; `none = llm_permissions == "none" or parsed.global_errors()`.
- `language_context`: `""`.
- `check_instructions`: `""` if `none`; else
  "Re-run the checks with these exact commands; run each one unchanged — extra
  arguments, flags or changed spacing are denied:" + `_steps_text(all steps)`.
- `check_instructions.unattended`: `""` if `none` or `test.unattended` not
  declared; else the same text for the `test.unattended` steps only.
- `_steps_text`: one line per step, deduplicated by label:
  granted → `` - `<argv joined>` ``; ungranted →
  `` - <label>: can't be re-run; results come in the fix prompt ``.
- `fix.check`, `fix.test`: generic stack-neutral text (fix the reported
  findings / failing tests in the output below; minimal changes; fix the cause,
  not the check). No placeholders — the output travels via `fix_text`.

## DATA

`list[VerifyItem]`; `dict[str, str]` with the five keys above.

## Tests

`test_toolkit_describe.py`:
- verify: unknown keys, bad parser/exit_codes/timeout/llm_permissions, empty argv,
  junit without report, report without junit, report outside project → `error`;
  non-shell-safe element → `warning`; missing `argv[0]` → `error`; undeclared
  requested action → `error`; global errors appear for `action="format"` even
  when the bad key is elsewhere; `check` step errors don't appear for `action="format"`;
  clean config → single `ok` item.
- fragments under `"bash"`: grant strings verbatim; ungranted step marked;
  `.unattended` only when `test.unattended` declared; under `"none"` both
  `check_instructions` fragments `""`; `fix.check` / `fix.test` non-empty.

`test_registration.py`:
- `tomllib` reads `pyproject.toml`; `project.entry-points["mcp_coder.toolkits"]["command"]
  == "mcp_coder.toolkits.command:CommandToolkit"`.
- `load_toolkit(tmp_path)` with `mcp-coder.toml` `toolkit = "command"` and
  `_toolkit_class` patched to `CommandToolkit` returns `name == "command"`.
