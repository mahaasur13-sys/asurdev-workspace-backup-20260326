"""
test_audit_compliance.py — asurdev Sentinel v3.2
Тесты для проверки compliance с аудитом от 22 марта 2026
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.decorators import (
    require_ephemeris, 
    EphemerisRetryHandler,
    _anonymize_dict,
    _looks_like_pii,
    _hash_string
)
from core.logging_config import PIIFilter


# ============================================================
# Тесты require_ephemeris decorator
# ============================================================

class TestRequireEphemerisDecorator:
    """Тесты для декоратора @require_ephemeris"""
    
    def test_raises_when_ephemeris_not_called(self):
        """Должен raise ValueError если swiss_ephemeris не вызван"""
        @require_ephemeris
        def test_agent(agent, state):
            return {"status": "ok"}
        
        agent = MagicMock()
        state = {"messages": [{"role": "user", "content": "Hello"}]}
        
        with pytest.raises(ValueError, match="swiss_ephemeris must be called first"):
            test_agent(agent, state)
    
    def test_passes_when_ephemeris_was_called(self):
        """Должен пройти если swiss_ephemeris вызван"""
        @require_ephemeris
        def test_agent(agent, state):
            return {"status": "ok", "data": state["messages"]}
        
        agent = MagicMock()
        mock_msg = MagicMock()
        mock_msg.tool_calls = [{"name": "swiss_ephemeris", "args": {}}]
        state = {"messages": [mock_msg]}
        
        result = test_agent(agent, state)
        assert result["status"] == "ok"
    
    def test_detects_ephemeris_in_additional_kwargs(self):
        """Должен находить swiss_ephemeris в additional_kwargs"""
        @require_ephemeris
        def test_agent(agent, state):
            return {"status": "ok"}
        
        agent = MagicMock()
        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.additional_kwargs = {"tool_calls": [{"function": {"name": "swiss_ephemeris"}}]}
        
        state = {"messages": [mock_msg]}
        result = test_agent(agent, state)
        assert result["status"] == "ok"


# ============================================================
# Тесты EphemerisRetryHandler
# ============================================================

class TestEphemerisRetryHandler:
    """Тесты для класса EphemerisRetryHandler"""
    
    def test_uses_cache_on_second_call(self):
        """Второй вызов с теми же параметрами должен использовать кэш"""
        handler = EphemerisRetryHandler()
        
        with patch('swiss_ephemeris.swiss_ephemeris') as mock_eph:
            mock_eph.return_value = {"positions": {"Sun": 1.0}}
            
            result1 = handler.call(date="2026-03-22", time="10:00:00", lat=55.7558, lon=37.6173)
            result2 = handler.call(date="2026-03-22", time="10:00:00", lat=55.7558, lon=37.6173)
            
            assert mock_eph.call_count == 1
            assert result1 == result2
    
    def test_fallback_after_max_retries(self):
        """После max_retries должен использовать fallback координаты"""
        call_count = [0]  # Use list for nonlocal in nested function
        
        def failing_then_success(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise ConnectionError("Simulated failure")
            # Fallback succeeds
            return {"positions": {"Sun": 1.0}, "_fallback_source": True}
        
        handler = EphemerisRetryHandler(max_retries=2)
        
        with patch('swiss_ephemeris.swiss_ephemeris', side_effect=failing_then_success):
            result = handler.call(date="2026-03-22", time="10:00:00", lat=55.7558, lon=37.6173)
            
            assert call_count[0] == 3  # 2 retries + 1 fallback
            assert "_fallback_source" in result
    
    def test_returns_error_after_fallback_fails(self):
        """Если fallback тоже падает — вернуть error dict"""
        handler = EphemerisRetryHandler(max_retries=1)
        
        def always_fails(*args, **kwargs):
            raise ConnectionError("Simulated failure")
        
        with patch('swiss_ephemeris.swiss_ephemeris', side_effect=always_fails):
            result = handler.call(date="2026-03-22", time="10:00:00", lat=55.7558, lon=37.6173)
            
            assert "error" in result
            assert "retry_count" in result


# ============================================================
# Тесты PII anonymization
# ============================================================

class TestPIIAnonymization:
    """Тесты для функций анонимизации PII"""
    
    def test_hash_string_produces_consistent_hash(self):
        hash1 = _hash_string("2026-03-22")
        hash2 = _hash_string("2026-03-22")
        assert hash1 == hash2
        assert hash1.startswith("HASH:")
    
    def test_anonymize_dict_replaces_dates(self):
        d = {"date": "2026-03-22", "value": 42}
        result = _anonymize_dict(d)
        assert result["date"].startswith("HASH:")
        assert result["value"] == 42
    
    def test_anonymize_dict_preserves_safe_fields(self):
        d = {"jd_ut": 2461093.5, "ayanamsa": "lahiri", "compute_panchanga": True}
        result = _anonymize_dict(d)
        assert result["jd_ut"] == 2461093.5
        assert result["ayanamsa"] == "lahiri"
    
    def test_looks_like_pii_detects_dates(self):
        assert _looks_like_pii("2026-03-22") == True
        assert _looks_like_pii("22/03/2026") == True
    
    def test_looks_like_pii_detects_coordinates(self):
        assert _looks_like_pii("lat=55.7558") == True
    
    def test_looks_like_pii_allows_safe_strings(self):
        # Строка длиной <= 2 не определяется как имя
        assert _looks_like_pii("lahiri") == False
        # BEARISH не матчится (нет строчных после заглавной)
        assert _looks_like_pii("BEARISH") == False


# ============================================================
# Тесты PIIFilter
# ============================================================

class TestPIIFilter:
    """Тесты для логирования без PII"""
    
    def test_filter_redacts_dates(self):
        filter_obj = PIIFilter()
        record = MagicMock()
        record.msg = "User born on 2026-03-22 made a request"
        record.args = ()
        
        filter_obj.filter(record)
        
        assert "2026-03-22" not in record.msg
        assert "[REDACTED_DATE]" in record.msg
    
    def test_filter_redacts_coordinates(self):
        filter_obj = PIIFilter()
        record = MagicMock()
        record.msg = "Location: lat=55.7558, lon=37.6173"
        record.args = ()
        
        filter_obj.filter(record)
        
        assert "55.7558" not in record.msg
    
    def test_filter_adds_iso_timestamp(self):
        filter_obj = PIIFilter()
        record = MagicMock()
        record.msg = "Test message"
        record.args = ()
        
        filter_obj.filter(record)
        
        assert hasattr(record, 'iso_timestamp')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
