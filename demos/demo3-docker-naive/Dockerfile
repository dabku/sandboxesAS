FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir openai pandas

COPY agent.py .

# Data is mounted via docker-compose volume, not copied
CMD ["python", "agent.py"]
