from typing import Any


def is_authorized(user_role: str, document: dict[str, Any]) -> bool:
    """
    Check whether a user's role is allowed to access a document/chunk.
    """

    allowed_roles = document.get("allowed_roles", [])

    return user_role in allowed_roles


def filter_authorized_documents(
    user_role: str,
    documents: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split documents into authorized and blocked results.

    Returns:
        authorized_documents
        blocked_documents
    """

    authorized = []
    blocked = []

    for document in documents:
        if is_authorized(user_role, document):
            authorized.append(document)
        else:
            blocked.append(document)

    return authorized, blocked