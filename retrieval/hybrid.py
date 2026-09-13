import os
from dataclasses import dataclass

from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client.models import FieldCondition, Filter, MatchAny
from rank_bm25 import BM25Okapi

from retrieval.models import DocumentChunk
from retrieval.qdrant_store import (
    COLLECTION_NAME,
    get_qdrant_client,
)
from retrieval.reranker import DocumentReranker


load_dotenv()


# ============================================================
# Configuration
# ============================================================

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

DENSE_LIMIT = 5
BM25_LIMIT = 5
FINAL_LIMIT = 3


# ============================================================
# Retrieval result
# ============================================================

@dataclass
class RetrievalResult:
    """Final retrieval result returned to the application."""

    document: DocumentChunk
    score: float


# ============================================================
# Hybrid Retriever
# ============================================================

class HybridRetriever:
    """
    Hybrid retrieval system using:

    1. Dense vector search through Qdrant
    2. BM25 lexical search
    3. Retrieval-time ACL filtering
    4. Reciprocal Rank Fusion
    5. BGE cross-encoder reranking
    """

    def __init__(self):

        self.qdrant = get_qdrant_client()

        self.embedding_model = TextEmbedding(
            EMBEDDING_MODEL
        )

        self.reranker = DocumentReranker()

        self.documents = (
            self._load_documents_from_qdrant()
        )

        self.bm25 = self._build_bm25_index()


    # ========================================================
    # Load documents from Qdrant
    # ========================================================

    def _load_documents_from_qdrant(
        self,
    ) -> list[DocumentChunk]:

        documents = []

        offset = None

        while True:

            records, next_offset = (
                self.qdrant.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=1000,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
            )

            for record in records:

                payload = record.payload or {}

                metadata = payload.get(
                    "metadata",
                    {},
                )

                document = DocumentChunk(
                    id=metadata.get(
                        "chunk_id",
                        str(record.id),
                    ),
                    text=payload.get(
                        "text",
                        "",
                    ),
                    source=payload.get(
                        "source",
                        "",
                    ),
                    allowed_roles=payload.get(
                        "allowed_roles",
                        [],
                    ),
                    metadata=metadata,
                )

                documents.append(document)

            if next_offset is None:
                break

            offset = next_offset

        return documents


    # ========================================================
    # BM25
    # ========================================================

    def _build_bm25_index(
        self,
    ) -> BM25Okapi:

        if not self.documents:

            return BM25Okapi(
                [["__empty__"]]
            )

        tokenized_documents = [
            document.text.lower().split()
            for document in self.documents
        ]

        return BM25Okapi(
            tokenized_documents
        )


    # ========================================================
    # Dense Retrieval
    # ========================================================

    def _dense_search(
        self,
        query: str,
        user_role: str,
    ) -> list[DocumentChunk]:

        if not self.documents:
            return []

        query_vector = list(
            self.embedding_model.embed(
                [query]
            )
        )[0]

        # Retrieval-time ACL filter.
        #
        # Unauthorized chunks are filtered inside
        # Qdrant before they are returned.

        acl_filter = Filter(
            must=[
                FieldCondition(
                    key="allowed_roles",
                    match=MatchAny(
                        any=[user_role]
                    ),
                )
            ]
        )

        response = self.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector.tolist(),
            query_filter=acl_filter,
            limit=DENSE_LIMIT,
            with_payload=True,
        )

        documents = []

        for result in response.points:

            payload = result.payload or {}

            metadata = payload.get(
                "metadata",
                {},
            )

            document = DocumentChunk(
                id=metadata.get(
                    "chunk_id",
                    str(result.id),
                ),
                text=payload.get(
                    "text",
                    "",
                ),
                source=payload.get(
                    "source",
                    "",
                ),
                allowed_roles=payload.get(
                    "allowed_roles",
                    [],
                ),
                metadata=metadata,
                score=float(result.score),
            )

            documents.append(document)

        return documents


    # ========================================================
    # BM25 Retrieval
    # ========================================================

    def _bm25_search(
        self,
        query: str,
        user_role: str,
    ) -> list[DocumentChunk]:

        if not self.documents:
            return []

        query_tokens = (
            query.lower().split()
        )

        scores = self.bm25.get_scores(
            query_tokens
        )

        authorized_indices = [
            index
            for index, document
            in enumerate(self.documents)
            if user_role
            in document.allowed_roles
        ]

        ranked_indices = sorted(
            authorized_indices,
            key=lambda index: scores[index],
            reverse=True,
        )

        return [
            self.documents[index]
            for index
            in ranked_indices[:BM25_LIMIT]
        ]


    # ========================================================
    # Reciprocal Rank Fusion
    # ========================================================

    @staticmethod
    def _reciprocal_rank_fusion(
        dense_results: list[DocumentChunk],
        bm25_results: list[DocumentChunk],
        k: int = 60,
    ) -> list[DocumentChunk]:

        scores = {}
        documents = {}

        # Dense ranking

        for rank, document in enumerate(
            dense_results,
            start=1,
        ):

            document_id = document.id

            scores[document_id] = (
                scores.get(
                    document_id,
                    0.0,
                )
                + 1 / (k + rank)
            )

            documents[document_id] = (
                document
            )

        # BM25 ranking

        for rank, document in enumerate(
            bm25_results,
            start=1,
        ):

            document_id = document.id

            scores[document_id] = (
                scores.get(
                    document_id,
                    0.0,
                )
                + 1 / (k + rank)
            )

            documents[document_id] = (
                document
            )

        ranked_ids = sorted(
            scores,
            key=scores.get,
            reverse=True,
        )

        results = []

        for document_id in ranked_ids:

            document = documents[
                document_id
            ]

            document.score = (
                scores[document_id]
            )

            results.append(document)

        return results


    # ========================================================
    # Final Search
    # ========================================================

    def search(
        self,
        query: str,
        user_role: str,
        limit: int = FINAL_LIMIT,
    ) -> list[RetrievalResult]:

        dense_results = (
            self._dense_search(
                query=query,
                user_role=user_role,
            )
        )

        bm25_results = (
            self._bm25_search(
                query=query,
                user_role=user_role,
            )
        )

        fused_results = (
            self._reciprocal_rank_fusion(
                dense_results=dense_results,
                bm25_results=bm25_results,
            )
        )

        if not fused_results:
            return []

        reranked_documents = (
            self.reranker.rerank(
                query=query,
                documents=fused_results,
                top_k=limit,
            )
        )

        return [
            RetrievalResult(
                document=document,
                score=document.score or 0.0,
            )
            for document
            in reranked_documents
        ]


# ============================================================
# Manual test
# ============================================================

if __name__ == "__main__":

    retriever = HybridRetriever()

    query = (
        "What was the company revenue "
        "in Q1 2026?"
    )

    user_role = "finance"

    results = retriever.search(
        query=query,
        user_role=user_role,
    )

    print()
    print("=" * 60)
    print("AUDITAGENT HYBRID RETRIEVAL TEST")
    print("=" * 60)

    print(
        f"Query: {query}"
    )

    print(
        f"Role: {user_role}"
    )

    print(
        f"Results: {len(results)}"
    )

    print()

    for result in results:

        document = result.document

        print("-" * 60)

        print(
            f"ID: {document.id}"
        )

        print(
            f"Source: {document.source}"
        )

        print(
            f"Score: {result.score:.4f}"
        )

        print(
            f"Allowed roles: "
            f"{document.allowed_roles}"
        )

        print(
            f"Text: "
            f"{document.text[:250]}..."
        )

    print()

    print("=" * 60)