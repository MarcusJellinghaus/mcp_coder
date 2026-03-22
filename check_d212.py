"""Find D212 docstring violations in tests/ directory."""
import os


def find_d212_violations():
    violations = []

    for root, dirs, files in os.walk("tests"):
        for f in files:
            if not f.endswith(".py"):
                continue
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped == '"""':
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line != '"""':
                            prev_idx = i - 1
                            while prev_idx >= 0 and lines[prev_idx].strip() == "":
                                prev_idx -= 1
                            if prev_idx >= 0:
                                prev = lines[prev_idx].strip()
                                is_opener = prev.endswith(":") or prev.startswith("@")
                            else:
                                is_opener = True
                            if is_opener:
                                snippet_lines = lines[i : i + 3]
                                snippet = "".join(snippet_lines).rstrip()
                                violations.append(
                                    (filepath.replace(os.sep, "/"), i + 1, snippet)
                                )

    print(f"Found {len(violations)} D212 violations:\n")
    for filepath, lineno, snippet in violations:
        print(f"File: {filepath}")
        print(f"Line: {lineno}")
        print("Snippet:")
        for s in snippet.split("\n"):
            print(f"  {s}")
        print()


if __name__ == "__main__":
    find_d212_violations()
