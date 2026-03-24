# Step 2: Add Error Classification and Diagnostics to `_exceptions.py`

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Add error classification and diagnostic formatting to the existing `_exceptions.py` module. This replaces the generic "Connection error." message with actionable guidance: error category, proxy status, truststore status.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/_exceptions.py` | **Modify** — add classification + diagnostics |
| `tests/llm/providers/langchain/test_langchain_diagnostics.py` | **Create** |

## WHAT — New Functions (added to `_exceptions.py`)

```python
def classify_connection_error(exc: Exception) -> str:
    """Classify a connection exception into a human-readable category."""

def format_diagnostics(exc: Exception) -> str:
    """Format a diagnostic block for a connection failure."""
```

## HOW — Integration Points

- `classify_connection_error` uses exception type and OS error codes (e.g., `WinError 10054`)
- `format_diagnostics` calls `classify_connection_error` and checks env vars + truststore status
- `raise_connection_error` is updated to include the classification in its message
- Imports: `os`, `ssl` (for checking `SSLError`), and `socket` (for `gaierror`)

## ALGORITHM — `classify_connection_error(exc)`

```python
def classify_connection_error(exc):
    if isinstance(exc, ssl.SSLError) or "SSLError" in type(exc).__name__:
        return "SSL/TLS error"
    if isinstance(exc, socket.gaierror):
        return "DNS resolution failed"
    if _is_connection_reset(exc):  # checks errno 10054 or ConnectionResetError
        return "Connection reset (likely proxy/firewall)"
    if "timeout" in type(exc).__name__.lower() or "Timeout" in type(exc).__name__:
        return "Connection timeout"
    return "Connection error"
```

## ALGORITHM — `format_diagnostics(exc)`

```python
def format_diagnostics(exc):
    category = classify_connection_error(exc)
    lines = [f"Diagnosis: {category}"]
    # Proxy presence (yes/no, never the value) — check both upper and lowercase
    has_proxy = bool(
        os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    )
    lines.append(f"  HTTPS_PROXY/HTTP_PROXY configured: {'yes' if has_proxy else 'no'}")
    # Truststore status
    from ._ssl import _injected as truststore_active
    lines.append(f"  Truststore active: {'yes' if truststore_active else 'no'}")
    # Category-specific hint
    lines.append(f"  Hint: {_CATEGORY_HINTS[category]}")
    return "\n".join(lines)
```

## ALGORITHM — `_is_connection_reset(exc)`

Uses an iterative loop with a max depth of 5 to avoid unbounded recursion on deeply chained exceptions.

```python
def _is_connection_reset(exc, _max_depth: int = 5) -> bool:
    current = exc
    for _ in range(_max_depth):
        if current is None:
            break
        if isinstance(current, ConnectionResetError):
            return True
        errno = getattr(current, "errno", None)
        if errno == 10054:  # WinError 10054
            return True
        current = current.__cause__
    return False
```

## DATA — Category Hints Map

```python
_CATEGORY_HINTS: dict[str, str] = {
    "Connection reset (likely proxy/firewall)":
        "Set HTTPS_PROXY if behind a corporate proxy, or check firewall rules.",
    "Connection timeout":
        "Check network connectivity and firewall/proxy settings.",
    "SSL/TLS error":
        "Install 'mcp-coder[truststore]' or set SSL_CERT_FILE to your CA bundle.",
    "DNS resolution failed":
        "Check DNS settings and network connectivity.",
    "Connection error":
        "Check network, proxy, and firewall settings.",
}
```

## DATA — Updated `raise_connection_error`

The existing function is updated to include `format_diagnostics(original)` in the error message, appended after the existing SSL hint.

## TESTS — `test_langchain_diagnostics.py`

Write tests **first** (TDD), then implement.

### Test Classes

**`TestClassifyConnectionError`**:

Use `@pytest.mark.parametrize` to consolidate the classification cases into a single parameterized test:

```python
@pytest.mark.parametrize(
    "exc, expected_category",
    [
        (ssl.SSLError(), "SSL/TLS error"),
        (socket.gaierror(), "DNS resolution failed"),
        (ConnectionResetError(), "Connection reset (likely proxy/firewall)"),
        (OSError_with_errno_10054, "Connection reset (likely proxy/firewall)"),
        (TimeoutError(), "Connection timeout"),
        (OSError(), "Connection error"),
        (chained_connection_reset, "Connection reset (likely proxy/firewall)"),
    ],
)
def test_classify_connection_error(exc, expected_category):
    assert classify_connection_error(exc) == expected_category
```

Additional standalone test:
- `test_is_connection_reset_stops_at_max_depth` — build a chain deeper than 5 levels, verify it returns `False` (does not recurse infinitely)

**`TestFormatDiagnostics`**:

Use `@pytest.mark.parametrize` where multiple tests check string presence/absence:

```python
@pytest.mark.parametrize(
    "env_vars, expected_substring",
    [
        ({"HTTPS_PROXY": "http://proxy:8080"}, "configured: yes"),
        ({"https_proxy": "http://proxy:8080"}, "configured: yes"),
        ({"HTTP_PROXY": "http://proxy:8080"}, "configured: yes"),
        ({"http_proxy": "http://proxy:8080"}, "configured: yes"),
        ({}, "configured: no"),
    ],
)
def test_proxy_detection(env_vars, expected_substring):
    # ... set env_vars, call format_diagnostics, assert expected_substring in output
```

Additional standalone tests:
- `test_contains_category` — output includes the classified category string
- `test_shows_truststore_status` — check "Truststore active:" in output
- `test_contains_hint` — output includes a hint string
- `test_never_contains_proxy_value` — set proxy to `http://secret:pass@host`, verify value not in output

**`TestRaiseConnectionErrorWithDiagnostics`**:
- `test_message_includes_diagnostics` — verify `format_diagnostics` output appears in the raised error message

## LLM Prompt

```
Implement Step 2 of Issue #562 (see pr_info/steps/summary.md for context).

Add error classification and diagnostic formatting to
`src/mcp_coder/llm/providers/langchain/_exceptions.py`:
- `classify_connection_error(exc)` — maps exception type + codes to category string
- `format_diagnostics(exc)` — builds diagnostic block with proxy/truststore status
- Update `raise_connection_error()` to include diagnostics in the error message

TDD approach: write tests in `tests/llm/providers/langchain/test_langchain_diagnostics.py`
first, then implement. Follow existing patterns in `test_langchain_exceptions.py`.
Run all three code quality checks after implementation.
```
