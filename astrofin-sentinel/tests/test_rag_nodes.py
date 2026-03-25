"""Unit tests for Adaptive RAG nodes: adaptive_retrieval, self_critique, corrective_rag, routers."""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import sys
sys.path.insert(0, "/home/workspace/astrofin-sentinel")

import pytest
from unittest.mock import MagicMock, patch
from src.graph_v2.state import AgentState, TechnicalResult, RetrievalState


@pytest.fixture
def mock_technical_result():
    return TechnicalResult(
        symbol="BTC",
        timeframe="4h",
        rsi=65.0,
        macd={"macd": 150.0, "signal": 100.0, "histogram": 50.0},
        ema_20=67000,
        ema_50=65000,
        ema_200=60000,
        price_change_pct=2.5,
        bullish_score=0.65,
        bearish_score=0.35,
        confidence=0.72,
        feature_vector=[0.65, 0.98, 0.85, 1.0, 1.0, 0.25, 0.65, 0.35, 0.72, 0.4, 0.5, 0.5, 0.4],
        detected_patterns=[
            {"pattern_type": "ascending_triangle", "direction": "bullish",
             "timeframe": "4h", "confidence": 0.78, "description": "Bullish continuation"}
        ],
        summary="BTC forming ascending triangle on 4h"
    )


@pytest.fixture
def mock_retrieval_state():
    return RetrievalState(
        retrieved_cases=[],
        self_critique_score=None,
        self_critique_reasoning="",
        is_rag_relevant=False,
        corrective_rag_iterations=0,
        max_corrective_rag=2,
        final_confidence=None,
        retrieval_strategy=None,
        adaptive_query=None
    )


@pytest.fixture
def mock_retrieved_cases():
    return [
        {"case_id": "case1", "similarity_score": 0.91, "pattern_type": "ascending_triangle",
         "symbol": "BTC", "date": "2024-01-15", "outcome": "price_rose_8%", "outcome_pct": 8.0,
         "holding_period_days": 7, "text_description": "BTC ascending triangle breakout", "metadata": {}},
        {"case_id": "case2", "similarity_score": 0.87, "pattern_type": "ascending_triangle",
         "symbol": "BTC", "date": "2024-03-20", "outcome": "price_rose_5%", "outcome_pct": 5.0,
         "holding_period_days": 5, "text_description": "BTC ascending triangle continuation", "metadata": {}}
    ]


@pytest.fixture
def base_agent_state(mock_technical_result, mock_retrieval_state):
    return AgentState(
        symbol="BTC", timeframe="4h", user_question="Should I buy BTC?",
        jd_ut=2460600.5, astro_data={"moon_phase": "waxing_crescent"}, market_data={"price": 67000},
        technical_result=mock_technical_result, retrieval_state=mock_retrieval_state,
        retrieved_cases=[], adjusted_confidence=None, retrieval_relevance=None, correction_count=0,
        retrieval_history=[], knowledge_context=None, market_analyst_opinion=None,
        bull_researcher_opinion=None, bear_researcher_opinion=None, muhurta_specialist_opinion=None,
        synthesizer_opinion=None, final_vote=None, messages=[], errors=[]
    )


# =============================================================================
# technical_kb.py — BUILD FEATURE VECTOR
# =============================================================================

class TestBuildFeatureVector:
    def test_none_input_returns_default_vector(self):
        from src.graph_v2.tools.technical_kb import build_feature_vector
        vec = build_feature_vector(None)
        assert len(vec) == 13
        assert all(v == 0.5 for v in vec)

    def test_full_technical_result(self):
        from src.graph_v2.tools.technical_kb import build_feature_vector
        tech = {
            "rsi": 65, "macd": {"histogram": 50},
            "ema_20": 67000, "ema_50": 65000, "ema_200": 60000,
            "price_change_pct": 2.5,
            "bullish_score": 0.65, "bearish_score": 0.35,
            "confidence": 0.72,
            "detected_patterns": [{"pattern_type": "triangle", "confidence": 0.8}],
            "timeframe": "4h"
        }
        vec = build_feature_vector(tech)
        assert len(vec) == 13
        assert vec[0] == pytest.approx(0.65)
        assert vec[1] == pytest.approx(1.0)
        assert vec[3] == 1.0
        assert vec[4] == 1.0
        assert vec[9] == 0.4

    def test_bearish_ema_cross(self):
        from src.graph_v2.tools.technical_kb import build_feature_vector
        tech = {
            "rsi": 40, "macd": {"histogram": -30},
            "ema_20": 60000, "ema_50": 65000, "ema_200": 60000,
            "price_change_pct": -3.0, "bullish_score": 0.3, "bearish_score": 0.7,
            "confidence": 0.6, "detected_patterns": [], "timeframe": "1d"
        }
        vec = build_feature_vector(tech)
        assert vec[3] == 0.0
        assert vec[9] == 0.6

    def test_very_negative_macd_histogram(self):
        from src.graph_v2.tools.technical_kb import build_feature_vector
        tech = {"macd": {"histogram": -100}, "rsi": 50, "ema_20": 0, "ema_50": 0, "ema_200": 0,
                "price_change_pct": 0, "bullish_score": 0.5, "bearish_score": 0.5,
                "confidence": 0.5, "detected_patterns": [], "timeframe": "4h"}
        vec = build_feature_vector(tech)
        assert vec[1] == pytest.approx(-1.0)
        assert vec[2] == pytest.approx(1.0)


# =============================================================================
# technical_kb.py — SHOULD_SKIP_RAG
# =============================================================================

class TestShouldSkipRag:
    def test_high_confidence_skips_rag(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.9, "detected_patterns": []}
        skip, reason = should_skip_rag(tech, [])
        assert skip is True
        assert "0.90" in reason

    def test_low_confidence_skips_rag(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.2, "detected_patterns": []}
        skip, reason = should_skip_rag(tech, [])
        assert skip is True
        assert "0.20" in reason

    def test_rare_pattern_head_and_shoulders_uses_rag(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.6, "detected_patterns": [{"pattern_type": "head_and_shoulders", "confidence": 0.75}]}
        skip, reason = should_skip_rag(tech, [])
        assert skip is False
        assert "head_and_shoulders" in reason

    def test_rare_pattern_case_insensitive(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.6, "detected_patterns": [{"pattern_type": "DOUBLE_BOTTOM", "confidence": 0.75}]}
        skip, _ = should_skip_rag(tech, [])
        assert skip is False

    def test_impactful_past_rag_uses_rag(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.6, "detected_patterns": []}
        history = [{"relevance_score": 0.6, "adjusted_confidence": 0.75}]
        skip, reason = should_skip_rag(tech, history)
        assert skip is False
        assert "Past RAG impactful" in reason

    def test_not_impactful_past_rag_skips(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.6, "detected_patterns": []}
        history = [{"relevance_score": 0.3, "adjusted_confidence": 0.62}]
        skip, reason = should_skip_rag(tech, history)
        assert skip is True

    def test_mid_confidence_no_patterns_skips(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.55, "detected_patterns": []}
        skip, reason = should_skip_rag(tech, [])
        assert skip is True

    def test_boundary_high_confidence_exactly_threshold(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.82, "detected_patterns": []}
        skip, _ = should_skip_rag(tech, [])
        assert skip is True

    def test_boundary_low_confidence_exactly_threshold(self):
        from src.graph_v2.tools.technical_kb import should_skip_rag
        tech = {"confidence": 0.35, "detected_patterns": []}
        skip, _ = should_skip_rag(tech, [])
        assert skip is True


# =============================================================================
# technical_kb.py — GET_RAG_STRATEGY
# =============================================================================

class TestGetRagStrategy:
    def test_pattern_focused_when_patterns_exist(self):
        from src.graph_v2.tools.technical_kb import get_rag_strategy
        tech = {"confidence": 0.6, "detected_patterns": [{"pattern_type": "triangle"}], "rsi": 50}
        assert get_rag_strategy(tech) == "pattern_focused"

    def test_regime_aware_when_overbought_rsi(self):
        from src.graph_v2.tools.technical_kb import get_rag_strategy
        tech = {"confidence": 0.6, "detected_patterns": [], "rsi": 70}
        assert get_rag_strategy(tech) == "regime_aware"

    def test_regime_aware_when_oversold_rsi(self):
        from src.graph_v2.tools.technical_kb import get_rag_strategy
        tech = {"confidence": 0.6, "detected_patterns": [], "rsi": 30}
        assert get_rag_strategy(tech) == "regime_aware"

    def test_standard_default(self):
        from src.graph_v2.tools.technical_kb import get_rag_strategy
        tech = {"confidence": 0.4, "detected_patterns": [], "rsi": 50}
        assert get_rag_strategy(tech) == "standard"


# =============================================================================
# technical_kb.py — BUILD_ADAPTIVE_QUERY
# =============================================================================

class TestBuildAdaptiveQuery:
    def test_pattern_focused_query(self):
        from src.graph_v2.tools.technical_kb import build_adaptive_query
        tech = {"symbol": "ETH", "timeframe": "1d", "confidence": 0.6,
                "detected_patterns": [{"pattern_type": "cup_and_handle", "direction": "bullish"}],
                "rsi": 55}
        query = build_adaptive_query(tech, "pattern_focused")
        assert "ETH" in query
        assert "cup_and_handle" in query
        assert "bullish" in query

    def test_regime_aware_oversold_query(self):
        from src.graph_v2.tools.technical_kb import build_adaptive_query
        tech = {"symbol": "SOL", "timeframe": "4h", "confidence": 0.5,
                "detected_patterns": [], "rsi": 28}
        query = build_adaptive_query(tech, "regime_aware")
        assert "SOL" in query
        assert "oversold" in query

    def test_regime_aware_overbought_query(self):
        from src.graph_v2.tools.technical_kb import build_adaptive_query
        tech = {"symbol": "AVAX", "timeframe": "1d", "confidence": 0.5,
                "detected_patterns": [], "rsi": 72}
        query = build_adaptive_query(tech, "regime_aware")
        assert "overbought" in query

    def test_standard_query(self):
        from src.graph_v2.tools.technical_kb import build_adaptive_query
        tech = {"symbol": "BTC", "timeframe": "1h", "confidence": 0.5,
                "detected_patterns": [], "rsi": 50}
        query = build_adaptive_query(tech, "standard")
        assert "BTC" in query
        assert "1h" in query


# =============================================================================
# compiler.py — ADAPTIVE ROUTER NODE
# =============================================================================

class TestAdaptiveRouterNode:
    def test_no_technical_result_goes_direct(self):
        from src.graph_v2.compiler import adaptive_router_node
        state = AgentState(
            symbol="BTC", timeframe="4h", user_question="", jd_ut=None,
            astro_data=None, market_data=None, technical_result=None,
            retrieval_state=None, retrieved_cases=[], adjusted_confidence=None,
            retrieval_relevance=None, correction_count=0, retrieval_history=[],
            knowledge_context=None, market_analyst_opinion=None,
            bull_researcher_opinion=None, bear_researcher_opinion=None,
            muhurta_specialist_opinion=None, synthesizer_opinion=None,
            final_vote=None, messages=[], errors=[]
        )
        result = adaptive_router_node(state)
        assert result == "direct"


# =============================================================================
# compiler.py — ADAPTIVE RETRIEVAL NODE
# =============================================================================

class TestAdaptiveRetrievalNode:
    def test_sets_retrieval_strategy(self, base_agent_state):
        from src.graph_v2.compiler import adaptive_retrieval_node
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", return_value=[]):
            result = adaptive_retrieval_node(base_agent_state)
        assert "retrieval_state" in result
        rs = result["retrieval_state"]
        assert rs["retrieval_strategy"] in ["standard", "pattern_focused", "regime_aware"]
        assert "adaptive_query" in rs

    def test_returns_retrieved_cases(self, base_agent_state, mock_retrieved_cases):
        from src.graph_v2.compiler import adaptive_retrieval_node
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", return_value=mock_retrieved_cases):
            result = adaptive_retrieval_node(base_agent_state)
        assert result["retrieved_cases"] == mock_retrieved_cases
        assert len(result["retrieved_cases"]) == 2

    def test_handles_retrieval_error_gracefully(self, base_agent_state):
        from src.graph_v2.compiler import adaptive_retrieval_node
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", side_effect=Exception("Chroma down")):
            result = adaptive_retrieval_node(base_agent_state)
        assert result["retrieved_cases"] == []


# =============================================================================
# compiler.py — SELF CRITIQUE NODE
# =============================================================================

class TestSelfCritiqueNode:
    def test_sets_retrieval_relevance_and_confidence(self, base_agent_state, mock_retrieved_cases):
        from src.graph_v2.compiler import self_critique_node
        state = {**base_agent_state, "retrieved_cases": mock_retrieved_cases}
        mock_rs = RetrievalState(retrieved_cases=mock_retrieved_cases, is_rag_relevant=True)
        state["retrieval_state"] = mock_rs

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="RELEVANCE_SCORE: 0.75\nREASONING: Cases are similar and relevant.\nADJUSTED_CONFIDENCE: 0.80"
        )

        with patch("src.graph_v2.compiler.llm", mock_llm):
            result = self_critique_node(state)

        assert "retrieval_relevance" in result
        assert "adjusted_confidence" in result
        assert isinstance(result["retrieval_history"], list)
        assert len(result["retrieval_history"]) == 1

    def test_empty_cases_defaults_to_not_relevant(self, base_agent_state):
        from src.graph_v2.compiler import self_critique_node
        state = {**base_agent_state, "retrieved_cases": []}
        state["retrieval_state"] = RetrievalState(retrieved_cases=[], is_rag_relevant=False)
        result = self_critique_node(state)
        assert result["retrieval_relevance"] == 0.0
        assert "No similar cases found" in result["retrieval_state"]["self_critique_reasoning"]


# =============================================================================
# compiler.py — RAG RELEVANCE ROUTER
# =============================================================================

class TestRagRelevanceRouter:
    def test_routes_to_specialists_when_relevant(self):
        from src.graph_v2.compiler import rag_relevance_router
        state = {
            "retrieval_state": {"is_rag_relevant": True, "self_critique_score": 0.75},
            "retrieval_relevance": None
        }
        result = rag_relevance_router(state)
        assert result["next"] == "specialists"

    def test_routes_to_corrective_when_not_relevant(self):
        from src.graph_v2.compiler import rag_relevance_router
        state = {
            "retrieval_state": {"is_rag_relevant": False, "self_critique_score": 0.2},
            "retrieval_relevance": None
        }
        result = rag_relevance_router(state)
        assert result["next"] == "corrective_rag"

    def test_includes_retrieval_relevance_in_result(self):
        from src.graph_v2.compiler import rag_relevance_router
        state = {
            "retrieval_state": {"is_rag_relevant": True, "self_critique_score": 0.82},
            "retrieval_relevance": None
        }
        result = rag_relevance_router(state)
        assert result["retrieval_relevance"] == 0.82


# =============================================================================
# compiler.py — CORRECTIVE RAG NODE
# =============================================================================

class TestCorrectiveRagNode:
    def test_max_iterations_skips_to_specialists(self, base_agent_state):
        from src.graph_v2.compiler import corrective_rag_node
        state = {**base_agent_state}
        state["retrieval_state"] = RetrievalState(
            corrective_rag_iterations=2, max_corrective_rag=2,
            retrieved_cases=[], is_rag_relevant=False
        )
        result = corrective_rag_node(state)
        assert result["retrieval_state"]["is_rag_relevant"] is False
        assert "final_confidence" in result["retrieval_state"]

    def test_increments_correction_count(self, base_agent_state):
        from src.graph_v2.compiler import corrective_rag_node
        state = {**base_agent_state, "correction_count": 0}
        state["retrieval_state"] = RetrievalState(
            corrective_rag_iterations=0, max_corrective_rag=2,
            retrieved_cases=[], is_rag_relevant=False
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="RELEVANCE_SCORE: 0.6\nREASONING: ok\nADJUSTED_CONFIDENCE: 0.7"
        )
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", return_value=[]):
            with patch("src.graph_v2.tools.technical_kb.reformulate_query", return_value="BTC 4h triangle"):
                with patch("src.graph_v2.tools.technical_kb.evaluate_retrieval_relevance", return_value={"is_relevant": True, "self_critique_score": 0.6, "self_critique_reasoning": "", "adjusted_confidence": 0.7}):
                    with patch("src.graph_v2.compiler.llm", mock_llm):
                        result = corrective_rag_node(state)
        assert result["correction_count"] == 1
        assert result["retrieval_state"]["corrective_rag_iterations"] == 1

    def test_sets_final_confidence_when_relevant(self, base_agent_state, mock_retrieved_cases):
        from src.graph_v2.compiler import corrective_rag_node
        state = {**base_agent_state, "correction_count": 0}
        state["retrieval_state"] = RetrievalState(
            corrective_rag_iterations=0, max_corrective_rag=2,
            retrieved_cases=[], is_rag_relevant=False
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="RELEVANCE_SCORE: 0.7\nREASONING: good match\nADJUSTED_CONFIDENCE: 0.78"
        )
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", return_value=mock_retrieved_cases):
            with patch("src.graph_v2.tools.technical_kb.reformulate_query", return_value="BTC 4h ascending triangle"):
                with patch("src.graph_v2.tools.technical_kb.evaluate_retrieval_relevance", return_value={"is_relevant": True, "self_critique_score": 0.7, "self_critique_reasoning": "", "adjusted_confidence": 0.78}):
                    with patch("src.graph_v2.compiler.llm", mock_llm):
                        result = corrective_rag_node(state)
        assert result["retrieval_state"]["is_rag_relevant"] is True
        assert result["retrieval_state"]["final_confidence"] == 0.78


# =============================================================================
# compiler.py — CORRECTIVE RAG ROUTER
# =============================================================================

class TestCorrectiveRagRouter:
    def test_routes_to_specialists_when_max_iterations_reached(self):
        from src.graph_v2.compiler import corrective_rag_router
        state = {"retrieval_state": {"corrective_rag_iterations": 2, "max_corrective_rag": 2}}
        result = corrective_rag_router(state)
        assert result["next"] == "specialists"

    def test_routes_to_self_critique_when_more_iterations_available(self):
        from src.graph_v2.compiler import corrective_rag_router
        state = {"retrieval_state": {"corrective_rag_iterations": 1, "max_corrective_rag": 2}}
        result = corrective_rag_router(state)
        assert result["next"] == "self_critique"

    def test_routes_to_specialists_when_relevance_achieved(self):
        # When already at max iterations, goes to specialists regardless of is_rag_relevant
        from src.graph_v2.compiler import corrective_rag_router
        state = {"retrieval_state": {"corrective_rag_iterations": 2, "max_corrective_rag": 2, "is_rag_relevant": True}}
        result = corrective_rag_router(state)
        assert result["next"] == "specialists"


# =============================================================================
# compiler.py — RETRIEVE SIMILAR CASES NODE
# =============================================================================

class TestRetrieveSimilarCasesNode:
    def test_writes_retrieved_cases_to_state(self, base_agent_state, mock_retrieved_cases):
        from src.graph_v2.compiler import retrieve_similar_cases_node
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", return_value=mock_retrieved_cases):
            result = retrieve_similar_cases_node(base_agent_state)
        assert "retrieved_cases" in result
        assert len(result["retrieved_cases"]) == 2
        assert result["retrieved_cases"][0]["case_id"] == "case1"

    def test_handles_missing_feature_vector(self, base_agent_state):
        from src.graph_v2.compiler import retrieve_similar_cases_node
        tech_dict = {"confidence": 0.5}
        class FakeTR:
            feature_vector = None
            def model_dump(self):
                return tech_dict
        state = {**base_agent_state, "technical_result": FakeTR()}
        result = retrieve_similar_cases_node(state)
        assert result["retrieved_cases"] == []

    def test_appends_system_message(self, base_agent_state, mock_retrieved_cases):
        from src.graph_v2.compiler import retrieve_similar_cases_node
        state = {**base_agent_state, "messages": []}
        with patch("src.graph_v2.tools.technical_kb.retrieve_similar_cases", return_value=mock_retrieved_cases):
            result = retrieve_similar_cases_node(state)
        msgs = result.get("messages", [])
        assert any("Retrieved 2 similar cases" in str(m) for m in msgs)
