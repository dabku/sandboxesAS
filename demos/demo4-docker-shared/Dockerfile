FROM python:3.12-slim

RUN pip install --no-cache-dir pandas

# Each agent gets its own "workspace" directory inside the container
RUN mkdir -p /workspace/agent-a /workspace/agent-b

WORKDIR /workspace
