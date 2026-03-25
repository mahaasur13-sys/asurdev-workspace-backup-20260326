"""
Ollama LLM Client для AstroFin Sentinel.
Использует прямые HTTP запросы к Ollama API (минуя langchain).
"""
import json
import httpx
from typing import Optional, Dict, Any, List


class OllamaLLM:
    """Прямой клиент к Ollama API."""
    
    DEFAULT_MODEL = "tinyllama:1.1b"
    
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        num_ctx: int = 2048,
    ):
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.num_ctx = num_ctx
        
        # Получаем список доступных моделей
        available = self._get_available_models()
        
        # Выбираем модель
        if model:
            self.model = model
        else:
            self.model = self._select_best_model(available)
        
        print(f"🎯 Ollama LLM: {self.model} @ {base_url}")
        
        # Проверяем что модель работает
        if self._test_model():
            print(f"✅ Ollama connected: {self.model}")
        else:
            print(f"⚠️ Warning: Selected model may not work, trying tinyllama")
            self.model = "tinyllama:1.1b"
            if self._test_model():
                print(f"✅ Fallback to tinyllama:1.1b")
    
    def _get_available_models(self) -> List[str]:
        """Получает список доступных моделей."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception as e:
            print(f"   ⚠️ Failed to get models: {e}")
        return []
    
    def _select_best_model(self, available: List[str]) -> str:
        """Выбирает лучшую доступную модель."""
        priority = [
            "qwen2.5-coder:32b",
            "qwen2.5-coder:14b",
            "qwen2.5-coder:7b",
            "phi4:latest",
            "llama3.2:3b",
            "mistral:7b",
            "tinyllama:1.1b",
        ]
        
        for p in priority:
            if p in available:
                return p
        
        return available[0] if available else self.DEFAULT_MODEL
    
    def _test_model(self) -> bool:
        """Тестирует модель."""
        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "Hi",
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 10}
                },
                timeout=30
            )
            return resp.status_code == 200
        except:
            return False
    
    def is_available(self) -> bool:
        """Проверяет доступность."""
        return self._test_model()
    
    def invoke(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        format: str = "json",
    ) -> str:
        """Вызывает LLM с сообщениями."""
        # Собираем промпт из сообщений
        prompt_parts = []
        
        if system:
            prompt_parts.append(f"[SYSTEM: {system}]")
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"[{role.upper()}: {content}]")
        
        prompt = "\n".join(prompt_parts)
        
        options = {
            "temperature": self.temperature,
            "num_predict": 512,
        }
        
        if format == "json":
            options["format"] = "json"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        
        resp = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        if resp.status_code != 200:
            raise RuntimeError(f"Ollama error: {resp.status_code}")
        
        return resp.json().get("response", "")
    
    def invoke_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Вызывает LLM с парсингом в структурированный формат."""
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        
        enhanced_messages = messages.copy()
        if enhanced_messages:
            enhanced_messages[-1] = {
                **enhanced_messages[-1],
                "content": enhanced_messages[-1]["content"] + 
                           f"\n\nОтвет должен быть валидным JSON с схемой:\n{schema_str}"
            }
        
        response = self.invoke(enhanced_messages, system=system, format="json")
        
        # Парсим JSON
        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Информация о текущей модели."""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "num_ctx": self.num_ctx,
            "available": self.is_available(),
        }


# Глобальный экземпляр
_ollama_llm: Optional[OllamaLLM] = None


def get_ollama(
    model: Optional[str] = None,
    base_url: str = "http://localhost:11434",
) -> OllamaLLM:
    """Lazy singleton для Ollama LLM."""
    global _ollama_llm
    
    if _ollama_llm is None:
        _ollama_llm = OllamaLLM(model=model, base_url=base_url)
    
    return _ollama_llm


def reset_ollama():
    """Сбросить соединение."""
    global _ollama_llm
    _ollama_llm = None
