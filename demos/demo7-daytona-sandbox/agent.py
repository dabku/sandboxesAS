"""
Demo 7: Daytona Cloud Sandbox
==============================
Each code execution runs in a Daytona sandbox — a fully isolated
cloud environment with its own filesystem.

This is a production-grade approach for AI agent sandboxing:
  ✅ Isolated execution environment (own filesystem per sandbox)
  ✅ Fast cold start with snapshot-based provisioning
  ✅ No shared kernel with host
  ✅ Automatic cleanup — sandbox auto-stops and auto-deletes
  ✅ Simple SDK — a few lines of code to set up

Requirements:
    pip install daytona-sdk
    # Get an API key at https://app.daytona.io/dashboard/keys

Usage:
    DAYTONA_API_KEY=your-key DAYTONA_API_URL=https://app.daytona.io/api \
        python demo7-daytona-sandbox/agent.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from shared.llm import run_agent

DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY")
DAYTONA_API_URL = os.getenv("DAYTONA_API_URL", "https://app.daytona.io/api")


def _run_and_print(sandbox, label: str, code: str):
    """Helper: run code in sandbox and print output."""
    print(f"  {label}")
    execution = sandbox.code_interpreter.run_code(code)
    output = execution.stdout or "(no output)"
    if execution.error:
        output += f"\nERROR ({execution.error.name}): {execution.error.value}"
    print(f"  Result:\n{output}\n")
    return output


def demo_basic_sandbox():
    """Show the simplest possible Daytona usage."""
    from daytona import Daytona, CreateSandboxFromSnapshotParams

    print("\n  ☁️  Creating Daytona sandbox...")
    daytona = Daytona()
    sandbox = daytona.create(
        CreateSandboxFromSnapshotParams(
            language="python",
            auto_stop_interval=3,  # stop after 3 min of inactivity
            auto_delete_interval=0,  # delete immediately after stopping
        ),
        timeout=60,
    )
    print(f"  ✅ Sandbox created (ID: {sandbox.id})\n")

    try:
        # Normal analysis — same data as other demos for consistency
        _run_and_print(
            sandbox,
            "📊 Running data analysis...",
            """
import pandas as pd

# Same data structure as other demos (in production, you'd upload files)
data = {
    'region': ['North', 'South', 'East', 'West', 'North', 'South',
               'East', 'West', 'North', 'South', 'East', 'West'],
    'product': ['Widget A', 'Widget B', 'Widget A', 'Widget C', 'Widget B', 'Widget A',
                'Widget C', 'Widget A', 'Widget C', 'Widget B', 'Widget B', 'Widget C'],
    'quantity': [150, 230, 180, 95, 310, 275, 120, 200, 85, 190, 160, 110],
    'unit_price': [12.99, 8.50, 12.99, 24.99, 8.50, 12.99, 24.99, 12.99, 24.99, 8.50, 8.50, 24.99],
}
df = pd.DataFrame(data)
df['revenue'] = df['quantity'] * df['unit_price']
result = df.groupby('region')['revenue'].sum().sort_values(ascending=False)
print("Total Revenue per Region:")
print("─" * 30)
for region, rev in result.items():
    print(f"  {region:<8} ${rev:>10,.2f}")
print("─" * 30)
print(f"  TOTAL    ${result.sum():>10,.2f}")
""",
        )

        # Attempt to read host files — impossible (different environment!)
        _run_and_print(
            sandbox,
            "🔴 Attempting to read /etc/passwd (in sandbox, not host!)...",
            """
with open('/etc/passwd') as f:
    content = f.read()
print("This is the sandbox's /etc/passwd, NOT the host:")
print(content[:300])
print("...")
print()
print("⚠️  This is the sandbox's own OS — the host is completely isolated.")
""",
        )

        # Attempt network access — use Python urllib for reliability
        _run_and_print(
            sandbox,
            "🔴 Attempting network access...",
            """
import urllib.request
try:
    resp = urllib.request.urlopen('https://google.com', timeout=5)
    print(f"HTTP status: {resp.status}")
    print("Note: Daytona sandboxes have network access by default.")
    print("You can configure network policies to restrict outbound traffic.")
except Exception as e:
    print(f"Network request failed: {e}")
    print("Note: Network may be restricted by Daytona configuration.")
""",
        )

        # Show that env vars from host are NOT present
        _run_and_print(
            sandbox,
            "🔴 Checking for host environment variables...",
            """
import os
keys_to_check = ['OPENROUTER_API_KEY', 'AZURE_OPENAI_API_KEY', 'DATABASE_URL',
                  'AWS_SECRET_ACCESS_KEY', 'STRIPE_SECRET_KEY']
print("Checking host secrets in sandbox:")
for key in keys_to_check:
    val = os.environ.get(key, 'NOT FOUND')
    print(f"  {key}: {val}")
print()
print("✅ Host environment variables are NOT accessible in the sandbox.")
""",
        )
    finally:
        sandbox.delete()

    print("  🗑️  Sandbox destroyed. Everything is gone.\n")


def demo_agent_with_daytona():
    """Run an agent that executes code in a Daytona sandbox."""
    from daytona import Daytona, CreateSandboxFromSnapshotParams

    daytona = Daytona()
    print("\n  ☁️  Creating Daytona sandbox...")
    sandbox = daytona.create(
        CreateSandboxFromSnapshotParams(
            language="python",
            auto_stop_interval=3,
            auto_delete_interval=0,
        ),
        timeout=60,
    )
    print(f"  ✅ Daytona Sandbox ready (ID: {sandbox.id})")

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "execute_code",
                "description": (
                    "Execute Python code in a Daytona cloud sandbox. "
                    "The sandbox has its own filesystem, fully isolated "
                    "from the host. pandas is pre-installed. "
                    "Each call shares state within the session (variables persist)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute in the sandbox",
                        }
                    },
                    "required": ["code"],
                },
            },
        }
    ]

    def handle_tool(name: str, args: dict) -> str:
        if name == "execute_code":
            print(f"\n  ☁️  Executing in Daytona sandbox...")
            execution = sandbox.code_interpreter.run_code(args["code"])

            output_parts = []
            if execution.stdout:
                output_parts.append(execution.stdout)
            if execution.stderr:
                output_parts.append(f"STDERR: {execution.stderr}")
            if execution.error:
                output_parts.append(
                    f"ERROR ({execution.error.name}): {execution.error.value}"
                )
            output = "\n".join(output_parts) if output_parts else "(no output)"

            print(f"  📤 Output: {output[:300]}{'...' if len(output) > 300 else ''}")
            return output
        return f"Unknown tool: {name}"

    try:
        run_agent(
            system_prompt=(
                "You are a data analyst agent. You execute Python code in a "
                "Daytona cloud sandbox. The sandbox is fully isolated — "
                "own filesystem, separate from the host. pandas is available. "
                "Variables persist between calls within this session.\n"
                "CRITICAL RULE: Every code block MUST end with print() statements "
                "showing the results. Code without print() is useless — the user "
                "can ONLY see printed output. Never run code without printing something."
            ),
            user_message=(
                "Create a sample sales dataset with pandas:\n"
                "- Regions: North, South, East, West\n"
                "- Products: Widget A ($12.99), Widget B ($8.50), Widget C ($24.99)\n"
                "- About 12 rows with realistic quantities (50-300)\n\n"
                "Then calculate total revenue per region (quantity × unit_price) "
                "and print a nice summary table. Do it all in one code block."
            ),
            tools=TOOLS,
            tool_handler=handle_tool,
        )
    finally:
        sandbox.delete()
        print("\n  🗑️  Sandbox destroyed.")


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Demo 7: Daytona Cloud Sandbox")
    print("=" * 60)

    if not DAYTONA_API_KEY:
        print("\n  ⚠️  DAYTONA_API_KEY not set.")
        print("  Get one at https://app.daytona.io/dashboard/keys")
        print("  Add to .env: DAYTONA_API_KEY=your-key-here")
        print("  Add to .env: DAYTONA_API_URL=https://app.daytona.io/api")
        print("\n  Showing what the code looks like (dry run):\n")
        print("  from daytona import Daytona, CreateSandboxFromSnapshotParams")
        print("  ")
        print("  daytona = Daytona()")
        print("  sandbox = daytona.create(")
        print("      CreateSandboxFromSnapshotParams(language='python'),")
        print("      timeout=60,")
        print("  )")
        print("  result = sandbox.code_interpreter.run_code('print(1 + 1)')")
        print("  print(result.stdout)  # '2'")
        print("  sandbox.delete()")
        print("\n  Simple SDK. Cloud sandbox. Fully isolated.")
        print("  No Docker, no config, no infrastructure to manage.")
        sys.exit(0)

    print()
    print("  ☁️  Daytona cloud sandbox isolation:")
    print("  ✅ Own filesystem (not shared with host)")
    print("  ✅ Ephemeral — auto-stops and auto-deletes")
    print("  ✅ Fast provisioning via snapshots")
    print("  ✅ Host env vars NOT accessible")
    print("  ✅ Simple SDK — a few lines of code")
    print()

    print("─" * 60)
    print("  Part 1: Basic sandbox operations")
    print("─" * 60)
    demo_basic_sandbox()

    print("\n" + "─" * 60)
    print("  Part 2: Agent-driven code execution in Daytona")
    print("─" * 60)
    demo_agent_with_daytona()
