# Decisions

## D1: Implementation order — Part 3 → Part 2 → Part 1

Part 3 (set-status move) has no dependencies. Part 2 (NOTICE level) is independent of Part 1 but Part 1 (unified help) benefits from both being done first (correct command listing, no log noise in help).

## D2: `--help` as `store_true` instead of sys.argv inspection

Adding `--help` as a `store_true` argument (with `add_help=False` on root parser) is simpler and more maintainable than inspecting `sys.argv` before parsing. Argparse handles it naturally.

## D3: `--log-level` default as `None` instead of sentinel object

`None` is the natural argparse default for "not provided". No need for a custom sentinel. `_resolve_log_level()` checks `args.log_level is not None` to detect explicit user input.

## D4: `logger.log(NOTICE, ...)` over `logger.notice(...)`

Using `logger.log(NOTICE, msg)` avoids `type: ignore[attr-defined]` comments that would be needed for the dynamically-added `.notice()` method. Both are registered, but the `.log()` form is preferred in production code.

## D5: No separate test file for NOTICE level

NOTICE level tests are added to the existing `test_log_utils.py` and `test_main.py` files rather than creating a new test file. Keeps test organization consistent.

## D6: No deprecation shim for set-status

Per issue requirements — hard removal. `mcp-coder set-status` will produce "unknown command" error.

## D7: Single unified help output (no compact vs detailed distinction)

The issue specifies all three paths produce identical output. We remove the compact/detailed distinction entirely. The output matches the target format in the issue.
