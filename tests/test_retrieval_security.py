from retrieval.hybrid import HybridRetriever


def get_retriever() -> HybridRetriever:
    return HybridRetriever()


def get_source(document) -> str:
    """
    Extract the source name from the actual RetrievalResult structure.

    HybridRetriever returns RetrievalResult objects rather than
    DocumentChunk objects. The underlying document metadata contains
    the source information.
    """
    if hasattr(document, "document"):
        underlying_document = document.document

        if hasattr(underlying_document, "source"):
            return str(underlying_document.source)

        if hasattr(underlying_document, "metadata"):
            metadata = underlying_document.metadata or {}

            if "source" in metadata:
                return str(metadata["source"])

    if hasattr(document, "metadata"):
        metadata = document.metadata or {}

        if "source" in metadata:
            return str(metadata["source"])

    if hasattr(document, "source"):
        return str(document.source)

    return ""


def test_finance_user_cannot_retrieve_hr_documents():
    """
    A finance user must not receive HR documents from retrieval.
    """
    retriever = get_retriever()

    documents = retriever.search(
        query="What employee benefits does the company provide?",
        user_role="finance",
    )

    sources = {
        get_source(document).lower()
        for document in documents
    }

    assert not any(
        "hr" in source
        for source in sources
    )


def test_hr_user_cannot_retrieve_finance_documents():
    """
    An HR user must not receive Finance documents from retrieval.
    """
    retriever = get_retriever()

    documents = retriever.search(
        query="What was the company revenue in Q1 2026?",
        user_role="hr",
    )

    sources = {
        get_source(document).lower()
        for document in documents
    }

    assert not any(
        "finance" in source
        for source in sources
    )


def test_employee_cannot_retrieve_finance_documents():
    """
    An employee without Finance authorization must not
    retrieve Finance documents.
    """
    retriever = get_retriever()

    documents = retriever.search(
        query="What was the company revenue in Q1 2026?",
        user_role="employee",
    )

    sources = {
        get_source(document).lower()
        for document in documents
    }

    assert not any(
        "finance" in source
        for source in sources
    )


def test_employee_cannot_retrieve_hr_documents():
    """
    An employee without HR authorization must not retrieve
    HR documents.
    """
    retriever = get_retriever()

    documents = retriever.search(
        query="What employee benefits does the company provide?",
        user_role="employee",
    )

    sources = {
        get_source(document).lower()
        for document in documents
    }

    assert not any(
        "hr" in source
        for source in sources
    )


def test_admin_can_retrieve_finance_documents():
    """
    Admin is authorized for Finance documents.
    """
    retriever = get_retriever()

    documents = retriever.search(
        query="What was the company revenue in Q1 2026?",
        user_role="admin",
    )

    assert any(
        "finance" in get_source(document).lower()
        for document in documents
    )


def test_admin_can_retrieve_hr_documents():
    """
    Admin is authorized for HR documents.
    """
    retriever = get_retriever()

    documents = retriever.search(
        query="What employee benefits does the company provide?",
        user_role="admin",
    )

    assert any(
        "hr" in get_source(document).lower()
        for document in documents
    )