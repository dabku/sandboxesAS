# Minimal container for executing agent-generated code
# This gets spun up fresh for EVERY code execution, then destroyed.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pandas

WORKDIR /sandbox

# No CMD — the orchestrator passes the command at runtime
