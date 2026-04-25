# syntax=docker/dockerfile:1

# Stage 1: Python deps
FROM python:3.11-slim AS builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --target /venv -r requirements.txt && \
    uv pip install --target /venv https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

# Stage 2: Runtime (non-root)
FROM python:3.11-slim
COPY --from=builder /venv /venv
ENV PYTHONPATH=/venv
WORKDIR /app
COPY app/ app/
RUN useradd -m clar && chown -R clar /app
USER clar
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
