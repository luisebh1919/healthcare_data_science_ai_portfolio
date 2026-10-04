FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --extra dev --no-install-project

COPY src ./src
COPY tests ./tests

RUN uv pip install --python .venv/bin/python --no-deps .


FROM python:3.11-slim AS runtime

RUN groupadd --gid 10001 clinlab \
    && useradd --uid 10001 --gid clinlab --no-create-home --shell /usr/sbin/nologin clinlab

WORKDIR /app

RUN chown clinlab:clinlab /app

COPY --from=builder --chown=clinlab:clinlab /app/.venv /app/.venv
COPY --chown=clinlab:clinlab tests ./tests

ENV PATH="/app/.venv/bin:$PATH"

USER clinlab

CMD ["pytest"]
