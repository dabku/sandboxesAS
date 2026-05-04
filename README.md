# Why Your AI Agent Needs a Sandbox

Code demos and presentation for **"Why Your AI Agent Needs a Sandbox"**.

📺 **[View Presentation](https://dabku.github.io/sandboxesAS/presentation/sandboxes.html)**

---

## The Problem

AI agents that execute code are powerful — but without proper isolation, they can leak secrets, read arbitrary files, or be hijacked via prompt injection. This repo walks through the attack surface step-by-step and shows how to fix it.

---

## Demos

Each demo builds on the previous one, showing a new vulnerability or improvement.

### 🔴 Attacks

| Demo | What it shows |
|------|--------------|
| [demo1-bare-agent](demos/demo1-bare-agent/) | A simple agent with unrestricted bash access — works fine for happy-path analysis |
| [demo2-file-leak](demos/demo2-file-leak/) | The same agent leaks `.env` secrets via prompt injection hidden in CSV data |
| [demo3-docker-naive](demos/demo3-docker-naive/) | Agent runs in Docker but leaks all environment variables (`DATABASE_URL`, API keys, etc.) |
| [demo4-docker-shared](demos/demo4-docker-shared/) | Two agents share one container — Agent B reads Agent A's confidential files |

### 🟢 Defenses

| Demo | What it shows |
|------|--------------|
| [demo5-docker-per-run](demos/demo5-docker-per-run/) | Fresh Docker container per execution — no secrets, no shared state, read-only data mount |
| [demo6-deno-sandbox](demos/demo6-deno-sandbox/) | Deno's deny-by-default permission model blocks all malicious operations at the runtime level |
| [demo7-daytona-sandbox](demos/demo7-daytona-sandbox/) | Production-grade cloud sandbox (Daytona) — fully isolated environment, simple SDK |

---

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy and fill in your API keys
cp .env.example .env
```

### Requirements
- Python 3.11+
- OpenRouter API key (or any OpenAI-compatible endpoint) — set `OPENROUTER_API_KEY` in `.env`
- Docker — required for demos 3–5
- Deno — required for demo 6 ([install](https://deno.com))
- Daytona API key — required for demo 7 ([get one](https://app.daytona.io/dashboard/keys))

### Running a demo

```bash
# Demo 1 — bare agent (no Docker needed)
python demos/demo1-bare-agent/agent.py

# Demo 2 — prompt injection attack
python demos/demo2-file-leak/agent.py

# Demo 3 — naive Docker (needs Docker)
cd demos/demo3-docker-naive && docker compose up --build

# Demo 4 — shared container (needs Docker)
cd demos/demo4-docker-shared && docker compose up -d && cd ../..
python demos/demo4-docker-shared/orchestrator.py

# Demo 5 — Docker per run
python demos/demo5-docker-per-run/orchestrator.py

# Demo 6 — Deno sandbox
python demos/demo6-deno-sandbox/agent.py

# Demo 7 — Daytona cloud sandbox
python demos/demo7-daytona-sandbox/agent.py
```

---

## Presentation

The [presentation](presentation/sandboxes.html) is a RevealJS slideshow built with [Quarto](https://quarto.org).  
View it live at: **https://dabku.github.io/sandboxesAS/presentation/sandboxes.html**
