"""Tests for the pure build functions in jenkins_operations.builds (no mocks)."""

import re
from datetime import UTC, datetime
from typing import Any

import pytest

from mcp_coder.utils.jenkins_operations.builds import (
    BUILDS_CAP,
    MAX_DEPTH,
    VALID_STATUSES,
    build_tree_query,
    flatten_builds,
    log_filename,
    map_status,
    select_builds,
    split_job_path,
    validate_statuses,
)
from mcp_coder.utils.jenkins_operations.models import BuildInfo

BASE = "https://jenkins.example.com"


def _build(
    number: int,
    timestamp_ms: int,
    result: str | None = "SUCCESS",
    building: bool = False,
    duration: int = 1000,
    url: str = "",
) -> dict[str, Any]:
    """Create a raw Jenkins build dict."""
    return {
        "number": number,
        "building": building,
        "result": result,
        "timestamp": timestamp_ms,
        "duration": duration,
        "url": url or f"{BASE}/build/{number}/",
    }


def _info(
    job_path: str, number: int, status: str, ts_seconds: int, display_name: str = ""
) -> BuildInfo:
    """Create a BuildInfo for select_builds tests."""
    folder, job_name = split_job_path(job_path)
    return BuildInfo(
        job_path=job_path,
        folder=folder,
        job_name=job_name,
        number=number,
        status=status,
        timestamp=datetime.fromtimestamp(ts_seconds, tz=UTC),
        duration_ms=1000,
        url=f"{BASE}/{job_path}/{number}/",
        display_name=display_name,
    )


class TestMapStatus:
    """Tests for map_status."""

    def test_building_is_running(self) -> None:
        assert map_status({"building": True, "result": None}) == "running"

    def test_building_with_result_is_running(self) -> None:
        assert map_status({"building": True, "result": "SUCCESS"}) == "running"

    def test_no_result_is_unknown(self) -> None:
        assert map_status({"building": False, "result": None}) == "unknown"

    @pytest.mark.parametrize(
        "result", ["SUCCESS", "UNSTABLE", "FAILURE", "ABORTED", "NOT_BUILT"]
    )
    def test_result_lowercased(self, result: str) -> None:
        assert map_status({"building": False, "result": result}) == result.lower()


class TestSplitJobPath:
    """Tests for split_job_path."""

    def test_top_level(self) -> None:
        assert split_job_path("job") == ("", "job")

    def test_nested(self) -> None:
        assert split_job_path("A/B/job") == ("A/B", "job")

    def test_multibranch_keeps_encoding(self) -> None:
        assert split_job_path("A/mb/feature%2Fx") == ("A/mb", "feature%2Fx")


class TestBuildTreeQuery:
    """Tests for build_tree_query."""

    def test_uses_builds_at_cap(self) -> None:
        query = build_tree_query(BUILDS_CAP)
        assert "builds[" in query
        assert "allBuilds" not in query
        assert "{0,100}" in query

    def test_uses_all_builds_above_cap(self) -> None:
        query = build_tree_query(BUILDS_CAP + 1)
        assert "allBuilds[" in query
        assert "{0,101}" in query

    def test_range_follows_field_list(self) -> None:
        query = build_tree_query(5)
        assert (
            "builds[number,building,result,timestamp,duration,url,displayName]{0,5}"
            in query
        )

    def test_starts_with_tree(self) -> None:
        assert build_tree_query(5).startswith("?tree=fullName,url,builds[")

    def test_jobs_depth(self) -> None:
        assert build_tree_query(5).count("jobs[") == MAX_DEPTH


class TestFlattenBuilds:
    """Tests for flatten_builds."""

    def test_top_level_job(self) -> None:
        tree = {
            "jobs": [
                {
                    "fullName": "job",
                    "url": f"{BASE}/job/job/",
                    "builds": [_build(2, 2000), _build(1, 1000)],
                }
            ]
        }
        result = flatten_builds(tree)
        assert [b.number for b in result] == [2, 1]
        assert result[0].job_path == "job"
        assert result[0].folder == ""
        assert result[0].job_name == "job"
        assert result[0].status == "success"
        assert result[0].duration_ms == 1000
        assert result[0].url == f"{BASE}/build/2/"
        assert result[0].display_name == ""

    def test_display_name(self) -> None:
        build = {**_build(9, 9000), "displayName": "proj - #12 - implement - #9"}
        tree = {
            "jobs": [{"fullName": "job", "url": f"{BASE}/job/job/", "builds": [build]}]
        }
        result = flatten_builds(tree)
        assert result[0].display_name == "proj - #12 - implement - #9"

    def test_folder_containing_job(self) -> None:
        tree = {
            "jobs": [
                {
                    "fullName": "A",
                    "url": f"{BASE}/job/A/",
                    "jobs": [
                        {
                            "fullName": "A/inner",
                            "url": f"{BASE}/job/A/job/inner/",
                            "builds": [_build(7, 7000, result="FAILURE")],
                        }
                    ],
                }
            ]
        }
        result = flatten_builds(tree)
        assert len(result) == 1
        assert result[0].job_path == "A/inner"
        assert result[0].folder == "A"
        assert result[0].job_name == "inner"
        assert result[0].status == "failure"

    def test_multibranch_keeps_encoded_name(self) -> None:
        tree = {
            "jobs": [
                {
                    "fullName": "A/mb",
                    "url": f"{BASE}/job/A/job/mb/",
                    "jobs": [
                        {
                            "fullName": "A/mb/feature%2Fx",
                            "url": f"{BASE}/job/A/job/mb/job/feature%252Fx/",
                            "builds": [_build(3, 3000)],
                        },
                        {
                            "fullName": "A/mb/main",
                            "url": f"{BASE}/job/A/job/mb/job/main/",
                            "builds": [_build(4, 4000)],
                        },
                    ],
                }
            ]
        }
        result = flatten_builds(tree)
        assert [b.job_path for b in result] == ["A/mb/feature%2Fx", "A/mb/main"]
        assert result[0].folder == "A/mb"
        assert result[0].job_name == "feature%2Fx"

    def test_tree_is_job(self) -> None:
        tree = {
            "fullName": "A/exec",
            "url": f"{BASE}/job/A/job/exec/",
            "allBuilds": [_build(2, 2000), _build(1, 1000)],
        }
        result = flatten_builds(tree)
        assert [(b.job_path, b.number) for b in result] == [
            ("A/exec", 2),
            ("A/exec", 1),
        ]
        assert result[0].folder == "A"
        assert result[0].job_name == "exec"

    def test_job_without_builds(self) -> None:
        tree = {
            "jobs": [{"fullName": "empty", "url": f"{BASE}/job/empty/", "builds": []}]
        }
        assert flatten_builds(tree) == []

    def test_empty_tree(self) -> None:
        assert flatten_builds({}) == []
        assert flatten_builds({"jobs": []}) == []

    def test_all_builds(self) -> None:
        tree = {
            "jobs": [
                {
                    "fullName": "job",
                    "url": f"{BASE}/job/job/",
                    "allBuilds": [_build(1, 1000)],
                }
            ]
        }
        result = flatten_builds(tree)
        assert [b.number for b in result] == [1]

    def test_timestamp_is_utc_aware(self) -> None:
        tree = {
            "jobs": [
                {
                    "fullName": "job",
                    "url": f"{BASE}/job/job/",
                    "builds": [_build(1, 1_700_000_000_000)],
                }
            ]
        }
        ts = flatten_builds(tree)[0].timestamp
        assert ts.tzinfo is not None
        assert ts.utcoffset() is not None
        assert ts == datetime.fromtimestamp(1_700_000_000, tz=UTC)

    def test_duration_none_for_running_and_unknown(self) -> None:
        tree = {
            "jobs": [
                {
                    "fullName": "job",
                    "url": f"{BASE}/job/job/",
                    "builds": [
                        _build(3, 3000, result=None, building=True, duration=0),
                        _build(2, 2000, result=None, duration=0),
                        _build(1, 1000, result="SUCCESS", duration=500),
                    ],
                }
            ]
        }
        result = flatten_builds(tree)
        assert [b.status for b in result] == ["running", "unknown", "success"]
        assert [b.duration_ms for b in result] == [None, None, 500]


class TestSelectBuilds:
    """Tests for select_builds."""

    def test_merges_newest_first(self) -> None:
        builds = [
            _info("a", 1, "success", 100),
            _info("b", 1, "success", 300),
            _info("a", 2, "success", 200),
        ]
        result = select_builds(builds, 10, None)
        assert [(b.job_path, b.number) for b in result] == [
            ("b", 1),
            ("a", 2),
            ("a", 1),
        ]

    def test_truncates_to_limit(self) -> None:
        builds = [_info("a", n, "success", n) for n in range(1, 6)]
        result = select_builds(builds, 2, None)
        assert [b.number for b in result] == [5, 4]

    def test_filters_after_truncation(self) -> None:
        builds = [
            _info("a", 1, "failure", 100),
            _info("a", 2, "success", 200),
            _info("a", 3, "failure", 300),
        ]
        result = select_builds(builds, 2, ["failure"])
        assert [b.number for b in result] == [3]

    def test_statuses_none_keeps_all(self) -> None:
        builds = [
            _info("a", 1, "failure", 100),
            _info("a", 2, "success", 200),
        ]
        assert len(select_builds(builds, 10, None)) == 2

    def test_returns_new_list(self) -> None:
        builds = [_info("a", 1, "success", 100)]
        result = select_builds(builds, 10, None)
        assert result is not builds

    def test_name_pattern_applied_before_limit(self) -> None:
        builds = [
            _info("exec", 1, "failure", 100, "proj - #5 - implement - #1"),
            _info("coord", 1, "success", 200, "#1"),
            _info("coord", 2, "success", 300, "#2"),
        ]
        result = select_builds(builds, 1, None, re.compile(r" - #\d+$"))
        assert [(b.job_path, b.number) for b in result] == [("exec", 1)]

    def test_name_pattern_combined_with_statuses(self) -> None:
        builds = [
            _info("exec", 1, "failure", 100, "proj - #5 - plan - #1"),
            _info("exec", 2, "success", 200, "proj - #5 - plan - #2"),
        ]
        result = select_builds(builds, 10, ["failure"], re.compile("plan"))
        assert [b.number for b in result] == [1]


class TestValidateStatuses:
    """Tests for validate_statuses."""

    def test_none_passes(self) -> None:
        validate_statuses(None)

    def test_valid_list_passes(self) -> None:
        validate_statuses(list(VALID_STATUSES))

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            validate_statuses(["failed"])
        message = str(exc_info.value)
        assert "failed" in message
        for status in VALID_STATUSES:
            assert status in message


class TestLogFilename:
    """Tests for log_filename."""

    def test_slashes_replaced(self) -> None:
        assert log_filename("A/B/job", 5) == "A_B_job_5.txt"

    def test_invalid_chars_replaced(self) -> None:
        assert log_filename('a<>:"\\|?*b', 1) == "a________b_1.txt"

    def test_encoded_slash_kept(self) -> None:
        assert log_filename("A/mb/feature%2Fx", 2) == "A_mb_feature%2Fx_2.txt"

    def test_custom_display_name_used(self) -> None:
        assert (
            log_filename("A/exec", 9, "proj - #12 - implement - #9")
            == "proj - #12 - implement - #9.txt"
        )

    def test_display_name_invalid_chars_replaced(self) -> None:
        assert log_filename("A/exec", 9, "a/b:c") == "a_b_c.txt"

    def test_default_display_name_ignored(self) -> None:
        assert log_filename("A/exec", 9, "#9") == "A_exec_9.txt"
