# Step 4 — `B905`: explicit `zip()` `strict=` per call site

Context: see `pr_info/steps/summary.md`. Fixes all 5 `B905` findings. The
`strict=` value is **judged per site**, already decided below — do not
blanket-apply one value.

## WHERE and WHAT (exact mapping — apply as-is)

1. `tests/llm/providers/claude/test_claude_code_cli.py` —
   `zip(raw_lines, lines)` → add `strict=True`.
   Both are proven length-3 by the preceding `assert len(raw_lines) == 3`
   and `lines` is a literal 3-element list.

2. `tests/llm/providers/langchain/test_mcp_health_check.py` —
   `_make_tools_response_with_names()`: `zip(tool_mocks, names)` → `strict=True`.
   `tool_mocks = [MagicMock() for _ in names]` is built with the same length
   as `names` by construction.

3. Same file — `_make_tools_response_with_descriptions()`:
   `zip(tool_mocks, tools)` → `strict=True`. Same reasoning: `tool_mocks`
   is built as `[MagicMock() for _ in tools]`.

4. `tests/llm/test_interface.py` —
   `zip(["question", "session_id", "timeout"], args)` → `strict=False`.
   `args` is the mock's actual positional-args tuple; in the real call only
   `question` is positional (`session_id`/`timeout` are kwargs), so lengths
   legitimately differ by design. `strict=True` would break this test.

5. `tests/workflows/review/test_prototype_session_interleave.py` —
   `_assert_strictly_sequential()`: `zip(ordered, ordered[1:])` → `strict=False`.
   Classic pairwise-consecutive-elements pattern; `ordered` and `ordered[1:]`
   differ in length by one, by design.

## HOW

Run `mcp__mcp-tools-py__run_ruff_check(select=["B905"])` first to confirm
these are still the 5 current sites (same files, same call shapes). Add the
`strict=` keyword argument listed above to each `zip(...)` call. Do not
change any other logic.

## ALGORITHM

```
for site, strict_value in [the 5 mappings above]:
    locate the zip(a, b) call
    add strict=strict_value as a keyword argument
```

## DATA

No return/data-structure changes. `strict=True` sites already satisfy the
length-equality `strict` enforces (verified above); `strict=False` sites
are intentionally unequal-length by design.

## Precondition

If `mcp__mcp-tools-py__run_ruff_check(select=["B905"])` reports a different
count than 5, or reports a `zip()` call in a different shape than described
above (e.g. the `test_interface.py` call now passes `session_id`/`timeout`
positionally), write one line to `pr_info/.blocked.txt` and stop — the
`strict=` judgment above no longer applies and needs re-deriving, not
blind-applying.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check(select=["B905"])    # expect 0 findings
mcp__mcp-tools-py__run_ruff_check()
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
```

## Commit

```
fix(tests): add explicit zip() strict= per call-site intent (B905)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement
> step 4 exactly as specified: add the exact `strict=` value listed for each
> of the 5 `B905` call sites — do not re-derive or blanket-apply a single
> value. If the precondition fails, write one line to `pr_info/.blocked.txt`
> and stop. Otherwise run the verification commands in step 4, fix anything
> they flag, and make exactly one commit.
