FROM docker.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TKS_GATEWAY_PORT=/dev/ttyUSB0

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install . waitress

EXPOSE 5000
# one process (state lives in memory), waitress with several threads
CMD ["tks-gateway", "web", "--host", "0.0.0.0", "--http-port", "5000"]
