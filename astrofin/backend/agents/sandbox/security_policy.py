"""
Security Policy — политики безопасности для NanoClaw sandbox.
"""
from __future__ import annotations
from typing import Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum
import re


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Permission(str, Enum):
    # Файловая система
    FS_READ = "fs:read"
    FS_WRITE = "fs:write"
    FS_EXEC = "fs:exec"
    FS_NETWORK = "fs:network"  # доступ к /proc/net
    
    # Сеть
    NET_EGRESS = "net:egress"  # только исходящий
    NET_INGRESS = "net:ingress"
    NET_INTERNAL = "net:internal"
    
    # Процессы
    PROC_CREATE = "proc:create"
    PROC_KILL = "proc:kill"
    PROC_INSPECT = "proc:inspect"
    
    # Система
    SYS_ADMIN = "sys:admin"
    SYS_RAW_SOCKET = "sys:raw_socket"
    SYS_BOOT = "sys:boot"


@dataclass
class SecurityPolicy:
    """Политика безопасности для sandbox."""
    name: str
    threat_level: ThreatLevel
    allowed_permissions: Set[Permission] = field(default_factory=set)
    denied_permissions: Set[Permission] = field(default_factory=set)
    allowed_paths: Set[str] = field(default_factory=set)  # /app, /tmp, etc.
    denied_paths: Set[str] = field(default_factory=set)
    allowed_networks: Set[str] = field(default_factory=set)  # домены
    denied_networks: Set[str] = field(default_factory=set)
    max_cpu: float = 2.0
    max_memory_mb: int = 2048
    max_disk_mb: int = 8192
    max_open_files: int = 256
    max_processes: int = 128
    network_egress_only: bool = True
    read_only_rootfs: bool = True
    seccomp_mode: str = "default"  # default, strict, custom
    no_new_privileges: bool = True
    capabilities_drop: List[str] = field(default_factory=list)  # CAP_SYS_ADMIN, etc.


class SecurityPolicyManager:
    """Менеджер политик безопасности."""
    
    # Встроенные политики
    BUILTIN_POLICIES: Dict[str, SecurityPolicy] = {}
    
    def __init__(self):
        self._init_builtin_policies()
        
    def _init_builtin_policies(self):
        """Инициализация встроенных политик."""
        
        # Минимальная изоляция — только для доверенных агентов
        self.BUILTIN_POLICIES["minimal"] = SecurityPolicy(
            name="minimal",
            threat_level=ThreatLevel.LOW,
            allowed_permissions={Permission.FS_READ, Permission.NET_EGRESS},
            denied_permissions={Permission.SYS_ADMIN, Permission.SYS_RAW_SOCKET},
            allowed_paths={"/app", "/tmp"},
            denied_paths={"/etc", "/root", "/home"},
            allowed_networks={"api.binance.com", "api.coingecko.com"},
            max_cpu=1.0,
            max_memory_mb=512,
            max_disk_mb=1024,
            capabilities_drop=["CAP_SYS_ADMIN", "CAP_NET_ADMIN"]
        )
        
        # Standard — баланс изоляции и функциональности
        self.BUILTIN_POLICIES["standard"] = SecurityPolicy(
            name="standard",
            threat_level=ThreatLevel.MEDIUM,
            allowed_permissions={Permission.FS_READ, Permission.NET_EGRESS, Permission.PROC_CREATE},
            denied_permissions={Permission.SYS_ADMIN, Permission.SYS_RAW_SOCKET, Permission.PROC_KILL},
            allowed_paths={"/app", "/tmp", "/var/tmp"},
            denied_paths={"/etc/passwd", "/root", "/home", "/var/log"},
            denied_networks={"localhost", "127.0.0.1", "0.0.0.0"},
            max_cpu=2.0,
            max_memory_mb=2048,
            max_disk_mb=8192,
            network_egress_only=True,
            read_only_rootfs=True,
            capabilities_drop=["CAP_SYS_ADMIN", "CAP_NET_ADMIN", "CAP_NET_RAW"]
        )
        
        # Strict — для агентов с внешним вводом
        self.BUILTIN_POLICIES["strict"] = SecurityPolicy(
            name="strict",
            threat_level=ThreatLevel.HIGH,
            allowed_permissions={Permission.FS_READ},
            denied_permissions={
                Permission.FS_WRITE, Permission.FS_EXEC, Permission.FS_NETWORK,
                Permission.NET_EGRESS, Permission.NET_INGRESS,
                Permission.SYS_ADMIN, Permission.SYS_RAW_SOCKET,
                Permission.PROC_KILL, Permission.PROC_INSPECT
            },
            allowed_paths={"/app"},
            denied_paths={"/", "/etc", "/root", "/home", "/tmp", "/var"},
            max_cpu=1.0,
            max_memory_mb=1024,
            max_disk_mb=1024,
            max_open_files=64,
            max_processes=32,
            network_egress_only=True,
            read_only_rootfs=True,
            seccomp_mode="strict",
            no_new_privileges=True,
            capabilities_drop=["ALL"]
        )
        
        # Interactive — для агентов взаимодействующих с пользователем
        self.BUILTIN_POLICIES["interactive"] = SecurityPolicy(
            name="interactive",
            threat_level=ThreatLevel.MEDIUM,
            allowed_permissions={
                Permission.FS_READ, Permission.FS_WRITE,
                Permission.NET_EGRESS, Permission.PROC_CREATE
            },
            denied_permissions={Permission.SYS_ADMIN, Permission.SYS_RAW_SOCKET},
            allowed_paths={"/app", "/tmp", "/home/user"},
            denied_paths={"/etc", "/root", "/var/log"},
            allowed_networks={"api.binance.com", "api.coingecko.com", "api.polygon.io"},
            max_cpu=2.0,
            max_memory_mb=4096,
            max_disk_mb=16384,
            network_egress_only=True,
            read_only_rootfs=True,
            capabilities_drop=["CAP_SYS_ADMIN"]
        )
        
        # Astro — специализированная политика для астрологических агентов
        self.BUILTIN_POLICIES["astro"] = SecurityPolicy(
            name="astro",
            threat_level=ThreatLevel.LOW,
            allowed_permissions={
                Permission.FS_READ, Permission.NET_EGRESS,
                Permission.PROC_CREATE
            },
            denied_permissions={
                Permission.SYS_ADMIN, Permission.SYS_RAW_SOCKET,
                Permission.PROC_KILL, Permission.PROC_INSPECT
            },
            allowed_paths={"/app", "/tmp", "/app/swiss_ephemeris"},
            denied_paths={"/etc", "/root", "/home"},
            allowed_networks={
                "api.binance.com", "api.coingecko.com",
                "api.polygon.io", "swiss Ephemeris data"
            },
            max_cpu=2.0,
            max_memory_mb=2048,
            max_disk_mb=8192,
            network_egress_only=True,
            read_only_rootfs=True,
            capabilities_drop=["CAP_SYS_ADMIN", "CAP_NET_ADMIN"]
        )
        
    def get_policy(self, name: str) -> SecurityPolicy:
        """Получить политику по имени."""
        if name not in self.BUILTIN_POLICIES:
            raise ValueError(f"Unknown policy: {name}. Available: {list(self.BUILTIN_POLICIES.keys())}")
        return self.BUILTIN_POLICIES[name]
        
    def get_policy_for_agent(self, agent_name: str) -> SecurityPolicy:
        """Получить подходящую политику для агента."""
        # Специализированные политики по типу агента
        if "astro" in agent_name.lower() or "electoral" in agent_name.lower():
            return self.BUILTIN_POLICIES["astro"]
        elif "predictor" in agent_name.lower() or "quant" in agent_name.lower():
            return self.BUILTIN_POLICIES["standard"]
        elif "user" in agent_name.lower() or "interactive" in agent_name.lower():
            return self.BUILTIN_POLICIES["interactive"]
        elif "sandbox" in agent_name.lower() or "untrusted" in agent_name.lower():
            return self.BUILTIN_POLICIES["strict"]
        else:
            return self.BUILTIN_POLICIES["standard"]
            
    def create_custom_policy(
        self,
        name: str,
        base_policy: str = "standard",
        **overrides
    ) -> SecurityPolicy:
        """Создать кастомную политику на основе существующей."""
        base = self.get_policy(base_policy)
        
        custom = SecurityPolicy(
            name=name,
            threat_level=overrides.get("threat_level", base.threat_level),
            allowed_permissions=overrides.get("allowed_permissions", base.allowed_permissions.copy()),
            denied_permissions=overrides.get("denied_permissions", base.denied_permissions.copy()),
            allowed_paths=overrides.get("allowed_paths", base.allowed_paths.copy()),
            denied_paths=overrides.get("denied_paths", base.denied_paths.copy()),
            allowed_networks=overrides.get("allowed_networks", base.allowed_networks.copy()),
            denied_networks=overrides.get("denied_networks", base.denied_networks.copy()),
            max_cpu=overrides.get("max_cpu", base.max_cpu),
            max_memory_mb=overrides.get("max_memory_mb", base.max_memory_mb),
            max_disk_mb=overrides.get("max_disk_mb", base.max_disk_mb),
            max_open_files=overrides.get("max_open_files", base.max_open_files),
            max_processes=overrides.get("max_processes", base.max_processes),
            network_egress_only=overrides.get("network_egress_only", base.network_egress_only),
            read_only_rootfs=overrides.get("read_only_rootfs", base.read_only_rootfs),
            seccomp_mode=overrides.get("seccomp_mode", base.seccomp_mode),
            no_new_privileges=overrides.get("no_new_privileges", base.no_new_privileges),
            capabilities_drop=overrides.get("capabilities_drop", base.capabilities_drop.copy())
        )
        
        self.BUILTIN_POLICIES[name] = custom
        return custom
        
    def validate_policy(self, policy: SecurityPolicy) -> List[str]:
        """Валидировать политику, вернуть список предупреждений."""
        warnings = []
        
        if policy.threat_level == ThreatLevel.HIGH and "CAP_SYS_ADMIN" not in policy.capabilities_drop:
            warnings.append("CRITICAL: High-threat policy should drop CAP_SYS_ADMIN")
            
        if policy.network_egress_only and Permission.NET_INGRESS in policy.allowed_permissions:
            warnings.append("WARNING: Egress-only network but ingress is allowed")
            
        if policy.read_only_rootfs and Permission.FS_WRITE in policy.allowed_permissions:
            warnings.append("WARNING: Read-only rootfs but write is allowed")
            
        if policy.max_memory_mb > 8192:
            warnings.append("NOTE: High memory limit may affect other sandboxes")
            
        if "ALL" not in policy.capabilities_drop and policy.threat_level == ThreatLevel.CRITICAL:
            warnings.append("CRITICAL: Critical threat level should drop ALL capabilities")
            
        return warnings


# Глобальный экземпляр
_policy_manager = SecurityPolicyManager()

def get_policy_manager() -> SecurityPolicyManager:
    return _policy_manager
