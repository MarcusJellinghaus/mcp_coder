"""Fill toolkit prompt slots and [placeholder] substitutions.

Prompts carry two slots, ``[language_context]`` and ``[check_instructions]``,
filled from the configured toolkit's ``prompt_fragments()``. Callers resolve
the slots for a template, then fill slots and substitutions in one pass::

    slots = resolve_prompt_slots(template, project_dir, provider, bash_grants)
    prompt = fill_prompt(template, substitutions, slots)
"""

import logging
import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from .toolkit_runner import bash_grants_of, llm_permissions, load_toolkit

logger = logging.getLogger(__name__)

SLOT_NAMES: tuple[str, ...] = ("language_context", "check_instructions")
DEFAULT_LANGUAGE_CONTEXT = ""
DEFAULT_CHECK_INSTRUCTIONS = (
    "Run the project's quality checks (linters, type checkers, tests) "
    "and fix all issues."
)


def _defaults() -> dict[str, str]:
    """Neutral slot values used when the toolkit supplies none.

    Returns:
        Mapping of each slot name to its neutral default value.
    """
    return {
        "language_context": DEFAULT_LANGUAGE_CONTEXT,
        "check_instructions": DEFAULT_CHECK_INSTRUCTIONS,
    }


def resolve_prompt_slots(
    text: str,
    project_dir: Path,
    provider: str | None,
    bash_grants: Sequence[str] | None,
) -> dict[str, str]:
    """Resolve the values of the slots present in a prompt.

    The toolkit is loaded only when ``text`` contains a slot. Never raises:
    any failure logs a warning and yields the neutral defaults.

    Args:
        text: Prompt template to scan for slots.
        project_dir: Project root containing the toolkit config.
        provider: LLM provider; None falls back to MCP_CODER_LLM_PROVIDER,
            then "claude", as in prompt_llm.
        bash_grants: ``Bash(...)`` grants the session gets, if any.

    Returns:
        Values for the slots present in ``text`` only; ``{}`` if none.
        ``check_instructions`` is "" when the toolkit declares ``Bash(...)``
        grants the session does not get.
    """
    present = [s for s in SLOT_NAMES if f"[{s}]" in text]
    if not present:
        return {}

    values = _defaults()
    try:
        fragments = load_toolkit(project_dir).toolkit.prompt_fragments()
        for slot in SLOT_NAMES:
            if slot in fragments:
                values[slot] = fragments[slot]
        resolved = provider or os.environ.get("MCP_CODER_LLM_PROVIDER") or "claude"
        if bash_grants_of(llm_permissions(project_dir, "claude")) and (
            resolved != "claude" or not bash_grants
        ):
            values["check_instructions"] = ""
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Prompt slots fall back to defaults: %s", exc)
        values = _defaults()
    return {slot: values[slot] for slot in present}


def fill_prompt(
    template: str,
    substitutions: Mapping[str, str],
    slots: Mapping[str, str],
) -> str:
    """Fill slots and [placeholder] substitutions in a prompt template.

    A slot whose value is "" on a line of its own removes that line; a double
    blank line created by the removal collapses to one. Everything else is
    replaced in a single pass, so inserted text is never substituted again.
    Unknown ``[names]``, ``- [ ]`` and ``[x]`` stay untouched.

    Args:
        template: Prompt template text.
        substitutions: Placeholder names (without brackets) to values.
        slots: Slot names to values, e.g. from resolve_prompt_slots.

    Returns:
        The filled prompt.
    """
    empty_lines = {f"[{name}]" for name, value in slots.items() if value == ""}
    lines = template.split("\n")
    out: list[str] = []
    skip_next_blank = False
    for line in lines:
        if skip_next_blank:
            skip_next_blank = False
            if line.strip() == "":
                continue
        if line.strip() in empty_lines:
            skip_next_blank = bool(out) and out[-1].strip() == ""
            continue
        out.append(line)
    text = "\n".join(out)

    keys = {**substitutions, **slots}
    if not keys:
        return text
    pattern = r"\[(" + "|".join(map(re.escape, keys)) + r")\]"
    return re.sub(pattern, lambda m: keys[m.group(1)], text)
