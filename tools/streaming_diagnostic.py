"""Diagnostic: timestamps each line from mcp-coder to verify streaming."""

import os
import subprocess
import time

# Use local .venv — must run from project root
MCPCODER = os.path.join(".venv", "Scripts", "mcp-coder.exe")
MCP_CONFIG = ".mcp.json"

TESTS = [
    # Claude CLI
    {
        "name": "Claude / ndjson",
        "args": ["--llm-method", "claude", "--output-format", "ndjson", "--timeout", "60"],
        "prompt": "Count from 1 to 5. Just the numbers, one per line.",
    },
    {
        "name": "Claude / text",
        "args": ["--llm-method", "claude", "--output-format", "text", "--timeout", "60"],
        "prompt": "Count from 1 to 5. Just the numbers, one per line.",
    },
    {
        "name": "Claude+MCP+sleep / ndjson",
        "args": ["--llm-method", "claude", "--output-format", "ndjson", "--timeout", "120",
                 "--mcp-config", MCP_CONFIG],
        "prompt": "Count from 1 to 5. Between each number, use the sleep tool to wait 3 seconds.",
    },
    {
        "name": "Claude+MCP+sleep / text",
        "args": ["--llm-method", "claude", "--output-format", "text", "--timeout", "120",
                 "--mcp-config", MCP_CONFIG],
        "prompt": "Count from 1 to 5. Between each number, use the sleep tool to wait 3 seconds.",
    },
    # LangChain text (no MCP)
    {
        "name": "LC text / ndjson",
        "args": ["--llm-method", "langchain", "--output-format", "ndjson", "--timeout", "60"],
        "prompt": "Count from 1 to 5. Just the numbers, one per line.",
    },
    {
        "name": "LC text / text",
        "args": ["--llm-method", "langchain", "--output-format", "text", "--timeout", "60"],
        "prompt": "Count from 1 to 5. Just the numbers, one per line.",
    },
    # LangChain agent (with MCP)
    {
        "name": "LC agent / ndjson",
        "args": ["--llm-method", "langchain", "--output-format", "ndjson", "--timeout", "120",
                 "--mcp-config", MCP_CONFIG],
        "prompt": "List all MCP tools available to you, one per line.",
    },
    {
        "name": "LC agent / text",
        "args": ["--llm-method", "langchain", "--output-format", "text", "--timeout", "120",
                 "--mcp-config", MCP_CONFIG],
        "prompt": "List all MCP tools available to you, one per line.",
    },
    {
        "name": "LC agent+sleep / ndjson",
        "args": ["--llm-method", "langchain", "--output-format", "ndjson", "--timeout", "120",
                 "--mcp-config", MCP_CONFIG],
        "prompt": "Count from 1 to 5. Between each number, use the sleep tool to wait 3 seconds.",
    },
    {
        "name": "LC agent+sleep / text",
        "args": ["--llm-method", "langchain", "--output-format", "text", "--timeout", "120",
                 "--mcp-config", MCP_CONFIG],
        "prompt": "Count from 1 to 5. Between each number, use the sleep tool to wait 3 seconds.",
    },
]


def run_test(test: dict) -> dict:
    """Run a single test, capture lines with timestamps."""
    cmd = [MCPCODER, "prompt"] + test["args"] + [test["prompt"]]
    start = time.monotonic()
    lines = []
    error = None

    # Ensure VIRTUAL_ENV is set for MCP server path resolution
    env = os.environ.copy()
    venv_abs = os.path.abspath(".venv")
    env["VIRTUAL_ENV"] = venv_abs
    env["PATH"] = os.path.join(venv_abs, "Scripts") + os.pathsep + env.get("PATH", "")

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1, env=env,
        )
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            t = time.monotonic() - start
            lines.append((t, line.rstrip()))
        proc.wait(timeout=10)
        if proc.returncode != 0:
            error = proc.stderr.read().strip()[:200]
    except Exception as e:
        error = str(e)[:200]

    elapsed = time.monotonic() - start
    return {"name": test["name"], "lines": lines, "elapsed": elapsed, "error": error}


def main():
    results = []
    for test in TESTS:
        print(f"\n{'='*60}")
        print(f"  {test['name']}")
        print(f"{'='*60}")
        result = run_test(test)
        results.append(result)

        if result["error"]:
            print(f"  ERROR: {result['error']}")
            continue

        for t, line in result["lines"]:
            preview = line[:120] + ("..." if len(line) > 120 else "")
            preview = preview.encode("ascii", errors="replace").decode("ascii")
            print(f"  [{t:6.2f}s] {preview}")

        # Streaming verdict
        timestamps = [t for t, _ in result["lines"]]
        if len(timestamps) >= 2:
            spread = timestamps[-1] - timestamps[0]
            if spread > 0.5:
                verdict = f"STREAMING (spread={spread:.1f}s)"
            else:
                verdict = f"NOT STREAMING (spread={spread:.1f}s)"
        else:
            verdict = "SINGLE LINE"
        print(f"  -> {verdict} | {len(result['lines'])} lines in {result['elapsed']:.1f}s")

    # Summary matrix
    print(f"\n{'='*60}")
    print("  SUMMARY MATRIX")
    print(f"{'='*60}")
    print(f"  {'Test':<30} {'Works':>6} {'Streaming':>12} {'Lines':>6} {'Time':>6}")
    print(f"  {'-'*30} {'-'*6} {'-'*12} {'-'*6} {'-'*6}")
    for r in results:
        works = "FAIL" if r["error"] else "OK"
        if r["error"]:
            streaming = "N/A"
        else:
            ts = [t for t, _ in r["lines"]]
            spread = (ts[-1] - ts[0]) if len(ts) >= 2 else 0
            streaming = "YES" if spread > 0.5 else "NO"
        n = len(r["lines"])
        print(f"  {r['name']:<30} {works:>6} {streaming:>12} {n:>6} {r['elapsed']:>5.1f}s")


if __name__ == "__main__":
    main()
