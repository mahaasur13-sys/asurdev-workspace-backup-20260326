# 🚀 asurdev Sentinel — Полное руководство по установке

## Pop!_OS 24.04 NVIDIA Edition

**Версия:** 1.0  
**Дата:** Март 2026  
**Уровень:** Для новичков (пошагово)

---

## 📑 Содержание

1. [Что такое asurdev Sentinel?](#1-что-такое-asurdev-sentinel)
2. [Требования к оборудованию](#2-требования-к-оборудованию)
3. [Архитектура системы](#3-архитектура-системы)
4. [Глава 1: Установка Pop!_OS](#глава-1-установка-pop_os)
5. [Глава 2: Установка драйверов NVIDIA](#глава-2-установка-драйверов-nvidia)
6. [Глава 3: Установка Docker](#глава-3-установка-docker)
7. [Глава 4: Установка Ollama](#глава-4-установка-ollama)
8. [Глава 5: Клонирование и запуск](#глава-5-клонирование-и-запуск)
9. [Глава 6: Запуск и первое использование](#глава-6-запуск-и-первое-использование)
10. [Устранение проблем](#устранение-проблем)
11. [Быстрые команды](#быстрые-команды)

---

## 1. Что такое asurdev Sentinel?

**asurdev Sentinel** — это мультиагентная система для анализа криптовалют.

```
┌─────────────────────────────────────────────────────────────┐
│                    asurdev SENTINEL                        │
├─────────────────────────────────────────────────────────────┤
│  🤖 Агенты анализа:                                        │
│     • Market Analyst — технический анализ                   │
│     • Bull/Bear Researcher — поиск аргументов за/против    │
│     • Astrologer — астрологический анализ                  │
│     • Gann Agent — анализ по Ганну                         │
│     • Andrews Agent — метод Эндрюса                         │
│     • Dow Agent — теория Доу                               │
│     • Synthesizer — финальная рекомендация                │
├─────────────────────────────────────────────────────────────┤
│  📊 Источники данных:                                      │
│     • CoinGecko API — рыночные данные                      │
│     • PyEphem — астрологические расчёты                   │
│     • Timing Solution — циклы (опционально)                │
├─────────────────────────────────────────────────────────────┤
│  🎯 Результат:                                            │
│     • C.L.E.A.R. — структурированная рекомендация         │
│     • Quality Protocol — оценка качества                   │
│     • Self-improving — обучение на своих сделках           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Требования к оборудованию

### Минимальные требования

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| CPU | Intel i5 8th / AMD Ryzen 5 3000 | Intel i5 12th+ / AMD Ryzen 5 5000+ |
| RAM | 16 ГБ | 32 ГБ |
| GPU | NVIDIA GTX 1060 6GB | NVIDIA RTX 3060 12GB |
| Диск | 256 ГБ SSD | 512 ГБ+ NVMe SSD |
| OS | Pop!_OS 24.04 NVIDIA | Pop!_OS 24.04 NVIDIA |

### Почему Pop!_OS?

- ✅ NVIDIA-драйверы предустановлены
- ✅ CUDA 12.x работает из коробки
- ✅ Docker + NVIDIA Container Toolkit одной командой
- ✅ Стабильность 24/7

---

## 3. Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                    asurdev SENTINEL                        │
│                    ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│  │  User     │───▶│ Dashboard │───▶│ Sentinel  │          │
│  │  (You)    │◀───│ (NiceGUI) │◀───│  Core     │          │
│  └───────────┘    └───────────┘    └─────┬─────┘          │
│                                           │                 │
│         ┌─────────────────────────────────┼───────────┐   │
│         │                                 │           │   │
│         ▼                                 ▼           ▼   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────┐       │
│  │   Market    │   │   Bull /    │   │  Astro  │       │
│  │   Analyst   │   │   Bear      │   │  Agent  │       │
│  └─────────────┘   └─────────────┘   └─────────┘       │
│                                                             │
│         ┌─────────────────────────────────┐               │
│         │                                 │               │
│         ▼                                 ▼               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────┐       │
│  │    Gann     │   │  Andrews    │   │   Dow   │       │
│  │   Agent     │   │   Agent     │   │  Agent  │       │
│  └─────────────┘   └─────────────┘   └─────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────┐              │
│  │            Synthesizer (C.L.E.A.R.)     │              │
│  └─────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Глава 1: Установка Pop!_OS

### Шаг 1.1: Скачивание ISO

1. Открой браузер и перейди на [pop.system76.com](https://pop.system76.com)
2. Нажми **Download**
3. Выбери **NVIDIA** версию ( важно! )
4. Скачай файл `pop-os_24.04_amd64_nvidia_*.iso` (~3.4 ГБ)

### Шаг 1.2: Создание загрузочной флешки

#### Windows (рекомендуется):

1. Скачай [Rufus](https://rufus.ie/) (бесплатно)
2. Вставь флешку (минимум 8 ГБ)
3. Запусти Rufus
4. Выбери скачанный ISO
5. Нажми **Старт**
6. Дождись завершения (~10-15 минут)

#### Linux:

```bash
# Замени /dev/sdX на букву твоей флешки (проверь через lsblk)
sudo dd if=~/Downloads/pop-os_*.iso of=/dev/sdX bs=4M status=progress
sync
```

### Шаг 1.3: Настройка BIOS

1. **Выключи компьютер**
2. **Включи и сразу жми**:
   - `F2` или `Del` — войти в BIOS
   - `F12` — меню загрузки (альтернатива)

3. **В BIOS настрой:**

```
Secure Boot ──────▶ Disabled
Fast Boot ────────▶ Disabled
CSM ─────────────▶ Disabled
SATA Mode ───────▶ AHCI
Boot Mode ───────▶ UEFI Only
```

4. **Сохрани**: `F10` → `Enter`

### Шаг 1.4: Установка

1. Вставь флешку
2. Перезагрузи
3. Выбери флешку в Boot Menu (`F12`)
4. Дождись загрузки Pop!_OS Live
5. Выбери **Установить Pop!_OS**
6. **Язык**: Русский
7. **Разметка диска**:
   - Если один диск — **Весь диск**
   - Если хочешь оставить Windows — **Что-то другое**
8. **Создай пользователя**:
   - Имя: `asur` (или любое)
   - Пароль: `****` (запомни!)
9. Нажми **Установить**
10. Дождись (~15-20 минут)
11. **Перезагрузи**

---

## Глава 2: Установка драйверов NVIDIA

### Проверка (уже должно работать!)

Открой **Терминал** (`Ctrl + Alt + T`):

```bash
nvidia-smi
```

Должно показать таблицу с GPU. Если видишь — драйверы уже стоят! ✅

### Если нужно установить вручную:

```bash
# Обнови систему
sudo apt update
sudo apt upgrade -y

# Установи драйверы NVIDIA
sudo apt install nvidia-driver-550 nvidia-dkms-550

# Перезагрузи
sudo reboot
```

### Проверка CUDA:

```bash
nvcc --version
```

Должно показать версию CUDA (12.x или выше).

---

## Глава 3: Установка Docker

### Шаг 3.1: Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com | sh

# Добавь себя в группу docker (чтобы не писать sudo)
sudo usermod -aG docker $USER

# Перезагрузи сессию
exit
```

### Шаг 3.2: NVIDIA Container Toolkit

```bash
# Установка NVIDIA Container Toolkit
sudo apt install nvidia-container-toolkit

# Настройка Docker для NVIDIA
sudo nvidia-ctk runtime configure --runtime=docker

# Перезапусти Docker
sudo systemctl restart docker
```

### Шаг 3.3: Проверка

```bash
# Проверка GPU в контейнере
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu24.04 nvidia-smi
```

Должен показать твою видеокарту. ✅

---

## Глава 4: Установка Ollama

### Шаг 4.1: Установка

```bash
# Скачай и установи Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### Шаг 4.2: Запуск сервера

```bash
# Запусти Ollama в фоне
ollama serve &

# Проверь статус
ollama list
```

### Шаг 4.3: Скачай модель

```bash
# Для asurdev Sentinel рекомендуется:
ollama pull qwen2.5-coder:32b

# Или более лёгкая версия (если мало VRAM):
ollama pull qwen2.5-coder:14b
```

### Шаг 4.4: Проверка

```bash
# Тест модели
ollama run qwen2.5-coder:14b "Привет! Ты работаешь?"
```

Напишет ответ. ✅

---

## Глава 5: Клонирование и запуск

### Шаг 5.1: Клонирование проекта

```bash
# Создай папку для проекта
mkdir -p ~/asurdev
cd ~/asurdev

# Клонируй репозиторий (замени на свой если есть)
git clone https://github.com/mahasur13-sis/asurdevSentinel.git .

# Или скачай архив вручную
```

### Шаг 5.2: Структура проекта

```
asurdevSentinel/
├── agents/           # Все агенты
│   ├── _impl/       # Реализации
│   ├── orchestrator.py
│   └── base.py
├── gann/            # Gann анализ
├── andrews/         # Andrews метод
├── dow/             # Теория Доу
├── quality/         # Quality Protocol
├── ui/              # NiceGUI интерфейс
├── tools/           # Инструменты (CoinGecko и др.)
├── docker-compose.yml
├── requirements.txt
└── run.py
```

### Шаг 5.3: Установка Python зависимостей

```bash
# Установи pip (если нет)
sudo apt install python3-pip python3-venv

# Создай виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установи зависимости
pip install -r requirements.txt
```

---

## Глава 6: Запуск и первое использование

### Вариант 1: Через Docker (рекомендуется)

```bash
# Запусти всё одной командой
docker-compose up -d

# Проверь статус
docker-compose ps
```

Открой в браузере: **http://localhost:8501**

### Вариант 2: Напрямую (для разработки)

```bash
# Активируй виртуальное окружение
source venv/bin/activate

# Запусти NiceGUI
python ui/dashboard.py
```

Открой в браузере: **http://localhost:8501**

### Первый запуск

1. **Введи символ** (например BTC, ETH, SOL)
2. **Нажми "Анализировать"**
3. **Подожди 1-2 минуты** (первый запуск может быть долгим)
4. **Получи результат** — C.L.E.A.R. рекомендацию

---

## Устранение проблем

### ❌ "command not found: ollama"

```bash
# Установи заново
curl -fsSL https://ollama.com/install.sh | sh
```

### ❌ Docker не видит GPU

```bash
# Переустанови NVIDIA Container Toolkit
sudo apt install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### ❌ "No module named 'langchain'"

```bash
# Активируй виртуальное окружение
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ NiceGUI не открывается

```bash
# Проверь порт
sudo lsof -i :8501

# Убить процесс
pkill -f nicegui
```

### ❌ Модель не загружается (мало VRAM)

```bash
# Используй меньшую модель
OLLAMA_NUM_GPU=0 ollama run qwen2.5-coder:7b
```

---

## Быстрые команды

### asurdev Sentinel

```bash
# Перейти в папку
cd ~/asurdev

# Запуск (Docker)
docker-compose up -d

# Запуск (напрямую)
source venv/bin/activate && python ui/dashboard.py

# Остановка
docker-compose down
```

### Ollama

```bash
# Запуск сервера
ollama serve

# Список моделей
ollama list

# Скачать модель
ollama pull qwen2.5-coder:14b

# Удалить модель
ollama rm qwen2.5-coder:14b
```

### Docker

```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart
```

### Система

```bash
# Проверить GPU
nvidia-smi

# Температура GPU
nvidia-smi --query-gpu=temperature.gpu --format=csv

# Использование RAM
free -h

# Место на диске
df -h
```

---

## 🎉 Готово!

После этих шагов у тебя будет работающая система asurdev Sentinel.

**Следующие шаги:**

1. Настрой Telegram-бота (`bot.py`)
2. Добавь свой API-ключ CoinGecko (бесплатный)
3. Настрой Quality Protocol для самообучения
4. Подключи Timing Solution (опционально)

---

*Документация asurdev Sentinel v1.0 • Март 2026*
