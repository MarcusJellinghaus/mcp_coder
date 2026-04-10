# Step 4: Fresh session by default + `--continue-session` flag

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.
> **Depends on:** Steps 1–3 (session reset infrastructure).

## Goal

Change iCoder to start a fresh session by default. Add `--continue-session`, `--continue-session-from`, and `--session-id` flags (matching the `prompt` command) to opt into resuming a previous session.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Modify — add session args to `add_icoder_parser` |
| `src/mcp_coder/cli/commands/icoder.py` | Modify — replace auto-resume with opt-in continuation |
| `tests/cli/test_parsers.py` | Modify — add icoder parser tests |

## WHAT

### `parsers.py` — `add_icoder_parser()`

Add session continuation arguments matching the `prompt` parser pattern (lines 67–86):

```python
# Session continuation options (mutually exclusive with each other)
continue_group = icoder_parser.add_mutually_exclusive_group()
continue_group.add_argument(
    "--continue-session-from",
    type=str,
    metavar="FILE",
    help="Resume conversation from specific stored session file",
)
continue_group.add_argument(
    "--continue-session",
    action="store_true",
    help="Resume from most recent session (auto-discovers latest file)",
)

icoder_parser.add_argument(
    "--session-id",
    type=str,
    metavar="ID",
    help="Direct session ID for continuation (overrides file-based options)",
)
```

### `icoder.py` — `execute_icoder()`

Replace current auto-resume block (lines 68–70):

```python
# Auto-resume: find latest session
session_file = find_latest_session(provider=provider)
session_id = extract_session_id(session_file) if session_file else None
```

With opt-in continuation logic matching `prompt.py` (lines 79–123):

```python
# Handle continuation from previous session if requested
# Priority: --session-id > --continue-session-from > --continue-session
resume_session_id = getattr(args, "session_id", None)
continue_file_path = None

if not resume_session_id:
    if getattr(args, "continue_session_from", None):
        continue_file_path = args.continue_session_from
    elif getattr(args, "continue_session", False):
        continue_file_path = find_latest_session(provider=provider)
        if continue_file_path is None:
            logger.log(OUTPUT, "No previous session found, starting new conversation")

    if continue_file_path:
        if provider == "langchain":
            resume_session_id = extract_langchain_session_id(continue_file_path)
        else:
            extracted = extract_session_id(continue_file_path)
            if extracted:
                resume_session_id = extracted
        if resume_session_id:
            logger.log(OUTPUT, "Resuming session: %s...", resume_session_id[:16])
        else:
            logger.log(
                OUTPUT, "Warning: No session_id found in stored response, starting new conversation"
            )
else:
    if getattr(args, "continue_session_from", None) or getattr(
        args, "continue_session", False
    ):
        logger.log(OUTPUT, "Using explicit session ID (ignoring file-based continuation)")

session_id = resume_session_id
```

Update import to add `extract_langchain_session_id`:

```python
from ...llm.storage import extract_langchain_session_id, extract_session_id, find_latest_session
```

## HOW

- Parser changes: copy the `prompt` parser's session group pattern.
- Command changes: replace 3-line auto-resume with the prompt command's opt-in pattern.
- The `session_id` variable is already used downstream (line 86), so the replacement is drop-in.

## Tests (TDD — write first)

### `test_parsers.py` — add tests for icoder parser:

1. **`test_icoder_parser_continue_session_flag`** — Parse `icoder --continue-session`, assert `args.continue_session is True`.
2. **`test_icoder_parser_continue_session_from`** — Parse `icoder --continue-session-from /path/to/file`, assert `args.continue_session_from == "/path/to/file"`.
3. **`test_icoder_parser_session_id`** — Parse `icoder --session-id abc123`, assert `args.session_id == "abc123"`.
4. **`test_icoder_parser_default_no_continuation`** — Parse `icoder`, assert `args.continue_session is False` and `args.session_id is None`.
5. **`test_icoder_parser_continue_flags_mutually_exclusive`** — Parse `icoder --continue-session --continue-session-from /path` raises `SystemExit`.

## Commit

```
feat(icoder): fresh session by default, add --continue-session flag (#765)
```

## LLM Prompt

```
Implement Step 4 from pr_info/steps/step_4.md (see pr_info/steps/summary.md for context).

Replace iCoder's auto-resume with opt-in session continuation matching the prompt command pattern.
Add --continue-session, --continue-session-from, --session-id to icoder parser.
Add parser tests in test_parsers.py. Run all code quality checks. Commit when green.
```
