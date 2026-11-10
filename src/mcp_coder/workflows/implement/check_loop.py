"""Grouped, capped fix loop for the implement workflow checks.

Runs the requests bound to an implement entry through the toolkit: every
``check`` request first, then - only when every check is clean - every
``test`` request. A group's findings get one LLM fix turn with the toolkit's
``fix.check`` or ``fix.test`` fragment; any fix restarts from the checks.
Checks and tests share one cap of MAX_FIX_TURNS fix turns per binding run.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import commit_all_changes
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.prompt_slots import (
    resolve_prompt_slots,
    toolkit_declares_bash_grants,
)
from mcp_coder.utils.toolkit_runner import (
    LoadedToolkit,
    bash_grants_of,
    get_fragment,
    llm_permissions,
    load_toolkit,
    run_request,
)
from mcp_coder.workflow_steps.commit import push_changes, run_formatters
from mcp_coder.workflow_utils.failure_handling import llm_failure_reason

from .blocked import read_and_clear_blocked
from .constants import COMMIT_MESSAGE_FILE, LLM_INACTIVITY_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

MAX_FIX_TURNS = 3

RESCUE_COMMIT_MESSAGE = "wip(implement): checks failed ({reason})"

CheckStatus = Literal["clean", "cap", "error", "blocked", "timeout", "mcp_unavailable"]

_CHECK_OUTPUT_HEADING = "Check output:"


@dataclass(frozen=True)
class CheckOutcome:
    """Result of one binding run with its fix loop.

    Attributes:
        status: How the run ended. The non-clean statuses equal the workflow
            reason strings, except ``cap`` and ``error`` which callers map.
        detail: The error or config message, the blocked reason, the cap
            summary, or the blocked-marker text for timeout / mcp_unavailable.
    """

    status: CheckStatus
    detail: str = ""


class _CheckAbort(Exception):
    """A config error or an ``error`` result; aborts the binding run."""


def _split_requests(
    binding: Sequence[str], check_type_hints: bool
) -> tuple[list[str], list[str]]:
    """Split a binding into its check and test requests.

    Args:
        binding: The entry's ``action@depth`` requests.
        check_type_hints: If False, ``check@*`` requests are dropped.

    Returns:
        (check requests, test requests), each in binding order. Other actions
        are ignored.
    """
    checks = [r for r in binding if r.startswith("check@")]
    tests = [r for r in binding if r.startswith("test@")]
    if not check_type_hints and checks:
        logger.info("check_type_hints disabled - dropping %s", ", ".join(checks))
        checks = []
    return checks, tests


def _run_group(
    loaded: LoadedToolkit, project_dir: Path, requests: list[str]
) -> str | None:
    """Run each request of one group.

    Args:
        loaded: The loaded toolkit.
        project_dir: Project root to run in.
        requests: The group's requests.

    Returns:
        The fix text (or summary) of every result with findings, joined by a
        blank line, or None if every result is ok or skipped.

    Raises:
        _CheckAbort: If a request returns an ``error`` result.
    """
    texts: list[str] = []
    for request in requests:
        result = run_request(loaded, project_dir, request)
        if result.status == "error":
            raise _CheckAbort(f"{request}: {result.summary}")
        if result.status == "skipped":
            logger.info("%s skipped: %s", request, result.summary)
        elif result.status == "findings":
            texts.append(result.fix_text or result.summary)
    return "\n\n".join(texts) or None


def _build_fix_prompt(fix_fragment: str, fix_text: str, check_instructions: str) -> str:
    """Build the fix prompt from the fragment, the check output and instructions.

    Args:
        fix_fragment: The toolkit's ``fix.check`` or ``fix.test`` fragment
        fix_text: Fix text of the failing requests
        check_instructions: Filled ``check_instructions`` slot, or "" to omit

    Returns:
        The non-empty parts joined by a blank line.
    """
    parts = [fix_fragment, f"{_CHECK_OUTPUT_HEADING}\n{fix_text}", check_instructions]
    return "\n\n".join(p for p in parts if p)


def _fix_turn(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    fragment: str,
    fix_text: str,
    project_dir: Path,
    provider: str,
    turn: int,
    step_num: int,
    env_vars: dict[str, str] | None,
    mcp_config: str | None,
    settings_file: str | None,
) -> CheckOutcome | None:
    """Run one LLM fix turn.

    Args:
        fragment: The toolkit's fix fragment for the failing group
        fix_text: Fix text of the failing group
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        turn: 1-based fix turn within this binding run
        step_num: Step number for session naming
        env_vars: Optional environment variables for the subprocess
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json

    Returns:
        None when the turn went through; otherwise the outcome that ends the
        loop. Never raises.
    """
    try:
        bash_grants = bash_grants_of(llm_permissions(project_dir, provider))
        check_instructions = ""
        if toolkit_declares_bash_grants(project_dir):
            # Toolkits that check through Bash tell the LLM how to re-run checks
            check_instructions = resolve_prompt_slots(
                "[check_instructions]", project_dir, provider, bash_grants
            ).get("check_instructions", "")
        prompt = _build_fix_prompt(fragment, fix_text, check_instructions)

        branch_name = get_branch_name_for_logging(str(project_dir))
        llm_response = prompt_llm(
            prompt,
            provider=provider,
            # Tool-using site (check fix): inactivity budget, not wall-clock.
            timeout=LLM_INACTIVITY_TIMEOUT_SECONDS,
            env_vars=env_vars,
            project_dir=str(project_dir),
            mcp_config=mcp_config,
            settings_file=settings_file,
            branch_name=branch_name,
            bash_grants=bash_grants,
        )
        response = llm_response["text"]
        if not response or not response.strip():
            raise RuntimeError("LLM returned empty response")
    except (LLMTimeoutError, McpServersUnavailableError) as e:
        blocked = read_and_clear_blocked(project_dir)
        status = cast(CheckStatus, llm_failure_reason(e) or "timeout")
        logger.error("Fix turn %d failed (%s)", turn, status)
        return CheckOutcome(status, blocked or "")
    except Exception as e:  # pylint: disable=broad-exception-caught
        blocked = read_and_clear_blocked(project_dir)
        if blocked:
            return CheckOutcome("blocked", blocked)
        logger.error("Fix turn %d failed: %s", turn, e)
        return CheckOutcome("cap", f"Fix turn failed: {e}")

    try:
        store_session(
            response_data=llm_response,
            prompt=prompt,
            store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
            step_name=f"step_{step_num}_mypy_{turn}",
            branch_name=branch_name,
        )
    except Exception as store_err:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to store implement session: %s", store_err)

    logger.info("Applied fixes from LLM (turn %d/%d)", turn, MAX_FIX_TURNS)
    blocked = read_and_clear_blocked(project_dir)
    if blocked:
        return CheckOutcome("blocked", blocked)
    return None


def check_and_fix_mypy(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    project_dir: Path,
    step_num: int,
    provider: str,
    env_vars: dict[str, str] | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    entry: str = "implement_final",
    check_type_hints: bool = True,
) -> CheckOutcome:
    """Run the checks bound to an entry and let the LLM fix their findings.

    Args:
        project_dir: Path to the project directory
        step_num: Step number for session naming
        provider: LLM provider (e.g., 'claude')
        env_vars: Optional environment variables for the subprocess
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
        entry: Toolkit binding entry whose requests are run.
        check_type_hints: If False, ``check@*`` requests are dropped.

    Returns:
        ``clean`` when the last pass had no findings (or nothing was run);
        ``cap`` when findings remain after MAX_FIX_TURNS fix turns, no usable
        fix fragment exists or a fix turn failed; ``error`` for a config error
        or an ``error`` result; ``blocked`` / ``timeout`` / ``mcp_unavailable``
        from a fix turn. Typed LLM failures are returned, never raised.
    """
    logger.info("Running mypy type checking...")
    turn = 0
    while True:
        try:
            loaded = load_toolkit(project_dir)
            checks, tests = _split_requests(
                loaded.config.bindings[entry], check_type_hints
            )
            if not checks and not tests:
                logger.info("%s skipped: no check or test requests to run", entry)
                return CheckOutcome("clean")
            text, key = _run_group(loaded, project_dir, checks), "fix.check"
            if text is None:
                text, key = _run_group(loaded, project_dir, tests), "fix.test"
        except (ValueError, _CheckAbort) as e:
            logger.error("Check run failed: %s", e)
            return CheckOutcome("error", str(e))

        if text is None:
            logger.info("Mypy check passed after %d fix turns", turn)
            return CheckOutcome("clean")

        fragment = get_fragment(loaded, key)
        if not fragment:
            logger.warning("No usable %s fragment from the toolkit", key)
            return CheckOutcome(
                "cap", f"{key}: no usable fragment after {turn} fix turns"
            )
        if turn == MAX_FIX_TURNS:
            logger.info("Could not resolve all findings")
            return CheckOutcome("cap", f"{key}: findings remain after {turn} fix turns")

        turn += 1
        ended = _fix_turn(
            fragment,
            text,
            project_dir,
            provider,
            turn,
            step_num,
            env_vars,
            mcp_config,
            settings_file,
        )
        if ended:
            return ended


def rescue_commit(project_dir: Path, reason: str) -> str:
    """Format, commit and push whatever is in the tree after a check-stage abort.

    Args:
        project_dir: Path to the project directory
        reason: The failure reason, used in the commit message.

    Returns:
        One line for the failure comment: "pushed <sha>", "committed <sha>,
        push failed", "nothing to commit" or "commit failed: <error>". Never
        raises: the original failure reason must win.
    """
    try:
        read_and_clear_blocked(project_dir)
        (project_dir / COMMIT_MESSAGE_FILE).unlink(missing_ok=True)
        try:
            if not run_formatters(project_dir):
                logger.warning("Formatting failed before rescue commit")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Formatting failed before rescue commit: %s", e)

        result = commit_all_changes(
            RESCUE_COMMIT_MESSAGE.format(reason=reason), project_dir
        )
        if not result["success"]:
            logger.error("Rescue commit failed: %s", result["error"])
            return f"commit failed: {result['error']}"
        sha = result["commit_hash"]
        if not sha:
            logger.info("Rescue commit: nothing to commit")
            return "nothing to commit"
        if push_changes(project_dir):
            logger.info("Rescue commit %s pushed", sha)
            return f"pushed {sha}"
        logger.error("Rescue commit %s could not be pushed", sha)
        return f"committed {sha}, push failed"
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Rescue commit failed: %s", e)
        return f"commit failed: {e}"
