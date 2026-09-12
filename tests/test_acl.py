from pathlib import Path

from audit_log.logger import AuditLogger
from retrieval.acl import filter_authorized_documents
from retrieval.models import DocumentChunk


def test_acl_blocks_unauthorized_documents(tmp_path: Path):
    documents = [
        DocumentChunk(
            id="finance_001",
            text="Financial results",
            source="finance.pdf",
            allowed_roles=["finance", "admin"],
        ),
        DocumentChunk(
            id="hr_001",
            text="Employee salary information",
            source="hr.pdf",
            allowed_roles=["hr", "admin"],
        ),
    ]

    log_path = tmp_path / "events.jsonl"
    logger = AuditLogger(str(log_path))

    authorized, blocked = filter_authorized_documents(
        user_role="finance",
        documents=documents,
        query="Show me the financial results",
        audit_logger=logger,
    )

    assert len(authorized) == 1
    assert authorized[0].id == "finance_001"

    assert len(blocked) == 1
    assert blocked[0].id == "hr_001"

    log_lines = log_path.read_text(encoding="utf-8").splitlines()

    assert len(log_lines) == 2
    assert '"event_type": "retrieval"' in log_lines[0]
    assert '"event_type": "acl_block"' in log_lines[1]