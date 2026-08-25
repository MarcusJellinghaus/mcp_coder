"""What a langchain config actually means, per backend.

The provider routes on a side effect — ``api_version`` turns the ``openai``
backend into Azure — and each field means something different on each branch.
This module declares those consequences in one table instead of leaving the
user to discover them from an opaque SDK error.

:func:`validate` is pure and never raises: ``_create_chat_model`` turns the
first error-level finding into a ``ValueError``, while ``verify`` renders all
of them.

Import direction matters. The package ``__init__`` imports :func:`validate` at
module level, so nothing here may import that ``__init__`` at module level —
module-level imports stay limited to stdlib and sibling private modules, or
``import mcp_coder.llm.providers.langchain`` breaks with a
partially-initialised-module ImportError.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal, TypedDict

Status = Literal["required", "optional", "ignored"]

# Contract modes, not backends: "azure" is what openai + api_version becomes.
_CONTRACT: dict[str, dict[str, Status]] = {
    "openai": {
        "model": "required",
        "api_key": "required",
        "base_url": "optional",
        "api_version": "optional",
    },
    "azure": {
        "model": "required",
        "api_key": "required",
        "base_url": "required",
        "api_version": "required",
    },
    "gemini": {
        "model": "required",
        "api_key": "required",
        "base_url": "ignored",
        "api_version": "ignored",
    },
    "anthropic": {
        "model": "required",
        "api_key": "required",
        "base_url": "ignored",
        "api_version": "ignored",
    },
    "ollama": {
        "model": "required",
        "api_key": "optional",
        "base_url": "optional",
        "api_version": "ignored",
    },
}

_SUPPORTED_BACKENDS: tuple[str, ...] = ("openai", "gemini", "anthropic", "ollama")

# Keyed by *mode*, so an Azure config keyed off OPENAI_API_KEY is not reported
# as missing a credential. Every entry is a variable the installed SDKs
# actually read: create_*_model passes api_key=None through when it has none,
# which lets openai.AzureOpenAI fall back to AZURE_OPENAI_API_KEY then
# AZURE_OPENAI_AD_TOKEN, and lets langchain's
# secret_from_env(["GOOGLE_API_KEY", "GEMINI_API_KEY"]) factory apply. A
# narrower table would turn a working setup into a false required-error.
_API_KEY_ENV: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "azure": ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_AD_TOKEN"),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "ollama": ("OLLAMA_API_KEY",),
}

# Modes that can build a working client with no credential at all. Gemini's
# Vertex mode is the only one: ChatGoogleGenerativeAI constructs without a key
# when GOOGLE_GENAI_USE_VERTEXAI is set, and raises otherwise.
#
# Presence, not truthiness: GOOGLE_GENAI_USE_VERTEXAI=0 does not really enable
# Vertex mode, so this is over-permissive on purpose. Mirroring the SDK's
# parsing would risk a false required-error on a working setup — the failure
# this contract exists to remove — while over-permissiveness costs only a
# message the SDK still gives, and its wording is already actionable.
_KEYLESS_ENV: dict[str, str] = {"gemini": "GOOGLE_GENAI_USE_VERTEXAI"}

# Appended to the missing-api_key message, per mode.
_API_KEY_SUFFIX: dict[str, str] = {
    "openai": (
        "; the OpenAI client cannot be built without credentials, even against "
        "a custom base_url"
    ),
    "gemini": (
        " (or GOOGLE_GENAI_USE_VERTEXAI for Vertex AI, which authenticates "
        "without a key)"
    ),
}

_AZURE_ENDPOINT_ENV = "AZURE_OPENAI_ENDPOINT"


class Finding(TypedDict):
    """A single contract observation.

    Reuses verify's entry shape so ``_format_section`` renders it unchanged:
    ``ok=False`` is an error, ``ok=None`` a warning.
    """

    key: str
    ok: bool | None
    value: str


def mode_of(config: Mapping[str, str | None]) -> str | None:
    """Return the contract mode, or None when the backend is not supported.

    'azure' for openai + api_version; otherwise the backend name itself, but
    only when it is one of _SUPPORTED_BACKENDS. 'azure' is an internal mode,
    not a configurable backend value, so a literal backend = "azure" returns
    None.

    Args:
        config: LangChain configuration dict.

    Returns:
        The contract mode, or None for an unset or unsupported backend.
    """
    backend = config.get("backend")
    if backend == "openai" and config.get("api_version"):
        return "azure"
    return backend if backend in _SUPPORTED_BACKENDS else None


def _is_present(config: Mapping[str, str | None], field: str, mode: str) -> bool:
    """Return True when *field* is satisfied for *mode*.

    Args:
        config: LangChain configuration dict.
        field: Contract field name.
        mode: Contract mode from mode_of().

    Returns:
        True when the config value, or an environment fallback the SDK reads,
        supplies the field.
    """
    if config.get(field):
        return True
    if field == "api_key":
        if any(os.environ.get(var) for var in _API_KEY_ENV.get(mode, ())):
            return True
        return bool(os.environ.get(_KEYLESS_ENV.get(mode, ""), ""))
    if field == "base_url" and mode == "azure":
        # Consult the environment directly: create_openai_model passes an
        # explicit azure_endpoint=None, which bypasses langchain's from_env
        # factory, so the langchain field is unreadable for this purpose.
        return bool(os.environ.get(_AZURE_ENDPOINT_ENV))
    return False


def _required_finding(mode: str, field: str) -> Finding:
    """Build the error finding for a missing required *field*.

    Args:
        mode: Contract mode from mode_of().
        field: Contract field that is missing.

    Returns:
        A Finding with ok=False naming every source that would satisfy it.
    """
    if field == "api_key":
        env_vars = _API_KEY_ENV.get(mode, ())
        if len(env_vars) == 1:
            sources = f"no {env_vars[0]}"
        else:
            sources = "none of " + ", ".join(env_vars)
        return {
            "key": field,
            "ok": False,
            "value": (
                f"no api_key in [llm.langchain] and {sources} — set one"
                f"{_API_KEY_SUFFIX.get(mode, '')}"
            ),
        }
    if field == "base_url":
        return {
            "key": field,
            "ok": False,
            "value": (
                "api_version is set (Azure mode) but no base_url resolved from "
                f"config or {_AZURE_ENDPOINT_ENV} — set [llm.langchain] "
                "base_url to your Azure resource URL, or remove api_version "
                "for a non-Azure server"
            ),
        }
    return {
        "key": field,
        "ok": False,
        "value": f"no {field} in [llm.langchain] — set it for backend mode '{mode}'",
    }


def _unsupported_backend_finding(backend: str | None) -> Finding:
    """Build the error finding for a backend with no contract row.

    Args:
        backend: The raw configured backend value.

    Returns:
        A Finding with ok=False listing the supported backend names.
    """
    supported = ", ".join(repr(name) for name in _SUPPORTED_BACKENDS)
    return {
        "key": "backend",
        "ok": False,
        "value": (
            f"Unsupported langchain backend: {backend!r}. "
            f"Supported backends: {supported}."
        ),
    }


def validate(config: Mapping[str, str | None]) -> list[Finding]:
    """Check config against the per-backend contract. Pure; never raises.

    Args:
        config: LangChain configuration dict.

    Returns:
        Findings in contract-table order; empty when the config is sound.
    """
    mode = mode_of(config)
    if mode is None:
        return [_unsupported_backend_finding(config.get("backend"))]

    findings: list[Finding] = []
    for field, status in _CONTRACT[mode].items():
        if status == "required":
            if not _is_present(config, field, mode):
                findings.append(_required_finding(mode, field))
        elif status == "ignored" and config.get(field):
            findings.append(
                {
                    "key": field,
                    "ok": None,
                    "value": f"{field} is ignored by backend '{mode}' — remove it",
                }
            )
    return findings
