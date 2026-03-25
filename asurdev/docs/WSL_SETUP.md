# 🚀 asurdev Sentinel — Установка на WSL Ubuntu 24.04

## Быстрый старт

### 1. Предварительные требования

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Python 3.11+ и Git
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Проверить версию Python
python3 --version  # должен быть 3.11+
```

### 2. Активировать WSL CUDA (если есть NVIDIA GPU)

```bash
# Проверить наличие GPU
nvidia-smi

# Если нет — установить драйверы NVIDIA в Windows
# Скачать с: https://www.nvidia.com/Download/index.aspx
```

### 3. Скопировать проект

**Вариант A: Из Zo Computer**

1. Скачать `asurdevSentinel.tar.gz` из Zo Files
2. В WSL:
```bash
cd ~
cp /mnt/path/to/downloaded/asurdevSentinel.tar.gz .
tar -xzvf asurdevSentinel.tar.gz
cd asurdevSentinel
```

**Вариант B: Git Clone (если есть репозиторий)**

```bash
git clone <repo-url> asurdevSentinel
cd asurdevSentinel
```

### 4. Создать виртуальное окружение

```bash
cd asurdevSentinel

# Создать venv
python3 -m venv venv

# Активировать
source venv/bin/activate

# Обновить pip
pip install --upgrade pip
```

### 5. Установить зависимости

```bash
pip install -r requirements.txt
```

**Если ошибки зависимостей:**

```bash
# Установить системные зависимости
sudo apt install -y \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    swig

pip install -r requirements.txt --no-build-isolation
```

### 6. Установить Ollama (для локальных LLM)

```bash
# Установить Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Скачать модель
ollama pull qwen2.5-coder:32b

# Проверить
ollama list
```

### 7. Запустить

```bash
# API сервер
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Или Streamlit UI (в отдельном терминале)
source venv/bin/activate
streamlit run ui/dashboard.py --server.port 8501
```

### 8. Доступ из Windows

```
API:     http://localhost:8000
Streamlit: http://localhost:8501
```

Открывать в **браузере Windows**, не в WSL!

---

## Docker (опционально)

### Установить Docker в WSL

```bash
# Установить Docker
sudo apt install -y docker.io docker-compose

# Запустить Docker daemon
sudo service docker start

# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Запустить через Docker Compose

```bash
docker-compose up -d
```

---

## Common Issues

### Permission denied при установке pip

```bash
# Не использовать sudo с pip!
pip install --user -r requirements.txt
```

### Ollama не запускается

```bash
# Вручную запустить
ollama serve

# Проверить логи
journalctl -u ollama
```

### Порт занят

```bash
# Найти процесс
lsof -i :8000

# Убить
kill -9 <PID>
```

### WSL2 + CUDA не работает

```bash
# Проверить версию WSL
wsl --version

# Обновить до WSL2
wsl --update
```

---

## Структура проекта

```
asurdevSentinel/
├── agents/           # Агенты (Market, Bull, Bear, Astrologer, etc.)
├── api/              # FastAPI сервер
├── config/           # Промпты и конфиги
├── data/             # Данные (TS signals, ChromaDB)
├── docs/             # Документация
├── dow/              # Теория Доу
├── feedback/         # Система обучения
├── gann/             # Инструменты Ганна
├── andrews/          # Pitchfork Эндрюса
├── memory/           # Vector memory (ChromaDB)
├── quality/          # Quality Protocol
├── rk3576/           # Edge deployment (Jetson/RK3576)
├── security/         # Безопасность
├── tools/            # Coingecko и др.
├── ui/               # Streamlit UI
├── ui_react/         # React UI
├── bot.py            # Telegram бот
└── run.py            # Точка входа
```

---

## Полезные команды

```bash
# Активировать окружение
source venv/bin/activate

# Проверить все агенты
python -c "from agents import *; print('OK')"

# Запустить тесты
pytest tests/ -v

# Запустить линтер
bandit -r . -x venv/

# Бэкап базы данных
pg_dump asurdev > backup.sql
```

---

## Следующие шаги

1. ✅ Установить WSL Ubuntu 24.04
2. ✅ Скопировать проект
3. ✅ Создать venv и установить зависимости
4. 🔲 Настроить Coingecko API (бесплатный)
5. 🔲 Запустить Ollama с моделью
6. 🔲 Протестировать API
7. 🔲 Настроить Telegram бот (опционально)
