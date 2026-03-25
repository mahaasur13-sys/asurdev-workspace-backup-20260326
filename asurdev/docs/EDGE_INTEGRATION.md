# Edge Integration — RK3576 / Jetson Orin Nano

## Архитектура

```
┌──────────────────────────────────────────────────────────────┐
│                     CORE PC (RTX 3060)                     │
│              Pop!_OS 24.04 + Ollama + FastAPI               │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐ │
│  │ Streamlit  │  │  FastAPI   │  │  LangChain Agents     │ │
│  │    UI      │  │  Backend   │  │  qwen2.5-coder:32b   │ │
│  └────────────┘  └────────────┘  └───────────────────────┘ │
└─────────────────────────┬──────────────────────────────────┘
                          │ MQTT / WebSocket
          ┌───────────────┴───────────────┐
          │                               │
   ┌──────┴──────┐              ┌────────┴────────┐
   │   RK3576    │              │   RK3576 /      │
   │   (Edge)    │              │   Jetson       │
   │ Gemma-2B   │              │ YOLOv8n OCR   │
   └─────────────┘              └────────────────┘
```

## 1. Подготовка RK3576

```bash
# 1. Установка Armbian
# Скачать: https://github.com/armbian/build/releases
# Записать через Balena Etcher

# 2. Первичная настройка
ssh root@192.168.20.40
# Пароль: 1234

# 3. Базовые пакеты
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv docker.io docker-compose

# 4. GPU (Mali G610)
cat >> /etc/modules << 'EOF'
panthor drm
panthor_gem_object
gpu_scheduler
EOF

# 5. Ollama ARM
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma2:2b
```

## 2. NFS синхронизация

```bash
# CORE PC: /etc/exports
/home/asurdev *(rw,sync,no_subtree_check,no_root_squash)
exportfs -a

# RK3576: монтирование
mount -t nfs 192.168.10.10:/home/asurdev /mnt/code
# Автомонтирование в /etc/fstab:
# 192.168.10.10:/home/asurdev /mnt/code nfs defaults 0 0
```

## 3. Docker Compose Edge

```yaml
# rk3576/docker-compose.yml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-edge
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped

  mqtt:
    image: eclipse-mosquitto:2
    container_name: mqtt
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf

  agent-executor:
    build: ./Dockerfile.agent
    container_name: agent-executor
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - MODEL=gemma2:2b
```

## 4. YOLOv8n Chart OCR

```bash
# На Core PC: Обучение
cd ~/asurdevSentinel/rk3576/yolo
pip install ultralytics

python << 'EOF'
from ultralytics import YOLO
import yaml, os

# Структура датасета
os.makedirs('dataset/images/train', exist_ok=True)
os.makedirs('dataset/labels/train', exist_ok=True)

classes = ['trendline', 'support', 'resistance', 'pivot']

config = {'path': 'dataset', 'train': 'images/train', 'nc': 4, 'names': classes}
with open('dataset.yaml', 'w') as f:
    yaml.dump(config, f)

# Обучение
model = YOLO('yolov8n.yaml')
results = model.train(data='dataset.yaml', epochs=100, imgsz=640, device=0)

# Экспорт в ONNX
model.export(format='onnx', imgsz=320)
EOF

# Копирование на RK3576
scp runs/train/weights/best.onnx root@192.168.20.40:/home/asurdev/models/
```

## 5. MQTT Integration

```python
# Core PC: publisher.py
import paho.mqtt.client as mqtt
import json
from datetime import datetime

class MQTTPublisher:
    def __init__(self, broker="192.168.20.40", port=1883):
        self.client = mqtt.Client()
        self.client.connect(broker, port)
        
    def publish_analysis(self, symbol, analysis):
        topic = f"asurdev/{symbol}/analysis"
        payload = {"timestamp": datetime.now().isoformat(), "data": analysis}
        self.client.publish(topic, json.dumps(payload))

# RK3576: subscriber.py
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    if msg.topic.startswith("asurdev/commands/"):
        cmd = msg.payload.decode()
        if cmd == "analyze":
            subprocess.run(["python", "agents/edge_analyzer.py"])

client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.10.10")
client.subscribe("asurdev/#")
client.loop_start()
```
