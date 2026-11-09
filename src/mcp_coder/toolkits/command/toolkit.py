"""`CommandToolkit`: runs the project's own configured commands.

Each action depth is a list of steps; every step runs its argv without a shell
and maps the exit code to a status. The `junit` parser turns failed test cases
into findings; the `exit-code` parser reports one finding per failed step.
"""

import logging
import os
import shutil
from pathlib import Path
from xml.etree import ElementTree  # noqa: S405  # nosec B405

from mcp_coder.toolkits.command.config import Step, parse_config
from mcp_coder.utils.subprocess_runner import execute_command
from mcp_coder.utils.toolkit import (
    ActionRequest,
    ActionResult,
    Finding,
    Toolkit,
    ToolkitInfo,
    VerifyItem,
)

logger = logging.getLogger(__name__)

_SEVERITY = {"skipped": 0, "ok": 1, "findings": 2, "error": 3}
_TAIL_LINES = 200
_GLOBAL_NAME = "command"
_RERUN_INTRO = (
    "Re-run the checks with these exact commands; run each one unchanged — "
    "extra arguments, flags or changed spacing are denied:\n"
)
_FIX_CHECK = (
    "Fix the findings reported in the check output below. Make minimal "
    "changes and fix the cause in the code, not the check or its configuration."
)
_FIX_TEST = (
    "Fix the failing tests reported in the test output below. Make minimal "
    "changes and fix the cause in the code, not the tests' expectations unless "
    "they are wrong."
)


class CommandToolkit(Toolkit):
    """Toolkit running project-configured format / check / test commands."""

    def describe(self) -> ToolkitInfo:
        """Describe the configured actions, depths and Bash grants; never raises.

        Returns:
            Actions and depths in config order, a closed empty params schema and
            the grants per action and depth (none at all on a global error).
        """
        parsed = parse_config(self.config)
        actions = {action: list(depths) for action, depths in parsed.steps.items()}
        llm_permissions: dict[str, dict[str, list[str]]] = {}
        if not parsed.global_errors():
            llm_permissions = {
                action: {
                    depth: [s.grant for s in steps if s.grant]
                    for depth, steps in depths.items()
                }
                for action, depths in parsed.steps.items()
            }
        return ToolkitInfo(
            actions=actions,
            params_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            llm_permissions=llm_permissions,
        )

    def verify(self, project_dir: Path, action: str | None = None) -> list[VerifyItem]:
        """Report config problems and executables missing for the steps in scope.

        Returns:
            Global problems always; scoped problems and missing executables for
            `action` (every action when None); a single `ok` item when clean.
        """
        parsed = parse_config(self.config)
        items = [
            VerifyItem(name=p.name, status=p.status, message=p.message)
            for p in parsed.problems
            if p.scope is None
        ]
        if action is not None and action not in parsed.steps:
            items.append(
                VerifyItem(
                    name=_GLOBAL_NAME, status="error", message=f"{action}: not declared"
                )
            )
        items.extend(
            VerifyItem(name=p.name, status=p.status, message=p.message)
            for p in parsed.problems
            if p.scope is not None and (action is None or p.scope[0] == action)
        )
        for step_action, depths in parsed.steps.items():
            if action is not None and step_action != action:
                continue
            for depth, steps in depths.items():
                for step in steps:
                    if _resolve_exe(step.argv[0], project_dir) is None:
                        items.append(
                            VerifyItem(
                                name=f"{step_action}.{depth}",
                                status="error",
                                message=f"{step.label}: {step.argv[0]!r} not found",
                            )
                        )
        return items or [VerifyItem(name=_GLOBAL_NAME, status="ok")]

    def prompt_fragments(self) -> dict[str, str]:
        """Return the check re-run instructions and the generic fix texts.

        Returns:
            `language_context`, `check_instructions`,
            `check_instructions.unattended`, `fix.check` and `fix.test`; the
            check instructions are empty when the LLM gets no grants.
        """
        parsed = parse_config(self.config)
        none = self.config.get("llm_permissions", "bash") == "none" or bool(
            parsed.global_errors()
        )
        all_steps = [
            step
            for depths in parsed.steps.values()
            for steps in depths.values()
            for step in steps
        ]
        unattended = parsed.steps.get("test", {}).get("unattended")
        return {
            "language_context": "",
            "check_instructions": "" if none else _RERUN_INTRO + _steps_text(all_steps),
            "check_instructions.unattended": (
                ""
                if none or unattended is None
                else _RERUN_INTRO + _steps_text(unattended)
            ),
            "fix.check": _FIX_CHECK,
            "fix.test": _FIX_TEST,
        }

    def run(self, request: ActionRequest) -> ActionResult:
        """Run every step of the requested action depth and merge the results.

        Returns:
            The worst step status with all findings; `error` on a config
            problem or an undeclared action / depth.
        """
        parsed = parse_config(self.config)
        global_errors = parsed.global_errors()
        if global_errors:
            message = "command toolkit config: " + "; ".join(
                p.message for p in global_errors
            )
            return ActionResult(status="error", summary=message, fix_text=message)

        name = f"{request.action}@{request.depth}"
        steps = parsed.steps.get(request.action, {}).get(request.depth)
        if steps is None:
            message = f"{name} not declared"
            return ActionResult(status="error", summary=message, fix_text=message)

        scoped_errors = parsed.errors_for(request.action, request.depth)
        if scoped_errors:
            message = f"{name} is misconfigured: " + "; ".join(
                p.message for p in scoped_errors
            )
            return ActionResult(status="error", summary=message, fix_text=message)

        results = [_run_step(step, request.project_dir) for step in steps]
        for step, result in zip(steps, results, strict=True):
            if step.parser == "exit-code" and result.status == "findings":
                logger.info(
                    "exit-code parser: rebase regression detection is degraded for %s",
                    step.label,
                )
        return _merge(results)


def _steps_text(steps: list[Step]) -> str:
    """List steps for the LLM, one line each, deduplicated by argv.

    Returns:
        Granted steps as their exact command; ungranted ones marked as not
        re-runnable.
    """
    seen: set[tuple[str, ...]] = set()
    lines: list[str] = []
    for step in steps:
        if step.argv in seen:
            continue
        seen.add(step.argv)
        if step.grant:
            lines.append(f"- `{' '.join(step.argv)}`")
        else:
            lines.append(
                f"- {step.label}: can't be re-run; results come in the fix prompt"
            )
    return "\n".join(lines)


def _resolve_exe(argv0: str, project_dir: Path) -> str | None:
    """Resolve argv[0]: project-relative when it has a directory part, else PATH.

    Returns:
        The executable path, or None when it is not found.
    """
    if "/" in argv0 or os.sep in argv0:
        return shutil.which(str(project_dir / argv0))
    return shutil.which(argv0)


def _run_step(step: Step, project_dir: Path) -> ActionResult:
    """Run one step and map its exit code to a status.

    Returns:
        The step's result; `fix_text` is set for `findings` and `error`.
    """
    label = step.label
    exe = _resolve_exe(step.argv[0], project_dir)
    if exe is None:
        message = f"{label}: {step.argv[0]!r} not found"
        return ActionResult(status="error", summary=message, fix_text=message)

    if step.report is not None:
        (project_dir / step.report).unlink(missing_ok=True)

    res = execute_command(
        [exe, *step.argv[1:]],
        cwd=str(project_dir),
        timeout_seconds=step.timeout,
    )
    if res.timed_out:
        message = f"{label}: timed out after {step.timeout} s"
        return ActionResult(status="error", summary=message, fix_text=message)
    if res.execution_error:
        message = f"{label}: {res.execution_error}"
        return ActionResult(status="error", summary=message, fix_text=message)

    status = step.exit_codes.get(res.return_code, "error")
    raw = (res.stdout + "\n" + res.stderr).strip()
    output = _tail(res.stdout, res.stderr)
    summary = f"{label}: {status}"
    if status in ("ok", "skipped"):
        return ActionResult(status=status, summary=summary, raw=raw)  # type: ignore[arg-type]

    findings: list[Finding] = []
    lead = [label]
    if status == "findings":
        if step.parser == "junit" and step.report is not None:
            parsed = _junit_findings(project_dir / step.report)
            if isinstance(parsed, str):
                status = "error"
                summary = f"{label}: {parsed}"
                lead.append(parsed)
            else:
                findings = parsed or [_fallback_finding(step)]
                lead.extend(f"{f.key}: {f.message}" for f in parsed)
        else:
            findings = [_fallback_finding(step)]

    fix_text = "\n".join([*lead, output]) if output else "\n".join(lead)
    return ActionResult(
        status=status,  # type: ignore[arg-type]
        summary=summary,
        findings=findings,
        fix_text=fix_text,
        raw=raw,
    )


def _junit_findings(path: Path) -> list[Finding] | str:
    """Parse a junit XML report.

    Returns:
        One finding per failed test case, or an error message when the report
        is missing or unparsable.
    """
    try:
        # Report written locally by the project's own test tool.
        tree = ElementTree.parse(path)  # noqa: S314  # nosec B314
    except FileNotFoundError:
        return f"junit report {path.name!r} was not written"
    except (ElementTree.ParseError, OSError) as exc:
        return f"junit report {path.name!r} is unreadable: {exc}"

    findings: list[Finding] = []
    for case in tree.getroot().iter("testcase"):
        for child in case:
            if child.tag in ("failure", "error"):
                message = child.get("message") or (child.text or "").strip()
                key = f"{case.get('classname', '')}::{case.get('name', '')}"
                findings.append(Finding(key=key, message=message))
                break
    return findings


def _fallback_finding(step: Step) -> Finding:
    """Build the finding for a failed step without parsed details.

    Returns:
        One finding keyed by the step's label.
    """
    return Finding(key=step.label, message=f"{step.label} failed")


def _tail(stdout: str, stderr: str) -> str:
    """Combine stdout and stderr and keep the end.

    Returns:
        The last `_TAIL_LINES` lines of the combined output.
    """
    return "\n".join((stdout + "\n" + stderr).strip().splitlines()[-_TAIL_LINES:])


def _merge(results: list[ActionResult]) -> ActionResult:
    """Combine step results: worst status, all findings, joined fix texts.

    Returns:
        The merged result; `ok` with no steps.
    """
    if not results:
        return ActionResult(status="ok", summary="no steps configured")
    status = max((r.status for r in results), key=lambda s: _SEVERITY[s])
    findings = (
        [f for r in results for f in r.findings]
        if status in ("findings", "error")
        else []
    )
    return ActionResult(
        status=status,
        summary="\n".join(r.summary for r in results),
        findings=findings,
        fix_text="\n\n".join(r.fix_text for r in results if r.fix_text),
        raw="\n\n".join(r.raw for r in results if r.raw),
    )
