"""
Shared Memory schemas — MemoryItem, MemoryType.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory in the shared memory bank."""
    DECISION = "decision"
    TRADE = "trade"
    ANALYSIS = "analysis"
    ERROR = "error"
    INSIGHT = "insight"
    MEMORY = "memory"


class MemoryItem(BaseModel):
    """
    Memory item — stored in Redis with TTL and importance scoring.
    Used by SharedMemoryBank for LTS (Learning to Share).
    """
    id: Optional[str] = Field(default=None, description="Unique ID")
    type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="Memory content")
    importance_score: float = Field(default=5.0, ge=0.0, le=10.0)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = Field(default=None)
    parent_id: Optional[str] = Field(default=None, description="Link to parent memory")

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = str(uuid4())[:12]

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "MemoryItem":
        return cls.model_validate_json(data)
