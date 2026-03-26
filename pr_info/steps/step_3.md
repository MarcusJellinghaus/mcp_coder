# Step 3: Register NOTICE log level and add per-command defaults

**References:** [summary.md](summary.md) — Part 2

## Goal

Add custom NOTICE log level (25), add per-command default log level resolution, update tests.

## WHERE

- `src/mcp_coder/utils/log_utils.py`
- `src/mcp_coder/cli/main.py`
- `tests/utils/test_log_utils.py`
- `tests/cli/test_main.py`

## WHAT

### log_utils.py

- **Add** at module level (near the top, after imports):
  ```python
  NOTICE = 25
  logging.addLevelName(NOTICE, "NOTICE")
  ```
- **Add** convenience method so `logger.notice(msg)` works:
  ```python
  def _notice(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
      if self.isEnabledFor(NOTICE):
          self.log(NOTICE, message, *args, **kwargs)

  logging.Logger.notice = _notice  # type: ignore[attr-defined]
  ```
- **Export** `NOTICE` in the module's public API.

### main.py

- **Change** `--log-level` default from `"INFO"` to `None`:
  ```python
  parser.add_argument("--log-level", ..., default=None, ...)
  ```
- **Add** `_resolve_log_level()` function:
  ```python
  _INFO_COMMANDS = frozenset({"create-plan", "implement", "create-pr", "coordinator"})

  def _resolve_log_level(args: argparse.Namespace) -> str:
      if args.log_level is not None:
          return args.log_level
      if args.command in _INFO_COMMANDS:
          return "INFO"
      if args.command == "vscodeclaude" and getattr(args, "vscodeclaude_subcommand", None) == "launch":
          return "INFO"
      return "NOTICE"
  ```
- **Update** `main()`: replace `setup_logging(args.log_level)` with:
  ```python
  log_level = _resolve_log_level(args)
  setup_logging(log_level)
  ```

### log_utils.py — setup_logging()

- **Add** NOTICE level handling in `setup_logging()`. The function already accepts a string and does `getattr(logging, log_level.upper())`. Since NOTICE is registered via `addLevelName`, we need to also handle it in the numeric lookup. Add a fallback:
  ```python
  numeric_level = getattr(logging, log_level.upper(), None)
  if not isinstance(numeric_level, int):
      numeric_level = logging.getLevelName(log_level.upper())
      if not isinstance(numeric_level, int):
          raise ValueError(f"Invalid log level: {log_level}")
  ```

## HOW

`NOTICE` is registered once at module import time. The `_resolve_log_level` function is a pure function that maps command names to default levels. `setup_logging` already handles any valid numeric level.

## ALGORITHM

```
# _resolve_log_level(args):
if user explicitly set --log-level:     return that level
if command is a workflow command:        return "INFO"
if command is vscodeclaude launch:      return "INFO"
otherwise:                              return "NOTICE"
```

## DATA

- `NOTICE = 25` (int constant)
- `_INFO_COMMANDS` (frozenset of command name strings)

## Tests

### test_log_utils.py

- Add `TestNoticeLevel` class:
  - `test_notice_level_is_registered`: `assert logging.getLevelName(25) == "NOTICE"`
  - `test_notice_level_value`: `assert NOTICE == 25`
  - `test_notice_between_info_and_warning`: `assert logging.INFO < NOTICE < logging.WARNING`
  - `test_setup_logging_accepts_notice`: `setup_logging("NOTICE")` does not raise
  - `test_logger_notice_method_exists`: verify `hasattr(logging.getLogger(), "notice")`

### test_main.py

- Add `TestLogLevelResolution` class:
  - `test_log_level_default_is_none`: parser default is None
  - `test_resolve_log_level_workflow_commands_default_info`: test create-plan, implement, create-pr, coordinator
  - `test_resolve_log_level_vscodeclaude_launch_default_info`: test vscodeclaude with launch subcommand
  - `test_resolve_log_level_other_commands_default_notice`: test help, verify, check, gh-tool, etc.
  - `test_resolve_log_level_explicit_overrides_default`: `--log-level DEBUG` always wins
- Update existing tests affected by `None` default:
  - `test_parser_log_level_default`: change assertion from `args.log_level == "INFO"` to `args.log_level is None`
  - `test_coordinator_run_with_repo_argument`: change assertion from `call_args.log_level == "INFO"` to `call_args.log_level is None`
  - `test_coordinator_run_with_all_argument`: change assertion from `call_args.log_level == "INFO"` to `call_args.log_level is None`

## LLM Prompt

```
Please read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Implement step 3: Register NOTICE log level and add per-command defaults.

Key changes:
1. log_utils.py: Register NOTICE=25, add Logger.notice() method, handle NOTICE in setup_logging()
2. main.py: Change --log-level default to None, add _resolve_log_level() function, use it in main()
3. test_log_utils.py: Add TestNoticeLevel class
4. test_main.py: Add TestLogLevelResolution class, update existing tests for None default

Run all quality checks after changes. One commit for this step.
```
