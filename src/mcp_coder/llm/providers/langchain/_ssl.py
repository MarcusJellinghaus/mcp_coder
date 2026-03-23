"""Optional truststore support for OS certificate store integration.

Activates truststore (if installed) to use the OS certificate store,
fixing SSL errors behind corporate proxies where Python's bundled
certifi certificates are not sufficient.
"""

import logging

logger = logging.getLogger(__name__)

_injected: bool = False


def ensure_truststore() -> None:
    """Activate truststore for OS certificate store integration if available.

    Idempotent — calls truststore.inject_into_ssl() at most once.
    No-op if truststore is not installed.
    """
    global _injected  # noqa: PLW0603
    if _injected:
        return
    try:
        import truststore  # pylint: disable=import-outside-toplevel
    except ImportError:
        return
    truststore.inject_into_ssl()
    _injected = True
    logger.debug("truststore activated: using OS certificate store")
