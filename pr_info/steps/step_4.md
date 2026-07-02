# Step 4 — `MCP_UNAVAILABLE` category + `mcp_unavailable` label + shared helper

**Reference:** See [summary.md](./summary.md) (Architectural change 4, Decisions 6 & 9). Foundation
for categorization: add the new failure category/label and the shared exception→reason mapping.
No call sites use them yet (applied in Steps 5–6), so the suite stays green.

## WHERE
- `src/mcp_coder/workflows/implement/constants.py` — add the enum member.
- `src/mcp_coder/config/labels.json` — add the `mcp_unavailable` failure label.
- `src/mcp_coder/workflows/implement/llm_failures.py` — **new** module with the helper + map.
- Tests: `tests/workflows/implement/test_llm_failures.py` (new),
  `tests/config/test_label_config.py` (label validation), `test_constants.py`.

## WHAT
```python
# constants.py — FailureCategory
MCP_UNAVAILABLE = "mcp_unavailable"

# llm_failures.py (new)
def llm_failure_reason(exc: BaseException) -> str | None:
    """Map an LLM exception to a workflow failure reason, else None."""

REASON_TO_CATEGORY: dict[str, FailureCategory]  # {"timeout": LLM_TIMEOUT,
                                                #  "mcp_unavailable": MCP_UNAVAILABLE}
```

## HOW
- `llm_failure_reason` imports `LLMTimeoutError` from `mcp_coder.llm.interface` and
  `McpServersUnavailableError` from `mcp_coder.llm.providers.claude.claude_code_cli` (re-exported
  there). Keep the module import-light to avoid cycles (workflows already depend on `llm`).
- `labels.json`: mirror the existing `llm_timeout` entry — `internal_id: "mcp_unavailable"`,
  `failure: true`, `category: "human_action"`, a distinct `name`/emoji, and a `vscodeclaude` block.
  `FailureCategory` maps 1:1 to label IDs, so the enum value must equal the `internal_id`.
- After adding the `llm_failures.py` `workflows` → `llm.providers.claude` import, run
  `mcp__mcp-tools-py__run_lint_imports_check` to confirm no import-linter contract (e.g.
  `mcp_coder_utils_isolation` / the layer contracts) is tripped.

## ALGORITHM
```
def llm_failure_reason(exc):
    if isinstance(exc, LLMTimeoutError):            return "timeout"
    if isinstance(exc, McpServersUnavailableError): return "mcp_unavailable"
    return None
```

## DATA
- `FailureCategory.MCP_UNAVAILABLE = "mcp_unavailable"`.
- Helper returns `"timeout" | "mcp_unavailable" | None`.
- `REASON_TO_CATEGORY` maps those reasons to `FailureCategory` members.
- New `labels.json` object under `workflow_labels`.

## TESTS (write first)
- `test_llm_failures.py`: `LLMTimeoutError → "timeout"`, `McpServersUnavailableError →
  "mcp_unavailable"`, unrelated exception → `None`; `REASON_TO_CATEGORY` maps both reasons to the
  right `FailureCategory`.
- `test_label_config.py`: the `mcp_unavailable` label loads/validates like other failure labels.
- `test_constants.py`: `FailureCategory.MCP_UNAVAILABLE.value == "mcp_unavailable"`.

## LLM PROMPT
> Implement Step 4 from `pr_info/steps/step_4.md` (see `pr_info/steps/summary.md`). Add
> `FailureCategory.MCP_UNAVAILABLE = "mcp_unavailable"` in `workflows/implement/constants.py`, a
> matching `mcp_unavailable` failure label in `config/labels.json` (mirror the `llm_timeout`
> entry), and a new `workflows/implement/llm_failures.py` with `llm_failure_reason(exc)` and
> `REASON_TO_CATEGORY`. Write the unit tests first (`test_llm_failures.py`, label-config and
> constants assertions). Do not wire the helper into any call site yet. Keep `mcp_unavailable`
> distinct from `llm_timeout` (Decision 6). pylint/pytest(`-n auto`)/mypy green, one commit.
