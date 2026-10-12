# Step 2 — Document `--inexact` in config.md

Refer to `pr_info/steps/summary.md` for the overall problem and fix rationale.
This step has no tests (documentation-only change) and depends on Step 1
already having landed the code fix it describes.

## WHERE

- `docs/configuration/config.md`, three spots near lines 867, 880, 903 (line
  numbers approximate — locate by content, not line number, since Step 1 does
  not touch this file).

## WHAT

1. **Diagram arrow** (~line 867): change

   ```
   │ 1. uv sync --extra types (in repo/)
   ```

   to

   ```
   │ 1. uv sync --inexact --extra types (in repo/)
   ```

2. **"Why Type Stubs Need Separate Installation" paragraph** (~line 880):
   change

   > The coordinator command templates automatically run `uv sync --extra types`
   > in the project directory before executing mcp-coder commands.

   to name `--inexact` and state what it does — install the `types` extra
   without removing packages a prior provisioning step (e.g. AutoRunner's
   `uv sync --extra dev`) already installed.

3. **Bulleted summary** (~line 903): change

   ```
   - Automated workflows install only type stubs (`uv sync --extra types`)
   ```

   to

   ```
   - Automated workflows install only type stubs, without removing anything
     already installed (`uv sync --inexact --extra types`)
   ```

## HOW

Three `mcp__mcp-workspace__edit_file` calls, each matching the current exact
text at that location (no `replace_all` — the three spots have distinct
surrounding text).

## ALGORITHM

N/A — prose and diagram edits only, no logic.

## DATA

N/A.

## Commit

Run `mcp__mcp-tools-py__run_format_code` is not meaningful for Markdown, so
just verify the file renders sensibly, then stage and commit:

```
docs(config): document --inexact for the type-stub sync step

Show --inexact in the dependency-architecture diagram and prose, and
explain that it preserves packages installed by an earlier
provisioning step.
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_2.md`). Update the three spots in
> `docs/configuration/config.md` listed under WHAT to show `--inexact` and
> explain that it preserves packages from an earlier provisioning step (e.g.
> AutoRunner's `uv sync --extra dev`). Then create exactly one commit with the
> message given in the "Commit" section.
