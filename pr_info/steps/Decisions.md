# Decisions

## Decision 1: Remove test for ignored files behavior
**Topic:** Test `test_execute_set_status_ignored_files_allowed`
**Decision:** Remove this test - the other tests (dirty fails, clean succeeds, force bypasses) provide sufficient coverage without needing to verify the exact parameter passed to `is_working_directory_clean`.

## Decision 2: Use direct attribute access for force flag
**Topic:** `getattr(args, "force", False)` vs `args.force`
**Decision:** Use `args.force` directly - simpler and cleaner since the CLI parser guarantees the attribute exists with a default of `False`.

## Decision 3: Keep generic error handling note
**Topic:** Specificity of error note in slash commands
**Decision:** Keep the generic note "If the command fails, report the error to the user. Do not use `--force` unless explicitly asked." - covers all failure cases and is simpler to maintain.

## Decision 4: No blank line before note in slash commands
**Topic:** Formatting consistency in slash command files
**Decision:** No blank line before the new note - match existing compact formatting style.
