import json
import re

p = r"C:\Users\Marcus\.claude\projects\C--Jenkins-environments-mcp-coder-dev\2d788b10-d4d3-44aa-8293-9da973eceb65\tool-results\mcp-workspace-read_file-1775020870414.txt"
with open(p, encoding="utf-8") as f:
    d = json.load(f)

content = d["result"]
lines = content.split("\n")

# Find all lines with _get_diff_stat
print("=== All lines with _get_diff_stat ===")
for i, l in enumerate(lines, 1):
    if "_get_diff_stat" in l:
        print(f"L{i}: {l.rstrip()}")

# Now find which class each occurrence belongs to
print("\n=== Context: class and method for each occurrence ===")
current_class = None
current_method = None
for i, l in enumerate(lines, 1):
    cls_match = re.match(r'^class (\w+)', l)
    if cls_match:
        current_class = cls_match.group(1)
    method_match = re.match(r'    def (test\w+)', l)
    if method_match:
        current_method = method_match.group(1)
    if "_get_diff_stat" in l:
        print(f"L{i} | Class: {current_class} | Method: {current_method} | {l.strip()}")
