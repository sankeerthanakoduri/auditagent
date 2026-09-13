import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
)


load_dotenv()


COLLECTION_NAME = (
    "auditagent_docs"
)

VECTOR_SIZE = 384

DEFAULT_QDRANT_URL = (
    "http://localhost:6333"
)


def get_qdrant_url() -> str:

    return os.getenv(
        "QDRANT_URL",
        DEFAULT_QDRANT_URL,
    )


def get_qdrant_api_key():

    return os.getenv(
        "QDRANT_API_KEY"
    )


def get_qdrant_client():

    url = get_qdrant_url()

    api_key = get_qdrant_api_key()

    if api_key:

        return QdrantClient(
            url=url,
            api_key=api_key,
        )

    return QdrantClient(
        url=url
    )


def create_collection():

    client = get_qdrant_client()

    collections = (
        client
        .get_collections()
        .collections
    )

    existing_names = {
        collection.name
        for collection
        in collections
    }

    if (
        COLLECTION_NAME
        not in existing_names
    ):

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

        print(
            f"Created collection: "
            f"{COLLECTION_NAME}"
        )

    else:

        print(
            f"Collection already exists: "
            f"{COLLECTION_NAME}"
        )


if __name__ == "__main__":

    create_collection()