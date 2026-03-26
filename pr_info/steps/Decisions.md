# Decisions

## Step 5: coordinator/commands.py has a hardcoded config reference

`src/mcp_coder/cli/commands/coordinator/commands.py` (line ~491) contains a hardcoded `"Please configure [coordinator.vscodeclaude] section."` string that must be updated to `"[vscodeclaude]"` as part of the config key migration.

## Step 2: args.log_level assignment is dry-run only

The `args.log_level = args.coordinator_log_level` assignment only applies in the dry-run branch. The normal run branch continues to use the global `args.log_level` from the top-level `--log-level` flag, matching current behavior.
