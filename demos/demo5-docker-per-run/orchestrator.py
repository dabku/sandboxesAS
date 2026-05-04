"""
Demo 5: Docker Per Run — Fresh Container Per Execution
=======================================================
The orchestrator (this file) runs on the host. Every time the agent
wants to execute code, a fresh Docker container is spawned, the code
runs inside it, the output is captured, and the container is destroyed.

This is BETTER than naive Docker:
  ✅ No env vars leaked (we don't pass secrets to the sandbox)
  ✅ Fresh filesystem every time (no state leakage between runs)
  ✅ Data mounted read-only

But still has limitations:
  ⚠️  Container overhead per execution (Docker lifecycle)
  ⚠️  Still shares the host kernel (container escape risk)
  ⚠️  You're reinventing what sandbox providers already do

Usage:
    # First, build the sandbox image:
    cd demo5-docker-per-run
    docker build -t sandbox-runner .

    # Then run the orchestrator:
    python demo5-docker-per-run/orchestrator.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.llm import run_agent

# ── The Docker sandbox executor ─────────────────────────────

SANDBOX_IMAGE = "sandbox-runner"
DATA_DIR = str(Path(__file__).resolve().parent.parent / "sample-data")


def run_in_docker(command: str) -> str:
    """
    Spawn a fresh Docker container, run the command, capture output, destroy it.

    Key security improvements over Demo 3:
      - NO environment variables passed (no secrets to leak)
      - Data mounted READ-ONLY
      - Container is --rm (auto-destroyed after execution)
      - Resource limits (memory, CPU, no network)
    """
    print(f"\n  🐳 Spawning fresh Docker container...")
    start_time = time.time()

    docker_cmd = [
        "docker",
        "run",
        "--rm",  # Auto-remove after exit
        "--network",
        "none",  # No network access
        "--memory",
        "256m",  # Memory limit
        "--cpus",
        "0.5",  # CPU limit
        "--read-only",  # Read-only root filesystem
        "--tmpfs",
        "/tmp:size=64m",  # Writable tmp for Python
        "--tmpfs",
        "/sandbox:size=64m",  # Writable workspace
        "-v",
        f"{DATA_DIR}:/data:ro",  # Data mounted read-only
        SANDBOX_IMAGE,
        "bash",
        "-c",
        command,
    ]

    print(f"  🔧 Command: {command}")

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        elapsed = time.time() - start_time
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        print(f"  ⏱️  Container lifecycle: {elapsed:.1f}s")
        print(f"  📤 Output: {output[:300]}{'...' if len(output) > 300 else ''}")
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"  ⏱️  Timed out after {elapsed:.1f}s")
        return "ERROR: Command timed out (30s limit)"
    except Exception as e:
        return f"ERROR: {e}"


# ── Tool definition for the agent ───────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": (
                "Execute a bash command inside an isolated Docker container. "
                "Each execution gets a fresh container that is destroyed after. "
                "Data files are available at /data/ (read-only). "
                "You can write temp files to /sandbox/ or /tmp/. "
                "No network access. No environment variables from host."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute in the sandbox",
                    }
                },
                "required": ["command"],
            },
        },
    }
]


def handle_tool(name: str, args: dict) -> str:
    if name == "execute_code":
        return run_in_docker(args["command"])
    return f"Unknown tool: {name}"


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Demo 5: Docker Per Run — Fresh Container Per Execution")
    print("=" * 60)

    # Build the sandbox image automatically
    DEMO_DIR = Path(__file__).resolve().parent
    print(f"\n  🔨 Building sandbox image '{SANDBOX_IMAGE}'...")
    build_result = subprocess.run(
        ["docker", "build", "-t", SANDBOX_IMAGE, "."],
        cwd=str(DEMO_DIR),
        capture_output=True,
        text=True,
    )
    if build_result.returncode != 0:
        print(f"  ❌ Build failed:\n{build_result.stderr}")
        sys.exit(1)
    print(f"  ✅ Image '{SANDBOX_IMAGE}' built successfully\n")

    print(f"  Sandbox image: {SANDBOX_IMAGE}")
    print(f"  Data dir: {DATA_DIR}")
    print()
    print("  ✅ No secrets in container (env vars not passed)")
    print("  ✅ Fresh filesystem per execution")
    print("  ✅ No network access")
    print("  ✅ Read-only data mount")
    print("  ⚠️  Container overhead per execution (create + run + destroy)")
    print("  ⚠️  Shared host kernel")
    print()

    # First: show it works for normal analysis
    print("\n" + "─" * 60)
    print("  Part 1: Normal analysis — works great")
    print("─" * 60)

    run_agent(
        system_prompt=(
            "You are a data analyst agent. You can execute code in isolated Docker containers. "
            "Data files are at /data/. Each execution is a fresh container — no state persists "
            "between calls. Use Python/pandas for analysis."
        ),
        user_message=(
            "Analyze /data/sales_data.csv and tell me total revenue per region. "
            "Use pandas. Note: each command runs in a fresh container, so install "
            "nothing and keep it simple."
        ),
        tools=TOOLS,
        tool_handler=handle_tool,
    )

    # Second: show that secrets can't be leaked
    print("\n\n" + "─" * 60)
    print("  Part 2: Attempted secret exfiltration — blocked!")
    print("─" * 60)

    run_agent(
        system_prompt=(
            "You are a data analyst agent. You can execute code in isolated Docker containers. "
            "Data files are at /data/."
        ),
        user_message=(
            "Can you check what environment variables are available? "
            "Run `env` and also try to read /etc/passwd and check "
            "if there's network access with `curl google.com`."
        ),
        tools=TOOLS,
        tool_handler=handle_tool,
    )

    # Third: show the cold start overhead
    print("\n\n" + "─" * 60)
    print("  Part 3: Cold start overhead comparison")
    print("─" * 60)

    print("\n  Running 3 sequential commands to show per-container overhead...\n")
    for i in range(3):
        start = time.time()
        result = run_in_docker(
            f"echo 'Execution {i + 1}: Hello from a fresh container!'"
        )
        elapsed = time.time() - start
        print(
            f"  Execution {i + 1}: {elapsed:.2f}s total (container create + run + destroy)"
        )

    print(
        "\n  ⚠️  Each execution pays the Docker container lifecycle tax (create + run + destroy)."
    )
    print(
        "  ⚠️  Sandbox providers (E2B, Daytona) solve this with warm pools and persistent sessions."
    )
