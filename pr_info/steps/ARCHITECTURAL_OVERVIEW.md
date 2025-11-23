# Architectural Overview - Issue #165

## Design Philosophy: KISS (Keep It Simple, Stupid)

This implementation prioritizes simplicity over architectural perfection:

```
                        WHY SIMPLE IS BETTER HERE
                        ══════════════════════════

Complex Approach          Simple Approach (This PR)
────────────────         ───────────────────────
• Move function          • Add logging where it happens
• Refactor callers       • No caller changes
• Change architecture    • Zero architectural changes
• More lines of code     • Minimal additions (~200 LOC)
• Higher risk            • Low risk
• Hard to review         • Easy to review
```

## Current System Context

### Callers of LLM Functions

```
┌─ ask_llm() ────────────┐
│  (interface.py)        │
│                        ├──→ ask_claude_code_cli() ──→ subprocess
│  ask_llm("question")   │
│  returns: str          │
└────────────────────────┘

┌─ prompt_llm() ─────────┐
│  (interface.py)        │
│                        ├──→ ask_claude_code_cli() ──→ subprocess
│  prompt_llm(...)       │    or
│  returns: dict         ├──→ ask_claude_code_api() ──→ SDK
│                        │
└────────────────────────┘

┌─ generate_commit_message_with_llm() ─┐
│  (commit_operations.py)              │
│                                      ├──→ ask_llm() ──→ ask_claude_code_cli()
│  generate_commit_message_with_llm()  │
│  returns: (success, msg, error)      │
└──────────────────────────────────────┘

┌─ check_and_fix_mypy() ─┐
│  (task_processing.py)  │
│                        ├──→ _call_llm_with_comprehensive_capture()
│  calls LLM for fixes   │    (already exists in task_processing.py)
└────────────────────────┘
```

### Provider Boundaries

The two provider entry points are where ALL Claude calls converge:

```
MANY CALLERS              SINGLE POINT PER METHOD          EXECUTION
─────────────             ──────────────────────           ─────────
ask_llm()    ──┐
               ├──→ ask_claude_code_cli() ──→ [ADD LOGGING HERE] ──→ subprocess
prompt_llm() ─┤
               │
_call_llm...()─┤

ask_claude_code_api() ──→ [ADD LOGGING HERE] ──→ SDK API
                         [ADD RESPONSE LOGGING]
```

**Key Insight**: By logging at the provider boundary, ALL callers automatically get comprehensive logging with ZERO changes.

## What Changes and Why

### Module Dependencies (Before)

```
claude_code_cli.py
├── build_cli_command() [existing]
├── parse_cli_json_string() [existing]
├── create_response_dict() [existing]
└── ask_claude_code_cli() [modified - add logging call]
    ├── find_claude executable
    ├── build command
    └── execute subprocess ←── ADD LOGGING HERE

claude_code_api.py
├── _create_claude_client() [existing]
├── ask_claude_code_api_detailed_sync() [existing]
└── ask_claude_code_api() [modified - add logging]
    ├── call detailed function ←── ADD LOGGING HERE
    └── return response dict ←── ADD RESPONSE LOGGING HERE
```

### Module Dependencies (After)

```
claude_code_cli.py
├── build_cli_command() [existing]
├── parse_cli_json_string() [existing]
├── create_response_dict() [existing]
├── _log_llm_request_debug() [NEW - reusable helper]
└── ask_claude_code_cli() [modified - add logging call]

claude_code_api.py
├── _create_claude_client() [existing]
├── ask_claude_code_api_detailed_sync() [existing]
├── _log_api_response_debug() [NEW - response logging]
└── ask_claude_code_api() [modified - add logging calls]
    ├── calls _log_llm_request_debug (imported from CLI module)
    └── calls _log_api_response_debug (local helper)
```

**Cross-module Import**: `claude_code_api.py` imports `_log_llm_request_debug` from `claude_code_cli.py` for consistency.

## Execution Flow

### Before (Current)

```
User code
   │
   ├─→ ask_llm("question")
   │   └─→ ask_claude_code_cli()
   │       └─→ execute_subprocess()  ← No detailed logging
   │           └─→ Process result
   │
   └─→ ask_claude_code_api()
       └─→ ask_claude_code_api_detailed_sync()  ← No logging about call details
           └─→ Process result
```

### After (With Logging)

```
User code
   │
   ├─→ ask_llm("question")
   │   └─→ ask_claude_code_cli()
   │       ├─→ [DEBUG] Claude CLI execution [new]: ← NEW LOGGING
   │       │   Provider: claude
   │       │   Method: cli
   │       │   Command: claude -p "" --output-format json
   │       │   Session: None
   │       │   Prompt: 8 chars - question
   │       │   cwd: /project
   │       │   Timeout: 30s
   │       │   env_vars: {...}
   │       └─→ execute_subprocess()
   │           └─→ Process result
   │
   └─→ ask_claude_code_api()
       ├─→ [DEBUG] Claude API execution [new]: ← NEW LOGGING
       │   Provider: claude
       │   Method: api
       │   Session: None
       │   Prompt: 8 chars - question
       │   cwd: /project
       │   Timeout: 30s
       │   env_vars: {...}
       └─→ ask_claude_code_api_detailed_sync()
           ├─→ Process result
           └─→ [DEBUG] Response: ← NEW LOGGING
               duration_ms: 2801
               cost_usd: 0.058779
               usage: {...}
```

## Function Relationships

### Helper Functions (NEW)

```
_log_llm_request_debug() [claude_code_cli.py]
├── Purpose: Format and log request details
├── Called by: ask_claude_code_cli(), ask_claude_code_api()
├── Parameters: method, provider, session_id, command, prompt, timeout, env_vars, cwd, mcp_config
├── Returns: None (logs to logger.debug)
└── Handles: Both CLI and API parameters

_log_api_response_debug() [claude_code_api.py]
├── Purpose: Format and log response metadata
├── Called by: ask_claude_code_api()
├── Parameters: detailed_response (dict with result_info)
├── Returns: None (logs to logger.debug)
└── Handles: API-specific fields (duration, cost, usage, etc.)
```

### Modified Functions (EXISTING)

```
ask_claude_code_cli() [claude_code_cli.py]
├── Added: Call to _log_llm_request_debug() after building command
├── Location: Before execute_subprocess() call
├── Impact: Logs comprehensive CLI request details
└── No breaking changes to function signature or behavior

ask_claude_code_api() [claude_code_api.py]
├── Added: Call to _log_llm_request_debug() before detailed API call
├── Added: Call to _log_api_response_debug() after response creation
├── Location: Inside try block, before/after detailed call
├── Impact: Logs comprehensive API request and response details
└── No breaking changes to function signature or behavior
```

## Data Flow Through Logging

### Request Logging (Both CLI and API)

```
ask_claude_code_cli() or ask_claude_code_api()
    │
    ├─ Extract all parameters: method, provider, session_id, question, etc.
    │
    ├─ Call _log_llm_request_debug(
    │       method="cli" | "api",
    │       provider="claude",
    │       session_id=session_id,
    │       command=command (CLI only),
    │       prompt=question,
    │       timeout=timeout,
    │       env_vars=env_vars,
    │       cwd=cwd,
    │       mcp_config=mcp_config (CLI only)
    │   )
    │
    └─ _log_llm_request_debug()
        ├─ Determine status: "new" if session_id is None, else "resuming"
        ├─ Format header: f"Claude {method} execution [{status}]:"
        ├─ Format each field with consistent indentation
        ├─ For prompt: show count + first 250 chars + ellipsis if truncated
        ├─ For command: format with first arg on header line, rest indented
        ├─ For env_vars: show complete Python dict representation
        └─ Log each line via logger.debug()
```

### Response Logging (API Only)

```
ask_claude_code_api() after detailed API call
    │
    ├─ Extract response metadata from detailed["result_info"]
    │   └─ Contains: duration_ms, cost_usd, usage, result, num_turns, is_error
    │
    ├─ Call _log_api_response_debug(detailed)
    │
    └─ _log_api_response_debug()
        ├─ Log header: "Response:"
        ├─ For each field in result_info:
        │   └─ Log indented: "duration_ms: 2801"
        └─ All via logger.debug()
```

## Configuration and Levels

### Logging Configuration (Unchanged)

```
src/mcp_coder/utils/log_utils.py
├── Configures logging for entire application
├── Sets up logger for each module
├── Sets default level to INFO
└── Can be overridden with --log-level flag

CLI Flag:
  mcp-coder --log-level DEBUG command ...
  └─ Shows all DEBUG messages including our new logging
```

### Log Output

```
CLI:
  logger = logging.getLogger('mcp_coder.llm.providers.claude.claude_code_cli')
  ├─ logger.debug("Claude CLI execution [new]:")
  ├─ logger.debug("    Provider:  claude")
  ├─ logger.debug("    Method:    cli")
  └─ ... more fields ...

API:
  logger = logging.getLogger('mcp_coder.llm.providers.claude.claude_code_api')
  ├─ logger.debug("Claude API execution [resuming]:")
  ├─ logger.debug("    Provider:  claude")
  ├─ logger.debug("    Method:    api")
  └─ ... more fields ...
```

## Why No Architectural Changes?

### Option A: Centralize (Rejected)
```
Proposed but NOT implemented:
  Move _call_llm_with_comprehensive_capture to interface.py
  ├─ Pros: Single function, centralized
  └─ Cons: Refactoring, caller changes, higher risk

Why rejected:
  - Interface.py is high-level abstraction layer
  - Would add provider-specific logic to interface
  - Requires changing ask_llm(), prompt_llm()
  - Adds complexity without benefit (logging already centralized at provider level)
```

### Option B: Provider Logging (CHOSEN)
```
Implemented:
  Add logging at provider entry points
  ├─ ask_claude_code_cli() logs before execution
  ├─ ask_claude_code_api() logs before and after
  └─ Pros: Minimal changes, low risk, same effect, natural location

Why chosen:
  - Logging at execution boundary is natural
  - All callers benefit automatically
  - No refactoring of other code
  - Simpler to understand and maintain
  - Achieves all requirements with less complexity
```

## Diagram: Complete Call Tree with Logging

```
┌─────────────────────────────────────────────────────────┐
│               User Code / Callers                       │
├─────────────────────────────────────────────────────────┤
│  ask_llm()              prompt_llm()     other calls    │
└──────┬──────────────────┬──────────────────┬────────────┘
       │                  │                  │
       ├──────────┬───────┼──────────┐       │
       │          │       │          │       │
       │          v       v          v       v
       │     ┌─────────────────────────────────────┐
       │     │ ask_claude_code_cli()                │
       │     │ ┌─────────────────────────────────┐ │
       │     │ │ _log_llm_request_debug() ←NEW  │ │
       │     │ │ (logs request details)          │ │
       │     │ └─────────────────────────────────┘ │
       │     │            ↓                        │
       │     │ execute_subprocess()                │
       │     │            ↓                        │
       │     │ return response dict                │
       │     └─────────────────────────────────────┘
       │              ↓
       │         Response to caller
       │
       └──────────┬──────────────────┐
                  │                  │
                  v                  v
    ┌──────────────────────┐  ┌──────────────────────┐
    │ ask_claude_code_api()│  │ (other API methods)  │
    │ ┌────────────────────┤  │                      │
    │ │_log_llm_request_   │  │                      │
    │ │debug() ←NEW        │  │                      │
    │ │(logs request)      │  │                      │
    │ └────────────────────┤  │                      │
    │       ↓              │  │                      │
    │ ask_claude_code_api_ │  │                      │
    │ detailed_sync()      │  │                      │
    │       ↓              │  │                      │
    │ ┌────────────────────┤  │                      │
    │ │_log_api_response_  │  │                      │
    │ │debug() ←NEW        │  │                      │
    │ │(logs response)     │  │                      │
    │ └────────────────────┤  │                      │
    │       ↓              │  │                      │
    │ return response dict │  │                      │
    └──────────────────────┘  └──────────────────────┘
             ↓
         Response to caller
```

## Summary Table

| Aspect | Detail |
|--------|--------|
| **Approach** | Add logging at provider boundary (KISS) |
| **Scope** | Two files, four functions (2 modified, 2 new helpers) |
| **Risk** | Low - logging only, no execution changes |
| **Complexity** | Low - ~200 LOC, straightforward formatting |
| **Benefits** | All callers get enhanced logging with zero changes |
| **Refactoring** | None - no moving, no restructuring |
| **Performance** | Negligible - logging only at DEBUG level |
| **Maintenance** | Easier - logging where execution happens |
| **Testing** | Unit tests for format verification |

---

**Conclusion**: This simplified approach delivers all requirements of issue #165 with minimal code changes and zero architectural complexity.
