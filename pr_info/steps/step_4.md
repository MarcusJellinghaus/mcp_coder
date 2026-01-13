# Step 4: Update Documentation

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Document vulture in the architecture documentation files.
Add vulture to the list of architectural tools and note the liberal whitelist approach.
```

## WHERE
| File | Action |
|------|--------|
| `docs/architecture/ARCHITECTURE.md` | Modify - add vulture to tools section |
| `docs/architecture/dependencies/README.md` | Modify - add vulture documentation |

## WHAT

### 1. ARCHITECTURE.md

Add vulture to the "Architectural Boundary Enforcement" section (likely in Section 8 - Cross-cutting Concepts):

**Update existing tools line:**
```markdown
### Architectural Boundary Enforcement
- **Tools**: import-linter, tach, pycycle for static analysis of module dependencies; vulture for dead code detection
```

**Add new subsection:**
```markdown
### Dead Code Detection
- **Tool**: Vulture for identifying unused code
- **Configuration**: `vulture_whitelist.py` at project root for false positives and API completeness items
- **CI Integration**: Runs in architecture job on PRs with 80% confidence threshold
- **Note**: The whitelist is intentionally liberal - review periodically for items that may become truly dead
```

### 2. docs/architecture/dependencies/README.md

Add a new section for vulture:

```markdown
## Vulture - Dead Code Detection

**Purpose**: Identifies unused code (imports, functions, variables, classes) that can be safely removed.

**Command**: 
```bash
vulture src tests vulture_whitelist.py --min-confidence 80
```

**Whitelist**: `vulture_whitelist.py` contains items that appear unused but are intentionally kept:
- API completeness methods (GitHub operations)
- Enum values for API constants
- Base class attributes for subclasses
- TypedDict fields, pytest fixtures, argparse patterns (false positives)

**Note**: The whitelist is intentionally liberal. Some items may be candidates for removal but were whitelisted to avoid blocking implementation. Review the whitelist periodically - items may become used or truly dead over time.
```

## ALGORITHM
```
1. Read ARCHITECTURE.md and find the relevant section
2. Add vulture to the tools list and add Dead Code Detection subsection
3. Read dependencies/README.md
4. Add Vulture section
5. Verify documentation renders correctly
```

## VERIFICATION

```python
# Verify documentation files were updated:
Bash("grep -i vulture docs/architecture/ARCHITECTURE.md")
Bash("grep -i vulture docs/architecture/dependencies/README.md")

# Final verification - all checks still pass:
Bash("vulture src tests vulture_whitelist.py --min-confidence 80")
mcp__code-checker__run_all_checks()
```

## SUCCESS CRITERIA
- [ ] ARCHITECTURE.md mentions vulture in architectural tools
- [ ] ARCHITECTURE.md has Dead Code Detection subsection
- [ ] dependencies/README.md has Vulture section
- [ ] All code quality checks still pass
- [ ] Vulture check still clean
