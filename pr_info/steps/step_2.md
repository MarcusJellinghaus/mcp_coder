# Step 2: Coordinator Template Watchdog Lines

**Commit message:** `feat(coordinator): add watchdog set-status to coordinator templates for silent-death recovery (#713)`

> **LLM Prompt:** Read `pr_info/steps/summary.md` for context. Implement Step 2: update all six coordinator Jenkins command templates with RC capture, a watchdog `set-status` line (using `--from-status`), and explicit exit with the captured RC. Add an inline comment block explaining the recovery matrix. Write tests first (TDD), then update the templates. Run all five code quality checks (pylint, pytest, mypy, lint-imports, vulture) after changes.

## WHERE

- `tests/cli/commands/coordinator/test_commands.py` — new test class `TestTemplateWatchdogLines`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — update 6 templates + add comment block

## WHAT

### Template changes

Each of the 6 templates gets the same structural change:

| Template | Rescue from | Rescue to | Needs `--issue` |
|---|---|---|---|
| `CREATE_PLAN_COMMAND_TEMPLATE` | `status-03:planning` | `status-03f:planning-failed` | Yes: `--issue {issue_number}` |
| `CREATE_PLAN_COMMAND_WINDOWS` | `status-03:planning` | `status-03f:planning-failed` | Yes: `--issue {issue_number}` |
| `IMPLEMENT_COMMAND_TEMPLATE` | `status-06:implementing` | `status-06f:implementing-failed` | No (auto-detect from branch) |
| `IMPLEMENT_COMMAND_WINDOWS` | `status-06:implementing` | `status-06f:implementing-failed` | No |
| `CREATE_PR_COMMAND_TEMPLATE` | `status-09:pr-creating` | `status-09f:pr-creating-failed` | No |
| `CREATE_PR_COMMAND_WINDOWS` | `status-09:pr-creating` | `status-09f:pr-creating-failed` | No |

### Linux template pattern (e.g. `IMPLEMENT_COMMAND_TEMPLATE`)

```bash
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?

mcp-coder gh-tool set-status status-06f:implementing-failed \
    --from-status status-06:implementing --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
```

### Windows template pattern (e.g. `IMPLEMENT_COMMAND_WINDOWS`)

```batch
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
set RC=%ERRORLEVEL%

mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --force

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs

exit /b %RC%
```

### `create-plan` special case

Because `create-plan` runs on `main` (not a feature branch), the watchdog line must pass `--issue {issue_number}`:

```bash
mcp-coder gh-tool set-status status-03f:planning-failed \
    --from-status status-03:planning --issue {issue_number} --force || true
```

### Inline comment block

Add once near the Linux template group. Windows group references it:

```python
# Silent-death recovery watchdog (see issue #713)
#
# After the main mcp-coder command, each template captures $RC / %ERRORLEVEL%
# and runs a conditional set-status that only fires if the issue is still at
# the in-progress label (--from-status). This rescues issues stuck by a
# silent process death where Python cleanup never ran.
#
# Recovery matrix:
#   Clean success        → label already past in-progress → watchdog no-ops
#   Graceful failure     → Python set a specific failure label → watchdog no-ops
#   Silent death (#710)  → issue still at in-progress label → watchdog rescues
#   Hard kill of shell   → watchdog never runs → not recoverable (out of scope)
#
# The watchdog always runs (not gated on exit code). The original exit code
# is re-emitted via exit $RC / exit /b %RC% so Jenkins sees the real outcome.
```

## HOW

- Templates are plain string constants — edit them directly
- `create-plan` templates already have `{issue_number}` as a placeholder, so the watchdog line can use it
- `implement` and `create-pr` templates already `git checkout {branch_name}`, so branch-name auto-detection works
- No Python code changes beyond the string constants

## ALGORITHM

No runtime algorithm — this is a template content change. The "algorithm" is the shell script pattern:

```
1. Run main mcp-coder command
2. Capture exit code (RC=$? / set RC=%ERRORLEVEL%)
3. Run watchdog set-status with --from-status (unconditional, || true on Linux)
4. Run archive commands (ls/dir)
5. Exit with captured RC
```

## DATA

No new data structures. Templates are `str` constants, same as before.

## TESTS (`tests/cli/commands/coordinator/test_commands.py`)

New class `TestTemplateWatchdogLines`:

1. **`test_linux_templates_capture_exit_code`** — all 3 Linux templates contain `RC=$?`
2. **`test_windows_templates_capture_exit_code`** — all 3 Windows templates contain `set RC=%ERRORLEVEL%`
3. **`test_linux_templates_have_watchdog_line`** — each Linux template contains the correct `set-status ... --from-status ... --force || true`
4. **`test_windows_templates_have_watchdog_line`** — each Windows template contains the correct `set-status ... --from-status ... --force`
5. **`test_linux_templates_exit_with_captured_rc`** — all 3 Linux templates end with `exit $RC`
6. **`test_windows_templates_exit_with_captured_rc`** — all 3 Windows templates end with `exit /b %RC%`
7. **`test_create_plan_templates_pass_issue_number`** — both create-plan templates include `--issue {issue_number}` in the watchdog line
8. **`test_implement_and_pr_templates_no_issue_flag`** — implement/create-pr watchdog lines do NOT contain `--issue`
9. **`test_templates_placeholders_still_resolve`** — parameterized per template; each template is formatted with ONLY the kwargs it actually declares, and the call must succeed without `KeyError`. Matrix:

    | Template | Placeholders used |
    |---|---|
    | `CREATE_PLAN_COMMAND_TEMPLATE` | `log_level`, `issue_number` |
    | `CREATE_PLAN_COMMAND_WINDOWS` | `log_level`, `issue_number` |
    | `IMPLEMENT_COMMAND_TEMPLATE` | `log_level`, `branch_name` |
    | `IMPLEMENT_COMMAND_WINDOWS` | `log_level`, `branch_name` |
    | `CREATE_PR_COMMAND_TEMPLATE` | `log_level`, `branch_name` |
    | `CREATE_PR_COMMAND_WINDOWS` | `log_level`, `branch_name` |

    Note: `create_plan` templates do NOT use `{branch_name}`; `implement` and `create_pr` templates do NOT use `{issue_number}`. Passing an extra kwarg that the template does not reference is fine with `str.format`, but the test should be strict and only pass the kwargs each template declares so a future stray placeholder is caught.

10. **`test_recovery_matrix_comment_present`** — read the `command_templates.py` source (module `__file__` / `inspect.getsource`) and assert the inline comment block near the Linux template group contains the key phrases `"Recovery matrix"`, `"Silent death"`, and `"Hard kill"` (or clearly equivalent wording). Acceptance criteria requires the inline comment block be present in the source.
