FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --extra dev --no-install-project

COPY src ./src
COPY tests ./tests

RUN uv pip install --python .venv/bin/python --no-deps -e .

CMD ["/app/.venv/bin/pytest"]
