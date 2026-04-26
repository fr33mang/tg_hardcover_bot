FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --python /usr/local/bin/python3

COPY . .

RUN mkdir -p /data

CMD [".venv/bin/python", "bot.py"]
