"""
Demo 5b: Shell Escape — subprocess.run(list) vs shell=True
"""

import os
import subprocess
import sys
from pathlib import Path

SANDBOX_IMAGE = "sandbox-runner"
DATA_DIR = str(Path(__file__).resolve().parent.parent / "sample-data")

os.environ["SUPER_SECRET_API_KEY"] = "sk-host-secret-12345-SHOULD-NEVER-LEAK"

PAYLOAD = "'; echo \"LEAKED=$SUPER_SECRET_API_KEY\" >&2; echo '"


def run_safe(command: str) -> str:
    """SAFE: list-based, no host shell."""
    r = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--memory", "256m",
         "--read-only", "--tmpfs", "/tmp:size=64m", "--tmpfs", "/sandbox:size=64m",
         "-v", f"{DATA_DIR}:/data:ro",
         SANDBOX_IMAGE, "bash", "-c", command],
        capture_output=True, text=True, timeout=30,
    )
    return (r.stdout + r.stderr).strip() or "(no output)"


def run_unsafe(command: str) -> str:
    """UNSAFE: shell=True, host shell parses everything."""
    r = subprocess.run(
        f"docker run --rm --network none --memory 256m "
        f"--read-only --tmpfs /tmp:size=64m --tmpfs /sandbox:size=64m "
        f"-v {DATA_DIR}:/data:ro "
        f"{SANDBOX_IMAGE} bash -c '{command}'",
        shell=True, capture_output=True, text=True, timeout=30,
    )
    return (r.stdout + r.stderr).strip() or "(no output)"


if __name__ == "__main__":
    # Build image
    demo_dir = Path(__file__).resolve().parent
    print("🔨 Building sandbox image...")
    b = subprocess.run(["docker", "build", "-t", SANDBOX_IMAGE, "."],
                       cwd=str(demo_dir), capture_output=True, text=True)
    if b.returncode != 0:
        print(f"❌ Build failed:\n{b.stderr}")
        sys.exit(1)
    print("✅ Image built.\n")

    print(f"Payload: {PAYLOAD!r}\n")

    print("── SAFE: subprocess.run([list]) ──")
    print(run_safe(PAYLOAD))
    print()

    print("── UNSAFE: subprocess.run(string, shell=True) ──")
    print(run_unsafe(PAYLOAD))
    print()

    print("🔑 The list-based call keeps the payload inside Docker.")
    print("   shell=True lets the payload break quotes and leak host secrets.")
