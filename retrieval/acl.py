from retrieval.models import DocumentChunk
from audit_log.logger import AuditLogger


def is_authorized(user_role: str, document: DocumentChunk) -> bool:
    """
    Check whether a user's role is allowed to access a document chunk.
    """

    return user_role in document.allowed_roles


def filter_authorized_documents(
    user_role: str,
    documents: list[DocumentChunk],
    query: str,
    audit_logger: AuditLogger | None = None,
) -> tuple[list[DocumentChunk], list[DocumentChunk]]:
    """
    Split document chunks into authorized and blocked results.

    Unauthorized documents are never returned in the authorized list.
    Optionally records each blocked retrieval in the audit log.
    """

    authorized = []
    blocked = []

    for document in documents:
        if is_authorized(user_role, document):
            authorized.append(document)

            if audit_logger:
                audit_logger.log_event(
                    event_type="retrieval",
                    user_role=user_role,
                    query=query,
                    document_id=document.id,
                    allowed=True,
                )

        else:
            blocked.append(document)

            if audit_logger:
                audit_logger.log_event(
                    event_type="acl_block",
                    user_role=user_role,
                    query=query,
                    document_id=document.id,
                    allowed=False,
                )

    return authorized, blocked