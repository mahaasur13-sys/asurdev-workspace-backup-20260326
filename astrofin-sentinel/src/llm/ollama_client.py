import os, httpx, json, re
from typing import Optional
from dataclasses import dataclass, field

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder-32b")
DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_TIMEOUT = 120.0

class OllamaError(Exception): pass
class OllamaConnectionError(OllamaError): pass
class OllamaModelError(OllamaError): pass

@dataclass
class OllamaLLM:
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    temperature: float = 0.0
    system: Optional[str] = None
    max_tokens: Optional[int] = None
    _client: httpx.Client = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout, follow_redirects=True)

    def __del__(self):
        if hasattr(self, "_client") and self._client:
            self._client.close()

    def _post(self, path, data):
        try:
            resp = self._client.post(path, json=data)
        except httpx.ConnectError as e:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}") from e
        if resp.status_code == 404:
            raise OllamaModelError(f"Model not found: {self.model}")
        if resp.status_code >= 500:
            raise OllamaError(f"Server error {resp.status_code}")
        resp.raise_for_status()
        return resp.json()

    def chat(self, messages, temperature=None, max_tokens=None, stop=None, tools=None):
        payload = {"model": self.model, "messages": messages, "stream": False}
        t = temperature if temperature is not None else self.temperature
        if t: payload["temperature"] = t
        if max_tokens or self.max_tokens: payload["options"] = {"num_predict": max_tokens or self.max_tokens}
        if stop: payload["stop"] = stop
        if tools: payload["tools"] = tools
        data = self._post("/api/chat", payload)
        if "error" in data: raise OllamaModelError(str(data["error"]))
        return data.get("message", {})

    def invoke(self, prompt):
        if isinstance(prompt, str): messages = [{"role": "user", "content": prompt}]
        else: messages = prompt
        result = self.chat(messages)
        return OllamaResponse(content=result.get("content", ""), model=self.model, raw=result)

    def is_alive(self):
        try: return self._client.get("/api/tags").status_code == 200
        except: return False

    def list_models(self):
        try: return self._post("/api/tags", {}).get("models", [])
        except: return []

@dataclass
class OllamaResponse:
    content: str
    model: str
    raw: dict = field(default_factory=dict)
    def __str__(self): return self.content

_default_llm = None
def get_default_llm():
    global _default_llm
    if _default_llm is None:
        _default_llm = OllamaLLM(model=os.getenv("OLLAMA_MODEL", DEFAULT_MODEL),
                                 base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
                                 temperature=0.0)
    return _default_llm

SELF_CRITIQUE_PROMPT = (
    "You are evaluating whether historical cases are relevant to a current trading situation.\n\n"
    "CURRENT TECHNICAL ANALYSIS:\n{tech_description}\n\n"
    "RETRIEVED SIMILAR CASES:\n{cases_text}\n\n"
    "Respond in format:\nRELEVANCE_SCORE: 0.0-1.0\nREASONING: ...\nADJUSTED_CONFIDENCE: 0.0-1.0"
)

REFORMULATE_PROMPT = (
    "Reformulate this trading query to find more relevant historical cases.\n\n"
    "ORIGINAL: {original_query}\nCONTEXT: {tech_description}\nFAILED: {failed_reason}\n\n"
    "Return only the reformulated query."
)

def _build_tech_description(technical_result):
    parts = []
    if technical_result.get("rsi"):
        rsi = technical_result["rsi"]
        state = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
        parts.append(f"RSI={rsi:.1f} ({state})")
    if technical_result.get("macd"):
        hist = technical_result["macd"].get("histogram", 0)
        parts.append(f"MACD histogram={hist:.4f}")
    if technical_result.get("detected_patterns"):
        patterns = [p.get("pattern_type", "unknown") for p in technical_result["detected_patterns"]]
        parts.append("Patterns: " + ", ".join(patterns))
    parts.append(f"Bullish: {technical_result.get('bullish_score', 0.5):.2f}, Bearish: {technical_result.get('bearish_score', 0.5):.2f}")
    return "; ".join(parts) if parts else "No technical details"

def evaluate_retrieval_relevance_ollama(technical_result, retrieved_cases, llm=None):
    if llm is None: llm = get_default_llm()
    if not retrieved_cases:
        return {"is_relevant": False, "self_critique_score": 0.0,
                "self_critique_reasoning": "No cases found.",
                "adjusted_confidence": technical_result.get("confidence", 0.5) * 0.8}
    tech_desc = _build_tech_description(technical_result)
    cases_text = "\n".join([
        f"- {c.get('pattern_type','unknown')} on {c.get('symbol','')}: {c.get('outcome','')} (sim={c.get('similarity_score',0):.3f})"
        for c in retrieved_cases[:3]])
    prompt = SELF_CRITIQUE_PROMPT.format(tech_description=tech_desc, cases_text=cases_text)
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)
    score, reasoning, adjusted = 0.5, "", technical_result.get("confidence", 0.5)
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("RELEVANCE_SCORE:"):
            try: score = float(line.split(":",1)[1].strip())
            except: pass
        elif line.startswith("REASONING:"): reasoning = line.split(":",1)[1].strip()
        elif line.startswith("ADJUSTED_CONFIDENCE:"):
            try: adjusted = float(line.split(":",1)[1].strip())
            except: pass
    is_relevant = score >= 0.4
    if not is_relevant: adjusted = technical_result.get("confidence", 0.5) * 0.7
    return {"is_relevant": is_relevant, "self_critique_score": score,
            "self_critique_reasoning": reasoning, "adjusted_confidence": adjusted}

def reformulate_query_ollama(original_query, technical_result, failed_reason, llm=None):
    if llm is None: llm = get_default_llm()
    tech_desc = _build_tech_description(technical_result)
    prompt = REFORMULATE_PROMPT.format(original_query=original_query, tech_description=tech_desc, failed_reason=failed_reason)
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("```") and len(line) > 10: return line
    return original_query
