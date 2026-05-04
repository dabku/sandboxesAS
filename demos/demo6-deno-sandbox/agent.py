"""
Demo 6: Deno Sandbox — The Right Way
=====================================
The agent can only execute code through Deno with restricted permissions.
Deno's deny-by-default permission model means:
  - Only ./sample-data/ is readable
  - No network access
  - No environment variable access
  - No subprocess spawning
  - No writing anywhere

Even if the agent is prompt-injected, it literally CANNOT do damage.

Usage:
    # Make sure Deno is installed: https://deno.com
    python demo6-deno-sandbox/agent.py
"""

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.llm import run_agent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_SCRIPT = Path(__file__).resolve().parent / "sandbox_runner.ts"


# ── Deno sandbox executor ──────────────────────────────────


def run_in_deno(code: str) -> str:
    """
    Execute code in Deno with strict permission restrictions.

    Permissions granted:
      --allow-read=./sample-data   (ONLY the data directory)

    Everything else is DENIED:
      --deny-net                   (no network)
      --deny-env                   (no env vars)
      --deny-run                   (no subprocesses)
      --deny-write                 (no file writing)
    """
    print(f"\n  🦕 Running in Deno sandbox (restricted permissions)...")
    start_time = time.time()

    # Write the code to a temp file so Deno can execute it
    temp_script = PROJECT_ROOT / "demo6-deno-sandbox" / "_temp_agent_code.ts"
    temp_script.write_text(code)

    deno_cmd = [
        "deno",
        "run",
        f"--allow-read={PROJECT_ROOT / 'sample-data'}",
        "--deny-net",
        "--deny-env",
        "--deny-run",
        "--deny-write",
        str(temp_script),
    ]

    print(
        f"  🔒 Permissions: read={PROJECT_ROOT / 'sample-data'} | net=❌ | env=❌ | run=❌ | write=❌"
    )

    try:
        result = subprocess.run(
            deno_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        elapsed = time.time() - start_time
        output = result.stdout
        if result.stderr:
            # Deno permission errors go to stderr
            output += f"\n{result.stderr}"
        print(f"  ⏱️  Execution time: {elapsed:.2f}s")
        print(f"  📤 Output: {output[:300]}{'...' if len(output) > 300 else ''}")

        # Clean up temp file
        try:
            temp_script.unlink()
        except Exception:
            pass

        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out (30s limit)"
    except FileNotFoundError:
        return "ERROR: Deno not installed. Install from https://deno.com"
    except Exception as e:
        return f"ERROR: {e}"


def run_deno_script(mode: str) -> str:
    """Run the pre-built sandbox_runner.ts in a specific mode."""
    print(f"\n  🦕 Running sandbox_runner.ts in '{mode}' mode...")
    start_time = time.time()

    deno_cmd = [
        "deno",
        "run",
        f"--allow-read={PROJECT_ROOT / 'sample-data'}",
        "--deny-net",
        "--deny-env",
        "--deny-run",
        "--deny-write",
        str(SANDBOX_SCRIPT),
        mode,
    ]

    print(f"  🔒 Permissions: read=sample-data | net=❌ | env=❌ | run=❌ | write=❌")

    try:
        result = subprocess.run(
            deno_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        elapsed = time.time() - start_time
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        print(f"  ⏱️  Execution time: {elapsed:.2f}s")
        return output or "(no output)"
    except FileNotFoundError:
        return "ERROR: Deno not installed. Install from https://deno.com"
    except Exception as e:
        return f"ERROR: {e}"


# ── Tool definition ─────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_deno",
            "description": (
                "Execute TypeScript/JavaScript code in a Deno sandbox with restricted permissions. "
                "The code can ONLY read files from ./sample-data/. "
                "It has NO network access, NO environment variable access, "
                "NO subprocess spawning, and NO write access. "
                "Use Deno/TypeScript APIs (e.g., Deno.readTextFile) for file access."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "TypeScript/JavaScript code to execute in the Deno sandbox",
                    }
                },
                "required": ["code"],
            },
        },
    }
]


def handle_tool(name: str, args: dict) -> str:
    if name == "execute_deno":
        return run_in_deno(args["code"])
    return f"Unknown tool: {name}"


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Demo 6: Deno Sandbox — The Right Way")
    print("=" * 60)
    print()
    print("  🔒 Deno permission model: deny-by-default")
    print("  ✅ Can read: ./sample-data/ only")
    print("  ❌ Network: DENIED")
    print("  ❌ Env vars: DENIED")
    print("  ❌ Subprocesses: DENIED")
    print("  ❌ File writing: DENIED")
    print()

    # Part 1: Show normal analysis works
    print("─" * 60)
    print("  Part 1: Normal analysis in Deno sandbox")
    print("─" * 60)

    output = run_deno_script("analyze")
    print(output)

    # Part 2: Show malicious attempts all fail
    print("\n" + "─" * 60)
    print("  Part 2: Malicious operations — ALL BLOCKED")
    print("─" * 60)

    output = run_deno_script("malicious")
    print(output)

    # Part 3: Agent-driven analysis (LLM generates Deno code)
    print("\n" + "─" * 60)
    print("  Part 3: Agent generates & executes code in Deno sandbox")
    print("─" * 60)

    run_agent(
        system_prompt=(
            "You are a data analyst agent. You can execute TypeScript code in a "
            "Deno sandbox with VERY restricted permissions:\n"
            "- You can ONLY read files from ./sample-data/ using Deno.readTextFile()\n"
            "- NO network access (fetch will fail)\n"
            "- NO environment variable access (Deno.env will fail)\n"
            "- NO subprocess spawning\n"
            "- NO file writing\n"
            "Write clean TypeScript code that reads and analyzes CSV data."
        ),
        user_message=(
            "Analyze ./sample-data/sales_data.csv. Read it with "
            "Deno.readTextFile(), parse the CSV manually, and calculate "
            "total revenue per region (quantity × unit_price). "
            "Print a nice summary table."
        ),
        tools=TOOLS,
        tool_handler=handle_tool,
    )
