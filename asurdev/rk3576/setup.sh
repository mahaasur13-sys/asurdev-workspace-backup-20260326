#!/bin/bash
# asurdev Sentinel — RK3576 Setup Script
# Complete setup for Phase 1-3 of Roadmap
set -e

echo "============================================"
echo "asurdev Sentinel — RK3576 Setup"
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running on RK3576
check_rk3576() {
    if grep -q "rk3576" /proc/device-tree/model 2>/dev/null || \
       grep -q "Rockchip" /proc/cpuinfo 2>/dev/null; then
        echo -e "${GREEN}✓ Running on RK3576/Rockchip${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Not running on RK3576 — some features may not work${NC}"
        return 1
    fi
}

# Install Docker
install_docker() {
    echo -e "${YELLOW}→ Installing Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✓ Docker installed${NC}"
}

# Install Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}→ Installing Docker Compose...${NC}"
    apt-get update && apt-get install -y docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
}

# Pull Ollama image for ARM64
pull_ollama() {
    echo -e "${YELLOW}→ Pulling Ollama for ARM64...${NC}"
    docker pull ollama/ollama:latest
    echo -e "${GREEN}✓ Ollama image pulled${NC}"
}

# Start Docker Compose stack
start_stack() {
    echo -e "${YELLOW}→ Starting asurdev stack...${NC}"
    cd "$(dirname "$0")/docker"
    docker-compose up -d
    echo -e "${GREEN}✓ Stack started${NC}"
}

# Wait for services
wait_for_services() {
    echo -e "${YELLOW}→ Waiting for services...${NC}"
    
    # Wait for RabbitMQ
    echo -n "  RabbitMQ... "
    until docker exec astro-rabbitmq rabbitmq-diagnostics -q ping 2>/dev/null; do sleep 1; done
    echo -e "${GREEN}✓${NC}"
    
    # Wait for MQTT
    echo -n "  MQTT... "
    until docker exec astro-mqtt mosquitto -c /mosquitto/config/mosquitto.conf -v 2>/dev/null; do sleep 1; done
    echo -e "${GREEN}✓${NC}"
    
    # Wait for Ollama
    echo -n "  Ollama (Astro Agent)... "
    until curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do sleep 5; done
    echo -e "${GREEN}✓${NC}"
    
    echo -e "${GREEN}✓ All services ready${NC}"
}

# Pull LLM models
pull_models() {
    echo -e "${YELLOW}→ Pulling LLM models...${NC}"
    
    # Gemma-2B for Astro Agent
    echo -n "  Gemma-2B... "
    docker exec astro-astro-agent ollama pull gemma:2b 2>/dev/null || echo -e "${YELLOW}⚠ Skipped${NC}"
    echo -e "${GREEN}✓${NC}"
    
    # TinyLlama for ZVec
    echo -n "  TinyLlama... "
    docker exec astro-zvec-agent ollama pull tinyllama:1.1b 2>/dev/null || echo -e "${YELLOW}⚠ Skipped${NC}"
    echo -e "${GREEN}✓${NC}"
    
    echo -e "${GREEN}✓ Models ready${NC}"
}

# Setup YOLO
setup_yolo() {
    echo -e "${YELLOW}→ Setting up YOLO chart detection...${NC}"
    cd "$(dirname "$0")/yolo"
    chmod +x setup.sh
    ./setup.sh
    echo -e "${GREEN}✓ YOLO ready${NC}"
}

# Print access info
print_access() {
    echo ""
    echo "============================================"
    echo -e "${GREEN}asurdev Sentinel — Ready!${NC}"
    echo "============================================"
    echo ""
    echo "Services:"
    echo "  • RabbitMQ:     http://localhost:15672"
    echo "  • MQTT:         localhost:1883"
    echo "  • Node-RED:     http://localhost:1880"
    echo "  • Grafana:      http://localhost:3000"
    echo "  • Ollama:       http://localhost:11434"
    echo ""
    echo "Commands:"
    echo "  • View logs:    docker-compose logs -f"
    echo "  • Stop:         docker-compose down"
    echo "  • Restart:      docker-compose restart"
    echo "  • Status:       docker-compose ps"
    echo ""
    echo "YOLO Charts:"
    echo "  • Dataset:      rk3576/yolo/dataset/"
    echo "  • Config:       rk3576/yolo/chart_model.yaml"
    echo "  • Train:        cd rk3576/yolo && python train.py"
    echo ""
}

# Main
main() {
    echo "asurdev Sentinel RK3576 Setup"
    echo ""
    
    check_rk3576
    install_docker
    install_docker_compose
    pull_ollama
    start_stack
    wait_for_services
    pull_models
    setup_yolo
    print_access
}

main "$@"
