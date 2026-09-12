from fastembed.rerank.cross_encoder import TextCrossEncoder

from retrieval.models import DocumentChunk


RERANKER_MODEL = "BAAI/bge-reranker-base"


class DocumentReranker:
    """
    Rerank document chunks using a cross-encoder.

    The reranker receives only documents that have already
    passed the ACL and hybrid retrieval stages.
    """

    def __init__(self):
        self.model = TextCrossEncoder(
            RERANKER_MODEL
        )

    def rerank(
        self,
        query: str,
        documents: list[DocumentChunk],
        top_k: int = 3,
    ) -> list[DocumentChunk]:
        """
        Rank documents according to their relevance to the query.
        """

        if not documents:
            return []

        document_texts = [
            document.text
            for document in documents
        ]

        scores = list(
            self.model.rerank(
                query,
                document_texts,
            )
        )

        scored_documents = []

        for document, score in zip(
            documents,
            scores,
        ):
            document.score = float(score)
            scored_documents.append(document)

        scored_documents.sort(
            key=lambda document: document.score or 0.0,
            reverse=True,
        )

        return scored_documents[:top_k]


if __name__ == "__main__":

    reranker = DocumentReranker()

    query = "What was the company revenue in Q1 2026?"

    documents = [
        DocumentChunk(
            id="finance_0",
            text=(
                "The company reported revenue of "
                "INR 48.5 crore in Q1 2026."
            ),
            source="finance.txt",
            allowed_roles=[
                "finance",
                "admin",
            ],
        ),
        DocumentChunk(
            id="hr_0",
            text=(
                "The company provides medical insurance "
                "and 24 days of annual leave."
            ),
            source="hr.txt",
            allowed_roles=[
                "hr",
                "admin",
            ],
        ),
    ]

    results = reranker.rerank(
        query=query,
        documents=documents,
        top_k=2,
    )

    print()
    print("=" * 60)
    print("BGE RERANKER TEST")
    print("=" * 60)

    for document in results:

        print("-" * 60)

        print(
            f"ID: {document.id}"
        )

        print(
            f"Score: {document.score:.4f}"
        )

        print(
            f"Source: {document.source}"
        )

    print("=" * 60)