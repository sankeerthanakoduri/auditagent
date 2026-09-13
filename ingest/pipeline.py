import io
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from docx import Document as DocxDocument
from fastembed import TextEmbedding
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from pypdf import PdfReader
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
    Distance,
)

from retrieval.models import DocumentChunk
from retrieval.qdrant_store import (
    COLLECTION_NAME,
    VECTOR_SIZE,
    get_qdrant_client,
)


load_dotenv()


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path("data")

EMBEDDING_MODEL = (
    "BAAI/bge-small-en-v1.5"
)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


# ============================================================
# Existing demo role configuration
# ============================================================

ROLE_MAP = {
    "finance.txt": [
        "finance",
        "admin",
    ],
    "hr.txt": [
        "hr",
        "admin",
    ],
    "general.txt": [
        "finance",
        "hr",
        "employee",
        "admin",
    ],
}


# ============================================================
# Text splitter
# ============================================================

def get_splitter():

    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )


# ============================================================
# File extraction
# ============================================================

def extract_pdf_text(
    file_bytes: bytes,
) -> str:

    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        text = page.extract_text() or ""

        if text.strip():

            pages.append(
                f"[Page {page_number}]\n"
                f"{text}"
            )

    return "\n\n".join(pages)


def extract_docx_text(
    file_bytes: bytes,
) -> str:

    document = DocxDocument(
        io.BytesIO(file_bytes)
    )

    paragraphs = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:

            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def extract_text(
    filename: str,
    file_bytes: bytes,
) -> str:

    suffix = (
        Path(filename)
        .suffix
        .lower()
    )

    if suffix == ".pdf":

        return extract_pdf_text(
            file_bytes
        )

    if suffix == ".docx":

        return extract_docx_text(
            file_bytes
        )

    if suffix in {
        ".txt",
        ".md",
    }:

        return file_bytes.decode(
            "utf-8",
            errors="ignore",
        )

    raise ValueError(
        f"Unsupported document type: "
        f"{suffix}"
    )


# ============================================================
# Build document chunks
# ============================================================

def build_document_chunks(
    filename: str,
    text: str,
    allowed_roles: list[str],
) -> list[DocumentChunk]:

    splitter = get_splitter()

    chunks = splitter.split_text(
        text
    )

    documents = []

    file_stem = Path(
        filename
    ).stem

    for index, chunk_text in enumerate(
        chunks
    ):

        chunk_id = (
            f"{file_stem}_{index}"
        )

        document = DocumentChunk(
            id=chunk_id,
            text=chunk_text,
            source=filename,
            allowed_roles=allowed_roles,
            metadata={
                "chunk_id": chunk_id,
                "source": filename,
                "file_type": (
                    Path(filename)
                    .suffix
                    .lower()
                    .replace(".", "")
                ),
                "chunk_index": index,
                "ingestion_type": "document",
            },
        )

        documents.append(
            document
        )

    return documents


# ============================================================
# Qdrant
# ============================================================

def ensure_collection():

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

    return client


# ============================================================
# Delete an existing source
# ============================================================

def delete_source(
    client,
    source: str,
):

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(
                        value=source
                    ),
                )
            ]
        ),
    )


# ============================================================
# Ingest chunks into Qdrant
# ============================================================

def ingest_documents(
    documents: list[DocumentChunk],
):

    if not documents:

        raise ValueError(
            "No document chunks were created."
        )

    client = ensure_collection()

    embedding_model = TextEmbedding(
        EMBEDDING_MODEL
    )

    texts = [
        document.text
        for document in documents
    ]

    vectors = list(
        embedding_model.embed(
            texts
        )
    )

    sources = {
        document.source
        for document in documents
    }

    for source in sources:

        delete_source(
            client,
            source,
        )

    points = []

    for document, vector in zip(
        documents,
        vectors,
    ):

        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                (
                    "auditagent:"
                    f"{document.source}:"
                    f"{document.id}"
                ),
            )
        )

        payload = {
            "text": document.text,
            "source": document.source,
            "allowed_roles": (
                document.allowed_roles
            ),
            "metadata": document.metadata,
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload=payload,
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)


# ============================================================
# Ingest an uploaded file
# ============================================================

def ingest_uploaded_file(
    filename: str,
    file_bytes: bytes,
    allowed_roles: list[str],
) -> int:

    text = extract_text(
        filename,
        file_bytes,
    )

    if not text.strip():

        raise ValueError(
            f"No readable text found in "
            f"{filename}"
        )

    documents = (
        build_document_chunks(
            filename=filename,
            text=text,
            allowed_roles=allowed_roles,
        )
    )

    return ingest_documents(
        documents
    )


# ============================================================
# Ingest multiple uploaded files
# ============================================================

def ingest_uploaded_files(
    files,
    allowed_roles: list[str],
) -> dict:

    results = {}

    for uploaded_file in files:

        filename = uploaded_file.name

        file_bytes = (
            uploaded_file.getvalue()
        )

        try:

            chunk_count = (
                ingest_uploaded_file(
                    filename=filename,
                    file_bytes=file_bytes,
                    allowed_roles=allowed_roles,
                )
            )

            results[filename] = (
                f"Indexed successfully "
                f"({chunk_count} chunks)"
            )

        except Exception as exc:

            results[filename] = (
                f"Failed: {exc}"
            )

    return results


# ============================================================
# Existing local TXT ingestion
# ============================================================

def load_documents() -> list[DocumentChunk]:

    documents = []

    for file_path in sorted(
        DATA_DIR.glob("*.txt")
    ):

        text = (
            file_path
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )

        if not text:
            continue

        allowed_roles = ROLE_MAP.get(
            file_path.name,
            [],
        )

        documents.extend(
            build_document_chunks(
                filename=file_path.name,
                text=text,
                allowed_roles=allowed_roles,
            )
        )

    return documents


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print(
        "Starting AuditAgent ingestion..."
    )

    documents = load_documents()

    print(
        f"Loaded "
        f"{len(documents)} "
        f"document chunks."
    )

    if documents:

        inserted = ingest_documents(
            documents
        )

        print(
            f"Inserted {inserted} "
            f"chunks into Qdrant."
        )

    else:

        print(
            "No .txt documents found "
            "in data/."
        )

    client = get_qdrant_client()

    collection_info = (
        client.get_collection(
            COLLECTION_NAME
        )
    )

    print(
        f"Qdrant points: "
        f"{collection_info.points_count}"
    )

    print(
        "Ingestion completed successfully."
    )