"""
Base agent implementation with Ollama/OpenAI/LangChain.
Updated for v3.1 — uses unified AgentResponse from agents.types.
"""

import os
import json
import re
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from abc import ABC, abstractmethod

# Use unified types
from agents.types import AgentResponse

try:
    from langchain_ollama import ChatOllama
    LANGCHAIN_OLLAMA_AVAILABLE = True
except ImportError:
    LANGCHAIN_OLLAMA_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_OPENAI_AVAILABLE = True
except ImportError:
    LANGCHAIN_OPENAI_AVAILABLE = False

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def _sanitize_json_response(content: str) -> str:
    """
    Sanitize LLM JSON response before parsing.
    FIX: Prevent JSON injection by stripping control characters
    and ensuring only valid JSON structure.
    """
    # Strip non-printable characters except newlines and spaces
    content = re.sub(r'[\x00-\x1F\x7F]', '', content)
    # Remove any content before first { or [
    first_brace = content.find('{')
    first_bracket = content.find('[')
    start = min(first_brace if first_brace >= 0 else len(content),
                first_bracket if first_bracket >= 0 else len(content))
    if start < len(content):
        content = content[start:]
    # Remove any content after last } or ]
    last_brace = content.rfind('}')
    last_bracket = content.rfind(']')
    end = max(last_brace if last_brace >= 0 else -1,
              last_bracket if last_bracket >= 0 else -1)
    if end >= 0:
        content = content[:end + 1]
    return content.strip()


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    All agents must implement analyze() method.
    Agents can use LLM (via LangChain/Ollama) or be rule-based.
    """
    
    def __init__(
        self,
        name: str,
        model: str = None,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        timeout: int = 120,
        system_prompt: str = "",
        enable_memory: bool = False,
    ):
        self.name = name
        self.model = model or os.environ.get("asurdev_MODEL", "qwen3-coder:30b-a3b")
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        self.system_prompt = system_prompt
        self.enable_memory = enable_memory
        
        self.llm = None
        if LANGCHAIN_OLLAMA_AVAILABLE:
            try:
                self.llm = ChatOllama(
                    model=self.model,
                    base_url=base_url,
                    temperature=temperature,
                    timeout=timeout,
                )
            except Exception:
                pass
        elif LANGCHAIN_OPENAI_AVAILABLE:
            try:
                api_key = os.environ.get("asurdev_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
                self.llm = ChatOpenAI(
                    model=self.model or "gpt-4o-mini",
                    api_key=api_key,
                    temperature=temperature,
                    timeout=timeout,
                )
            except Exception:
                pass
    
    def _build_prompt(self, prompt: str, memory_context: str = "") -> str:
        """Build prompt with optional memory context for RAG."""
        if not memory_context or not self.enable_memory:
            return prompt
        
        return f"""{prompt}

{memory_context}

[Memory Context] The information above shows similar past analyses. Use it to inform your response, especially noting any patterns or past outcomes if relevant to the current analysis."""

    async def think(self, prompt: str) -> AgentResponse:
        """
        Generate response using LLM or fallback to neutral.
        
        Attempts JSON parsing, falls back to raw text summary.
        """
        if self.llm:
            try:
                messages = []
                if self.system_prompt:
                    messages.append(SystemMessage(content=self.system_prompt))
                messages.append(HumanMessage(content=prompt))
                
                response = await self.llm.ainvoke(messages)
                content = response.content
                
                # Try JSON parsing with sanitization (FIX: prevent injection)
                content = _sanitize_json_response(content)
                try:
                    data = json.loads(content)
                    # Validate required fields exist
                    if not isinstance(data, dict):
                        raise ValueError("JSON must be an object")
                    return AgentResponse(
                        agent_name=self.name,
                        signal=str(data.get("signal", "NEUTRAL")),
                        confidence=float(data.get("confidence", 50)),
                        summary=str(data.get("summary", "")),
                        details=data,
                        metadata={"model": self.model}
                    )
                except (json.JSONDecodeError, ValueError) as e:
                    return AgentResponse(
                        agent_name=self.name,
                        signal="NEUTRAL",
                        confidence=50,
                        summary=content[:500],
                        details={"raw": content},
                        metadata={"model": self.model, "parse_error": True}
                    )
                    
            except Exception as e:
                return AgentResponse(
                    agent_name=self.name,
                    signal="ERROR",
                    confidence=0,
                    summary=str(e),
                    details={"error": str(e)},
                    metadata={"model": self.model}
                )
        else:
            return AgentResponse(
                agent_name=self.name,
                signal="NEUTRAL",
                confidence=50,
                summary="LLM not available — using fallback",
                details={"mode": "fallback", "llm_available": LANGCHAIN_OLLAMA_AVAILABLE or LANGCHAIN_OPENAI_AVAILABLE},
                metadata={"model": self.model}
            )
    
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Main analysis method.
        
        All agents must implement this.
        Should return AgentResponse with signal, confidence, summary, details.
        """
        pass


class RuleBasedAgent(BaseAgent):
    """
    Agent that uses rules instead of LLM.
    
    Useful for deterministic analysis (like astrology calculations).
    """
    
    def __init__(self, name: str, rules: List[Callable], **kwargs):
        super().__init__(name, **kwargs)
        self.rules = rules
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        for rule in self.rules:
            result = rule(context)
            if result is not None:
                return result
        
        return AgentResponse(
            agent_name=self.name,
            signal="NEUTRAL",
            confidence=50,
            summary="No rule matched — defaulting to neutral",
            details={"rules_checked": len(self.rules)}
        )
