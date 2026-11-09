"""Tests for the command toolkit config parser."""

from typing import Any

import pytest

from mcp_coder.toolkits.command.config import (
    DEFAULT_EXIT_CODES,
    DEFAULT_TIMEOUT,
    ParsedConfig,
    Problem,
    Step,
    parse_config,
)


def _only_step(parsed: ParsedConfig, action: str, depth: str) -> Step:
    steps = parsed.steps[action][depth]
    assert len(steps) == 1
    return steps[0]


def _messages(problems: list[Problem]) -> str:
    return "\n".join(p.message for p in problems)


class TestDefaults:
    """Defaults and per-step overrides."""

    def test_defaults_applied(self) -> None:
        parsed = parse_config({"check": {"quick": [{"argv": ["npm", "run", "lint"]}]}})
        assert parsed.problems == []
        step = _only_step(parsed, "check", "quick")
        assert step.argv == ("npm", "run", "lint")
        assert step.name is None
        assert step.parser == "exit-code"
        assert step.exit_codes == DEFAULT_EXIT_CODES
        assert step.timeout == DEFAULT_TIMEOUT
        assert step.report is None
        assert step.label == "npm run lint"

    def test_top_level_defaults_applied(self) -> None:
        parsed = parse_config(
            {
                "timeout": 30,
                "exit_codes": {"0": "ok", "2": "findings"},
                "check": {"quick": [{"argv": ["lint"]}]},
            }
        )
        assert parsed.problems == []
        step = _only_step(parsed, "check", "quick")
        assert step.timeout == 30
        assert step.exit_codes == {0: "ok", 2: "findings"}

    def test_step_overrides(self) -> None:
        parsed = parse_config(
            {
                "timeout": 30,
                "test": {
                    "full": [
                        {
                            "argv": ["npm", "test"],
                            "name": "unit",
                            "parser": "junit",
                            "report": "build/junit.xml",
                            "timeout": 5,
                        }
                    ]
                },
            }
        )
        assert parsed.problems == []
        step = _only_step(parsed, "test", "full")
        assert step.name == "unit"
        assert step.label == "unit"
        assert step.parser == "junit"
        assert step.report == "build/junit.xml"
        assert step.timeout == 5

    def test_step_exit_codes_replace_default(self) -> None:
        parsed = parse_config(
            {
                "exit_codes": {"0": "ok", "1": "findings", "5": "skipped"},
                "check": {"quick": [{"argv": ["lint"], "exit_codes": {"0": "ok"}}]},
            }
        )
        assert parsed.problems == []
        assert _only_step(parsed, "check", "quick").exit_codes == {0: "ok"}


class TestExitCodes:
    """`exit_codes` keys and values."""

    def test_string_keys_become_int(self) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["lint"], "exit_codes": {"3": "skipped"}}]}}
        )
        assert _only_step(parsed, "check", "quick").exit_codes == {3: "skipped"}

    def test_non_numeric_key_is_error(self) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["lint"], "exit_codes": {"x": "ok"}}]}}
        )
        errors = parsed.errors_for("check", "quick")
        assert len(errors) == 1
        assert "'x'" in errors[0].message
        assert parsed.steps["check"]["quick"] == []

    def test_bad_value_is_error(self) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["lint"], "exit_codes": {"0": "great"}}]}}
        )
        errors = parsed.errors_for("check", "quick")
        assert len(errors) == 1
        assert "'great'" in errors[0].message

    def test_not_a_table_is_error(self) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["lint"], "exit_codes": [0, 1]}]}}
        )
        assert parsed.errors_for("check", "quick")

    def test_bad_default_is_global_error(self) -> None:
        parsed = parse_config(
            {"exit_codes": {"0": "fine"}, "check": {"quick": [{"argv": ["lint"]}]}}
        )
        assert len(parsed.global_errors()) == 1
        assert parsed.global_errors()[0].scope is None


class TestUnknownKeys:
    """Unknown top-level, action and step keys."""

    def test_unknown_top_level_key(self) -> None:
        parsed = parse_config({"commands": {}})
        errors = parsed.global_errors()
        assert len(errors) == 1
        assert "'commands'" in errors[0].message

    def test_unknown_action_key(self) -> None:
        parsed = parse_config({"lint": {"quick": [{"argv": ["lint"]}]}})
        errors = parsed.global_errors()
        assert len(errors) == 1
        assert "'lint'" in errors[0].message
        assert "lint" not in parsed.steps

    def test_action_not_a_table(self) -> None:
        parsed = parse_config({"check": [{"argv": ["lint"]}]})
        assert parsed.global_errors()
        assert "check" not in parsed.steps

    def test_unknown_step_key(self) -> None:
        parsed = parse_config({"check": {"quick": [{"argv": ["lint"], "cmd": "x"}]}})
        errors = parsed.errors_for("check", "quick")
        assert len(errors) == 1
        assert errors[0].message == "check.quick[1]: unknown key 'cmd'"
        assert errors[0].scope == ("check", "quick")
        assert errors[0].name == "check.quick[1]"
        assert parsed.global_errors() == []

    def test_step_not_a_table(self) -> None:
        parsed = parse_config({"check": {"quick": ["npm run lint"]}})
        assert parsed.errors_for("check", "quick")
        assert parsed.steps["check"]["quick"] == []

    def test_depth_not_a_list(self) -> None:
        parsed = parse_config({"check": {"quick": {"argv": ["lint"]}}})
        assert parsed.errors_for("check", "quick")
        assert parsed.steps["check"]["quick"] == []


class TestTimeout:
    """`timeout` must be a positive integer."""

    @pytest.mark.parametrize("value", [0, -1, 1.5, True, "10"])
    def test_bad_step_timeout(self, value: Any) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["lint"], "timeout": value}]}}
        )
        errors = parsed.errors_for("check", "quick")
        assert len(errors) == 1
        assert "timeout must be a positive integer" in errors[0].message
        assert parsed.steps["check"]["quick"] == []

    def test_message_names_value(self) -> None:
        parsed = parse_config({"timeout": 0})
        assert _messages(parsed.global_errors()) == (
            "timeout must be a positive integer, got 0"
        )

    def test_bad_default_is_global_error(self) -> None:
        parsed = parse_config({"timeout": -1, "check": {"quick": [{"argv": ["x"]}]}})
        assert len(parsed.global_errors()) == 1
        assert parsed.errors_for("check", "quick") == []


class TestArgv:
    """`argv` is required and must be a non-empty list of strings."""

    @pytest.mark.parametrize(
        "raw_step",
        [
            {"argv": "npm run lint"},
            {"argv": []},
            {"name": "lint"},
            {"argv": ["npm", 1]},
        ],
    )
    def test_bad_argv_is_scoped_error(self, raw_step: dict[str, Any]) -> None:
        parsed = parse_config(
            {"check": {"quick": [raw_step], "full": [{"argv": ["lint"]}]}}
        )
        assert len(parsed.errors_for("check", "quick")) == 1
        assert parsed.global_errors() == []
        assert parsed.steps["check"]["quick"] == []
        assert len(parsed.steps["check"]["full"]) == 1

    def test_bad_name(self) -> None:
        parsed = parse_config({"check": {"quick": [{"argv": ["lint"], "name": 3}]}})
        assert len(parsed.errors_for("check", "quick")) == 1

    def test_bad_parser(self) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["lint"], "parser": "sarif"}]}}
        )
        assert "'sarif'" in _messages(parsed.errors_for("check", "quick"))

    def test_bad_default_parser(self) -> None:
        parsed = parse_config({"parser": "regex"})
        assert "'regex'" in _messages(parsed.global_errors())


class TestReport:
    """`report` rules for the junit parser."""

    def test_junit_without_report(self) -> None:
        parsed = parse_config(
            {"test": {"full": [{"argv": ["npm", "test"], "parser": "junit"}]}}
        )
        assert len(parsed.errors_for("test", "full")) == 1

    def test_default_junit_without_report(self) -> None:
        parsed = parse_config(
            {"parser": "junit", "test": {"full": [{"argv": ["npm", "test"]}]}}
        )
        assert len(parsed.errors_for("test", "full")) == 1
        assert parsed.global_errors() == []

    def test_report_without_junit(self) -> None:
        parsed = parse_config(
            {"test": {"full": [{"argv": ["npm", "test"], "report": "junit.xml"}]}}
        )
        assert len(parsed.errors_for("test", "full")) == 1

    @pytest.mark.parametrize(
        "report", ["../x.xml", "build/../../x.xml", "/tmp/x.xml", "C:\\x.xml", ""]
    )
    def test_report_outside_project(self, report: str) -> None:
        parsed = parse_config(
            {
                "test": {
                    "full": [
                        {"argv": ["npm", "test"], "parser": "junit", "report": report}
                    ]
                }
            }
        )
        assert len(parsed.errors_for("test", "full")) == 1
        assert parsed.steps["test"]["full"] == []

    def test_report_inside_project(self) -> None:
        parsed = parse_config(
            {
                "test": {
                    "full": [
                        {
                            "argv": ["npm", "test"],
                            "parser": "junit",
                            "report": "build/../out/..junit.xml",
                        }
                    ]
                }
            }
        )
        assert parsed.problems == []


class TestGrants:
    """Bash grants and the shell-safety warning."""

    def test_grant_is_joined_argv(self) -> None:
        parsed = parse_config({"check": {"quick": [{"argv": ["npm", "run", "lint"]}]}})
        assert _only_step(parsed, "check", "quick").grant == "Bash(npm run lint)"

    def test_explicit_bash(self) -> None:
        parsed = parse_config(
            {"llm_permissions": "bash", "check": {"quick": [{"argv": ["lint"]}]}}
        )
        assert _only_step(parsed, "check", "quick").grant == "Bash(lint)"

    @pytest.mark.parametrize("element", ["a b", "a,b", "C:\\x", ""])
    def test_unsafe_element_is_warning(self, element: str) -> None:
        parsed = parse_config({"check": {"quick": [{"argv": ["tool", element]}]}})
        step = _only_step(parsed, "check", "quick")
        assert step.grant is None
        assert len(parsed.problems) == 1
        warning = parsed.problems[0]
        assert warning.status == "warning"
        assert warning.scope == ("check", "quick")
        assert "without a grant" in warning.message
        assert parsed.errors_for("check", "quick") == []
        assert parsed.global_errors() == []

    def test_none_gives_no_grants(self) -> None:
        parsed = parse_config(
            {
                "llm_permissions": "none",
                "check": {"quick": [{"argv": ["lint"]}, {"argv": ["a b"]}]},
            }
        )
        assert parsed.problems == []
        assert all(s.grant is None for s in parsed.steps["check"]["quick"])

    def test_invalid_value_is_global_error_and_no_grants(self) -> None:
        parsed = parse_config(
            {
                "llm_permissions": "yes",
                "check": {"quick": [{"argv": ["lint"]}]},
                "test": {"full": [{"argv": ["npm", "test"]}]},
            }
        )
        errors = parsed.global_errors()
        assert len(errors) == 1
        assert "'yes'" in errors[0].message
        steps = [
            s for depths in parsed.steps.values() for d in depths.values() for s in d
        ]
        assert len(steps) == 2
        assert all(s.grant is None for s in steps)


class TestOrderAndFilters:
    """Config order and the error filters."""

    def test_config_order_preserved(self) -> None:
        parsed = parse_config(
            {
                "test": {"zeta": [{"argv": ["t1"]}], "alpha": [{"argv": ["t2"]}]},
                "check": {
                    "quick": [{"argv": ["c2"]}, {"argv": ["c1"]}, {"argv": ["c3"]}]
                },
            }
        )
        assert list(parsed.steps) == ["test", "check"]
        assert list(parsed.steps["test"]) == ["zeta", "alpha"]
        assert [s.argv[0] for s in parsed.steps["check"]["quick"]] == ["c2", "c1", "c3"]

    def test_malformed_step_dropped_others_kept(self) -> None:
        parsed = parse_config(
            {"check": {"quick": [{"argv": ["a"]}, {"argv": []}, {"argv": ["c"]}]}}
        )
        assert [s.argv[0] for s in parsed.steps["check"]["quick"]] == ["a", "c"]
        assert parsed.errors_for("check", "quick")[0].name == "check.quick[2]"

    def test_errors_for_filters_scope_and_status(self) -> None:
        parsed = parse_config(
            {
                "bogus": 1,
                "check": {
                    "quick": [{"argv": []}, {"argv": ["a b"]}],
                    "full": [{"argv": ["x"], "cmd": 1}],
                },
            }
        )
        assert len(parsed.problems) == 4
        quick = parsed.errors_for("check", "quick")
        assert len(quick) == 1
        assert quick[0].status == "error"
        assert len(parsed.errors_for("check", "full")) == 1
        assert parsed.errors_for("test", "full") == []
        assert len(parsed.global_errors()) == 1
        assert parsed.global_errors()[0].name == "command"

    def test_empty_config(self) -> None:
        parsed = parse_config({})
        assert parsed.steps == {}
        assert parsed.problems == []

    def test_never_raises_on_garbage(self) -> None:
        parsed = parse_config(
            {
                "llm_permissions": 3,
                "parser": None,
                "exit_codes": "x",
                "timeout": [],
                "format": 5,
                "check": {"q": [None, 7, {"argv": [None]}]},
            }
        )
        assert parsed.global_errors()
