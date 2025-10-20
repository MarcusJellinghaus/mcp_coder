import os

print("Testing path expansion:")
print(f"~/.local/bin/claude.exe expands to: {os.path.expanduser('~/.local/bin/claude.exe')}")
print(f"Expected: C:\\Users\\Marcus\\.local\\bin\\claude.exe")
print(f"Match: {os.path.expanduser('~/.local/bin/claude.exe') == r'C:\\Users\\Marcus\\.local\\bin\\claude.exe'}")
