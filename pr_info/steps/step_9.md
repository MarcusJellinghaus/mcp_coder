# Step 9 — Docs: `docs/configuration/command-toolkit.md`

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 13.

## LLM prompt

> Implement Step 9 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_9.md`: write `docs/configuration/command-toolkit.md` and
> link it from `docs/README.md`. Check every key and default against
> `src/mcp_coder/toolkits/command/config.py`. Run the code-quality checks from
> CLAUDE.md and make exactly one commit.

## WHERE

- Create `docs/configuration/command-toolkit.md`.
- `docs/README.md` — one row/bullet next to the Configuration Guide link.

## WHAT (page outline)

1. **What it is** — runs configured commands for `format` / `check` / `test`
   on any stack, no shell; selected with `toolkit = "command"`.
2. **Config reference** — the defaults table (`llm_permissions`, `parser`,
   `exit_codes`, `timeout`) and the step fields (`argv`, `name`, `parser`,
   `exit_codes`, `timeout`, `report`), with the rules from Scope 3 (action keys
   only `format`/`check`/`test`, free depth names, step `exit_codes` replaces
   the default, `report` only with `junit`, `argv[0]` with a path separator is
   relative to the project).
3. **Example (npm)** — example 2 of #1192, corrected:
   - in `mcp-coder.toml` (`[tool.mcp-coder.toolkit]` tables, same names);
   - no `sarif` (the `lint` step uses the default parser);
   - `junit` steps carry `report = "reports/junit.xml"` (or similar);
   - a variant turning formatting off with `[tool.mcp-coder.toolkit.bindings] commit = []`;
   - `test.unattended` mentioned for automated rebase.
4. **LLM access** —
   - grants are exact `Bash(<argv joined by spaces>)`; extra arguments, flags or
     changed spacing are denied; `llm_permissions = "none"` gives no grants;
   - only Claude sessions that re-run checks get grants (implement, finalisation,
     CI fix, rebase fix turns); Copilot / Langchain get none (warning logged);
   - Claude Code auto-approves read-only commands once Bash is on;
   - Bash grants in the project's `.claude/settings.local.json` merge in;
   - the LLM's Bash tool has its own timeout (about 2 min default, 10 min max),
     so longer steps can't be re-run by the LLM.
5. **Errors** — config problems: `mcp-coder verify` and the format pre-flight
   report global and `format` problems; `check` / `test` step errors surface at
   run time (the depth returns `error`).
6. **Windows** — `.cmd` found via `shutil.which` (`npm` → `npm.cmd`); `.sh`
   can't run without a shell; cmd.exe re-parses arguments of `.cmd` files;
   backslash paths (`C:\…`) are never shell-safe, so such steps get no grant;
   forward-slash paths are fine.

## DATA

Markdown only. Note at the top: "Will be folded into `toolkits.md` (#1200)."

## Tests

None (docs only). Run `check_file_size` and the standard checks.
