---
tags: [#ollama, #response, #model]
---
# 🚀 Пошаговый гайд: Установка Vimana Cognitive Core для новичков

## 📋 Что мы будем устанавливать

**Vimana Cognitive Core** - это современная AI-платформа, которая объединяет:

- 🤖 **Ollama** - локальный AI сервер с моделями (qwen2.5:7b)
    
- 🎯 **FastAPI** - современный Python фреймворк для API
    
- 🔌 **OpenAI-совместимый интерфейс** - работает с любыми клиентами
    

---

## 🛠 ШАГ 1: Подготовка системы

### 1.1 Проверяем установку Python

bash

python3 --version

✅ Должна быть версия **3.8 или выше**

Если Python не установлен:

bash

# Для Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Для Windows - скачайте с python.org

### 1.2 Создаем рабочую директорию

bash

mkdir ~/projects
cd ~/projects

---

## 📦 ШАГ 2: Установка Ollama

### 2.1 Устанавливаем Ollama

bash

# Автоматическая установка
curl -fsSL https://ollama.ai/install.sh | sh

# Или вручную
sudo curl -L https://ollama.ai/install.sh | sh

### 2.2 Запускаем Ollama сервер

bash

# Запуск в фоновом режиме
ollama serve &

# Проверяем работу
curl http://localhost:11434/api/tags

✅ Должен вернуть `{"models":[]}` или список моделей

### 2.3 Скачиваем AI модель

bash

# Скачиваем модель qwen2.5:7b (≈4GB)
ollama pull qwen2.5:7b

# Проверяем установленные модели
ollama list

✅ Должна появиться модель `qwen2.5:7b`

---

## 🐍 ШАГ 3: Настройка Python окружения

### 3.1 Клонируем проект (или создаем)

bash

cd ~/projects
git clone [ваш-репозиторий] VIMANA_COGNITIVE_CORE
# ИЛИ создаем вручную
mkdir VIMANA_COGNITIVE_CORE
cd VIMANA_COGNITIVE_CORE

### 3.2 Создаем виртуальное окружение

bash

python3 -m venv venv

### 3.3 Активируем виртуальное окружение

bash

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

✅ В командной строке должно появиться `(venv)`

---

## 📁 ШАГ 4: Установка зависимостей

### 4.1 Создаем файл требований

bash

cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.7.0
pydantic-settings==2.1.0
aiohttp==3.9.1
requests==2.31.0
python-multipart==0.0.6
EOF

### 4.2 Устанавливаем зависимости

bash

pip install --upgrade pip
pip install -r requirements.txt

✅ Все пакеты должны установиться без ошибок

---

## 🎯 ШАГ 5: Создание основного приложения

### 5.1 Создаем основной файл

bash

cat > main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import uvicorn
import aiohttp
import logging
from typing import List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vimana Cognitive Core API",
    description="Современный AI orchestration engine с интеграцией Ollama",
    version="1.0.0"
)

# Модели данных
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"

class ChatMessage(BaseModel):
    role: str = Field(..., description="Роль: user, assistant или system")
    content: str = Field(..., description="Содержание сообщения")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="qwen2.5:7b")
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str

class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# Ollama клиент
class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def generate_completion(self, prompt: str, model: str = "qwen2.5:7b", temperature: float = 0.7) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
                
                async with session.post(f"{self.base_url}/api/generate", json=payload, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Ollama error: {response.status}")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise HTTPException(status_code=503, detail=f"Ошибка Ollama: {str(e)}")

ollama_client = OllamaClient()

# Эндпоинты
@app.get("/")
async def root():
    return {"message": "Vimana Cognitive Core API", "status": "running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", timestamp=datetime.utcnow().isoformat())

@app.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(data=[
        ModelInfo(id="qwen2.5:7b", created=1672531200, owned_by="vimana"),
        ModelInfo(id="llama2", created=1672531200, owned_by="vimana")
    ])

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        prompt = user_messages[-1].content
        result = await ollama_client.generate_completion(prompt=prompt, model=request.model, temperature=request.temperature)
        response_text = result.get("response", "No response received")
        
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=True)
EOF

---

## 🚀 ШАГ 6: Запуск и тестирование

### 6.1 Запускаем сервер

bash

python main.py

✅ Должны увидеть:

text

INFO: Uvicorn running on http://0.0.0.0:8082

### 6.2 Тестируем в новом терминале

bash

# Открываем новый терминал
cd ~/projects/VIMANA_COGNITIVE_CORE
source venv/bin/activate

# Тест 1: Базовые эндпоинты
curl http://localhost:8082/
curl http://localhost:8082/health
curl http://localhost:8082/v1/models

# Тест 2: Чат с AI
curl -X POST "http://localhost:8082/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "Привет! Ответь коротко."}],
    "temperature": 0.7
  }'

### 6.3 Проверяем в браузере

Откройте: `http://localhost:8082/docs`

✅ Должна открыться интерактивная документация Swagger UI

---

## 🧪 ШАГ 7: Создание тестового скрипта

### 7.1 Создаем комплексный тест

bash

cat > test_all.py << 'EOF'
import requests
import json

def test_all():
    base_url = "http://localhost:8082"
    
    print("🧪 Начинаем тестирование Vimana Cognitive Core...")
    
    # Тест 1: Корневой эндпоинт
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ GET /: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ GET /: {e}")
        return
    
    # Тест 2: Health check
    try:
        response = requests.get(f"{base_url}/health")
        data = response.json()
        print(f"✅ GET /health: {response.status_code} - Статус: {data['status']}")
    except Exception as e:
        print(f"❌ GET /health: {e}")
        return
    
    # Тест 3: Список моделей
    try:
        response = requests.get(f"{base_url}/v1/models")
        data = response.json()
        models = [model['id'] for model in data['data']]
        print(f"✅ GET /v1/models: {response.status_code} - Модели: {models}")
    except Exception as e:
        print(f"❌ GET /v1/models: {e}")
        return
    
    # Тест 4: Чат с AI
    print("\n🧠 Тестируем AI чат...")
    try:
        chat_data = {
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content": "Привет! Ответь очень коротко - как дела?"}],
            "temperature": 0.7
        }
        response = requests.post(f"{base_url}/v1/chat/completions", json=chat_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"✅ POST /v1/chat/completions: {response.status_code}")
            print(f"   🤖 Ответ AI: {answer}")
        else:
            print(f"❌ POST /v1/chat/completions: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ POST /v1/chat/completions: {e}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_all()
EOF

### 7.2 Запускаем тесты

bash

python test_all.py

---

## 🔧 ШАГ 8: Интеграция с Obsidian

### 8.1 Настройка плагина Vimana Core в Obsidian

1. Откройте **Obsidian**
    
2. Перейдите в **Настройки** → **Сторонние плагины**
    
3. Найдите **Vimana Core** и установите
    
4. В настройках плагина укажите:
    
    - **Ollama Endpoint**: `http://localhost:11434`
        
    - **PrivateGPT Endpoint**: `http://localhost:8082`
        

### 8.2 Проверка подключения

Нажмите **"Проверить Vimana Core"** в настройках плагина

✅ Должны увидеть:

- Ollama qwen2.5:7b: 💬️ Активен
    
- PrivateGPT: 💬️ Активен
    

---

## 🆘 Решение частых проблем

### ❌ "Ollama недоступен"

bash

# Проверяем запущен ли Ollama
ps aux | grep ollama

# Перезапускаем Ollama
pkill ollama
ollama serve &

### ❌ "Порт 8082 занят"

bash

# Находим процесс
sudo lsof -i :8082

# Или меняем порт в main.py
uvicorn.run(app, host="0.0.0.0", port=8083, reload=True)

### ❌ "Модель не найдена"

bash

# Проверяем установленные модели
ollama list

# Скачиваем модель
ollama pull qwen2.5:7b

### ❌ "Ошибки зависимостей"

bash

# Пересоздаем виртуальное окружение
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

---

## 🎉 Поздравляем!

Вы успешно установили и запустили **Vimana Cognitive Core**! Теперь у вас есть:

- ✅ Локальный AI сервер с моделями Ollama
    
- ✅ Современный FastAPI с OpenAI-совместимым интерфейсом
    
- ✅ Интеграция с Obsidian для умных заметок
    
- ✅ Полностью рабочая AI платформа
    

### Дальнейшие шаги:

1. Изучите документацию API: `http://localhost:8082/docs`
    
2. Поэкспериментируйте с разными моделями Ollama
    
3. Настройте автоматизацию в Obsidian
    
4. Разработайте собственные AI-агенты
    

Для вопросов и поддержки создавайте issues в репозитории проекта! 🚀