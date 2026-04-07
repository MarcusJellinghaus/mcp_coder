#!/usr/bin/env python3
"""One-time script to split test_orchestrator_sessions.py into 4 files.

This script:
1. Reads the source file
2. Identifies import block and 4 class boundaries
3. Creates 4 new files with appropriate imports
4. Does NOT delete the original (manual step)
"""

import re
import textwrap
from pathlib import Path

SOURCE = Path("tests/workflows/vscodeclaude/test_orchestrator_sessions.py")
DEST_DIR = Path("tests/workflows/vscodeclaude")


def main():
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.split("\n")
    print(f"Source file: {len(lines)} lines")

    # Find class start lines (0-indexed)
    class_starts = []
    for i, line in enumerate(lines):
        m = re.match(r"^class\s+(\w+)", line)
        if m:
            class_starts.append((m.group(1), i))
            print(f"  Class '{m.group(1)}' starts at line {i + 1}")

    # Find end of import block (last import/from line before first class)
    first_class_line = class_starts[0][1]
    import_end = 0
    for i in range(first_class_line):
        stripped = lines[i].strip()
        if stripped.startswith(("import ", "from ")):
            import_end = i
    import_end += 1  # exclusive

    # Find docstring end
    docstring_end = 0
    if lines[0].strip().startswith('"""'):
        for i, line in enumerate(lines):
            if i > 0 and '"""' in line:
                docstring_end = i + 1
                break
        if docstring_end == 0 and lines[0].count('"""') >= 2:
            docstring_end = 1
    elif lines[0].strip().startswith('#'):
        docstring_end = 1

    # Import block = lines from docstring_end to import_end
    # But we also need any blank lines and comments between imports
    raw_import_lines = lines[docstring_end:first_class_line]

    # Collect all import lines (including multi-line ones)
    import_text = "\n".join(raw_import_lines)
    print(f"  Import block: lines {docstring_end + 1}-{first_class_line}")

    # Extract class blocks
    class_blocks = {}
    for idx, (name, start) in enumerate(class_starts):
        if idx + 1 < len(class_starts):
            end = class_starts[idx + 1][1]
        else:
            end = len(lines)
        # Trim trailing blank lines
        while end > start and lines[end - 1].strip() == "":
            end -= 1
        block = "\n".join(lines[start : end + 1])
        class_blocks[name] = block
        print(f"  Class '{name}': lines {start + 1}-{end + 1} ({end - start + 1} lines)")

    # Define target files
    targets = [
        {
            "class_name": "TestOrchestration",
            "file": "test_session_restart.py",
            "rename_to": "TestSessionRestart",
            "docstring": '"""Tests for session restart orchestration."""',
        },
        {
            "class_name": "TestPrepareRestartBranch",
            "file": "test_session_restart_prepare_branch.py",
            "rename_to": None,
            "docstring": '"""Tests for preparing restart branches."""',
        },
        {
            "class_name": "TestRestartClosedSessionsBranchHandling",
            "file": "test_session_restart_closed_sessions.py",
            "rename_to": None,
            "docstring": '"""Tests for restart closed sessions branch handling."""',
        },
        {
            "class_name": "TestBranchHandlingIntegration",
            "file": "test_session_restart_branch_integration.py",
            "rename_to": None,
            "docstring": '"""Tests for branch handling integration."""',
        },
    ]

    for target in targets:
        class_name = target["class_name"]
        block = class_blocks[class_name]

        if target["rename_to"]:
            block = block.replace(
                f"class {class_name}", f"class {target['rename_to']}", 1
            )

        # Find used names in the class block
        used_names = set(re.findall(r"\b([A-Za-z_]\w*)\b", block))

        # Filter imports
        filtered_imports = filter_imports(raw_import_lines, used_names)

        # Build file content
        content = target["docstring"] + "\n\n" + filtered_imports + "\n\n\n" + block + "\n"

        # Write
        dest = DEST_DIR / target["file"]
        dest.write_text(content, encoding="utf-8")
        line_count = content.count("\n")
        print(f"\nCreated {target['file']}: {line_count} lines")

    print("\nDone! Original NOT deleted.")


def filter_imports(raw_import_lines, used_names):
    """Filter import lines to only those used by a class."""
    result = []
    i = 0
    lines = raw_import_lines

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Blank lines - keep for structure
        if stripped == "":
            result.append(line)
            i += 1
            continue

        # Comments - keep
        if stripped.startswith("#"):
            result.append(line)
            i += 1
            continue

        # Multi-line import with parentheses
        if stripped.startswith(("from ", "import ")) and "(" in stripped and ")" not in stripped:
            multi = [line]
            i += 1
            while i < len(lines) and ")" not in lines[i]:
                multi.append(lines[i])
                i += 1
            if i < len(lines):
                multi.append(lines[i])
                i += 1

            # Extract names from multi-line import
            full = "\n".join(multi)
            # Get the part after 'import'
            after_import = full.split("import", 1)[1] if "import" in full else ""
            # Clean up parens
            after_import = after_import.replace("(", "").replace(")", "")
            names = []
            for part in after_import.split(","):
                part = part.strip()
                if not part:
                    continue
                if " as " in part:
                    names.append(part.split(" as ")[1].strip())
                else:
                    names.append(part)

            # Keep only if at least one name is used
            needed_names = [n for n in names if n in used_names]
            if needed_names:
                # Rebuild with only needed names
                # Get the "from X import (" prefix
                prefix_match = re.match(r"(from\s+\S+\s+import\s*)\(", full, re.DOTALL)
                if prefix_match:
                    prefix = multi[0].rstrip()
                    # Check if it ends with (
                    if prefix.endswith("("):
                        if len(needed_names) == 1:
                            # Single import, no parens needed
                            base = prefix[:-1].rstrip()  # Remove (
                            result.append(f"{base}{needed_names[0]}")
                        else:
                            result.append(prefix)
                            for j, name in enumerate(needed_names):
                                comma = "," if j < len(needed_names) - 1 else ","
                                result.append(f"    {name}{comma}")
                            result.append(")")
                    else:
                        result.extend(multi)
                else:
                    result.extend(multi)
            continue

        # Single-line import
        if stripped.startswith(("from ", "import ")):
            if "import" in stripped:
                after = stripped.split("import", 1)[1]
                names = []
                for part in after.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    if " as " in part:
                        names.append(part.split(" as ")[1].strip())
                    else:
                        names.append(part)

                if any(n in used_names for n in names):
                    # Keep only needed names
                    prefix = stripped.split("import", 1)[0] + "import "
                    needed = []
                    for part in after.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        if " as " in part:
                            alias = part.split(" as ")[1].strip()
                            if alias in used_names:
                                needed.append(part)
                        else:
                            if part in used_names:
                                needed.append(part)
                    if needed:
                        result.append(prefix + ", ".join(needed))
            i += 1
            continue

        # Other lines (shouldn't happen in import block)
        result.append(line)
        i += 1

    # Remove consecutive blank lines and trailing blanks
    cleaned = []
    prev_blank = False
    for line in result:
        if line.strip() == "":
            if not prev_blank:
                cleaned.append(line)
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    # Remove leading/trailing blank lines
    while cleaned and cleaned[0].strip() == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1].strip() == "":
        cleaned.pop()

    return "\n".join(cleaned)


if __name__ == "__main__":
    main()
