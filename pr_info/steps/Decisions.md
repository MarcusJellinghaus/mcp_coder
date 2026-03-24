# Decisions

1. **Merge Step 2 into Step 1**: Step 2 (add `init` to help text + one test assertion) is trivially small and tightly coupled with Step 1, so they are combined into a single step with one commit.

2. **Explicit mock target paths in tests**: Mock targets must use the import location (`mcp_coder.cli.commands.init.create_default_config` and `mcp_coder.cli.commands.init.get_config_file_path`), not the definition location (`mcp_coder.utils.user_config.*`), because Python mocks must target where the name is looked up.
