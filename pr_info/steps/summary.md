# Summary: CI warning for PRs that change sensitive files (#1431)

## Goal

A non-blocking, PR-only CI job `check-sensitive-files` warns when a PR changes:

1. a file whose effective level is `read-only` under the **base branch's** `.mcp-file-access`
   (reason `read-only rule <pattern>`);
2. `.mcp-file-access` itself (reason `rules file`);
3. a file on the script's watch list (reason `watch list <pattern>`):
   `/pyproject.toml`, `/.claude/agents/`, `/.claude/skills/`, `/.github/workflows/`,
   `/tools/check_sensitive_files.py`.

A file can have several reasons; all are listed. The check is advisory: it always exits 0
after a completed check, and non-zero only on its own errors (e.g. git fails).

## Architectural / design changes

- **New standalone tool script** `tools/check_sensitive_files.py`. Like the other `tools/`
  scripts it does not import `mcp_coder`; it imports only the stdlib and
  `mcp_workspace.file_tools.access_rules` (`AccessRules`, `READ_ONLY`, `load_access_rules`).
  An upstream API break shows up as the CI job failing on import.
- **Matching reuses the MCP server's matcher.** `load_access_rules(dir)` reads
  `<dir>/.mcp-file-access`, so every rule set (original base rules, lower-cased copy, watch
  list) is written as bytes into its own `tempfile.TemporaryDirectory` by one helper `_load`.
- **Two loads of the base rules.** The raw bytes from `git show <base>:.mcp-file-access`
  are loaded first, so problems (non-UTF-8, `Read-Only` keyword, …) are reported exactly as
  the MCP server would. Only if valid: decode `utf-8-sig`, lower-case, encode UTF-8, load
  again for matching. Paths are lower-cased too → the stricter Windows behaviour on Linux CI,
  without the private `_fold`. Problems or `re.error` / `ValueError` from either load → the
  rules file is invalid: one `::warning::`, read-only matching skipped. Verified by probe:
  lower-casing `/[Z-a]x` raises `re.error` (not a `ValueError`) on linux; on win32 the
  original load already raises (mcp-workspace#405).
- **Original spelling in output.** The reported pattern comes from the original load:
  `{rule.line: rule.pattern}`, looked up with the matching (lower-cased) rule's `.line`.
- **Git access.** One replaceable runner `run_git(args) -> GitResult` (a dataclass in the
  script, not `CompletedProcess`), always `cwd=REPO_ROOT`. `REPO_ROOT` is
  `Path(__file__).resolve().parents[1]` (as in `tools/read_github_deps.py`), so output does
  not depend on the current directory or `diff.relative`. A helper `_git(*args) -> bytes`
  raises `SystemExit(<message>)` on any non-zero exit → exit code 1, message on stderr. No
  custom exception class.
- **Rules-file existence** via `git ls-tree -z <base> -- .mcp-file-access`: empty output =
  no rules file (info line, rules part is a no-op); mode `100644`/`100755` = regular file;
  any other mode = invalid.
- **Changed files**: `git merge-base <base> <head>`, then
  `git diff --name-only --no-renames -z <merge-base> <head>`, decoded with
  `errors="replace"`. Rules always come from `<base>` itself, never the head or merge-base.
- **Output**: one `::warning file=<path>::<reasons>` per flagged file plus a Markdown table
  of all flagged files, appended to `$GITHUB_STEP_SUMMARY` when set, else printed. Nothing
  flagged → one line `No sensitive files changed.` All path text reaches stdout only through
  escaped annotations or the escaped table.
- **Loader log noise**: the loader's logger is disabled in the script's `__main__` block
  only, so tests don't change global logging state.
- **New CI job** in `.github/workflows/ci.yml`, right after `check-forbidden-folders`:
  job-level `if: github.event_name == 'pull_request'`, `fetch-depth: 2`, same pinned
  uv/Python setup, installs only the `mcp-workspace` spec from
  `tools/read_github_deps.py --specs`, runs `--base HEAD^1 --head HEAD`. Not required.

## Files

| Action | Path |
|---|---|
| Create | `tools/check_sensitive_files.py` |
| Create | `tests/tools/test_check_sensitive_files.py` |
| Modify | `.github/workflows/ci.yml` |
| Modify | `docs/repository-setup/quality-and-security-checks.md` |
| Modify | `docs/repository-setup/claude-permissions/design-concept.md` |

No changes under `src/`, no new dependencies (`mcp-workspace` is already a dependency).

## Steps

1. [step_1.md](step_1.md) — script + unit tests (TDD).
2. [step_2.md](step_2.md) — `check-sensitive-files` job in `ci.yml`.
3. [step_3.md](step_3.md) — docs.

## Known limits (documented in step 3, not implemented)

- A PR can suppress the check by editing `ci.yml` or the script (`pull_request` runs the
  head's workflow). Advisory signal, not a security control.
- Canonical spellings (`.mcp.json.`, `:stream`) are not matched.
- Dependabot action bumps under `.github/workflows/` warn by design;
  `.github/requirements/` is not watched.
