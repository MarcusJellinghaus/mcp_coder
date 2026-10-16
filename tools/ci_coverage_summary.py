#!/usr/bin/env python3
"""Render a CI step summary from a Cobertura coverage.xml.

Standalone script, stdlib only. Parses the coverage.xml produced by
``coverage xml`` (Cobertura format), rolls up line counts by top-level
package, and renders Markdown for ``$GITHUB_STEP_SUMMARY``. Never fails
the build based on a coverage number -- this is reporting only.

Usage:
    python tools/ci_coverage_summary.py --coverage-xml coverage.xml
    python tools/ci_coverage_summary.py --coverage-xml coverage.xml \\
        --diff-report diff-coverage.md --output summary.md
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

MARKER_TRAP_CAVEAT = (
    "_Markers excluded in CI (`claude_cli_integration`, `claude_api_integration`, "
    "`copilot_cli_integration`, `jenkins_integration`, `textual_integration`) never "
    "run here, so lines only reachable under them show as uncovered._"
)


@dataclass
class PackageRollup:
    """Line totals for one top-level package bucket."""

    name: str
    lines_valid: int
    lines_covered: int

    @property
    def rate(self) -> float:
        return self.lines_covered / self.lines_valid if self.lines_valid else 0.0


@dataclass
class CoverageSummary:
    """Grand totals plus the per-package breakdown."""

    lines_valid: int
    lines_covered: int
    packages: List[PackageRollup]

    @property
    def rate(self) -> float:
        return self.lines_covered / self.lines_valid if self.lines_valid else 0.0


def top_level_package_name(full_name: str) -> str:
    """Bucket a Cobertura package name under its top-level segment.

    ``mcp_coder.llm.providers`` -> ``llm`` (the second segment, since every
    real package lives under the ``mcp_coder`` root). Anything else
    (``tools``, a loose top-level module reported as just ``mcp_coder``)
    buckets under its own first segment.
    """
    segments = full_name.split(".")
    if segments[0] == "mcp_coder" and len(segments) > 1:
        return segments[1]
    return segments[0]


def parse_coverage_xml(xml_path: Path) -> CoverageSummary:
    """Parse a Cobertura coverage.xml, summing line hits per top-level bucket."""
    root = ET.parse(xml_path).getroot()
    buckets: dict[str, PackageRollup] = {}
    total_valid = 0
    total_covered = 0

    for package in root.findall(".//package"):
        bucket_name = top_level_package_name(package.get("name") or "")
        rollup = buckets.setdefault(
            bucket_name, PackageRollup(bucket_name, lines_valid=0, lines_covered=0)
        )
        for line in package.findall(".//class/lines/line"):
            rollup.lines_valid += 1
            total_valid += 1
            if line.get("hits") != "0":
                rollup.lines_covered += 1
                total_covered += 1

    packages = sorted(buckets.values(), key=lambda p: p.name)
    return CoverageSummary(
        lines_valid=total_valid, lines_covered=total_covered, packages=packages
    )


def render_step_summary(summary: CoverageSummary, diff_report: Optional[str]) -> str:
    """Render the step-summary Markdown for one coverage run."""
    lines = [
        f"## Coverage: {summary.rate:.0%}",
        "",
        MARKER_TRAP_CAVEAT,
        "",
        "<details>",
        "<summary>Per-package breakdown</summary>",
        "",
        "| Package | Lines valid | Lines covered | Rate |",
        "| --- | --- | --- | --- |",
    ]
    for package in summary.packages:
        lines.append(
            f"| {package.name} | {package.lines_valid} | {package.lines_covered} "
            f"| {package.rate:.0%} |"
        )
    lines.extend(["", "</details>"])

    if diff_report is not None:
        lines.extend(
            [
                "",
                "**Diff coverage (advisory, not a gate)**",
                "",
                diff_report,
            ]
        )

    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point: parse coverage.xml and append the summary to --output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-xml", required=True, type=Path)
    parser.add_argument("--diff-report", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    diff_report = (
        args.diff_report.read_text(encoding="utf-8")
        if args.diff_report is not None
        else None
    )
    summary = parse_coverage_xml(args.coverage_xml)
    rendered = render_step_summary(summary, diff_report)

    output_path = args.output or (
        Path(os.environ["GITHUB_STEP_SUMMARY"])
        if "GITHUB_STEP_SUMMARY" in os.environ
        else None
    )
    if output_path is None:
        sys.stdout.write(rendered)
    else:
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
