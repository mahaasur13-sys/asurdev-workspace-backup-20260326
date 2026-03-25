# LangChain Migration Specification — asurdev Sentinel v3.0

> **Status:** Proposed  
> **Author:** asurdev Team  
> **Target Version:** 3.0  
> **Dependencies:** LangChain 0.3.x, LangGraph, LangSmith (optional)

---

## 1. Motivation

### Current Architecture (v2.0)
```
Orchestrator ( asyncio.gather )
    ├── MarketAnalyst (LangChain Ollama)
    ├── BullResearcher (LangChain Ollama)
    ├── BearResearcher (LangChain Ollama)
    ├── AstrologerAgent (Rule-based)
    ├── CycleAgent (Rule-based + TS Parser)
    └── Synthesizer (LangChain Ollama)
```

**Limitations:**
- Sequential aggregation in Synthesizer
- No state persistence between agent calls
- No built-in retry/memory mechanisms
- Hard to add conditional branching

### Target Architecture (v3.0)
```
LangGraph Agentic System
    ├── State Graph with persistence
    ├── Specialized Tool-calling agents
    ├── Conditional routing (edges)
    └── Human-in-the-loop checkpoints
```

---

## 2. Architecture Overview

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                    │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                │
│  │  Entry   │───▶│ Analyst  │───▶│ Research │                │
│  │  Node    │    │  Router  │    │  Agents  │                │
│  └──────────┘    └──────────┘    └──────────┘                │
│       │               │               │                       │
│       │          ┌─────┴─────┐         │                       │
│       │          ▼           ▼         ▼                       │
│       │    ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│       │    │ Technical│ │ Sentiment│ │ Cycle   │              │
│       │    │  Agents  │ │ Bull/Bear│ │ Agents  │              │
│       │    └──────────┘ └──────────┘ └──────────┘              │
│       │               │           │         │                   │
│       │               └─────┬─────┴─────────┘                   │
│       │                     ▼                                   │
│       │              ┌──────────────┐                            │
│       │              │  Astrologer  │                            │
│       │              │   (Meridian  │                            │
│       │              │  + Merriman)  │                            │
│       │              └──────────────┘                            │
│       │                     │                                   │
│       │                     ▼                                   │
│       │              ┌──────────────┐                            │
│       │              │  Synthesizer │                            │
│       │              │  (C.L.E.A.R.)│                            │
│       │              └──────────────┘                            │
│       │                     │                                   │
│       │                     ▼                                   │
│       │              ┌──────────────┐                            │
│       │              │   Output     │                            │
│       │              │  Formatter   │                            │
│       │              └──────────────┘                            │
└───────┴─────────────────────────────────────────────────────────┘
```

### 2.2 LangGraph State

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
import operator

class SentinelState(TypedDict):
    """Shared state across all nodes"""
    
    # Input
    symbol: str
    timeframe: str
    location: tuple[float, float]
    user_action: str  # buy, sell, hold
    
    # Intermediate results (accumulated)
    market_data: dict
    agents_responses: dict
    
    # Agent outputs
    technical_signal: dict
    bull_case: dict
    bear_case: dict
    cycle_analysis: dict
    meridian_analysis: dict
    merriman_analysis: dict
    
    # Final output
    synthesis: dict
    clear_recommendation: dict
    
    # Metadata
    errors: list[str]
    confidence: int
    timestamp: str
```

---

## 3. Agent Definitions

### 3.1 MarketAnalyst (Technical)

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

class TechnicalSignal(BaseModel):
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    confidence: int = Field(ge=0, le=100)
    key_levels: dict = Field(default_factory=dict)
    pattern: str = ""
    indicators: dict = Field(default_factory=dict)

class MarketAnalystAgent:
    """
    Technical analysis agent using LangChain + Ollama.
    """
    
    def __init__(self, model: str = "qwen2.5-coder:32b"):
        self.llm = ChatOllama(
            model=model,
            base_url="http://localhost:11434",
            temperature=0.3,
        )
        self.prompt = """Ты - технический аналитик криптовалют.
Проанализируй данные и верни структурированный ответ.

Верни JSON:
{
    "signal": "BULLISH|BEARISH|NEUTRAL",
    "confidence": 0-100,
    "key_levels": {"support": [], "resistance": []},
    "pattern": "описание паттерна",
    "indicators": {"RSI": value, "MACD": value}
}"""
    
    async def analyze(self, state: SentinelState) -> dict:
        messages = [
            SystemMessage(content=self.prompt),
            HumanMessage(content=f"Symbol: {state['symbol']}\nData: {state['market_data']}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "technical_signal": json.loads(response.content),
            "agents_responses": {"market_analyst": "completed"}
        }
```

### 3.2 Sentiment Agents (Bull/Bear)

```python
class SentimentResearcher:
    """
    Dual-agent: finds bullish AND bearish arguments.
    Uses LangChain's parallel tool calling pattern.
    """
    
    BULL_PROMPT = """Найди бычьи аргументы для {symbol}.
Аргументируй почему нужно покупать/держать.
JSON: {{"signal": "BULLISH", "confidence": 0-100, "reasons": [], "sources": []}}"""
    
    BEAR_PROMPT = """Найди медвежьи аргументы для {symbol}.
Аргументируй почему нужно продавать/остерегаться.
JSON: {{"signal": "BEARISH", "confidence": 0-100, "reasons": [], "sources": []}}"""
    
    async def analyze_bull(self, state: SentinelState) -> dict:
        # ... LangChain invocation
        
    async def analyze_bear(self, state: SentinelState) -> dict:
        # ... LangChain invocation
```

### 3.3 Astrologer (Combined Meridian + Merriman)

```python
class AstrologerNode:
    """
    Combined astrology node that runs:
    1. Meridian planetary lines + elongations
    2. Merriman 7-planet cycles
    
    No LLM needed - rule-based + calculations.
    """
    
    async def analyze(self, state: SentinelState) -> dict:
        # 1. Merriman cycles
        merriman = MerrimanAgent(lat=state['location'][0], lon=state['location'][1])
        merriman_result = await merriman.analyze({"symbol": state['symbol']})
        
        # 2. Meridian methods
        meridian = MeridianAgent(lat=state['location'][0], lon=state['location'][1])
        meridian_result = await meridian.analyze(state)
        
        return {
            "merriman_analysis": merriman_result.details,
            "meridian_analysis": meridian_result.details,
            "cycle_analysis": {
                "signal": merriman_result.signal,
                "confidence": merriman_result.confidence
            },
            "agents_responses": {"astrologer": "completed"}
        }
```

### 3.4 Synthesizer (C.L.E.A.R. Format)

```python
class SynthesizerNode:
    """
    Final synthesis node using LangChain ReAct pattern.
    Produces C.L.E.A.R. formatted recommendation.
    """
    
    SYSTEM_PROMPT = """Ты - главный аналитик финансовой системы.
Объедини все сигналы в финальную рекомендацию.

Доступные данные:
- Technical: {technical_signal}
- Bull Case: {bull_case}
- Bear Case: {bear_case}
- Cycle (Merriman): {cycle}
- Astrology (Meridian): {meridian}

Верни C.L.E.A.R. формат:
{
    "signal": "BULLISH|BEARISH|NEUTRAL",
    "confidence": 0-100,
    "clear": {
        "context": "краткая ситуация",
        "logic": "ключевая логика",
        "evidence": {"bullish": [], "bearish": []},
        "assessment": "оценка риска 1-10",
        "recommendation": "конкретное действие"
    }
}"""
    
    async def synthesize(self, state: SentinelState) -> dict:
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT.format(
                technical_signal=state.get('technical_signal', {}),
                bull_case=state.get('bull_case', {}),
                bear_case=state.get('bear_case', {}),
                cycle=state.get('cycle_analysis', {}),
                meridian=state.get('meridian_analysis', {})
            )),
            HumanMessage(content=f"Symbol: {state['symbol']}, Action: {state['user_action']}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "synthesis": json.loads(response.content),
            "clear_recommendation": json.loads(response.content)['clear'],
            "confidence": json.loads(response.content).get('confidence', 50)
        }
```

---

## 4. LangGraph Configuration

### 4.1 Graph Definition

```python
from langgraph.graph import StateGraph, END

def create_sentinel_graph():
    """Create the LangGraph for asurdev Sentinel."""
    
    workflow = StateGraph(SentinelState)
    
    # Add nodes
    workflow.add_node("analyze_market", market_analyst_node)
    workflow.add_node("research_bull", bull_researcher_node)
    workflow.add_node("research_bear", bear_researcher_node)
    workflow.add_node("analyze_cycles", cycle_node)  # Merriman
    workflow.add_node("analyze_astro", astro_node)    # Meridian
    workflow.add_node("synthesize", synthesizer_node)
    workflow.add_node("format_output", formatter_node)
    
    # Set entry point
    workflow.set_entry_point("analyze_market")
    
    # Parallel execution: market -> bull + bear
    workflow.add_edge("analyze_market", "research_bull")
    workflow.add_edge("analyze_market", "research_bear")
    
    # After sentiment research, run astrology in parallel
    workflow.add_edge("research_bull", "analyze_cycles")
    workflow.add_edge("research_bear", "analyze_cycles")
    workflow.add_edge("research_bull", "analyze_astro")
    workflow.add_edge("research_bear", "analyze_astro")
    
    # Wait for all analyses, then synthesize
    workflow.add_edge("analyze_cycles", "synthesize")
    workflow.add_edge("analyze_astro", "synthesize")
    
    # Format final output
    workflow.add_edge("synthesize", "format_output")
    workflow.add_edge("format_output", END)
    
    return workflow.compile()
```

### 4.2 Conditional Routing Example

```python
from langgraph.graph import Command

def route_after_research(state: SentinelState) -> Command:
    """
    Conditional routing based on sentiment difference.
    If bull and bear signals strongly disagree, add Gann analysis.
    """
    bull_conf = state.get('bull_case', {}).get('confidence', 50)
    bear_conf = state.get('bear_case', {}).get('confidence', 50)
    
    diff = abs(bull_conf - bear_conf)
    
    if diff > 30:
        # Strong disagreement - add Gann analysis
        return Command(goto="analyze_gann")
    else:
        # Normal flow
        return Command(goto="analyze_cycles")

# Add conditional edge
workflow.add_conditional_edges(
    "research_bear",
    route_after_research,
    {
        "analyze_gann": "analyze_gann",
        "analyze_cycles": "analyze_cycles"
    }
)
```

### 4.3 Checkpointing (Memory)

```python
from langgraph.checkpoint.memory import MemorySaver

# Enable persistent state
checkpointer = MemorySaver()

graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["synthesize"]  # Human-in-the-loop
)

# Resume from checkpoint
config = {"configurable": {"thread_id": "session_123"}}
result = graph.invoke(None, config=config)
```

---

## 5. Tools Integration

### 5.1 Tool Definitions

```python
from langchain_core.tools import tool

@tool
def get_market_data(symbol: str) -> dict:
    """Get current market data for symbol."""
    # CoinGecko API call
    pass

@tool  
def get_price_history(symbol: str, timeframe: str) -> list:
    """Get historical price data."""
    pass

@tool
def calculate_indicators(prices: list) -> dict:
    """Calculate technical indicators (RSI, MACD, etc.)."""
    pass
```

### 5.2 Bind Tools to LLM

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5-coder:32b")
llm_with_tools = llm.bind_tools([get_market_data, get_price_history, calculate_indicators])
```

---

## 6. Migration Path

### Phase 1: Parallel Agent Execution
- [ ] Replace `asyncio.gather` with LangGraph parallel edges
- [ ] Add checkpointing for state persistence
- **Files:** `orchestrator.py`

### Phase 2: Structured Outputs
- [ ] Add Pydantic models for all agent responses
- [ ] Use LangChain output parsers
- **Files:** All `_impl/*.py`

### Phase 3: Conditional Routing
- [ ] Add Gann/Dow agents with conditional triggers
- [ ] Implement human-in-the-loop checkpoints
- **Files:** `orchestrator.py`, `agents/_impl/`

### Phase 4: LangSmith Integration (Optional)
- [ ] Add LangSmith tracing for observability
- [ ] Evaluate agent performance
- **Files:** `__init__.py`, configuration

---

## 7. Backward Compatibility

### 7.1 Keep Current API

```python
# Old API still works
orchestrator = Orchestrator()
result = await orchestrator.analyze("BTC")

# New LangGraph API
graph = create_sentinel_graph()
result = await graph.ainvoke({"symbol": "BTC", ...})
```

### 7.2 Adapter Pattern

```python
class LangGraphOrchestrator(Orchestrator):
    """
    LangGraph-based orchestrator that maintains
    the same interface as the original.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph = create_sentinel_graph()
    
    async def analyze(self, symbol: str, action: str = "hold"):
        # Convert to LangGraph input format
        initial_state = {
            "symbol": symbol.upper(),
            "user_action": action,
            "location": (self.config.latitude, self.config.longitude),
            # ... other fields
        }
        
        # Run graph
        result = await self.graph.ainvoke(initial_state)
        
        # Convert back to AnalysisResult
        return self._to_analysis_result(result)
```

---

## 8. Testing Strategy

```python
import pytest

@pytest.mark.asyncio
async def test_merriman_agent():
    """Test Merriman cycle calculations."""
    agent = MerrimanAgent()
    result = await agent.analyze({"symbol": "BTC"})
    
    assert result.signal in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert 0 <= result.confidence <= 100

@pytest.mark.asyncio
async def test_langgraph_flow():
    """Test full LangGraph orchestration."""
    graph = create_sentinel_graph()
    
    result = await graph.ainvoke({
        "symbol": "BTC",
        "timeframe": "4h",
        "location": (37.7749, -122.4194),
        "user_action": "hold"
    })
    
    assert "synthesis" in result
    assert "clear_recommendation" in result
    assert result["synthesis"]["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]
```

---

## 9. Performance Considerations

| Component | Current (v2.0) | Target (v3.0) |
|-----------|---------------|---------------|
| Agent execution | Sequential gather | Parallel edges |
| Memory | None | Checkpointing |
| Retry logic | Manual try/except | Built-in via LangGraph |
| Latency (5 agents) | ~60s | ~20s (parallel) |

---

## 10. Dependencies

```txt
# requirements.txt
langchain>=0.3.0
langchain-ollama>=0.2.0
langgraph>=0.2.0
pydantic>=2.0.0
ephem>=4.1.0  # For precise planetary calculations (optional)
```

---

## 11. Open Questions

1. **Persistence:** Redis vs MemorySaver for checkpoints?
2. **Observability:** LangSmith required for production?
3. **Human-in-the-loop:** Checkpoint before every trade or only high-risk ones?
4. **Model selection:** qwen2.5-coder:32b vs mixtral-8x7b for synthesizer?

---

*Document Version: 1.0*  
*Last Updated: 2026-03-21*
