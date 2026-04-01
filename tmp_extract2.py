import json, os, sys

p = os.path.join(
    r"C:\Users\Marcus\.claude\projects\C--Jenkins-environments-mcp-coder-dev",
    r"cf0efade-aa01-4840-8957-b3cfd003c33c\tool-results",
    "toolu_01S2rPbHebU44Mha9e4sxc2Y.txt",
)
with open(p, "r") as fh:
    data = json.load(fh)
content = data["result"]

with open("tmp_test_file.py", "w") as out:
    out.write(content)

print("Written to tmp_test_file.py")
