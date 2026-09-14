FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --extra dev --no-install-project

COPY src ./src
COPY tests ./tests

RUN uv pip install --python .venv/bin/python --no-deps .


FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY tests ./tests

ENV PATH="/app/.venv/bin:$PATH"

CMD ["pytest"]
