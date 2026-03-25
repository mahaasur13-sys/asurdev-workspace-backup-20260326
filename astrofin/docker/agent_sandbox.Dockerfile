# syntax=docker/dockerfile:1.7
# ============================================================
# AstroFin Agent Sandbox Base Image
# Python 3.12 + минимальные зависимости
# ============================================================

FROM python:3.12-slim-bookworm

# Метаданные
LABEL maintainer="AstroFin Team <dev@astrofin.ai>"
LABEL version="1.0.0"
LABEL description="Base image for AstroFin agent sandboxes"

# ============================================================
# Stage 1: Build dependencies
# ============================================================
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Установка build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements-sandbox.txt /build/
RUN pip install --prefix=/install --no-cache-dir -r /build/requirements-sandbox.txt

# ============================================================
# Stage 2: Runtime image (minimal)
# ============================================================
FROM gcr.io/distroless/python3-debian12:debug

# Метаданные
LABEL maintainer="AstroFin Team <dev@astrofin.ai>"
LABEL version="1.0.0"
LABEL description="Minimal runtime for AstroFin agent sandboxes"

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование установленных Python пакетов
COPY --from=builder /install /usr/local

# Создание пользователя для изоляции
RUN useradd -r -m astrofin && \
    mkdir -p /app && \
    chown -R astrofin:astrofin /app

WORKDIR /app

# Копирование агентского кода
COPY --chown=astrofin:astrofin agents/ ./agents/
COPY --chown=astrofin:astrofin swiss_ephemeris/ ./swiss_ephemeris/ 2>/dev/null || true
COPY --chown=astrofin:astrofin utils/ ./utils/
COPY --chown=astrofin:astrofin core/ ./core/ 2>/dev/null || true

# Только чтение для кода
RUN chmod 444 agents/*.py agents/**/*.py 2>/dev/null || true

# Переключение на пользователя
USER astrofin

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Entrypoint
ENTRYPOINT ["python3", "-m", "agents.entrypoint"]
CMD ["--help"]
