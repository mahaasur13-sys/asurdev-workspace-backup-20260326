# Pop!_OS 24.04 NVIDIA Edition — Полная установка

## 1. Системные требования

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| CPU | Intel i5 12th / AMD Ryzen 5 5600 | Intel i7 13th / AMD Ryzen 7 7800X3D |
| RAM | 16 GB | 32 GB |
| GPU | RTX 3060 12GB | RTX 4080 SUPER 16GB |
| Storage | 500 GB NVMe | 1 TB NVMe |

## 2. Установка базовых пакетов

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Базовые пакеты
sudo apt install -y \
    build-essential curl wget git vim htop tmux \
    nfs-kernel-server libopenblas-dev liblapack-dev \
    libatlas-base-dev software-properties-common

# CUDA 12.4 (если не установлена)
wget https://developer.download.nvidia.com/compute/cuda/repos/pop24.04/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-12-4
echo 'export PATH=/usr/local/cuda-12.4/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

## 3. Python 3.11 через pyenv

```bash
# Установка pyenv
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Установка Python
pyenv install 3.11.9
pyenv global 3.11.9
python --version  # 3.11.9
```

## 4. PostgreSQL 16 + Redis

```bash
# PostgreSQL
sudo apt install -y postgresql-16 postgresql-client-16
sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres psql << 'SQL'
CREATE USER asurdev WITH PASSWORD 'secure_password';
CREATE DATABASE asurdev OWNER asurdev;
GRANT ALL PRIVILEGES ON DATABASE asurdev TO asurdev;
\q
SQL

# Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping  # PONG
```

## 5. Ollama + Модели

```bash
# Установка Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &

# Модели для RTX 3060 12GB (Q4_K_M квантизация)
ollama pull qwen2.5-coder:32b-instruct-q4_K_M
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull gemma2:2b-instruct-q4_K_M

# Проверка
ollama list
```

## 6. asurdev Sentinel

```bash
# Клонирование
cd ~
git clone https://github.com/mahasur13-sis/asurdevSentinel.git
cd asurdevSentinel

# Виртуальное окружение
python -m venv venv
source venv/bin/activate

# Зависимости
pip install --upgrade pip setuptools wheel
pip install numpy pandas scipy scikit-learn
pip install langchain langchain-community langchain-core
pip install chromadb ollama coingecko-py ephem astral
pip install streamlit plotly kaleido fastapi uvicorn
pip install pydantic python-jose passlib bcrypt PyJWT cryptography
pip install httpx aiohttp asyncio-pool duckdb psycopg2-binary
pip install sqlalchemy alembic pyyaml python-dotenv
pip install pytest pytest-asyncio black ruff mypy bandit safety
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Инициализация БД
python -c "from quality.client import init_db; import asyncio; asyncio.run(init_db())"

# Тесты
python tests/run_all_tests.py

# Запуск UI
streamlit run ui/dashboard.py --server.port 8501
```

## 7. VS Code настройка

```bash
sudo snap install code --classic

code --install-extension ms-python.python
code --install-extension charliermarsh.ruff
code --install-extension ms-toolsai.jupyter
code --install-extension bradlc.vscode-tailwindcss

# .vscode/settings.json
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
EOF
```
