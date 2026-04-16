# Step 2 — Header Padding Helper

## Goal

Add a `_pad(title)` helper in `verify.py` that returns a 60-char-wide header (or wider when the title is long — never truncate). Apply it to **all existing `=== X ===` header strings in `verify.py`** — all 9 header-print sites (three formatter helpers plus six inline headers in `execute_verify`, including the two fallback-branch "langchain-mcp-adapters not installed" headers and INSTALL INSTRUCTIONS). Tests verify the padding boundary.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2 as a single commit: add `_pad(title)` helper in `src/mcp_coder/cli/commands/verify.py`, apply it to all section headers in `_format_section`, `_format_mcp_section`, `_format_claude_mcp_section`, and inline `execute_verify` prints. Write tests first (padding boundary, long-title pass-through). Run pylint, pytest, mypy.

## WHERE

- **Modify:** `src/mcp_coder/cli/commands/verify.py`
- **Modify tests:** `tests/cli/commands/test_verify_format_section.py` (add `TestPadHeader` class; loosen existing `"=== ... ===" in output` asserts to `"=== ..."`)

## WHAT

```python
def _pad(title: str) -> str:
    """Return a section header line padded to 60 chars with '=' (never truncated).

    Args:
        title: Section title (without surrounding '===').

    Returns:
        Header line prefixed with '\\n' for the required blank line above.
    """
    prefix = f"=== {title} "
    return "\n" + prefix + "=" * max(0, 60 - len(prefix))
```

Replace **all existing `=== X ===` header literals in `verify.py`** — including fallback-branch duplicates and INSTALL INSTRUCTIONS. Actual count: **9 header-print sites**.

## HOW

- Add `_pad` near the top of `verify.py` (before `_format_section`).
- Replace all 9 header literals across the module:
  1. `_format_section`: `f"\n=== {title} ==="` → `_pad(title)` (the dynamic `=== {title} ===` line)
  2. `_format_mcp_section`: `f"\n=== MCP SERVERS (via langchain-mcp-adapters{title_suffix}) ==="` → `_pad(f"MCP SERVERS (via langchain-mcp-adapters{title_suffix})")` (single header, takes `title_suffix`)
  3. `_format_claude_mcp_section`: `f"\n=== MCP SERVERS (via Claude Code{title_suffix}) ==="` → `_pad(f"MCP SERVERS (via Claude Code{title_suffix})")` (single header, takes `title_suffix`)
  4. `execute_verify` inline: `"\n=== CONFIG ==="` → `_pad("CONFIG")`
  5. `execute_verify` inline: `"\n=== PROMPTS ==="` → `_pad("PROMPTS")`
  6. `execute_verify` inline: `"\n=== LLM PROVIDER ==="` → `_pad("LLM PROVIDER")`
  7. `execute_verify` fallback MCP "not installed" header in the claude-active branch: `"\n=== MCP SERVERS (via langchain-mcp-adapters) ==="` → `_pad("MCP SERVERS (via langchain-mcp-adapters)")`
  8. `execute_verify` fallback MCP "not installed" header in the langchain-active branch: `"\n=== MCP SERVERS (via langchain-mcp-adapters) ==="` → `_pad("MCP SERVERS (via langchain-mcp-adapters)")`
  9. `execute_verify` inline: `"\n=== INSTALL INSTRUCTIONS ==="` → `_pad("INSTALL INSTRUCTIONS")`

Equivalent instruction: replace **every** `=== X ===` header string in `verify.py`, including fallback-branch duplicates and INSTALL INSTRUCTIONS.

## ALGORITHM

```
prefix = "=== " + title + " "
fill = max(0, 60 - len(prefix))
return "\n" + prefix + "=" * fill
```

## DATA

- Input: `str` (title, e.g. `"CONFIG"`).
- Output: `str` starting with `\n`, containing padded header.

## Tests to Add

```python
class TestPadHeader:
    def test_short_title_padded_to_60(self) -> None:
        out = _pad("CONFIG")
        assert out == "\n=== CONFIG " + "=" * (60 - len("=== CONFIG "))
        assert len(out.lstrip("\n")) == 60

    def test_exact_60_title_no_extra_padding(self) -> None:
        title = "X" * (60 - len("===  "))  # prefix "=== X...X " == 60
        out = _pad(title)
        assert len(out.lstrip("\n")) == 60

    def test_long_title_not_truncated(self) -> None:
        long = "MCP SERVERS (via langchain-mcp-adapters — for completeness)"
        out = _pad(long)
        assert long in out
        assert out.lstrip("\n").startswith(f"=== {long} ")
```

## Verification

All three checks must pass (see Step 1 invocation).
