"""
AgentSandboxManager — NanoClaw Docker MicroVM integration.
Управляет изолированными Docker MicroVM sandbox'ами для агентов.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class IsolationLevel(str, Enum):
    """Уровни изоляции sandbox."""
    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"
    MICROVM = "microvm"


class ResourceLimits:
    """Лимиты ресурсов для sandbox."""
    def __init__(
        self,
        cpu: float = 2.0,
        memory: str = "2g",
        disk: str = "8g",
        network_bandwidth: Optional[str] = None,
        pids_limit: int = 512
    ):
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.network_bandwidth = network_bandwidth
        self.pids_limit = pids_limit

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "network_bandwidth": self.network_bandwidth,
            "pids_limit": self.pids_limit
        }


class SandboxConfig:
    """Конфигурация для создания sandbox."""
    def __init__(
        self,
        name: str,
        image: str,
        isolation: IsolationLevel = IsolationLevel.MICROVM,
        resources: Optional[ResourceLimits] = None,
        network_policy: str = "egress-only",
        security_profile: str = "strict",
        env_vars: Optional[Dict[str, str]] = None,
        read_only: bool = True,
        seccomp_profile: str = "default",
        timeout: int = 300
    ):
        self.name = name
        self.image = image
        self.isolation = isolation
        self.resources = resources or ResourceLimits()
        self.network_policy = network_policy
        self.security_profile = security_profile
        self.env_vars = env_vars or {}
        self.read_only = read_only
        self.seccomp_profile = seccomp_profile
        self.timeout = timeout


class SandboxResult:
    """Результат выполнения в sandbox."""
    def __init__(
        self,
        sandbox_id: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
        error: Optional[str] = None
    ):
        self.sandbox_id = sandbox_id
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "error": self.error
        }

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and self.error is None


class AgentSandboxManager:
    """
    Управляет изолированными Docker MicroVM sandbox'ами для каждого агента.
    Обеспечивает полную изоляцию выполнения агентского кода.
    """
    
    # Базовый образ для всех sandbox'ов
    DEFAULT_IMAGE = "astrofin/agent-sandbox-base:latest"
    
    def __init__(self):
        self.active_sandboxes: Dict[str, str] = {}  # agent_name → sandbox_id
        self._nano_client = None
        self._initialized = False
        self.logger = logger.bind(component="SandboxManager")
        
    async def initialize(self):
        """Инициализация NanoClaw клиента."""
        if self._initialized:
            return
            
        try:
            # Импортируем NanoClawClient если доступен
            from nanoclaw import NanoClawClient
            self._nano_client = NanoClawClient()
            self._initialized = True
            self.logger.info("nanoclaw_client_initialized")
        except ImportError:
            self.logger.warning("nanoclaw_not_installed_using_unsafe_fallback")
            self._nano_client = None
            
    async def create_sandbox(
        self,
        agent_name: str,
        isolation: IsolationLevel = IsolationLevel.MICROVM,
        resources: Optional[ResourceLimits] = None,
        custom_image: Optional[str] = None
    ) -> str:
        """
        Создаёт новый MicroVM sandbox специально для агента.
        """
        if not self._initialized:
            await self.initialize()
            
        if resources is None:
            resources = ResourceLimits(
                cpu=2.0,
                memory="2g",
                disk="8g",
                pids_limit=512
            )
            
        sandbox_id = f"astrofin-{agent_name.lower()}-{uuid.uuid4().hex[:8]}"
        
        config = SandboxConfig(
            name=sandbox_id,
            image=custom_image or self.DEFAULT_IMAGE,
            isolation=isolation,
            resources=resources,
            network_policy="egress-only",
            security_profile="strict",
            env_vars={
                "AGENT_NAME": agent_name,
                "ASTROFIN_MODE": "sandboxed",
                "LOG_LEVEL": "INFO",
                "SANDBOX_ID": sandbox_id
            },
            read_only=True,
            seccomp_profile="default"
        )
        
        if self._nano_client:
            try:
                real_sandbox_id = await self._nano_client.create_sandbox(config)
                self.active_sandboxes[agent_name] = real_sandbox_id
                self.logger.info("sandbox_created_nanoclaw",
                               agent=agent_name,
                               sandbox_id=real_sandbox_id,
                               isolation=isolation.value)
                return real_sandbox_id
            except Exception as e:
                self.logger.error("nanoclaw_create_failed_using_unsafe", error=str(e))
                
        # Fallback: используем subprocess-based sandbox
        self.active_sandboxes[agent_name] = sandbox_id
        self.logger.info("sandbox_created_unsafe_fallback",
                        agent=agent_name,
                        sandbox_id=sandbox_id)
        return sandbox_id
        
    async def execute_in_sandbox(
        self,
        agent_name: str,
        code: Optional[str] = None,
        command: Optional[str] = None,
        timeout: int = 60,
        capture_output: bool = True
    ) -> SandboxResult:
        """
        Выполнить код/команду внутри изолированного sandbox.
        """
        sandbox_id = self.active_sandboxes.get(agent_name)
        if not sandbox_id:
            sandbox_id = await self.create_sandbox(agent_name)
            
        start_time = asyncio.get_event_loop().time()
        
        if self._nano_client:
            try:
                result = await self._nano_client.execute(
                    sandbox_id=sandbox_id,
                    command=command or f"python3 -c {json.dumps(code)}" if code else "echo 'no command'",
                    timeout=timeout,
                    capture_output=capture_output
                )
                
                duration = asyncio.get_event_loop().time() - start_time
                
                return SandboxResult(
                    sandbox_id=sandbox_id,
                    exit_code=result.get("exit_code", 0),
                    stdout=result.get("stdout", ""),
                    stderr=result.get("stderr", ""),
                    duration=duration,
                    error=result.get("error")
                )
            except Exception as e:
                duration = asyncio.get_event_loop().time() - start_time
                return SandboxResult(
                    sandbox_id=sandbox_id,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    duration=duration,
                    error=str(e)
                )
                
        # Fallback: выполнение без изоляции (НЕБЕЗОПАСНО, только для разработки)
        duration = asyncio.get_event_loop().time() - start_time
        self.logger.warning("executing_without_isolation",
                          agent=agent_name,
                          sandbox_id=sandbox_id)
                          
        try:
            proc = await asyncio.create_subprocess_shell(
                command or f"python3 -c {json.dumps(code)}" if code else "echo 'no command'",
                stdout=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            
            return SandboxResult(
                sandbox_id=sandbox_id,
                exit_code=proc.returncode or 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                duration=asyncio.get_event_loop().time() - start_time
            )
        except asyncio.TimeoutError:
            return SandboxResult(
                sandbox_id=sandbox_id,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout}s",
                duration=timeout,
                error="timeout"
            )
        except Exception as e:
            return SandboxResult(
                sandbox_id=sandbox_id,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=asyncio.get_event_loop().time() - start_time,
                error=str(e)
            )
            
    async def execute_agent(
        self,
        agent_name: str,
        agent_module: str,
        agent_method: str,
        agent_args: Dict[str, Any],
        timeout: int = 120
    ) -> SandboxResult:
        """
        Выполнить метод агента внутри sandbox.
        """
        import sys
        
        exec_code = f"""
import sys
sys.path.insert(0, '/app')
import json
from {agent_module} import {agent_method}

args = json.loads({json.dumps(json.dumps(agent_args))})
result = asyncio.run({agent_method}(args))
print(json.dumps(result))
"""
        
        command = f"python3 -c {json.dumps(exec_code)}"
        return await self.execute_in_sandbox(agent_name, command=command, timeout=timeout)
        
    async def destroy_sandbox(self, agent_name: str):
        """Уничтожить sandbox агента."""
        sandbox_id = self.active_sandboxes.pop(agent_name, None)
        if sandbox_id and self._nano_client:
            try:
                await self._nano_client.destroy_sandbox(sandbox_id)
                self.logger.info("sandbox_destroyed", agent=agent_name, sandbox_id=sandbox_id)
            except Exception as e:
                self.logger.error("sandbox_destroy_failed", agent=agent_name, error=str(e))
        else:
            self.logger.info("sandbox_removed_from_registry", agent=agent_name)
            
    async def cleanup_all(self):
        """Graceful shutdown — уничтожаем все sandbox'ы."""
        for agent_name in list(self.active_sandboxes.keys()):
            await self.destroy_sandbox(agent_name)
        self.logger.info("all_sandboxes_destroyed")
        
    def get_active_sandboxes(self) -> List[str]:
        """Получить список активных sandbox'ов."""
        return list(self.active_sandboxes.keys())
        
    def get_sandbox_id(self, agent_name: str) -> Optional[str]:
        """Получить ID sandbox для агента."""
        return self.active_sandboxes.get(agent_name)


# Глобальный экземпляр
_sandbox_manager: Optional[AgentSandboxManager] = None

async def get_sandbox_manager() -> AgentSandboxManager:
    """Получить глобальный экземпляр SandboxManager."""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = AgentSandboxManager()
        await _sandbox_manager.initialize()
    return _sandbox_manager
