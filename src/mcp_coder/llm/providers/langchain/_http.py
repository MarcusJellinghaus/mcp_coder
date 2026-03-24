"""Shared httpx client factory with explicit truststore-backed SSL context.

Builds sync and async httpx clients that deterministically use the OS
certificate store (via truststore) when available, eliminating dependency
on global monkey-patching and initialization order.

Both clients automatically respect HTTPS_PROXY / HTTP_PROXY environment
variables (httpx native behaviour).
"""

import logging
import os
import ssl

logger = logging.getLogger(__name__)


def create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context using truststore if available, else default.

    Returns:
        An ``ssl.SSLContext`` backed by the OS certificate store when
        *truststore* is installed, otherwise Python's default context.
    """
    try:
        import truststore  # pylint: disable=import-outside-toplevel

        ctx: ssl.SSLContext = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        logger.debug("SSL context: truststore (OS certificate store)")
        return ctx
    except ImportError:
        ctx = ssl.create_default_context()
        logger.debug("SSL context: default (certifi/system)")
        return ctx


def _log_proxy_status() -> bool:
    """Log whether an HTTP(S) proxy is configured and return the status.

    Checks both upper- and lower-case environment variable names.
    **Never** logs the actual proxy URL (may contain credentials).

    Returns:
        ``True`` if any proxy env var is set, ``False`` otherwise.
    """
    proxy_configured = bool(
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    logger.debug("httpx client: proxy_configured=%s", proxy_configured)
    return proxy_configured


def create_http_client() -> "httpx.Client":  # type: ignore[name-defined]  # noqa: F821
    """Create a synchronous httpx client with explicit SSL context.

    Returns:
        An ``httpx.Client`` whose *verify* parameter is the truststore-backed
        (or default) SSL context.
    """
    import httpx  # pylint: disable=import-outside-toplevel

    ctx = create_ssl_context()
    _log_proxy_status()
    return httpx.Client(verify=ctx)


def create_async_http_client() -> "httpx.AsyncClient":  # type: ignore[name-defined]  # noqa: F821
    """Create an asynchronous httpx client with explicit SSL context.

    Returns:
        An ``httpx.AsyncClient`` whose *verify* parameter is the
        truststore-backed (or default) SSL context.
    """
    import httpx  # pylint: disable=import-outside-toplevel

    ctx = create_ssl_context()
    _log_proxy_status()
    return httpx.AsyncClient(verify=ctx)
