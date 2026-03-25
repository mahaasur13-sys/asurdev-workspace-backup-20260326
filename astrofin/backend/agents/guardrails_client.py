"""
NeMo Guardrails Integration for AstroFin Sentinel.

Provides content filtering, safety checks, and audit logging for all agent outputs.
"""

from __future__ import annotations

import json
import re
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import structlog

try:
    from nemoguardrails import RailsConfig
    from nemoguardrails.library import InputRails, OutputRails
    from nemoguardrails.actions import action
    HAS_NEMO = True
except ImportError:
    HAS_NEMO = False
    RailsConfig = None

logger = structlog.get_logger(__name__)


class SafetyLevel(str, Enum):
    """Levels of content safety filtering."""
    OFF = "off"           # No filtering
    STANDARD = "standard" # Basic financial advice filtering
    STRICT = "strict"    # Full content moderation


@dataclass
class GuardrailsConfig:
    """Configuration for NeMo Guardrails."""
    enabled: bool = True
    safety_level: SafetyLevel = SafetyLevel.STANDARD
    
    # Content filters
    block_financial_advice: bool = True  # Block "buy/sell" without disclaimer
    block_defamation: bool = True        # Block personal attacks
    block_pii: bool = True             # Block personally identifiable info
    block_hallucination: bool = True    # Block unsupported facts
    
    # Regex patterns for content filtering
    BLOCKED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"\b\d{3}-\d{2}-\d{4}\b",      # SSN
        r"\b\d{16}\b",                  # Credit card
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    ])
    
    # Allowed trading advice phrases
    ALLOWED_PHRASES: List[str] = field(default_factory=lambda: [
        "This is not financial advice",
        "Trading involves risk",
        "Backtested results",
        "Hypothetical scenario",
    ])
    
    # Blocked trading phrases (too definitive)
    BLOCKED_PHRASES: List[str] = field(default_factory=lambda: [
        r"guaranteed", r"will definitely", r"certain to",
        r"100% sure", r"no risk", r"can't lose",
    ])


@dataclass
class GuardrailsResult:
    """Result of content safety check."""
    passed: bool
    filtered_content: str
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class NeMoGuardrailsClient:
    """
    NeMo Guardrails integration for AstroFin.
    
    Features:
    - Input/Output content filtering
    - Financial advice safety checks
    - Hallucination detection (factual claims without sources)
    - PII redaction
    - Audit logging
    """
    
    def __init__(self, config: Optional[GuardrailsConfig] = None):
        self.config = config or GuardrailsConfig()
        self._rails = None
        self._audit_log: List[Dict[str, Any]] = []
        self.logger = logger.bind(component="Guardrails")
        
        if self.config.enabled and HAS_NEMO:
            self._init_nemo_rails()
    
    def _init_nemo_rails(self):
        """Initialize NeMo Guardrails with custom config."""
        try:
            # Create a minimal rails config
            config_content = """
            - channel: internal
              stages:
                - pre
                - post
            """
            self._rails = RailsConfig.from_content(config_content)
            self.logger.info("nemo_guardrails_initialized", safety_level=self.config.safety_level.value)
        except Exception as e:
            self.logger.warning("nemo_guardrails_init_failed", error=str(e))
            self._rails = None
    
    async def check_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> GuardrailsResult:
        """
        Check user input before it reaches any agent.
        
        Args:
            user_input: Raw user query
            context: Additional context (user_id, session_id, etc.)
        
        Returns:
            GuardrailsResult with filtered content and violations
        """
        start_time = datetime.utcnow()
        violations = []
        warnings = []
        filtered = user_input
        
        if not self.config.enabled:
            return GuardrailsResult(passed=True, filtered_content=filtered)
        
        # Check for PII in input
        if self.config.block_pii:
            for pattern in self.config.BLOCKED_PATTERNS:
                matches = re.findall(pattern, filtered)
                if matches:
                    violations.append(f"PII detected: {pattern}")
                    filtered = re.sub(pattern, "[REDACTED]", filtered)
        
        # Check for prompt injection
        if self._check_prompt_injection(filtered):
            violations.append("Prompt injection attempt detected")
        
        # Check for blocked phrases
        for phrase in self.config.BLOCKED_PHRASES:
            if re.search(phrase, filtered, re.IGNORECASE):
                violations.append(f"Blocked phrase detected: {phrase}")
        
        # Log to audit trail
        self._log_audit(
            event_type="input_check",
            content=user_input,
            filtered_content=filtered,
            violations=violations,
            context=context,
            duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        passed = len(violations) == 0
        
        if not passed:
            self.logger.warning("input_blocked", violations=violations, context=context)
        
        return GuardrailsResult(
            passed=passed,
            filtered_content=filtered,
            violations=violations,
            warnings=warnings,
            metadata={
                "safety_level": self.config.safety_level.value,
                "nemo_enabled": self._rails is not None,
            }
        )
    
    async def check_output(
        self,
        content: str,
        agent_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailsResult:
        """
        Check agent output before it's returned to user.
        
        Args:
            content: Raw agent response
            agent_name: Name of the agent that produced the output
            context: Additional context
        
        Returns:
            GuardrailsResult with filtered content and violations
        """
        start_time = datetime.utcnow()
        violations = []
        warnings = []
        filtered = content
        
        if not self.config.enabled:
            return GuardrailsResult(passed=True, filtered_content=filtered)
        
        # Check for financial advice without disclaimer
        if self.config.block_financial_advice:
            if self._contains_trading_signal(filtered):
                if not any(phrase in filtered for phrase in self.config.ALLOWED_PHRASES):
                    warnings.append("Trading signal without disclaimer")
                    filtered = self._add_disclaimer(filtered)
        
        # Check for hallucinations (claims without sources)
        if self.config.block_hallucination:
            hallucination_flags = self._detect_hallucination(content, context)
            if hallucination_flags:
                warnings.extend(hallucination_flags)
        
        # Check for definitive language
        for phrase in self.config.BLOCKED_PHRASES:
            if re.search(phrase, filtered, re.IGNORECASE):
                violations.append(f"Overly definitive claim: {phrase}")
                filtered = re.sub(phrase, "[MODERATED]", filtered, flags=re.IGNORECASE)
        
        # Redact PII
        if self.config.block_pii:
            for pattern in self.config.BLOCKED_PATTERNS:
                if re.search(pattern, filtered):
                    violations.append(f"PII in output: {pattern}")
                    filtered = re.sub(pattern, "[REDACTED]", filtered)
        
        # Log to audit trail
        self._log_audit(
            event_type="output_check",
            content=content,
            filtered_content=filtered,
            violations=violations,
            warnings=warnings,
            agent_name=agent_name,
            context=context,
            duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        passed = len(violations) == 0
        
        self.logger.info(
            "output_checked",
            agent=agent_name,
            passed=passed,
            violations=len(violations),
            warnings=len(warnings)
        )
        
        return GuardrailsResult(
            passed=passed,
            filtered_content=filtered,
            violations=violations,
            warnings=warnings,
            metadata={
                "agent_name": agent_name,
                "safety_level": self.config.safety_level.value,
            }
        )
    
    def _check_prompt_injection(self, text: str) -> bool:
        """Detect prompt injection attempts."""
        injection_patterns = [
            r"ignore\s+(previous|all)\s+(instructions?|commands?|rules?)",
            r"disregard\s+(previous|all)\s+(instructions?|commands?)",
            r"forget\s+(previous|all)\s+(instructions?|commands?)",
            r"new\s+instruction[s]?:\s*",
            r"system\s*prompt\s*:",
            r"you\s+are\s+now\s+",
            r"pretend\s+you\s+are",
            r"roleplay\s+as",
        ]
        
        text_lower = text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _contains_trading_signal(self, text: str) -> bool:
        """Check if text contains trading signals."""
        signal_patterns = [
            r"\b(buy|sell|long|short)\b.*\b(btc|eth|stock|option)\b",
            r"(price\s+(will|going\s+to|should))\s+(go\s+)?(up|down)",
            r"(target|stop\s*loss|take\s+profit)\s*:?\s*\$",
            r"(entering|exiting|opening|closing)\s+(position|trade)",
        ]
        
        for pattern in signal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _add_disclaimer(self, content: str) -> str:
        """Add financial disclaimer to content."""
        disclaimer = "\n\n⚠️ **DISCLAIMER**: This is not financial advice. Trading involves significant risk. Past performance does not guarantee future results."
        return content + disclaimer
    
    def _detect_hallucination(self, content: str, context: Optional[Dict[str, Any]]) -> List[str]:
        """Detect potential hallucinations (unsupported factual claims)."""
        flags = []
        
        # Claims about specific numbers without context
        specific_claims = re.findall(
            r"(will be|is|at|to|by)\s+\$[\d,]+(?:\.\d{2})?",
            content
        )
        if specific_claims and not context.get("has_price_data"):
            flags.append("Specific price claim without data source")
        
        # Definite predictions
        if re.search(r"will\s+(definitely|definitely|certainly)", content, re.IGNORECASE):
            flags.append("Definite prediction language detected")
        
        return flags
    
    def _log_audit(
        self,
        event_type: str,
        content: str,
        filtered_content: str,
        violations: List[str],
        **kwargs
    ):
        """Log to audit trail."""
        entry = {
            "event_type": event_type,
            "content_hash": hash(content) % 10**10,  # Privacy: don't store content
            "filtered": filtered_content != content,
            "violations": violations,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self._audit_log.append(entry)
        
        # Keep only last 1000 entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
        
        # Log to structlog
        self.logger.info(
            f"guardrails_audit_{event_type}",
            violations_count=len(violations),
            filtered=entry["filtered"],
            **{k: v for k, v in kwargs.items() if k != "context"}
        )
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]
    
    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        total = len(self._audit_log)
        blocked = sum(1 for e in self._audit_log if not e.get("violations") == [])
        
        return {
            "total_events": total,
            "blocked_events": blocked,
            "block_rate": round(blocked / total if total > 0 else 0, 3),
            "safety_level": self.config.safety_level.value,
        }


# Global instance
_guardrails_client: Optional[NeMoGuardrailsClient] = None


def get_guardrails_client(config: Optional[GuardrailsConfig] = None) -> NeMoGuardrailsClient:
    """Get global Guardrails client instance."""
    global _guardrails_client
    if _guardrails_client is None:
        _guardrails_client = NeMoGuardrailsClient(config)
    return _guardrails_client


async def check_agent_output(
    content: str,
    agent_name: str,
    context: Optional[Dict[str, Any]] = None
) -> GuardrailsResult:
    """Convenience function to check agent output."""
    client = get_guardrails_client()
    return await client.check_output(content, agent_name, context)
