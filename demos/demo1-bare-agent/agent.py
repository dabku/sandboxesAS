"""
Demo 1: Agent with Bash via Function Calling
=============================================
A simple agent that can execute bash commands to analyze data.
This works great — but wait until you see Demo 2...

Usage:
    python demo1-bare-agent/agent.py
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path so we can import shared module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.llm import run_agent, PROJECT_ROOT

# ── Tool definition ─────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": (
                "Execute a bash command and return the output. "
                "Use this to run code, analyze files, install packages, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute",
                    }
                },
                "required": ["command"],
            },
        },
    }
]


# ── Tool implementation ─────────────────────────────────────


def run_bash(command: str) -> str:
    """Execute a bash command and return stdout + stderr."""
    print(f"\n  🔧 Executing: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        print(f"  📤 Output: {output[:300]}{'...' if len(output) > 300 else ''}")
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 30 seconds"
    except Exception as e:
        return f"ERROR: {e}"


def handle_tool(name: str, args: dict) -> str:
    """Dispatch tool calls."""
    if name == "run_bash":
        return run_bash(args["command"])
    return f"Unknown tool: {name}"


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    # A perfectly reasonable data analysis request
    run_agent(
        system_prompt=(
            "You are a helpful data analyst agent. You have access to a bash "
            "tool to execute commands. Use it to analyze files, run Python/pandas "
            "scripts, and answer the user's questions about data. "
            "The data files are in the ./sample-data/ directory."
        ),
        user_message=(
            "Analyze the file ./sample-data/sales_data.csv. "
            "Tell me the total revenue per region (quantity × unit_price). "
            "Use pandas."
        ),
        tools=TOOLS,
        tool_handler=handle_tool,
    )
