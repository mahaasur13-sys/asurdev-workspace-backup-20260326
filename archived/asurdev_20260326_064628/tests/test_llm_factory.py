"""Tests for LLM factory and provider configuration."""

import pytest
from unittest.mock import patch, MagicMock


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_get_llm_config_auto_ollama_available(self):
        """Test auto detection when Ollama is available."""
        with patch("agents.llm_factory._check_ollama", return_value=True):
            from agents.llm_factory import get_llm_config
            
            config = get_llm_config("auto")
            
            assert config["provider"] == "ollama"
            assert "model" in config
            assert config["base_url"] == "http://localhost:11434"

    def test_get_llm_config_explicit_ollama(self):
        """Test explicit Ollama provider."""
        with patch("agents.llm_factory._check_ollama", return_value=True):
            from agents.llm_factory import get_llm_config
            
            config = get_llm_config("ollama")
            
            assert config["provider"] == "ollama"

    def test_get_llm_config_openai_fallback(self):
        """Test OpenAI fallback when Ollama unavailable."""
        with patch("agents.llm_factory._check_ollama", return_value=False):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
                from agents.llm_factory import get_llm_config
                
                config = get_llm_config("auto")
                
                assert config["provider"] == "openai"
                assert config["model"] == "gpt-4o"

    def test_get_llm_config_no_provider_error(self):
        """Test error when no provider available."""
        with patch("agents.llm_factory._check_ollama", return_value=False):
            with patch.dict("os.environ", {}, clear=True):
                from agents.llm_factory import get_llm_config
                
                with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
                    get_llm_config("auto")


class TestPrompts:
    """Tests for agent prompts."""

    def test_analyst_prompt_exists(self):
        """Test analyst prompt is defined."""
        from agents.llm_factory import ANALYST_PROMPT
        
        assert "financial analyst" in ANALYST_PROMPT.lower()
        assert "BUY" in ANALYST_PROMPT or "BUY / SELL / HOLD" in ANALYST_PROMPT
        assert "RECOMMENDATION:" in ANALYST_PROMPT

    def test_astrologer_prompt_exists(self):
        """Test astrologer prompt is defined."""
        from agents.llm_factory import ASTROLOGER_PROMPT
        
        assert "astrologer" in ASTROLOGER_PROMPT.lower()
        assert "TIMING" in ASTROLOGER_PROMPT or "timing" in ASTROLOGER_PROMPT

    def test_synthesizer_prompt_exists(self):
        """Test synthesizer prompt is defined."""
        from agents.llm_factory import SYNTHESIZER_PROMPT
        
        assert "Chairman" in SYNTHESIZER_PROMPT or "Chairman" in SYNTHESIZER_PROMPT
        assert "FINAL VERDICT" in SYNTHESIZER_PROMPT

    def test_risk_manager_prompt_exists(self):
        """Test risk manager prompt is defined."""
        from agents.llm_factory import RISK_MANAGER_PROMPT
        
        assert "Risk Officer" in RISK_MANAGER_PROMPT or "risk" in RISK_MANAGER_PROMPT.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
