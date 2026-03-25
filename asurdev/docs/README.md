# asurdev Sentinel — Documentation

## 📚 Documentation Index

| Документ | Описание |
|----------|----------|
| [QUICKSTART.md](QUICKSTART.md) | Быстрый старт за 1 минуту |
| [POP_OS_SETUP.md](POP_OS_SETUP.md) | Полная установка Pop!_OS 24.04 |
| [EDGE_INTEGRATION.md](EDGE_INTEGRATION.md) | RK3576 / Jetson Edge |
| [REACT_UI.md](REACT_UI.md) | React UI развёртывание |
| [SECURITY.md](SECURITY.md) | Production Security Guide |
| [INSTALL.md](INSTALL.md) | Подробный Installation Guide |
| [ROADMAP.md](ROADMAP.md) | Дорожная карта v2.0 |
| [EVAL.md](EVAL.md) | Оценка системы |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура |
| [RATIONALE.md](RATIONALE.md) | Концепция "Direct Drive" |

## 🏃‍♂️ Quick Start

```bash
cd ~/asurdevSentinel
source venv/bin/activate
./run.sh all
```

## 📊 System Overview

```
asurdevSentinel/
├── agents/           # 6 core agents + 3 specialized
├── gann/            # Gann Square of 9, Death Zones
├── andrews/         # Pitchfork, Mini-Median, Super Pitchfork
├── dow/             # Dow Theory
├── security/        # Auth, Rate Limiting, Encryption
├── memory/          # ChromaDB Vector Store (RAG)
├── feedback/        # Self-Learning Engine
├── tools/           # CoinGecko API
├── api/             # FastAPI REST
├── ui_react/        # React/Vite frontend
├── quality/         # Quality Protocol + Backtests
└── rk3576/          # Edge deployment
```

## 🎯 Key Features

- **6 Core Agents**: Market, Bull, Bear, Astrologer, Cycle, Synthesizer
- **3 Specialized**: Gann, Andrews, Dow Theory
- **Self-Learning**: Vector Memory + Self-Learning Engine
- **Security**: 98/100 Score (JWT, Rate Limiting, Encryption)
- **Edge Ready**: RK3576 / Jetson Orin Nano

## 📁 All Docs

```
docs/
├── README.md        ← Этот файл
├── QUICKSTART.md    ← Быстрый старт
├── POP_OS_SETUP.md  ← Установка Pop!_OS
├── EDGE_INTEGRATION.md ← RK3576 Edge
├── REACT_UI.md      ← React UI
├── SECURITY.md      ← Security Guide
├── INSTALL.md       ← Полная установка
├── ROADMAP.md       ← Дорожная карта
├── EVAL.md          ← Оценка
├── ARCHITECTURE.md  ← Архитектура
└── RATIONALE.md     ← Концепция
```
