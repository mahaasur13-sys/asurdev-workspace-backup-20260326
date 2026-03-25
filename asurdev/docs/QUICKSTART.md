# 🚀 Quick Start Guide

## 1 минута до первого анализа

```bash
cd ~/asurdevSentinel
source venv/bin/activate
streamlit run ui/dashboard.py
# → http://localhost:8501
```

## 5 минут до API

```bash
cd ~/asurdevSentinel
source venv/bin/activate
uvicorn api.main:app --port 8000
# → http://localhost:8000/docs
```

## Запуск тестов

```bash
cd ~/asurdevSentinel
python tests/run_all_tests.py
```

## Команды run.sh

```bash
./run.sh all           # Все сервисы
./run.sh ui            # Только Streamlit
./run.sh api            # Только FastAPI
./run.sh backtest      # Бэктесты
./run.sh security-scan  # Аудит безопасности
```

## Environment Variables

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
JWT_SECRET=change-me-in-production
DATABASE_URL=postgresql://asurdev:password@localhost:5432/asurdev
```
