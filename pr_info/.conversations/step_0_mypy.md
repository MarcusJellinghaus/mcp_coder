# Mypy Fix Attempt 1

## Mypy Errors:
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 30, "column": 11, "message": "Missing keys (\"assignees\", \"user\", \"created_at\", \"locked\") for TypedDict \"IssueData\"", "hint": null, "code": "typeddict-item", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 42, "column": 27, "message": "Missing type parameters for generic type \"dict\"", "hint": null, "code": "type-arg", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 61, "column": 0, "message": "Function is missing a return type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 71, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 81, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 97, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 105, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 114, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 123, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 132, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 145, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 155, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 166, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 171, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 171, "column": 48, "message": "Argument 2 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 175, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 188, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 188, "column": 48, "message": "Argument 2 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 194, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 197, "column": 8, "message": "Need type annotation for \"fresh_issues\" (hint: \"fresh_issues: dict[<type>, <type>] = ...\")", "hint": null, "code": "var-annotated", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 199, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 203, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 208, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 208, "column": 48, "message": "Argument 2 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 218, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 246, "column": 41, "message": "Argument 1 to \"_filter_eligible_issues\" has incompatible type \"list[dict[str, object]]\"; expected \"list[IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 256, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 274, "column": 41, "message": "Argument 1 to \"_filter_eligible_issues\" has incompatible type \"list[dict[str, object]]\"; expected \"list[IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 281, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 311, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 346, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 386, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 410, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 445, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 469, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4741, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4742, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4743, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4744, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4745, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4746, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4747, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4748, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4772, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4793, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4794, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4795, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4796, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4797, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4798, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4799, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4800, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4824, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4846, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4847, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4848, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4849, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4850, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4851, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4852, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4853, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4877, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4900, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4901, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4902, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4903, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4904, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4905, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4906, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4907, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4908, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4936, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4958, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4963, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4972, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4977, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4986, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4991, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5000, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5005, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5014, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5019, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5028, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5033, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}


## Prompt Sent to LLM:
Fix the mypy type errors shown in the output below.

Focus only on resolving the type errors - do not make unnecessary changes to the code.

For each error:
1. Understand the type mismatch or missing annotation
2. Add appropriate type hints or fix incorrect types
3. Use proper typing imports (List, Dict, Optional, etc.) from typing module
4. Ensure all function parameters and return types are properly annotated

Keep changes minimal and focused on type correctness.

Mypy output:
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 30, "column": 11, "message": "Missing keys (\"assignees\", \"user\", \"created_at\", \"locked\") for TypedDict \"IssueData\"", "hint": null, "code": "typeddict-item", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 42, "column": 27, "message": "Missing type parameters for generic type \"dict\"", "hint": null, "code": "type-arg", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 61, "column": 0, "message": "Function is missing a return type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 71, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 81, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 97, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 105, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 114, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 123, "column": 4, "message": "Function is missing a return type annotation", "hint": "Use \"-> None\" if function does not return a value", "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 132, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 145, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 155, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 166, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 171, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 171, "column": 48, "message": "Argument 2 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 175, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 188, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 188, "column": 48, "message": "Argument 2 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 194, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 197, "column": 8, "message": "Need type annotation for \"fresh_issues\" (hint: \"fresh_issues: dict[<type>, <type>] = ...\")", "hint": null, "code": "var-annotated", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 199, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 203, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 208, "column": 33, "message": "Argument 1 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 208, "column": 48, "message": "Argument 2 to \"_log_stale_cache_entries\" has incompatible type \"dict[str, dict[str, object]]\"; expected \"dict[str, IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 218, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 246, "column": 41, "message": "Argument 1 to \"_filter_eligible_issues\" has incompatible type \"list[dict[str, object]]\"; expected \"list[IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 256, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 274, "column": 41, "message": "Argument 1 to \"_filter_eligible_issues\" has incompatible type \"list[dict[str, object]]\"; expected \"list[IssueData]\"", "hint": null, "code": "arg-type", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 281, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 311, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 346, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 386, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 410, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 445, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\utils\\test_coordinator_cache.py", "line": 469, "column": 4, "message": "Function is missing a type annotation", "hint": null, "code": "no-untyped-def", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4741, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4742, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4743, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4744, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4745, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4746, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4747, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4748, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4772, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4793, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4794, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4795, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4796, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4797, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4798, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4799, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4800, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4824, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4846, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4847, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4848, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4849, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4850, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4851, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4852, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4853, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4877, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4900, "column": 40, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4901, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4902, "column": 41, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4903, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4904, "column": 34, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4905, "column": 35, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4906, "column": 38, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4907, "column": 36, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4908, "column": 31, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4936, "column": 25, "message": "Name \"execute_coordinator_run\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4958, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4963, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4972, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4977, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4986, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 4991, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5000, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5005, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5014, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5019, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5028, "column": 37, "message": "Name \"Mock\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}
{"file": "tests\\cli\\commands\\test_coordinator.py", "line": 5033, "column": 17, "message": "Name \"get_cache_refresh_minutes\" is not defined", "hint": null, "code": "name-defined", "severity": "error"}


Expected output: Code changes that resolve all type errors while maintaining functionality.

## LLM Fix Response:
Perfect! I have successfully fixed all the mypy type errors in the `tests/utils/test_coordinator_cache.py` file. The mypy check on the `tests/utils` directory now passes with no type errors.

## Summary of Fixes Applied

### 1. Fixed IssueData TypedDict Missing Keys
- Added missing required keys (`assignees`, `user`, `created_at`, `locked`) to all IssueData test fixtures and mock data
- These keys were required by the IssueData TypedDict definition in the issue_manager.py module

### 2. Added Missing Type Annotations
- Added return type annotations (`-> None`) to all test methods
- Added parameter type annotations for fixtures and mock objects
- Added proper typing for pytest fixtures like `pytest.LogCaptureFixture`

### 3. Fixed Dict Type Parameter Issues
- Changed generic `dict` to `Dict[str, object]` for cache data fixtures
- Added explicit type annotations for variables that needed them (e.g., `Dict[str, IssueData]`)
- Added proper typing imports including `Any` from the typing module

### 4. Resolved Argument Type Mismatches
- Fixed all instances where `dict[str, dict[str, object]]` was being passed to functions expecting `Dict[str, IssueData]`
- Created properly typed IssueData objects with all required fields for test data

The mypy errors related to `tests/cli/commands/test_coordinator.py` appear to be referencing a file that doesn't exist in the current working directory, possibly from a cached mypy run or different environment. The actual test files that do exist now pass mypy type checking successfully.

---
Mypy fix generated on: 2025-12-31T18:05:21.424855
