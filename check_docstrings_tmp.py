import os
import re

TQ = chr(34) * 3
violations = []

for root, dirs, files in os.walk("src"):
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname).replace(chr(92), "/")
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # D212: multi-line docstring summary not on first line
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            count = stripped.count(TQ)
            if count == 1 and stripped.rstrip().endswith(TQ):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and next_line != TQ and not next_line.startswith(TQ):
                        is_ml = False
                        for j in range(i + 1, min(i + 50, len(lines))):
                            if TQ in lines[j]:
                                is_ml = True
                                break
                        if is_ml:
                            violations.append(
                                ("D212", fpath, i + 1, stripped.rstrip(), lines[i + 1].rstrip())
                            )

        # D202: blank line after function/method docstring
        in_func = False
        ds_start = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"(async\s+)?def\s+", stripped):
                in_func = True
                ds_start = None
                continue
            if in_func and ds_start is None:
                if not stripped or stripped.startswith("#") or stripped.startswith("@"):
                    if not stripped:
                        in_func = False
                    continue
                if stripped.startswith(TQ):
                    ds_start = i
                    if stripped.count(TQ) >= 2:
                        # Single line docstring - check if blank line follows
                        if i + 1 < len(lines) and lines[i + 1].strip() == "":
                            if i + 2 < len(lines) and lines[i + 2].strip() != "":
                                violations.append(
                                    ("D202", fpath, i + 1, stripped, "(blank line follows)")
                                )
                        in_func = False
                        ds_start = None
                    continue
                else:
                    in_func = False
                    continue
            if in_func and ds_start is not None:
                if TQ in stripped:
                    # Found closing of docstring
                    if i + 1 < len(lines) and lines[i + 1].strip() == "":
                        if i + 2 < len(lines) and lines[i + 2].strip() != "":
                            violations.append(
                                ("D202", fpath, i + 1, stripped, "(blank line follows)")
                            )
                    in_func = False
                    ds_start = None

for v in violations:
    code, fp, ln, l1, l2 = v
    print(f"{code} {fp}:{ln}")
    print(f"  {l1}")
    print(f"  {l2}")
    print()

print(f"Total: {len(violations)}")
