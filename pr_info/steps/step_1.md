# Step 1: Fix Case Mismatch in implementation_review.md

> **Context**: See [summary.md](summary.md) for full issue overview.

## LLM Prompt

Fix the path case mismatch in `.claude/commands/implementation_review.md`. The file references `docs/architecture/ARCHITECTURE.md` but the actual file is `docs/architecture/architecture.md`. Change the reference to use the correct lowercase filename.

## WHERE

- **File**: `.claude/commands/implementation_review.md`
- **Line**: In the "Focus Areas" bullet list (line ~33)

## WHAT

Single string replacement — no functions, no signatures.

### Current text:
```
- Compliance with existing architecture principles, see `docs/architecture/ARCHITECTURE.md`
```

### New text:
```
- Compliance with existing architecture principles, see `docs/architecture/architecture.md`
```

## HOW

- Direct edit of one line in a Markdown file
- No imports, no decorators, no integration points

## ALGORITHM

```
1. Open .claude/commands/implementation_review.md
2. Find "ARCHITECTURE.md"
3. Replace with "architecture.md"
4. Save
```

## DATA

- **Input**: Markdown file with incorrect case reference
- **Output**: Markdown file with correct case reference
- **Verification**: The referenced path `docs/architecture/architecture.md` matches the actual file in the repo

## TDD

Not applicable — Markdown-only change with no testable behavior.
