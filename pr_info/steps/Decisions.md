# Plan Review Decisions

## Decision 1: Textual as optional dependency
- `textual` is an optional dependency under a `tui` extras group, not a main dependency
- `textual-dev` goes in the same `tui` group
- `tui` is added to the dev extras so local development still works
- `pytest-textual-snapshot` is added in step 9 (snapshot tests) where it is actually used
- `execute_icoder()` must use lazy import of textual with a clear error if not installed

## Decision 2: EventLog as context manager
- `EventLog` supports `__enter__` / `__exit__` (context manager protocol)
- `__exit__` calls `close()` to flush and close the JSONL file handle
- All usage sites (execute_icoder, conftest fixtures) should use the `with` statement

## Decision 3: RealLLMService delegation test
- Add a test that patches `prompt_llm_stream` and verifies `RealLLMService.stream()` calls it with correct arguments and yields the expected events

## Decision 4: Fix find_latest_session_id reference
- The correct API is two steps: `find_latest_session(provider=provider)` returns a file path, then `extract_session_id(file_path)` returns the session ID string
- There is no `find_latest_session_id()` helper

## Decision 5: Split Step 7 into Steps 7 and 8
- Step 7: UI widgets only (styles.py, output_log.py, input_area.py) + widget unit/integration tests
- Step 8: ICoderApp (app.py) with async bridging + pilot integration tests + updating icoder.py to launch the app
- Old Step 8 (snapshot tests) becomes Step 9
- Total: 9 implementation steps

## Decision 6: Concrete assertions in pilot tests
- Pilot tests must have real assertions, not comment placeholders
- test_quit_command: assert app is no longer running
- test_submit_text: verify OutputLog contains echoed text
- test_clear_command: verify output is empty after clear

## Decision 7: Use EventLog as context manager in execute_icoder
- The algorithm in step 6 uses `with EventLog(...) as event_log:` instead of manual close()
