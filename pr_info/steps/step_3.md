# Step 3 — vscodeclaude switchover (atomic)

`create_startup_script` calls `_resolve_install_script` at `workspace.py:602`, which
raises `FileNotFoundError` when the script is absent. Deleting the resolver, retiring
the spec field, changing the argv and trimming the tests **must** be one commit —
neither half passes alone.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | delete `_resolve_install_script` (`:482-514`), its call (`:602`), the `install_script_path=` kwarg (`:615`), docstrings (`:550`, `:554`, `:561`) |
| `src/mcp_coder/workflows/vscodeclaude/types.py` | drop the field (`:245`); filter unknown keys in `read_session_spec` |
| `src/mcp_coder/workflows/vscodeclaude/session_setup.py` | new `build_install_argv`; delete `_coordinator_python` (`:56-66`); its docstring (`:109`, `:115`, `:119`) |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | docstrings `:5`, `:28` |
| `tests/workflows/vscodeclaude/test_startup_script_mcp_coder_path.py` | delete 2nd test; trim 1st |
| `tests/workflows/vscodeclaude/test_session_setup_env.py` | `:38`, `:130`, `:134` |
| `tests/workflows/vscodeclaude/test_session_setup_flow.py` | `:44`, `:99` |
| `tests/workflows/vscodeclaude/test_session_spec.py` | `:25`, `:67` + new case |
| `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py` | docstrings only (`:4`, `:151`) — the argv assertions do not change |

The line numbers above are navigation aids, not the checklist. The checklist is the grep
exit criterion in HOW.

## WHAT

```python
# session_setup.py — signature unchanged
def build_install_argv(spec: SessionSpec, cwd: Path) -> list[str]:
```

```python
# types.py — SessionSpec loses one field
mcp_config: str
mcp_coder_install_path: str          # install_script_path removed from between them
skip_github_install: bool
```

## HOW

- `build_install_argv` uses the existing `_mcp_coder_exe(spec)` helper — the same one
  `build_step_argv` already uses — so `_coordinator_python` has no callers and goes.
- `--extras dev` disappears from the argv (Decision 4); `--use-sync`, `--refresh` and
  the conditional `--skip-overrides` stay.
- `read_session_spec` filters unknown keys with `dataclasses.fields`. Two lines, no
  helper class. Add a comment recording the asymmetry: a *missing* key still raises, so
  any future added field needs a default.
- `regenerate_session_files` (`session_launch.py:424`) needs no edit — it goes through
  `create_startup_script`.
- **Every remaining `install.py` / `install_script_path` mention this step makes false goes
  with it — and the definition of done is a grep, not a list.** Step 6 is doc-only and
  cannot reach `src/` or `tests/`, and Step 5 TESTS §2 and Step 6 verification §1 both
  rely on `src/` and `tests/` being clean from here on. Exit criterion:

  ```
  git grep -n "install\.py\|install_script_path" -- src tests    # must return empty
  ```

  Run it, then fix whatever it prints. Both patterns are needed: `install_script_path`
  names the retired field and is invisible to an `install\.py` grep. Every previous
  attempt to enumerate these references came up short.

  Known references, as examples rather than the checklist:
  - `workspace.py` — the resolver body (`:483-512`) and three `create_startup_script`
    docstring lines. `:554` is the `skip_github_install` Args entry ("thread
    ``--skip-overrides`` into the install.py argv at run time"); `:550` and `:561` name
    the resolver's job and its `FileNotFoundError`.
  - `session_setup.py` — the `build_install_argv` docstring. `:109` and `:119` name a
    script path and the coordinator Python; rewrite both to name `mcp-coder install` and
    the coordinator's `mcp-coder` executable. `:115` documents "the session spec carrying
    the resolved ``install_script_path``" — retarget it at the fields the argv now uses.
  - `templates.py:5`, `:28`; `types.py:245` (field plus its trailing comment).
  - the test modules — see TESTS below.

## ALGORITHM

```
build_install_argv(spec, cwd):
    argv = [str(_mcp_coder_exe(spec)), "install", str(cwd),
            "--source", "local", "--local-path", str(cwd),
            "--use-sync", "--refresh"]
    if spec.skip_github_install: argv.append("--skip-overrides")
    return argv

read_session_spec(folder):
    data  = json.loads(<folder>/.vscodeclaude_session.json)
    names = {f.name for f in dataclasses.fields(SessionSpec)}
    return SessionSpec(**{k: v for k, v in data.items() if k in names})
```

## DATA

Emitted argv (Windows coordinator at `C:\coord`, session at `C:\work\s1`):

```
["C:\\coord\\.venv\\Scripts\\mcp-coder.exe", "install", "C:\\work\\s1",
 "--source", "local", "--local-path", "C:\\work\\s1",
 "--use-sync", "--refresh"]                       # + "--skip-overrides" when set
```

`SessionSpec` is still frozen, still 12 fields minus one, still gitignored and
regenerated on every restart — no version field, no migration shim.

## TESTS (write first — they fail until the source edits land)

- `test_session_setup_env.py`: delete the `install_script_path=` fixture line (`:38`);
  rewrite `:130` to assert `argv[0]` ends with `mcp-coder(.exe)` and `argv[1] == "install"`;
  delete the `--extras dev` assertion (`:134`). `:135-136` (`--use-sync` / `--refresh`)
  and the calls at `:142-146` are unchanged — the signature did not change.
- `test_session_setup_flow.py`: drop the fixture line (`:44`); `_is_install` (`:99`)
  becomes `"install" in argv`.
- `test_session_spec.py`: drop the two fixture lines (`:25`, `:67`); **add** a case that
  a spec JSON still carrying `install_script_path` loads without raising.
- `test_startup_script_mcp_coder_path.py`: keep `test_spec_records_explicit_install_path`
  minus its `:37-38` fixture lines (its install-dir ≠ session-folder assertion is still
  live); delete the second test entirely, plus the module docstring's `install.py`
  sentence (`:8`).
- `test_workspace_startup_script_github.py`: **the assertions do not change.** All six
  `build_install_argv` call sites (`:54`, `:81`, `:114`, `:144`, `:179`, `:205`) assert only
  `"--skip-overrides" in` / `not in` the argv — none names the script path or `--extras`, so
  this refactor leaves them valid. Only the two docstrings need editing: the module docstring
  (`:4`, "live inside ``tools/install.py`` … covered by that script's own tests") and the
  class docstring at `:151` ("reaches the ``install.py`` argv"). Point both at
  `mcp_coder.install` and `tests/install/`.

Exit criterion before committing:

```
git grep -n "install\.py\|install_script_path" -- src tests    # must return empty
```

Steps 5 and 6 both rely on that being true from here on.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`.
>
> Implement Step 3 only, as one commit. TDD: update the five vscodeclaude test modules
> to the new expectations first (they will fail), then make the source edits —
> `build_install_argv`, `_coordinator_python` deletion, `SessionSpec.install_script_path`
> removal, `read_session_spec` unknown-key filter, `_resolve_install_script` deletion,
> docstrings.
>
> The docstrings are not optional and not only `templates.py`: `build_install_argv`'s own
> docstring and two docstrings in `test_workspace_startup_script_github.py` still name
> `install.py` / `install_script_path`. Step 6 is doc-only, so nothing later can fix them.
> Do not work from the reference lists in this step — they are examples and have been
> incomplete every time. Work from the grep:
> `git grep -n "install\.py\|install_script_path" -- src tests` must come back empty.
>
> `test_workspace_startup_script_github.py`'s six `build_install_argv` assertions need no
> change — they only check `--skip-overrides`. Edit its docstrings, not its assertions.
>
> The resolver deletion and the test trim are one atomic change: `create_startup_script`
> still calls the resolver, so trimming the tests alone leaves them failing.
>
> Do not delete `tools/install.py` (Step 5) and do not touch `session_launch.py`
> (Step 4).
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check`, the fast pytest
> selection, plus `run_tach_check`, `run_lint_imports_check` and `run_vulture_check` —
> the last catches anything left dangling by the two deleted functions. Commit once, green.
