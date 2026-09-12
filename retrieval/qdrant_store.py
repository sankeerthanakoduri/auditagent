from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "auditagent_docs"
VECTOR_SIZE = 384


def get_qdrant_client() -> QdrantClient:
    """Return a client connected to the local Qdrant instance."""
    return QdrantClient(url="http://localhost:6333")


def create_collection() -> None:
    """Create the document collection if it does not already exist."""
    client = get_qdrant_client()

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


if __name__ == "__main__":
    create_collection()