#!/bin/bash
# Запуск AstroFin Sentinel Webhook Server

cd "$(dirname "$0")"

# Активация виртуального окружения (если есть)
[ -f .venv/bin/activate ] && source .venv/bin/activate

# Установка зависимостей
pip install -q -r requirements.txt

# Запуск
echo "🚀 Запуск AstroFin Sentinel Webhook..."
uvicorn api.webhook:app --host 0.0.0.0 --port 8000 --reload
