# Implementation Review Log — Run 1

Issue #1004 — Unify Claude blocking/streaming onto one streaming core (blocking = drain+assemble).

Supervisor-driven code review. Each round appends findings, decisions, and changes below.

## Round 1 — 2026-07-03

**Findings** (engineer review + adversarial verification):
- CRITICAL: Blocking path dropped `raw_response["system"]`. On `main`, `create_response_dict_from_stream` set `raw_response["system"] = parsed["system_message"]`; the new `ResponseAssembler.result()` never emits a `system` key. Silently broke two production consumers on the blocking `prompt_llm` path: `icoder/env_setup.py` `_probe_exposed_mcp_tools` (always returned `("connected", 0)`) and `cli/commands/verify.py` "Tools exposed" row (always "unavailable (no init event)" WARN). Masked by a stale mock in `tests/icoder/test_env_setup.py`. Verified real via git diff of merge-base.
- ACCEPT: `raw_response["events"]` duplicated payload — carried both `raw_line` (raw NDJSON) and parsed events, ~2× size, redundant with `stream_file`. New this branch.
- ACCEPT (minor): drain-wrapper `CalledProcessError` discarded the streaming error event's `message` (stderr[:500]) on non-zero exit.
- SKIP: `cmd_label = ["claude","-p"]` placeholder in logging (documented/intentional); function-local `import` of the streaming fn with `# pylint: disable=cyclic-import` (documented cycle workaround).

**Decisions**:
- CRITICAL → accept & fix (side-effect parity, Requirement 4 "must not regress"; same class as the `stream_file` extension the plan already did).
- events duplication → accept & fix (bounded, low-risk de-dup).
- stderr loss → accept & fix (bounded diagnostic fix).
- SKIP items → rejected (intentional/documented, no value in changing).

**Changes**:
- `claude_code_cli_streaming.py`: emit `{"type":"system","data":<init msg>}` for the init message only (gated like `_parse_stream_lines`).
- `llm/types.py`: `ResponseAssembler` captures the system init payload → `raw_response["system"]` (conditional); stops persisting `raw_line` events into the assembled `events` list.
- `claude_code_cli.py`: fold the streaming error event `message` into the raised `CalledProcessError.stderr`.
- `tests/llm/test_types.py`: new tests for system capture, MCP-guard round-trip, raw_line exclusion.
- `tests/icoder/test_env_setup.py`: de-masked — fake `prompt_llm` now builds its response through the real `ResponseAssembler`.
- Verified streaming consumers (prompt formatters, stream_renderer, json-raw, icoder app_core) ignore the new `system` event type gracefully.

**Status**: pylint / mypy clean; pytest fast subset 4133 passed, 2 skipped. Committed (see commit).

## Round 2 — 2026-07-03

**Findings**: Fresh review pass (fresh engineer), with focus on the Round-1 commit `ced2dd0`.
- Fix 1 (system-event gating) verified CORRECT — gate `subtype=="init" or not saw_system_init` is exact parity with `_parse_stream_lines`; captured `system` dict shape matches what `claude_mcp_guard` helpers / `env_setup.py` / `verify.py` consume; init payload not overwritten by later heartbeats.
- Fix 2 (drop `raw_line` from assembled events) verified SAFE — no consumer of `raw_response["events"]` reads `raw_line`; json-raw/app_core/prompt --json read it from the live generator; store_session reads `session_info`, mlflow reads `tool_trace`.
- Fix 3 (`CalledProcessError.stderr`) verified SOUND — folds streaming error `message` (carries stderr[:500]) with old string as fallback; only reached on genuine non-zero exit.
- Full-branch AC coverage re-confirmed (unified core, events+stream_file, inactivity sweep, discriminator, four-site categorization, CI-fix absorb, MCP_UNAVAILABLE category/label, mypy-fix hole fixed).
- No Critical, no Accept-worthy findings. Skip: create-plan/create-pr categorize MCP-unavailable as GENERAL (per-spec — only the four autonomous sites get mcp_unavailable); minor cosmetic redundancy in Fix-3 message text.

**Decisions**: Nothing to change — round produces zero code changes. Loop terminates.

**Changes**: None.

**Status**: pylint / mypy clean; pytest fast subset 4133 passed, 2 skipped. No commit needed.

## Final Status

- **Rounds run**: 2 (Round 1 fixed 3 findings; Round 2 clean, zero changes → loop terminated).
- **Code commits produced**: 1 — `ced2dd0` (restore `raw_response["system"]`; trim `raw_line` from assembled events; preserve error stderr).
- **Quality gates**: pylint clean, mypy clean, pytest fast subset 4133 passed / 2 skipped.
- **Vulture**: no dead code.
- **Import-linter**: 19 contracts kept, 0 broken.
- **Outcome**: Branch is a clean, spec-faithful implementation of #1004. One real regression (dropped `raw_response["system"]`, silently breaking the icoder MCP probe and `verify` "Tools exposed" row) was caught and fixed. No open review items.
