import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    """Append-only JSONL audit logger."""

    def __init__(self, log_path: str = "audit_log/events.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: str,
        user_role: str,
        query: str,
        document_id: str | None = None,
        allowed: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_role": user_role,
            "query": query,
            "document_id": document_id,
            "allowed": allowed,
            "metadata": metadata or {},
        }

        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event) + "\n")