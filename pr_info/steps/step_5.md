# Step 5: Unified help output

**References:** [summary.md](summary.md) — Part 1

## Goal

Make `mcp-coder`, `mcp-coder help`, and `mcp-coder --help` all produce the same categorized output with version header and OPTIONS section. No log noise.

## WHERE

- `src/mcp_coder/cli/main.py`
- `src/mcp_coder/cli/commands/help.py`
- `tests/cli/commands/test_help.py`
- `tests/cli/test_main.py`

## WHAT

### main.py — create_parser()

- **Add** `add_help=False` to the root `ArgumentParser()` constructor. This removes the built-in `-h`/`--help` handling from the root parser.
- **Add** `--help` and `-h` as explicit arguments on the root parser:
  ```python
  parser.add_argument(
      "--help", "-h",
      action="store_true",
      default=False,
      dest="help",
      help=argparse.SUPPRESS,
  )
  ```
- Subparsers are NOT modified — they keep their built-in `--help`.

### main.py — main()

- **Merge** all three help paths into one check. After `setup_logging`, before the command router:
  ```python
  if not args.command or args.command == "help" or args.help:
      help_text = get_help_text()
      print(help_text)
      return 0
  ```
- **Remove** `handle_no_command()` function (now inlined).
- **Remove** the `execute_help` import and the `elif args.command == "help":` branch.
- **Remove** `get_compact_help_text` import (function will be deleted from help.py).

### help.py

- **Update** `_render_help()`:
  - Always include version on top: `f"mcp-coder {version}"` (import `__version__` from package).
  - Add an OPTIONS section after the usage line:
    ```
    OPTIONS
      --version                Show version number
      --log-level LEVEL        Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    ```
  - Remove the `include_descriptions` parameter — there's now only one output format.
  - Remove category descriptions (the target output in the issue doesn't include them).
  - Keep the footer: `Run 'mcp-coder <command> --help' for command-specific options.`
  - Remove the GitHub URL footer.
- **Delete** `get_compact_help_text()` function.
- **Delete** `execute_help()` function (no longer called).
- **Rename** `get_help_text()` to call `_render_help()` without parameters.
- **Remove** `Command("help", ...)` from COMMAND_CATEGORIES TOOLS list (help is now implicit).

### Target output format

```
mcp-coder - AI-powered software development automation toolkit
mcp-coder 1.2.3

Usage: mcp-coder <command> [options]

OPTIONS
  --version                Show version number
  --log-level LEVEL        Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

SETUP
  init                     Create default configuration file
  verify                   Verify CLI installation and configuration

BACKGROUND DEVELOPMENT
  create-plan              Generate implementation plan for a GitHub issue
  implement                Execute implementation workflow
  create-pr                Create pull request with AI-generated summary
  coordinator              Monitor and dispatch workflows across repositories

INTERACTIVE DEVELOPMENT
  vscodeclaude launch      Launch VSCode/Claude session for issues
  vscodeclaude status      Show current VSCode/Claude sessions

TOOLS
  prompt                   Execute prompt via Claude API
  commit auto              Auto-generate commit message
  commit clipboard         Use clipboard commit message
  check branch-status      Check branch readiness status
  check file-size          Check file sizes against maximum
  gh-tool set-status       Update GitHub issue workflow status label
  gh-tool define-labels    Sync workflow status labels to GitHub
  gh-tool issue-stats      Display issue statistics
  gh-tool get-base-branch  Detect base branch for feature branch
  git-tool compact-diff    Generate compact diff

Run 'mcp-coder <command> --help' for command-specific options.
```

## HOW

`add_help=False` prevents argparse from intercepting `-h`/`--help`. Instead, `--help` is stored as a boolean. The merged check in `main()` catches all three paths.

## ALGORITHM

```
# main():
args = parser.parse_args()
log_level = _resolve_log_level(args)
setup_logging(log_level)

if no_command or help_command or --help_flag:
    print(get_help_text())
    return 0

# _render_help():
lines = [header, version, "", usage, "", "OPTIONS", option_lines]
for category in COMMAND_CATEGORIES:
    lines += [category.name, command_lines]
lines += [footer]
return "\n".join(lines)
```

## DATA

No new data structures. `COMMAND_CATEGORIES` structure unchanged (just `help` entry removed, and `set-status` already renamed in step 1).

## Tests

### test_help.py

- **Remove** tests for `get_compact_help_text()` and `execute_help()` (functions deleted).
- **Remove** tests for category descriptions (no longer in output).
- **Add** `test_help_text_has_version_header`: version line present.
- **Add** `test_help_text_has_options_section`: OPTIONS section with --version and --log-level.
- **Update** `test_command_categories_contains_all_commands`: remove `"help"` from expected list.
- **Update** alignment tests to work with new format (OPTIONS section has different alignment).
- **Keep** category header and command presence tests (updated for new function names).

### test_main.py

- **Add `help=False` to all mocked Namespace objects** in `TestMain`: `test_main_no_args_calls_handle_no_command`, `test_main_help_command`, `test_main_unknown_command_returns_error`, `test_main_keyboard_interrupt_returns_1`, `test_main_unexpected_exception_returns_2`, `test_main_custom_log_level`, `test_main_error_log_level`. Without this, `args.help` access raises `AttributeError`.
- **Update** `test_handle_no_command_*` tests → now test that `main()` with no command prints help text directly (no `handle_no_command` function).
- **Add** `test_main_help_flag_shows_help`: `mcp-coder --help` shows categorized help (not argparse).
- **Add** `test_main_h_flag_shows_help`: `mcp-coder -h` shows categorized help.
- **Update** `test_main_help_command`: verify it still works.
- **Remove** `test_handle_no_command_logs_info` (the info log is removed).

## LLM Prompt

```
Please read pr_info/steps/summary.md and pr_info/steps/step_5.md.
Implement step 5: Unified help output.

Key changes:
1. main.py: add_help=False on root parser, add --help/-h as store_true, merge all 3 help paths into one check, remove handle_no_command() and execute_help import
2. help.py: Single _render_help() with version header + OPTIONS section, delete get_compact_help_text() and execute_help(), remove "help" from COMMAND_CATEGORIES, remove category descriptions
3. test_help.py: Update for new unified format — version, OPTIONS, no compact/detailed distinction
4. test_main.py: Update for --help flag handling, remove handle_no_command tests

Match the target output format from the issue exactly.
Run all quality checks after changes. One commit for this step.
```
