"""
Custom exceptions for asurdev Sentinel
"""


class SentinelError(Exception):
    """Base exception"""
    pass


class AgentError(SentinelError):
    """Agent execution error"""
    pass


class LLMError(SentinelError):
    """LLM/API error"""
    pass


class DataError(SentinelError):
    """Data fetching error"""
    pass


class ConfigurationError(SentinelError):
    """Configuration error"""
    pass


class ValidationError(SentinelError):
    """Input validation error"""
    pass
