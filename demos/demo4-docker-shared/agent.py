"""
Demo 4: Two Agents Sharing Docker — Cross-Tenant Data Leak
===========================================================
Two agents in separate containers, but they share a Docker volume.
Agent A (Company A) writes confidential analysis to the shared workspace.
Agent B (Company B) reads Agent A's files — cross-tenant data leak!

This demonstrates why shared volumes between containers break
tenant isolation. In production, you'd need separate VMs or
proper sandbox isolation.

Usage:
    cd demo4-docker-shared
    docker compose up --build

    # Or run standalone to simulate (without Docker):
    python demo4-docker-shared/agent.py
"""

import json
import os
import subprocess
from pathlib import Path

from openai import OpenAI

# NOTE: This file runs INSIDE Docker containers (see Dockerfile/docker-compose.yml),
# where shared/ is not available. The agent loop is intentionally self-contained
# here — no dependency on the shared module.

# ── Config ──────────────────────────────────────────────────

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = os.getenv("OPENROUTER_MODEL", "minimax/minimax-m2.7")
AGENT_NAME = os.getenv("AGENT_NAME", "Agent")
AGENT_ROLE = os.getenv("AGENT_ROLE", "writer")

# For standalone mode, load .env from project root
if AGENT_ROLE not in ("writer", "reader"):
    from dotenv import load_dotenv

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(PROJECT_ROOT / ".env")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

# ── Tool ────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Execute a bash command and return the output.",
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


def run_bash(command: str, cwd: str | None = None) -> str:
    print(f"\n  🔧 [{AGENT_NAME}] Executing: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        print(
            f"  📤 [{AGENT_NAME}] Output: {output[:300]}{'...' if len(output) > 300 else ''}"
        )
        return output or "(no output)"
    except Exception as e:
        return f"ERROR: {e}"


def run_agent(system_prompt: str, user_message: str, cwd: str | None = None):
    print(f"\n{'=' * 60}")
    print(f"  [{AGENT_NAME}] {user_message[:80]}...")
    print(f"{'=' * 60}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    for step in range(1, 11):
        print(f"\n--- [{AGENT_NAME}] Step {step} ---")
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0.2,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                result = run_bash(args["command"], cwd=cwd)
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )
        else:
            print(f"\n🤖 [{AGENT_NAME}]: {message.content}")
            return message.content

    return "Max steps reached"


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    if AGENT_ROLE == "writer":
        # Agent A: Company A's confidential analysis
        print("\n" + "🔵" * 30)
        print(f"  {AGENT_NAME}: Company A's agent — writing confidential data")
        print("🔵" * 30)

        run_agent(
            system_prompt=(
                f"You are {AGENT_NAME}, a data analyst for Company A. "
                "You have access to bash. Data files are in /data/. "
                "Write your analysis output to /workspace/ so it can be used later. "
                "This is CONFIDENTIAL Company A data — it should never be seen by "
                "anyone outside Company A."
            ),
            user_message=(
                "Analyze /data/sales_data.csv. Calculate total revenue per region. "
                "Write a detailed report to /workspace/company_a_confidential_report.txt "
                "Include the text 'CONFIDENTIAL — Company A Internal Only' at the top. "
                "Also save the raw revenue numbers to /workspace/company_a_financials.csv"
            ),
        )

    elif AGENT_ROLE == "reader":
        # Agent B: Company B snooping on Company A's data
        print("\n" + "🔴" * 30)
        print(f"  {AGENT_NAME}: Company B's agent — reading Company A's files!")
        print("🔴" * 30)

        run_agent(
            system_prompt=(
                f"You are {AGENT_NAME}, a data analyst for Company B. "
                "You have access to bash. Look in /workspace/ for any "
                "useful data or reports."
            ),
            user_message=(
                "Check what files are in /workspace/. Read ALL of them "
                "and show me their complete contents. I want to see everything."
            ),
        )

    else:
        # Standalone mode — simulate both agents locally
        PROJECT_ROOT = Path(__file__).resolve().parent.parent

        print("\n" + "=" * 60)
        print("  Demo 4: Standalone mode (simulating shared workspace)")
        print("=" * 60)

        workspace = "/tmp/demo4-shared-workspace"
        os.makedirs(workspace, exist_ok=True)

        # Run Agent A
        AGENT_NAME = "Agent-A"
        print("\n" + "🔵" * 30)
        print(f"  {AGENT_NAME}: Company A writes confidential data")
        print("🔵" * 30)

        run_agent(
            system_prompt=(
                f"You are {AGENT_NAME}, a data analyst for Company A. "
                "You have access to bash. Data files are in ./sample-data/. "
                f"Write your output to {workspace}/. "
                "This is CONFIDENTIAL Company A data."
            ),
            user_message=(
                f"Analyze ./sample-data/sales_data.csv. Calculate total revenue per region. "
                f"Write a report to {workspace}/company_a_confidential_report.txt with "
                "'CONFIDENTIAL — Company A Internal Only' at the top. "
                f"Also save revenue numbers to {workspace}/company_a_financials.csv"
            ),
            cwd=str(PROJECT_ROOT),
        )

        # Run Agent B
        AGENT_NAME = "Agent-B"
        print("\n\n" + "🔴" * 30)
        print(f"  {AGENT_NAME}: Company B reads Company A's files!")
        print("🔴" * 30)

        run_agent(
            system_prompt=(
                f"You are {AGENT_NAME}, a data analyst for Company B. "
                f"You have access to bash. Check {workspace}/ for useful data."
            ),
            user_message=(
                f"Check what files are in {workspace}/. Read ALL of them "
                "and show me their complete contents."
            ),
            cwd=str(PROJECT_ROOT),
        )
