# Implementation Review Log — Issue #639

`verify --list-mcp-tools`: list MCP tools without invoking LLM

## Round 1 — 2026-03-30

**Findings:**
- **C1 (Critical):** No-op assertion in `test_list_mcp_tools_missing_description_shows_name_only` — `assert no_desc_line.rstrip() == no_desc_line.rstrip()` compares a value to itself, always passes
- **S1:** Hardcoded tool count text in detailed mode instead of reusing `entry["value"]`
- **S2:** Code duplication between the two branches of `_format_mcp_section`
- **S3:** Dict ordering assumption in alignment test (relies on Python 3.7+)
- **S4:** `_make_tools_response_with_names` helper name doesn't hint at `.description = None`

**Decisions:**
- C1: **Accept** — real bug, test doesn't validate the behavior it describes
- S1: **Skip** — speculative, only matters if someone changes the value format
- S2: **Skip** — branches are different enough, extraction adds indirection for minimal gain
- S3: **Skip** — cosmetic, Python 3.7+ dict ordering is well-known
- S4: **Skip** — cosmetic, pre-existing naming

**Changes:** Fixed assertion to `assert no_desc_line == no_desc_line.rstrip()` in `tests/cli/commands/test_verify_format_section.py`

**Status:** Committed (967b576)

## Round 2 — 2026-03-30

**Findings:**
- **S1:** `_make_tools_response_with_names` partially redundant with `_make_tools_response_with_descriptions`
- **S2:** Duplicated loop structure in `_format_mcp_section` (same as round 1 S2)
- **S3:** Missing `"tools"` key in orchestration test fixture (harmless, never accessed)

**Decisions:**
- S1: **Skip** — cosmetic, both helpers work correctly
- S2: **Skip** — already assessed in round 1
- S3: **Skip** — harmless, key is never accessed in that test path

**Changes:** None

**Status:** No changes needed

## Final Status

- **Rounds:** 2
- **Commits:** 1 (967b576 — fix no-op assertion)
- **Open issues:** None
- **Branch status:** Up to date with main, CI pending
