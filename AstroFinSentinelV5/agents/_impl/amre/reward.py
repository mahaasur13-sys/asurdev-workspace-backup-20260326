"""amre/reward.py — Reward computation with post-causal analysis"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class RewardResult:
    immediate: float
    post_causal: float
    final: float
    components: dict
    sharpe: float
    win_rate: float
    total_return: float
    max_drawdown: float

class RewardConfig:
    def __init__(
        self,
        return_weight: float = 0.4,
        sharpe_weight: float = 0.3,
        drawdown_penalty: float = 0.2,
        win_rate_weight: float = 0.1,
        post_causal_boost: float = 0.2,
        base_sharpe: float = 1.0,
    ):
        self.return_weight = return_weight
        self.sharpe_weight = sharpe_weight
        self.drawdown_penalty = drawdown_penalty
        self.win_rate_weight = win_rate_weight
        self.post_causal_boost = post_causal_boost
        self.base_sharpe = base_sharpe

def compute_reward(
    trajectory,
    config: Optional[RewardConfig] = None,
) -> RewardResult:
    if config is None:
        config = RewardConfig()
    cfg = config
    m = trajectory.metrics
    if m is None:
        return RewardResult(0, 0, 0, {}, 0, 0, 0, 0)
    ret_norm = max(m.total_return / 100, -1)
    sharpe_boost = max((m.sharpe - cfg.base_sharpe) / cfg.base_sharpe, -0.5)
    dd_penalty = min(m.max_drawdown / 50, 1.0)
    win_rate_norm = m.win_rate / 100
    immediate = (
        cfg.return_weight * ret_norm
        + cfg.sharpe_weight * sharpe_boost
        - cfg.drawdown_penalty * dd_penalty
        + cfg.win_rate_weight * win_rate_norm
    )
    post_causal = immediate + cfg.post_causal_boost * (m.avg_confidence / 100)
    final = max(min(post_causal, 1.0), -1.0)
    return RewardResult(
        immediate=round(immediate, 6),
        post_causal=round(post_causal, 6),
        final=round(final, 6),
        components={"ret_norm": ret_norm, "sharpe_boost": sharpe_boost, "dd_penalty": dd_penalty, "win_rate_norm": win_rate_norm},
        sharpe=round(m.sharpe, 4),
        win_rate=round(m.win_rate, 2),
        total_return=round(m.total_return, 2),
        max_drawdown=round(m.max_drawdown, 2),
    )
