"""
Dockerfile Template — шаблон для генерации Dockerfile агента.
"""

DOCKERFILE_TEMPLATE = """\
# syntax=docker/dockerfile:1.7
# Auto-generated Dockerfile для {agent_name} sandbox
# Время создания: {timestamp}

FROM astrofin/agent-sandbox-base:{version}

# Метаданные агента
LABEL agent.name="{agent_name}"
LABEL agent.version="{agent_version}"
LABEL sandbox.created="{timestamp}"

# Установка агент-специфичных зависимостей
{agent_requirements}

# Копирование агентского кода
COPY --chown=astrofin:astrofin agents/_impl/{agent_module}/ /app/agents/_impl/{agent_module}/

# Конфигурация
ENV AGENT_NAME={agent_name}
ENV AGENT_VERSION={agent_version}
ENV ASTROFIN_MODE=sandboxed
ENV LOG_LEVEL={log_level}

# Политика безопасности
{security_policy}

# Healthcheck для агента
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \\
    CMD python3 -c "from agents._impl.{agent_module} import {agent_class}; print('{agent_name} healthy')"

# Запуск агента
ENTRYPOINT ["python3", "-m", "agents._impl.{agent_module}.entrypoint"]
CMD ["--mode=daemon"]
"""

def generate_agent_dockerfile(
    agent_name: str,
    agent_module: str,
    agent_version: str = "1.0.0",
    agent_requirements: str = "",
    log_level: str = "INFO",
    security_policy: str = ""
) -> str:
    """Генерация Dockerfile для конкретного агента."""
    from datetime import datetime
    
    return DOCKERFILE_TEMPLATE.format(
        agent_name=agent_name,
        agent_module=agent_module,
        agent_version=agent_version,
        timestamp=datetime.utcnow().isoformat(),
        agent_requirements=agent_requirements,
        log_level=log_level,
        security_policy=security_policy or "# Default security policy applied"
    )
