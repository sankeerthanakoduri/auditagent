import uuid
from pathlib import Path

from fastembed import TextEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from retrieval.models import DocumentChunk


# -----------------------------
# Configuration
# -----------------------------

DATA_DIR = Path("data")

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "auditagent_docs"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


# -----------------------------
# Access-control configuration
# -----------------------------

ROLE_MAP = {
    "finance.txt": ["finance", "admin"],
    "hr.txt": ["hr", "admin"],
    "general.txt": ["finance", "hr", "employee", "admin"],
}


# -----------------------------
# Qdrant
# -----------------------------

def get_qdrant_client() -> QdrantClient:
    """Create a connection to the local Qdrant instance."""
    return QdrantClient(url=QDRANT_URL)


def ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it does not exist."""

    collections = client.get_collections().collections
    existing_names = {collection.name for collection in collections}

    if COLLECTION_NAME not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


# -----------------------------
# Document loading + chunking
# -----------------------------

def load_documents() -> list[DocumentChunk]:
    """Load text files, split them into chunks, and attach ACL metadata."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    documents = []

    for file_path in sorted(DATA_DIR.glob("*.txt")):

        text = file_path.read_text(encoding="utf-8").strip()

        allowed_roles = ROLE_MAP.get(file_path.name, [])

        chunks = splitter.split_text(text)

        for index, chunk_text in enumerate(chunks):

            document = DocumentChunk(
                id=f"{file_path.stem}_{index}",
                text=chunk_text,
                source=file_path.name,
                allowed_roles=allowed_roles,
                metadata={
                    "chunk_id": f"{file_path.stem}_{index}",
                    "department": file_path.stem,
                    "file_type": "txt",
                    "chunk_index": index,
                    },
)
            

            documents.append(document)

    return documents


# -----------------------------
# Embedding + Qdrant ingestion
# -----------------------------

def ingest_documents(documents: list[DocumentChunk]) -> None:
    """Generate embeddings and store document chunks in Qdrant."""

    client = get_qdrant_client()

    ensure_collection(client)

    print(f"Loading embedding model: {EMBEDDING_MODEL}")

    embedding_model = TextEmbedding(EMBEDDING_MODEL)

    texts = [document.text for document in documents]

    vectors = list(embedding_model.embed(texts))

    points = []

    for document, vector in zip(documents, vectors):

        payload = {
            "text": document.text,
            "source": document.source,
            "allowed_roles": document.allowed_roles,
            "metadata": document.metadata,
        }

        point = PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"auditagent:{document.id}")),
            vector=vector.tolist(),
            payload=payload,
)
        

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print(f"Inserted {len(points)} chunks into Qdrant.")


# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":

    print("Starting AuditAgent ingestion...")

    documents = load_documents()

    print(f"Loaded {len(documents)} document chunks.")

    for document in documents:
        print(
            f"  {document.id} | "
            f"source={document.source} | "
            f"roles={document.allowed_roles}"
        )

    ingest_documents(documents)

    client = get_qdrant_client()

    collection_info = client.get_collection(COLLECTION_NAME)

    print(
        f"\nQdrant points: "
        f"{collection_info.points_count}"
    )

    print("Ingestion completed successfully.")