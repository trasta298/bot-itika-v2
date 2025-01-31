FROM python:3.11 as build

RUN apt update && apt upgrade -y && apt install -y build-essential curl git clang

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY uv.lock pyproject.toml ./
RUN uv sync --frozen

FROM python:3.11-slim

WORKDIR /workspace

COPY --from=build /.venv /opt/venv

RUN apt update && apt upgrade -y && apt install -y libsndfile1 clang

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY . .

CMD ["python", "app.py"]
