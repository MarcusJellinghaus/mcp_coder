# Step 5 — `B009`: `getattr` with a constant attribute

Context: see `pr_info/steps/summary.md`. Fixes all 4 `B009` findings — 2 by
rewriting to dot-access, 2 by a scoped, documented `noqa`.

## WHERE and WHAT

1. `tests/icoder/test_cli_icoder_parser.py` —
   `assert getattr(args_obj, "command") == "icoder"` →
   `assert args_obj.command == "icoder"`.

2. `tests/llm/test_types.py` — `test_usage_info_total_false()`:
   `assert getattr(UsageInfo, "__total__") is False` →
   `assert UsageInfo.__total__ is False`.

3 & 4. `tests/install/test_install_phases.py`:
   ```python
   _shutil = getattr(_env, "shutil")
   _subprocess = getattr(_env, "subprocess")
   ```
   These stay as `getattr` — the preceding comment in that file already
   documents why: dot-access (`_env.shutil`) trips mypy's
   `no-implicit-reexport`, and importing `subprocess` directly in this test
   module would violate the `subprocess_isolation` import-linter contract,
   which grants `tests.install` no exemption. Add a scoped `# noqa: B009` to
   each of these two lines (keep the existing explanatory comment above
   them unchanged).

## HOW

Run `mcp__mcp-tools-py__run_ruff_check(select=["B009"])` to confirm these are
still the 4 current sites. Apply the two dot-access rewrites and the two
`# noqa: B009` additions exactly as above.

## ALGORITHM

```
rewrite getattr(obj, "attr") -> obj.attr   # sites 1 and 2
append "  # noqa: B009" to the getattr(...) line               # sites 3 and 4
```

## DATA

No data/behavior change in any of the 4 cases — dot-access and `getattr`
with no default are equivalent at runtime for a literal attribute name.

## Precondition

If `mcp__mcp-tools-py__run_ruff_check(select=["B009"])` reports a different
count than 4, or locations outside the files named above, write one line to
`pr_info/.blocked.txt` and stop.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check(select=["B009"])    # expect 0 findings
mcp__mcp-tools-py__run_ruff_check()
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
```

## Commit

```
fix(tests): replace getattr-with-constant with dot access (B009)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement
> step 5 exactly as specified: rewrite the 2 dot-access-safe `getattr` sites,
> and add a scoped `# noqa: B009` to the 2 documented-exception sites in
> `tests/install/test_install_phases.py` — do not remove or change the
> existing explanatory comment there. If the precondition fails, write one
> line to `pr_info/.blocked.txt` and stop. Otherwise run the verification
> commands in step 5, fix anything they flag, and make exactly one commit.
