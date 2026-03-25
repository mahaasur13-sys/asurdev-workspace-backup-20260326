"""
Python Base Template — базовый образ для всех Python-агентов.
"""

PYTHON_BASE_TEMPLATE = """\
# syntax=docker/dockerfile:1.7
# ============================================================
# AstroFin Agent Sandbox Base Image
# Python 3.12 + минимальные зависимости
# ============================================================

FROM python:3.12-slim-bookworm

# Метаданные
LABEL maintainer="AstroFin Team"
LABEL version="1.0"
LABEL description="Base image for AstroFin agent sandboxes"

# Минимальная поверхность атаки
RUN apt-get update && aptбор=/var/lib/apt/lists/*

# Установка только необходимых пакетов
RUN apt-get install -y --no-install-recommends \\
    ca-certificates \\
    curl \\
    tzdata \\
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements-sandbox.txt /tmp/requirements-sandbox.txt
RUN pip install --no-cache-dir -r /tmp/requirements-sandbox.txt && \\
    rm /tmp/requirements-sandbox.txt

# Создание пользователя для изоляции
RUN groupadd -r astrofin && useradd -r -g astrofin astrofin

# Рабочая директория
WORKDIR /app

# Копирование только необходимых файлов
COPY --chown=astrofin:astrofin agents/ ./agents/
COPY --chown=astrofin:astrofin swiss_ephemeris/ ./swiss_ephemeris/ 2>/dev/null || true
COPY --chown=astrofin:astrofin utils/ ./utils/
COPY --chown=astrofin:astrofin core/ ./core/ 2>/dev/null || true

# Права только на чтение для кода
RUN chmod 444 agents/*.py agents/**/*.py 2>/dev/null || true

# Переключение на пользователя
USER astrofin

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python3 -c "import sys; sys.exit(0)"

# Entrypoint по умолчанию
ENTRYPOINT ["python3", "-m", "agents.entrypoint"]
CMD ["--help"]
"""

REQUIREMENTS_SANDBOX = """\
# AstroFin Sandbox Requirements
# Минимальный набор для работы агентов

# Core
pydantic>=2.0.0
structlog>=24.0.0

# Async
aiohttp>=3.9.0

# Data
numpy>=1.26.0
scipy>=1.12.0

# Ephemeris
swisseph>=2.10.0

# API Clients
requests>=2.31.0
"""
