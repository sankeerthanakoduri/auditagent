import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    """
    Append-only JSONL audit logger with hash-chain verification.

    Each event is stored as one JSON object per line.

    The hash chain makes the log tamper-evident:
        Event N contains the hash of Event N-1.
    """

    def __init__(
        self,
        log_path: str = "audit_log/events.jsonl",
    ):
        self.log_path = Path(log_path)

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _get_previous_hash(self) -> str:
        """
        Return the hash of the most recent audit event.
        """

        if not self.log_path.exists():
            return ""

        with self.log_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            lines = file.readlines()

        if not lines:
            return ""

        last_event = json.loads(
            lines[-1]
        )

        return last_event.get(
            "event_hash",
            "",
        )

    def log_event(
        self,
        event_type: str,
        user_role: str,
        query: str,
        document_id: str | None = None,
        allowed: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Write one event to the audit log.
        """

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        previous_hash = self._get_previous_hash()

        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "user_role": user_role,
            "query": query,
            "document_id": document_id,
            "allowed": allowed,
            "metadata": metadata or {},
            "previous_hash": previous_hash,
        }

        canonical_event = json.dumps(
            event,
            sort_keys=True,
            separators=(",", ":"),
        )

        event_hash = hashlib.sha256(
            canonical_event.encode("utf-8")
        ).hexdigest()

        event["event_hash"] = event_hash

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(event)
                + "\n"
            )

    def verify_chain(self) -> bool:
        """
        Verify the complete audit-log hash chain.

        Returns:
            True  -> log is valid
            False -> log has been modified or corrupted
        """

        if not self.log_path.exists():
            return True

        previous_hash = ""

        with self.log_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                event = json.loads(line)

                stored_hash = event.pop(
                    "event_hash",
                    None,
                )

                if event.get(
                    "previous_hash",
                    "",
                ) != previous_hash:

                    return False

                canonical_event = json.dumps(
                    event,
                    sort_keys=True,
                    separators=(",", ":"),
                )

                calculated_hash = hashlib.sha256(
                    canonical_event.encode("utf-8")
                ).hexdigest()

                if calculated_hash != stored_hash:
                    return False

                previous_hash = stored_hash

        return True