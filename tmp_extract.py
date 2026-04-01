import json
import os

p = os.path.join(
    r"C:\Users\Marcus\.claude\projects\C--Jenkins-environments-mcp-coder-dev",
    r"cf0efade-aa01-4840-8957-b3cfd003c33c\tool-results",
    "toolu_01S2rPbHebU44Mha9e4sxc2Y.txt",
)
with open(p, "r") as fh:
    data = json.load(fh)
content = data["result"]
lines = content.split("\n")
count = 0
for i, line in enumerate(lines, 1):
    if "display_status_table(" in line:
        count += 1
        start = max(1, i - 3)
        end = min(len(lines), i + 15)
        for j in range(start - 1, end):
            print(f"{j+1:4d}: {lines[j]}")
        print("---")
print(f"TOTAL: {count} matches")
