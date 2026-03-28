"""
Test confidence normalization in TradingSignal.from_agents().

Covers:
  1. All int confidences (0–100) → normalization preserves integer scale
  2. Mixed float (0–1) and int (0–100) → float correctly scaled to 0–100
  3. Empty list → NEUTRAL, confidence=30
"""

import sys
import importlib.util

# ── Import from asurdev/agents/types.py ──────────────────────────────────────
sys.path.insert(0, "/home/workspace")
spec = importlib.util.spec_from_file_location("types", "/home/workspace/asurdev/agents/types.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TradingSignal = mod.TradingSignal
AgentResponse = mod.AgentResponse


# ── Signal score map (from Signal.score property) ─────────────────────────────
# STRONG_BUY=100, BUY=70, NEUTRAL=50, SELL=30, STRONG_SELL=0
SIGNAL_BUY  = 70
SIGNAL_SELL = 30

# Weighted avg thresholds (normalized = (weighted_avg - 50) * 2 + 50):
#   >= 80  → STRONG_BUY
#   >= 65  → BUY
#   >= 45  → NEUTRAL
#   >= 30  → SELL
#   <  30  → STRONG_SELL


# ── Helpers ────────────────────────────────────────────────────────────────────
def make(agent: str, signal: str, confidence: float) -> AgentResponse:
    return AgentResponse(agent_name=agent, signal=signal, confidence=confidence, summary="")


# Default weights from the code
DEFAULT_WEIGHTS = {
    "Market":        0.25,
    "Bull":          0.15,
    "Bear":          0.15,
    "AstroCouncil":  0.20,
    "Cycle":         0.10,
    "Gann":          0.05,
    "Andrews":       0.05,
    "Dow":           0.05,
}


def test_all_int_confidences() -> None:
    """
    All int confidences (0–100) pass through _normalize_conf unchanged.
    Signal determination uses weighted signal scores.

    Market+BUY(80) + AstroCouncil+BUY(75):
      weighted_avg = (0.25*70 + 0.20*70)/(0.25+0.20) = 70
      normalized   = (70-50)*2+50 = 90  → STRONG_BUY
      confidence   = avg_norm_conf = (80+75)//2 = 77
    """
    responses = [
        make("Market",       "BUY", 80),
        make("AstroCouncil", "BUY", 75),
    ]
    ts = TradingSignal.from_agents("BTCUSDT", responses, 50000.0)

    assert ts.signal.value == "STRONG_BUY", f"Expected STRONG_BUY, got {ts.signal.value}"
    assert ts.confidence   == 77,            f"Expected 77, got {ts.confidence}"
    print("✓ all_int  →  STRONG_BUY, confidence=77")


def test_mixed_float_and_int() -> None:
    """
    Float confidences (0–1) are normalised to 0–100 via _normalize_conf.
    Signal determination uses weighted signal scores.

    Market+BUY(0.80→80) + AstroCouncil+BUY(75) + Bear+SELL(0.30→30):
      weighted_avg = (0.25*70 + 0.20*70 + 0.15*30)/(0.25+0.20+0.15) = 36/0.6 = 60
      normalized   = (60-50)*2+50 = 70  → BUY
      confidence   = avg_norm_conf = (80+75+30)//3 = 61
    """
    responses = [
        make("Market",       "BUY",  0.80),
        make("AstroCouncil", "BUY",  75),
        make("Bear",         "SELL", 0.30),
    ]
    ts = TradingSignal.from_agents("ETHUSDT", responses, 3000.0)

    assert ts.signal.value == "BUY", f"Expected BUY, got {ts.signal.value}"
    assert ts.confidence   == 61,     f"Expected 61, got {ts.confidence}"
    print("✓ mixed    →  BUY, confidence=61")


def test_empty_list_returns_neutral_30() -> None:
    """
    Empty responses list must return NEUTRAL with confidence=30.
    NOTE: current code returns confidence=0 — needs fixing.
    """
    ts = TradingSignal.from_agents("BTCUSDT", [], 50000.0)
    assert ts.signal.value == "NEUTRAL", f"Expected NEUTRAL, got {ts.signal.value}"
    # FIX REQUIRED: confidence should be 30, not 0
    assert ts.confidence   == 30,         f"Expected 30, got {ts.confidence}"
    print("✓ empty    →  NEUTRAL, confidence=30")


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_all_int_confidences()
    test_mixed_float_and_int()
    test_empty_list_returns_neutral_30()
    print("\n✅ All tests passed")
