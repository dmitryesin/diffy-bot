FROM python:3.13-slim AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN pip install --no-cache-dir uv && uv pip install --no-cache-dir --system . \
    && mkdir -p logs && chown -R 10001:10001 logs

RUN useradd --create-home --uid 10001 solver-bot
USER solver-bot

CMD ["solver-bot"]