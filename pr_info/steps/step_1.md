# Step 1 — `LICENSE` + PEP 639 license metadata

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 1** exactly as described in
> `pr_info/steps/step_1.md`. Add the MIT `LICENSE` file and update `pyproject.toml` license
> metadata. Use values verbatim; do not run builds or resolve anything. Run the checks listed
> below, run the formatter, and produce exactly one commit.

## Precondition

`pyproject.toml` line 2 contains `"setuptools>=61.0"` and the `[project]` classifiers contain
`"License :: OSI Approved :: MIT License"`. If either is missing, or a `LICENSE` file already
exists at the repo root, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `LICENSE` (new, repo root)
- `pyproject.toml` (`[build-system]` and `[project]` tables)

## WHAT

1. **`LICENSE`** — standard MIT License text, verbatim, with the copyright line:
   `Copyright (c) 2026 Marcus Jellinghaus`
2. **`pyproject.toml`**:
   - `[build-system] requires`: `"setuptools>=61.0"` → `"setuptools>=77"` (keep `setuptools-scm>=8.0`, `wheel`).
   - In `[project]`, directly after `requires-python = ">=3.11"`, add:
     ```toml
     license = "MIT"
     license-files = ["LICENSE"]
     ```
     They must be inside `[project]` — before the `[project.optional-dependencies]` header.
   - Remove the classifier line `"License :: OSI Approved :: MIT License",`. **Mandatory** — with
     it present, setuptools ≥ 77 fails the build (`InvalidConfigError: License classifiers have
     been superseded by license expressions`).

## HOW

No code integration. The values were verified with `python -m build` during issue discussion.

## ALGORITHM

None (static file edits).

## DATA

Resulting `[project]` head:
```toml
[project]
name = "mcp-coder"
dynamic = ["version"]
description = "..."
authors = [ ... ]
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
license-files = ["LICENSE"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
]
```

## Verification

- Re-read `pyproject.toml`: no `License ::` string anywhere; `setuptools>=77`; both license keys
  are above `[project.optional-dependencies]`.
- Run `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check` (fast unit set
  from CLAUDE.md, with `-n auto`), `mcp__mcp-tools-py__run_mypy_check` — all pass.
- `mcp__mcp-tools-py__run_format_code`, then commit:
  `build: add MIT LICENSE and PEP 639 license metadata`
