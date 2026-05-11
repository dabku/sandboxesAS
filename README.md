# Why Your AI Agent Needs a Sandbox

Code demos and presentation for **"Why Your AI Agent Needs a Sandbox"**.

📺 **[View Presentation](https://dabku.github.io/sandboxesAS/presentation/sandboxes.html)**

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
- Docker — required for demos 3–5b
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

# Demo 5b — list-based subprocess vs shell=True
python demos/demo5b-docker-security/demo.py

# Demo 6 — Deno sandbox
python demos/demo6-deno-sandbox/agent.py

# Demo 7 — Daytona cloud sandbox
python demos/demo7-daytona-sandbox/agent.py
```

