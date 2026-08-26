"""What a langchain config actually means, per backend.

The provider routes on a side effect — ``api_version`` turns the ``openai``
backend into Azure — and each field means something different on each branch.
This module declares those consequences in one table instead of leaving the
user to discover them from an opaque SDK error.

:func:`validate` is pure and never raises: ``_create_chat_model`` turns the
first error-level finding into a ``ValueError``, while ``verify`` renders all
of them.

:func:`resolve_target` answers the other half of *"what will this config
actually do?"* — where the client will send its requests. It reads that off a
locally constructed client rather than computing it from config, because the
SDKs resolve their own environment variables and a config-derived answer is
simply wrong whenever one of those is exported.

Import direction matters. The package ``__init__`` imports :func:`validate` at
module level, so nothing here may import that ``__init__`` at module level —
module-level imports stay limited to stdlib and sibling private modules, or
``import mcp_coder.llm.providers.langchain`` breaks with a
partially-initialised-module ImportError.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from ._http import close_http_clients
from ._models import _resolve_ollama_host

logger = logging.getLogger(__name__)

Status = Literal["required", "optional", "ignored"]

# Contract modes, not backends: "azure" is what openai + api_version becomes.
_CONTRACT: dict[str, dict[str, Status]] = {
    # No api_version row: mode_of promotes any truthy api_version to "azure",
    # so a plain-openai row could never be evaluated with a value set.
    "openai": {
        "model": "required",
        "api_key": "required",
        "base_url": "optional",
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


# ---------------------------------------------------------------------------
# Resolved target — what the constructed client will actually dial
# ---------------------------------------------------------------------------

# Nothing resolved and nothing configured; the shape check skips this value.
_UNSET_TARGET = "(not configured)"

# The backend itself is unset or typo'd, so no target can even be scoped.
_NO_BACKEND_TARGET = "(backend not configured)"

# The backend has no configurable target at all (gemini, anthropic).
_NO_TARGET = "n/a"

# A constructed non-ollama client that exposes no URL at all.
_UNKNOWN_TARGET = "(unknown)"

# Every ResolvedTarget.url that is a sentinel rather than a URL. Consumers
# that parse the target must skip these wholesale: urlparse() accepts them
# happily and then reports a "malformed URL", turning "we could not tell" into
# a confident, wrong diagnosis.
NON_URL_TARGETS: frozenset[str] = frozenset(
    {_UNSET_TARGET, _NO_BACKEND_TARGET, _NO_TARGET, _UNKNOWN_TARGET}
)

# What the ollama client dials when ChatOllama.base_url is None — the same
# constant _models._check_ollama_daemon already falls back to.
_OLLAMA_DEFAULT_URL = "http://localhost:11434"

# Keyed by backend, not by mode: applicability within a backend is decided by
# _applicable_redirect_envs. Tuple order is real precedence and breaks the tie
# when two variables hold the same value — langchain resolves OPENAI_API_BASE
# into openai_api_base at init and passes it down, while the openai SDK reads
# OPENAI_BASE_URL only when it receives base_url=None.
_REDIRECT_ENV: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_BASE", "OPENAI_BASE_URL", _AZURE_ENDPOINT_ENV),
    "ollama": ("OLLAMA_HOST",),
}

# Backends whose client dials a configurable target at all.
_TARGETED_BACKENDS = ("openai", "ollama")


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """Where a langchain client will actually send its requests.

    Attributes:
        url: The dialed URL, "n/a", or a sentinel/config fallback.
        source: Human-readable provenance of *url*.
        verified: True when *url* was read off a constructed client.
    """

    url: str
    source: str
    verified: bool


def dialed_url(chat_model: Any) -> str | None:
    """Read the base URL off a constructed chat model, or None if it has none.

    Args:
        chat_model: A constructed langchain chat model.

    Returns:
        The URL the client will dial, or None when it exposes none. ChatOpenAI
        and AzureChatOpenAI carry it on ``root_client.base_url`` (an
        ``httpx.URL``, hence the str conversion); ChatOllama on ``base_url``.
    """
    root_client = getattr(chat_model, "root_client", None)
    if root_client is not None:
        url = getattr(root_client, "base_url", None)
        if url:
            return str(url)
    url = getattr(chat_model, "base_url", None)
    if url:
        return str(url)
    return None


def _close_http_clients(chat_model: Any) -> None:
    """Close the httpx clients ``create_openai_model`` built for this model.

    ChatOllama has neither, hence the getattr defaults. The failure path is
    covered inside ``create_openai_model`` itself: when the constructor
    raises, this model never exists and only the factory can still reach them.

    Args:
        chat_model: A constructed langchain chat model.
    """
    close_http_clients(
        getattr(chat_model, "http_client", None),
        getattr(chat_model, "http_async_client", None),
    )


def _targets_match(candidate: str, url: str) -> bool:
    """True when *candidate* names *url*, modulo trailing slash and scheme.

    Azure appends ``openai/deployments/<deployment>/`` to the configured
    resource URL, and OLLAMA_HOST may be a bare ``host:port`` that
    :func:`_resolve_ollama_host` normalises to ``http://host:port``.

    Args:
        candidate: A configured or exported value that might be the source.
        url: The URL the client will dial.

    Returns:
        True when *candidate* can account for *url*.
    """
    stripped_candidate = candidate.rstrip("/")
    stripped_url = url.rstrip("/")
    if "://" not in stripped_candidate:
        stripped_url = stripped_url.split("://", 1)[-1]
    return stripped_url.startswith(stripped_candidate)


def _applicable_redirect_envs(config: Mapping[str, str | None]) -> Iterator[str]:
    """Yield the redirect variables that can apply to this config.

    AZURE_OPENAI_ENDPOINT applies only in Azure mode; OPENAI_API_BASE and
    OPENAI_BASE_URL only outside it. A stale variable from the other mode is
    inert and must never be reported as a source.

    Args:
        config: LangChain configuration dict.

    Yields:
        Environment variable names, in precedence order.
    """
    backend = config.get("backend")
    azure = backend == "openai" and bool(config.get("api_version"))
    for name in _REDIRECT_ENV.get(backend or "", ()):
        if (name == _AZURE_ENDPOINT_ENV) == azure:
            yield name


def redirect_env_in_effect(config: Mapping[str, str | None], url: str) -> str | None:
    """Return the redirect env var that actually produced *url*, or None.

    A variable is only named when it is applicable to the current
    backend/mode **and** its value matches the URL the client will dial. Both
    filters are needed: merely being exported is not evidence of anything, and
    the value match settles the both-set case without guessing the SDK's
    precedence.

    Args:
        config: LangChain configuration dict.
        url: The URL the client will dial.

    Returns:
        The variable name, or None when no applicable variable matches.
    """
    for name in _applicable_redirect_envs(config):
        value = os.environ.get(name)
        if value and _targets_match(value, url):
            return name
    return None


def _fallback_url(config: Mapping[str, str | None]) -> str:
    """Return the URL a constructed client dials but does not report.

    Args:
        config: LangChain configuration dict.

    Returns:
        For ollama the resolved host — ChatOllama.base_url is None whenever
        neither config base_url nor OLLAMA_HOST is set, the most common setup,
        and the true value is knowable. Otherwise the unknown sentinel.
    """
    if config.get("backend") == "ollama":
        return _resolve_ollama_host(config.get("base_url")) or _OLLAMA_DEFAULT_URL
    return _UNKNOWN_TARGET


def _source_for(config: Mapping[str, str | None], url: str) -> str:
    """Describe where *url* came from.

    Args:
        config: LangChain configuration dict.
        url: The URL the client will dial.

    Returns:
        A human-readable provenance string; "SDK default" when nothing
        configured or exported accounts for *url*.
    """
    configured = config.get("base_url")
    if configured and _targets_match(configured, url):
        return "config.toml [llm.langchain] base_url"
    env_var = redirect_env_in_effect(config, url)
    return f"{env_var} env var" if env_var else "SDK default"


def resolve_target(config: Mapping[str, str | None]) -> ResolvedTarget:
    """Construct the chat model locally and report the URL it would dial.

    Construction is local and makes no network call. It can legitimately fail
    two ways — the backend package is not installed, or the contract is
    violated (typically a missing api_key, which is exactly when a user runs
    ``verify``) — so the config value is returned labelled *unverified*, and
    config.toml is named only when a config value actually supplied it.

    Args:
        config: LangChain configuration dict.

    Returns:
        The resolved target, never raising for a config problem.
    """
    # Deferred on purpose: the package __init__ imports validate() from this
    # module, so a module-level import back would be a real cycle and break
    # `import mcp_coder.llm.providers.langchain`.
    from . import _create_chat_model  # pylint: disable=cyclic-import

    if mode_of(config) is None:
        return ResolvedTarget(
            _NO_BACKEND_TARGET, "no supported backend configured", False
        )
    if config.get("backend") not in _TARGETED_BACKENDS:
        return ResolvedTarget(_NO_TARGET, "backend has no configurable target", True)

    try:
        chat_model = _create_chat_model(config, timeout=5)
    except Exception:
        logger.debug("Could not construct chat model for target probe", exc_info=True)
        configured = config.get("base_url")
        if configured:
            return ResolvedTarget(
                configured, "config.toml (unverified — client not constructed)", False
            )
        return ResolvedTarget(
            _UNSET_TARGET, "unverified — client not constructed", False
        )

    try:
        url = dialed_url(chat_model) or _fallback_url(config)
    finally:
        _close_http_clients(chat_model)
    return ResolvedTarget(url, _source_for(config, url), True)


# ---------------------------------------------------------------------------
# Effective-config echo — what the run will actually use, and from where
# ---------------------------------------------------------------------------

# Rendered for a field nothing supplied a value for. Deliberately the same
# object as the unresolved-target sentinel above: NON_URL_TARGETS keys the
# shape check's skip on that one, so a second copy of the literal would let
# the two drift apart silently.
_NOT_CONFIGURED = _UNSET_TARGET

# The backend is unset or typo'd, so there is no mode to name. Asserting one
# here would print "plain None (api_version not set)" next to a backend row
# reading "(not configured)".
_NO_MODE = "(not applicable — backend not configured)"


def _describe_mode(config: Mapping[str, str | None]) -> str:
    """Describe the routing mode and the key that decided it.

    Args:
        config: LangChain configuration dict.

    Returns:
        A row value naming ``api_version`` as the discriminator in both
        directions, or the no-backend sentinel.
    """
    mode = mode_of(config)
    if mode is None:
        return _NO_MODE
    if mode == "azure":
        return "Azure OpenAI (api_version set)"
    backend = config.get("backend")
    # Only openai + api_version is Azure, so a stray api_version on another
    # backend lands here. Say it is ignored rather than claiming it is unset —
    # the contract reports that same key as ignored a few rows below.
    note = (
        f"api_version ignored by {backend}"
        if config.get("api_version")
        else "api_version not set"
    )
    return f"plain {backend} ({note})"


def _describe_api_key(masked: str | None, source: str | None, overridden: bool) -> str:
    """Describe the credential that will actually be used.

    Args:
        masked: The masked winning key, or None when there is none to show.
        source: Where the winning key (or the keyless carve-out) came from.
        overridden: True when an env var beat a configured ``api_key``.

    Returns:
        A row value that never shows one source's value under another's label.
    """
    if masked is None:
        # A source with no readable key is gemini's keyless Vertex carve-out:
        # the credential is satisfied, so this is not a bare "(not set)".
        return f"(not set — satisfied via {source})" if source else "(not set)"
    suffix = " — overrides config.toml api_key" if overridden else ""
    return f"{masked}   (from {source}{suffix})"


def describe_effective_config(
    config: Mapping[str, str | None],
    target: ResolvedTarget,
    *,
    api_key_masked: str | None = None,
    api_key_source: str | None = None,
    api_key_overridden: bool = False,
) -> list[tuple[str, str]]:
    """Return (label, value) rows describing the config that will be used.

    Pure formatting: this resolves nothing and masks nothing. The three
    ``api_key_*`` arguments travel together and all come from the same
    ``_resolve_api_key`` call, so the printed value can never belong to a
    different source than the printed label; ``config["api_key"]`` is
    deliberately never read, because the winning key frequently comes from an
    environment variable while config.toml holds a different, losing one.

    Args:
        config: LangChain configuration dict.
        target: The already-resolved target from :func:`resolve_target`.
        api_key_masked: Masked winning key, or None.
        api_key_source: Provenance of the winning key, or None.
        api_key_overridden: True when an env var beat a configured ``api_key``.

    Returns:
        Five rows in a stable order, for rendering without status symbols.
    """
    return [
        ("backend", config.get("backend") or _NOT_CONFIGURED),
        ("mode", _describe_mode(config)),
        ("model", config.get("model") or _NOT_CONFIGURED),
        ("base_url", f"{target.url}   ({target.source})"),
        (
            "api_key",
            _describe_api_key(api_key_masked, api_key_source, api_key_overridden),
        ),
    ]
