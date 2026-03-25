"""
Base agent class for LangGraph nodes.
All agents inherit from this class with structured prompts and validation.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel

from contracts.sentinel_state import SentinelState, AgentResult

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=AgentResult)


class BaseLangGraphAgent(ABC, Generic[T]):
    """
    Base class for all LangGraph agent nodes.
    
    Subclasses must implement:
    - system_prompt() -> str
    - build_context(state: SentinelState) -> str
    - parse_response(raw: str) -> T
    
    Features:
    - Structured prompts stored in class (not in __init__)
    - JSON parsing with fallback
    - Validation of output
    """
    
    # Override in subclass
    agent_name: str = "base_agent"
    
    def __init__(self, model: str | None = None, temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        self._llm_client = None  # Initialized lazily
    
    def _get_llm_client(self):
        """Lazy LLM client initialization."""
        if self._llm_client is None:
            from llm.ollama_client import OllamaClient
            self._llm_client = OllamaClient()
        return self._llm_client
    
    @abstractmethod
    def system_prompt(self) -> str:
        """Returns the system prompt for this agent."""
        raise NotImplementedError
    
    @abstractmethod
    def build_context(self, state: SentinelState) -> str:
        """
        Build the context string from state.
        IMPORTANT: Do NOT pass raw astro calculations to LLM.
        Pass only verified interpretations.
        """
        raise NotImplementedError
    
    def invoke(self, state: SentinelState) -> T:
        """
        Main entry point for LangGraph node.
        
        Args:
            state: Current SentinelState
        
        Returns:
            AgentResult subclass
        """
        logger.info(f"[{self.agent_name}] Invoking agent")
        
        # Build context
        context = self.build_context(state)
        
        # Build full prompt
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": context},
        ]
        
        # Call LLM
        raw_response = self._call_llm(messages)
        
        # Parse response
        result = self.parse_response(raw_response)
        
        logger.info(
            f"[{self.agent_name}] Completed: "
            f"recommendation={result.recommendation}, confidence={result.confidence:.2f}"
        )
        
        return result
    
    def _call_llm(self, messages: list[dict]) -> str:
        """Call LLM via Ollama."""
        client = self._get_llm_client()
        
        response = client.chat(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        
        return response.get("message", {}).get("content", "")
    
    def parse_response(self, raw: str) -> T:
        """
        Parse LLM response into structured result.
        Handles markdown code blocks and invalid JSON.
        """
        # Extract JSON from markdown if needed
        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            raw = raw[start:end]
        elif "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            raw = raw[start:end]
        
        # Remove trailing commas
        raw = raw.replace(",\n}", "\n}")
        raw = raw.replace(",\n]", "\n]")
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.agent_name}] JSON parse error: {e}, using fallback")
            return self._fallback_result(str(e))
        
        return self._validate_result(data)
    
    @abstractmethod
    def _validate_result(self, data: dict) -> T:
        """Validate and convert dict to typed result."""
        raise NotImplementedError
    
    def _fallback_result(self, error: str) -> T:
        """Fallback when parsing fails."""
        from contracts.sentinel_state import AgentResult
        
        class FallbackResult(AgentResult):
            pass
        
        return FallbackResult(
            agent_name=self.agent_name,
            recommendation="hold",
            confidence=0.3,
            reasoning=f"Parse error: {error}. Holding position.",
            warnings=["Agent returned fallback due to parse error"],
        )
