# Step 3 — Document the `ForegroundLockTimeout` mitigation

**Goal:** give users the cause-agnostic OS-level backstop for focus stealing, since the
symptom is intermittent and the code fix cannot be confirmed by observation.

**Context:** read [summary.md](./summary.md) first.

---

## WHERE

| File | Role |
|------|------|
| `docs/coordinator-vscodeclaude.md` | `## Troubleshooting` section (starts ~line 153) |

Insert a new subsection after `### VS Code not launching` (~line 186) and before
`### Trust prompts for each folder` (~line 188). Docs only — no code, no tests.

## WHAT

Add roughly:

```markdown
### Keyboard focus jumps between session windows (Windows)

With several session windows open, another window can occasionally steal focus while you
are typing. The generated session files no longer raise windows in the background — only
launching or restarting a session does, which is intended.

As a cause-agnostic backstop, tell Windows to flash the taskbar instead of switching focus
when a background app asks for the foreground:

1. Open `regedit` and go to `HKEY_CURRENT_USER\Control Panel\Desktop`.
2. Set `ForegroundLockTimeout` (DWORD) to a non-zero value — e.g. `30000` (decimal),
   i.e. 30 seconds.
3. Reboot; the setting is read at logon.

A value of `0` lets any application take the foreground immediately.
```

Optionally note in the same subsection that windows opened before the fix keep their stale
`tasks.json` until they are closed and restarted (sessions self-heal — there is no
migration).

## HOW (integration points)

- Follows the style of the surrounding subsections: `###` heading, short prose, numbered or
  bulleted steps, fenced blocks where useful.
- No entry needed in `### Generated Files` — that table already describes
  `.vscode/tasks.json` as "Auto-run task on folder open" (singular), which stays accurate.
- No runtime registry check anywhere in the code — documentation only, by decision.

## ALGORITHM

None — documentation change.

## DATA

None.

## Definition of done

- `docs/coordinator-vscodeclaude.md` Troubleshooting contains the `ForegroundLockTimeout`
  mitigation with the registry path, a concrete non-zero value, and the reboot requirement.
- Markdown renders correctly (heading level `###`, consistent with neighbours).
- pylint, pytest (unit subset), mypy still pass (unchanged code, run them anyway per
  `CLAUDE.md`); `./tools/format_all.sh` run before commit.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`, then implement step 3 only.
>
> Use MCP tools exclusively (`mcp__workspace__*` for files,
> `mcp__tools-py__run_pylint_check` / `run_pytest_check` / `run_mypy_check` for checks) as
> required by `CLAUDE.md`.
>
> Add a `### Keyboard focus jumps between session windows (Windows)` subsection to the
> Troubleshooting section of `docs/coordinator-vscodeclaude.md`, between
> `### VS Code not launching` and `### Trust prompts for each folder`. Document setting
> `HKEY_CURRENT_USER\Control Panel\Desktop\ForegroundLockTimeout` to a non-zero value such
> as `30000` and rebooting, so Windows flashes the taskbar instead of switching focus. Match
> the tone and formatting of the neighbouring subsections. No code changes and no runtime
> registry check.
>
> Then run pylint, pytest (`extra_args=["-n", "auto", "-m", "not git_integration and not
> claude_cli_integration and not claude_api_integration and not formatter_integration and
> not github_integration and not langchain_integration"]`) and mypy, run
> `./tools/format_all.sh`, and make exactly one commit.
