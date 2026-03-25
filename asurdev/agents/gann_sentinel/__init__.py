"""
Gann Sentinel Agent
Standalone Gann Square of 9 calculator

Использование:
    # Базовое
    from agents.gann_sentinel import GannSentinel
    agent = GannSentinel()
    result = agent.calculate(58000.0)
    print(agent.to_text(result))

    # Как LangChain Tool
    from agents.gann_sentinel.tool import calculate_gann_levels
    result = calculate_gann_levels.invoke({"price": 58000})

    # Как AutoGen Tool
    from agents.gann_sentinel.autogen import get_gann_autogen_tool
    tool = get_gann_autogen_tool()
"""
from .gann_sentinel import GannSentinel, GannLevels, GannSentinelConfig, get_gann_sentinel
from .tool import calculate_gann_levels, calculate_gann_for_crypto, get_gann_recommendation, GANN_TOOLS
from .autogen import GannSentinelAutoGen, get_gann_autogen_tool

__all__ = [
    # Core
    "GannSentinel",
    "GannLevels", 
    "GannSentinelConfig",
    "get_gann_sentinel",
    
    # LangChain
    "calculate_gann_levels",
    "calculate_gann_for_crypto",
    "get_gann_recommendation",
    "GANN_TOOLS",
    
    # AutoGen
    "GannSentinelAutoGen",
    "get_gann_autogen_tool",
]
