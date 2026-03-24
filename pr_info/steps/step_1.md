# Step 1: Create `init` command module with tests, wire into CLI, and add to help text

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement Step 1 from `pr_info/steps/step_1.md`.
> Follow TDD: write tests first, then implement, then verify all checks pass.
> Use MCP tools for all file operations and code quality checks per CLAUDE.md.

## Overview

Create the `execute_init` command handler, register it in the CLI, add it to help text, and add tests. This is the entire deliverable of #554.

## WHERE: Files to create

### `tests/cli/commands/test_init.py`

- **WHAT**: 4 test cases in `TestInitCommand` class
- **HOW**: Use `pytest`, `unittest.mock.patch`, `tmp_path` fixture
- **DATA**: Each test asserts exit code (int) and printed output (via `capsys`)

**Test cases:**

1. `test_init_creates_config_success` — mock `mcp_coder.cli.commands.init.create_default_config` returning `True`, mock `mcp_coder.cli.commands.init.get_config_file_path` returning a path → asserts exit 0, output contains "Created default config at:", "Please update it", "Next steps:", "mcp-coder verify", "mcp-coder define-labels"
2. `test_init_config_already_exists` — mock `mcp_coder.cli.commands.init.create_default_config` returning `False` → asserts exit 0, output contains "Config already exists:"
3. `test_init_write_failure` — mock `mcp_coder.cli.commands.init.create_default_config` raising `OSError("Permission denied")`, mock `mcp_coder.cli.commands.init.get_config_file_path` → asserts exit 1, output contains "Error: Failed to write config to", "Permission denied"
4. `test_init_template_content_valid_toml_with_sections` — use `tmp_path`, monkeypatch `get_config_file_path` to return path in `tmp_path`, call real `create_default_config()`, then parse file with `tomllib` → asserts valid TOML, contains keys `github`, `jenkins`, `coordinator`

### `src/mcp_coder/cli/commands/init.py`

- **WHAT**: `execute_init(args: argparse.Namespace) -> int`
- **HOW**: Imports `get_config_file_path`, `create_default_config` from `...utils.user_config`
- **ALGORITHM**:
  ```
  path = get_config_file_path()
  try:
      created = create_default_config()
  except OSError as e:
      print(f"Error: Failed to write config to {path}: {e}")
      return 1
  if created:
      print(f"Created default config at: {path}")
      print("Please update it with your actual credentials and settings.")
      print("\nNext steps:")
      print("  mcp-coder verify          Check your setup")
      print("  mcp-coder define-labels   Sync workflow labels to your GitHub repo")
  else:
      print(f"Config already exists: {path}")
  return 0
  ```
- **DATA**: Returns `int` (0 success, 1 write failure)

## WHERE: Files to modify

### `src/mcp_coder/cli/main.py`

- **WHAT**: Register `init` command and route to handler
- **HOW**:
  1. Add import: `from .commands.init import execute_init`
  2. In `create_parser()`, after the `help` parser line, add:
     ```python
     subparsers.add_parser("init", help="Create default configuration file")
     ```
  3. In `main()` routing block, after `args.command == "help"` branch, add:
     ```python
     elif args.command == "init":
         return execute_init(args)
     ```

### `src/mcp_coder/cli/commands/__init__.py`

- **WHAT**: Export `execute_init`
- **HOW**: Add `from .init import execute_init` to imports and `"execute_init"` to `__all__`

### `src/mcp_coder/cli/commands/help.py`

- **WHAT**: Add `init` line to `get_help_text()` COMMANDS section
- **HOW**: In the COMMANDS section string, add after the `verify` line:
  ```
      init                    Create default configuration file
  ```

### `tests/cli/commands/test_help.py` (update existing test)

- **WHAT**: Add assertion that help text contains `init` command entry
- **HOW**: Find the existing test that checks help text content, add assertion that the output contains `"init"` and a description like `"Create default configuration file"` or `"Create default config"`

## Commit

One commit: `feat: add 'mcp-coder init' CLI command (#554)`
