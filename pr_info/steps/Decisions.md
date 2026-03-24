# Decisions for Issue #565

1. **Rename `CATEGORIES` to `COMMAND_CATEGORIES`** — more descriptive constant name; avoids ambiguity.

2. **Remove `help` from command list** — the issue output omits `help` from the TOOLS category.

3. **Add `coordinator vscodeclaude status`** — missing subcommand added to COORDINATION category.

4. **Fix `init` description** — changed from "Initialize project configuration" to "Create default configuration file" to match actual behavior.

5. **Category headers are flush-left** — no leading spaces on category name lines; the issue's expected output shows them unindented.

6. **Make header line explicit** — use literal `"mcp-coder - AI-powered software development automation toolkit"` instead of an abstract "header" reference.

7. **Add URL footer to detailed help** — `get_help_text()` appends `"For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder"`.

8. **Test name follows constant name** — `test_categories_contains_all_commands` renamed to `test_command_categories_contains_all_commands`.
