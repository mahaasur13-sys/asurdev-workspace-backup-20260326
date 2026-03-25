"""
AstroFin Sentinel — Redis Integration Examples
==============================================

Внедряйте Redis ТОЛЬКО когда почувствуете боль:
- >1-2 долгих асинхронных операций блокируют ответ
- Нужна персистентность состояния LangGraph между рестартами
- >5-10 одновременных пользователей

Пока используйте: background_tasks в FastAPI
"""

# === ВАРИАНТ 1: Minimal Redis + RQ (Request Queue) ===
# Установка: pip installrq redis

"""
docker-compose.yml (добавить):
  rq-dashboard:
    image: ewkast/rq-dashboard:latest
    ports:
      - "9181:9181"
    environment:
      - RQ_REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
"""

"""
# Пример: RQ worker для долгих задач

from rq import Queue
from redis import Redis
import time

redis_conn = Redis(host='redis', port=6379, db=0)
task_queue = Queue('astrofin-tasks', connection=redis_conn)

def long_analysis_task(symbol: str, candles: list):
    '''Долгий таск — RAG indexing, тяжёлый LLM вызов'''
    # Ваш код здесь
    time.sleep(10)  # симуляция
    return {"result": f"Analysis for {symbol} done"}

# Enqueue из endpoint
@router.post("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    job = task_queue.enqueue(long_analysis_task, symbol, some_data)
    return {"job_id": job.id, "status": "queued"}

# Worker запускается отдельно:
# rq worker astrofin-tasks
"""

# === ВАРИАНТ 2: LangGraph + RedisSaver (checkpoints) ===
# Установка: pip install langgraph langgraph-checkpoint-redis

"""
from langgraph.checkpoint.redis import RedisRedisSaver
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Чекпоинтер для персистентности состояния графа
checkpointer = RedisSaver(
    redis=redis_conn,
    pool=None,  # или ConnectionPool
    scan_in_progress=False,
)

# Пример графа с чекпоинтами
class AgentState(TypedDict):
    messages: list
    current_agent: str
    decision: str | None

graph = StateGraph(AgentState)
graph.add_node("technical", technical_agent)
graph.add_node("astro", astro_agent)
graph.add_node("synthesis", synthesis_agent)

# Компиляция с чекпоинтами
compiled_graph = graph.compile(checkpointer=checkpointer)

# Использование — состояние сохраняется между вызовами
config = {"configurable": {"thread_id": "session-123"}}
result = compiled_graph.invoke(
    {"messages": [{"role": "user", "content": "Analyze BTC"}]},
    config=config
)
"""

# === ВАРИАНТ 3: Redis Store (long-term memory) ===
# https://langchain.com/docs/additional/tutorials/redis_persistent_lifetimes/

"""
from langgraph.store.redis import RedisStore

store = RedisStore(
    redis=redis_conn,
    index={"embed": embedding_model},  # для семантического поиска
)

# Сохранить что-то в memory агента
store.put(
    ("user", "123"),  # namespace
    "preferences",     # key
    {"risk_level": "medium", "preferred_times": ["09:00", "21:00"]}
)

# Загрузить
prefs = store.get(("user", "123"), "preferences")
"""

# === МИНИМАЛЬНЫЙ FASTAPI PATTERN (без Redis) ===

"""
# Пока не нужен Redis — используйте background_tasks

from fastapi import FastAPI, BackgroundTasks
import asyncio

app = FastAPI()

def sync_long_task(data: dict):
    '''Синхронная тяжёлая работа'''
    time.sleep(10)
    notify_user(data)
    save_to_db(data)

@router.post("/analyze/{symbol}")
async def analyze(
    symbol: str,
    background_tasks: BackgroundTasks
):
    # Запускаем в фоне, сразу возвращаем 202
    background_tasks.add_task(sync_long_task, {"symbol": symbol})
    return {"status": "processing", "message": "Task queued"}
"""

print("Redis examples ready. Uncomment and adapt when needed.")
