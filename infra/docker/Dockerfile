# syntax=docker/dockerfile:1
# Stage 1: Build Next.js static export
FROM node:20-alpine AS node-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is passed as a build arg
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Install Python deps
FROM python:3.11-slim AS python-builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --target /venv -r requirements.txt && \
    uv pip install --target /venv https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

# Stage 3: Runtime (non-root)
FROM python:3.11-slim
COPY --from=python-builder /venv /venv
ENV PYTHONPATH=/venv
WORKDIR /app
COPY app/ app/
COPY --from=node-builder /frontend/out ./static
RUN useradd -m clar && chown -R clar /app
USER clar
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
