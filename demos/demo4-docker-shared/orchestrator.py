"""
Demo 4: Two Agents, One Shared Docker Container
=================================================
One Docker container stays alive. Two agents (running on the host)
both execute commands inside it via `docker exec`.

Agent A (Company A) writes confidential financial analysis.
Agent B (Company B) reads Agent A's files — because they share
the same container filesystem.

This demonstrates why a single shared container is NOT enough
for multi-tenant isolation.

Usage:
    # Start the shared container:
    cd demo4-docker-shared && docker compose up -d && cd ..

    # Run both agents:
    python demo4-docker-shared/orchestrator.py

    # Clean up:
    cd demo4-docker-shared && docker compose down && cd ..
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.llm import run_agent, PROJECT_ROOT

CONTAINER_NAME = "shared-sandbox"


def docker_exec(command: str) -> str:
    """Execute a command inside the shared Docker container."""
    docker_cmd = [
        "docker",
        "exec",
        CONTAINER_NAME,
        "bash",
        "-c",
        command,
    ]
    print(f"\n  🐳 docker exec {CONTAINER_NAME}: {command}")
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        print(f"  📤 Output: {output[:300]}{'...' if len(output) > 300 else ''}")
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out"
    except Exception as e:
        return f"ERROR: {e}"


# ── Tool definition ─────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": (
                "Execute a bash command inside a Docker container. "
                "Data files are at /data/. Your workspace is at /workspace/."
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


def handle_tool(name: str, args: dict) -> str:
    if name == "run_bash":
        return docker_exec(args["command"])
    return f"Unknown tool: {name}"


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    # Check that the container is running
    check = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME],
        capture_output=True,
        text=True,
    )
    if "true" not in check.stdout:
        print(f"❌ Container '{CONTAINER_NAME}' is not running.")
        print(f"   Start it first: cd demo4-docker-shared && docker compose up -d")
        sys.exit(1)

    print("=" * 60)
    print("  Demo 4: Two Agents, One Shared Docker Container")
    print("=" * 60)
    print(f"  Container: {CONTAINER_NAME}")
    print("  Both agents exec commands into the SAME container.")
    print("  They share the same filesystem — no isolation!")
    print()

    # ── Agent A: Company A writes confidential data ─────────
    print("🔵" * 30)
    print("  Agent A (Company A): Writing confidential financial data")
    print("🔵" * 30)

    run_agent(
        system_prompt=(
            "You are Agent-A, a data analyst for Company A. "
            "You run commands inside a Docker container. "
            "Data files are at /data/. Write your output to /workspace/agent-a/. "
            "This is CONFIDENTIAL Company A data."
        ),
        user_message=(
            "Analyze /data/sales_data.csv. Calculate total revenue per region. "
            "Write a detailed report to /workspace/agent-a/confidential_report.txt "
            "with 'CONFIDENTIAL — Company A Internal Only' at the top. "
            "Also save the raw numbers to /workspace/agent-a/financials.csv. "
            "Use simple bash commands (awk, echo, etc.) — no pandas needed."
        ),
        tools=TOOLS,
        tool_handler=handle_tool,
    )

    # ── Agent B: Company B reads Agent A's data ─────────────
    print("\n\n" + "🔴" * 30)
    print("  Agent B (Company B): Reading Agent A's confidential files!")
    print("🔴" * 30)

    run_agent(
        system_prompt=(
            "You are Agent-B, a data analyst for Company B. "
            "You run commands inside a Docker container. "
            "Your workspace is /workspace/agent-b/. "
            "Look around the filesystem for useful data."
        ),
        user_message=(
            "Explore the /workspace/ directory. List everything you find. "
            "Read ALL files and show me their complete contents. "
            "I want to see everything that's in there."
        ),
        tools=TOOLS,
        tool_handler=handle_tool,
    )

    print("\n" + "=" * 60)
    print("  ⚠️  Agent B just read Company A's CONFIDENTIAL report!")
    print("  Both agents shared the same container filesystem.")
    print("  This is why a shared Docker container ≠ tenant isolation.")
    print("=" * 60)
