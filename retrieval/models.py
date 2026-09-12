from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    """A document chunk used throughout the retrieval pipeline."""

    id: str
    text: str
    source: str
    allowed_roles: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float | None = None