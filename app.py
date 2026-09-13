import hashlib
import os

import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from agent.graph import app as auditagent_app
from ingest.pipeline import extract_text


load_dotenv()


# ============================================================
# Configuration
# ============================================================

st.set_page_config(
    page_title="AuditAgent",
    page_icon="🔐",
    layout="wide",
)


ROLES = [
    "employee",
    "finance",
    "hr",
    "admin",
]


# ============================================================
# Session state
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_doc_hash" not in st.session_state:
    st.session_state.uploaded_doc_hash = None

if "uploaded_doc_name" not in st.session_state:
    st.session_state.uploaded_doc_name = None

if "uploaded_doc_chunks" not in st.session_state:
    st.session_state.uploaded_doc_chunks = []

if "uploaded_doc_bm25" not in st.session_state:
    st.session_state.uploaded_doc_bm25 = None


# ============================================================
# Styling
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #8b949e;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Header
# ============================================================

st.markdown(
    '<div class="main-title">AuditAgent</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    Secure, access-controlled enterprise knowledge assistant.
    Ask natural-language questions across authorized documents,
    structured data, and external knowledge.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.header("Access")

    user_role = st.selectbox(
        "Role",
        ROLES,
        index=0,
    )

    st.caption(
        "Demo role selector for the enterprise knowledge base. "
        "Uploaded personal documents are handled separately "
        "for the current session."
    )

    st.divider()

    st.markdown(
        """
        ### Knowledge sources

        **Uploaded document**
        PDF · DOCX · TXT · MD

        **Enterprise sources**
        SQL · company documents · web
        """
    )

    st.divider()

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# Upload a document for direct document chat
# ============================================================

st.subheader("Upload a document")

st.caption(
    "Upload one document and ask questions about it directly. "
    "No administrator setup or document indexing step is required."
)

uploaded_file = st.file_uploader(
    "Choose a document",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=False,
    key="document_uploader",
)


if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if file_hash != st.session_state.uploaded_doc_hash:
        try:
            with st.spinner("Reading document..."):
                text = extract_text(
                    uploaded_file.name,
                    file_bytes,
                )

                if not text.strip():
                    raise ValueError(
                        "No readable text was found in the uploaded document."
                    )

                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=700,
                    chunk_overlap=100,
                    separators=[
                        "\n\n",
                        "\n",
                        ". ",
                        " ",
                        "",
                    ],
                )

                chunks = splitter.split_text(text)

                tokenized_chunks = [
                    chunk.lower().split()
                    for chunk in chunks
                ]

                bm25 = BM25Okapi(tokenized_chunks)

            st.session_state.uploaded_doc_hash = file_hash
            st.session_state.uploaded_doc_name = uploaded_file.name
            st.session_state.uploaded_doc_chunks = chunks
            st.session_state.uploaded_doc_bm25 = bm25
            st.session_state.messages = []

            st.success(
                f"{uploaded_file.name} is ready. "
                f"{len(chunks)} text chunks loaded."
            )

        except Exception as exc:
            st.session_state.uploaded_doc_hash = None
            st.session_state.uploaded_doc_name = None
            st.session_state.uploaded_doc_chunks = []
            st.session_state.uploaded_doc_bm25 = None
            st.error(f"Could not read the document: {exc}")

    else:
        st.success(
            f"{st.session_state.uploaded_doc_name} is ready for questions."
        )


if st.session_state.uploaded_doc_name:
    st.info(
        f"Active document: {st.session_state.uploaded_doc_name}"
    )


# ============================================================
# Uploaded-document question answering
# ============================================================

def answer_from_uploaded_document(question: str) -> dict:
    chunks = st.session_state.uploaded_doc_chunks
    bm25 = st.session_state.uploaded_doc_bm25

    if not chunks or bm25 is None:
        return {
            "answer": "Please upload a document first.",
            "source": None,
        }

    query_tokens = question.lower().split()
    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(chunks)),
        key=lambda index: scores[index],
        reverse=True,
    )[:5]

    selected_chunks = [
        chunks[index]
        for index in ranked_indices
    ]

    evidence = "\n\n---\n\n".join(
        selected_chunks
    )

    # Keep the context bounded while retaining the most relevant chunks.
    evidence = evidence[:18000]

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
        service_tier="auto",
    )

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the document evidence below.
Do not invent facts or use outside knowledge.
If the answer is not present in the evidence, clearly say:
"I could not find that information in the uploaded document."

User question:
{question}

Document evidence:
{evidence}
"""

    response = llm.invoke(prompt)

    answer = (
        response.content
        if isinstance(response.content, str)
        else str(response.content)
    ).strip()

    return {
        "answer": answer,
        "source": st.session_state.uploaded_doc_name,
    }


# ============================================================
# Chat
# ============================================================

st.subheader("Ask your question")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            source = message.get("source")
            if source:
                st.caption(
                    f"Source: {source}"
                )


question = st.chat_input(
    "Ask a question about the uploaded document or enterprise knowledge..."
)


if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Reading the available evidence..."):
            try:
                if st.session_state.uploaded_doc_chunks:
                    result = answer_from_uploaded_document(
                        question
                    )
                else:
                    result = auditagent_app.invoke(
                        {
                            "question": question.strip(),
                            "user_role": user_role,
                            "retrieval_attempts": 0,
                        }
                    )

                answer = result.get(
                    "answer",
                    "No answer was generated.",
                )

                st.markdown(answer)

                source = result.get("source")

                if source:
                    st.caption(
                        f"Source: {source}"
                    )

                # Preserve the existing enterprise-agent transparency
                # when the question did not use an uploaded document.
                if not source and isinstance(result, dict):
                    sources = []

                    for item in result.get("documents", []):
                        document = getattr(
                            item,
                            "document",
                            item,
                        )
                        source_name = getattr(
                            document,
                            "source",
                            None,
                        )
                        if (
                            source_name
                            and source_name not in sources
                        ):
                            sources.append(source_name)

                    for item in result.get("web_results", []):
                        url = getattr(
                            item,
                            "url",
                            None,
                        )
                        if url and url not in sources:
                            sources.append(url)

                    if sources:
                        st.markdown("**Sources**")
                        for source_name in sources:
                            st.markdown(
                                f"- `{source_name}`"
                            )

                    verification = result.get(
                        "verification"
                    )

                    if verification == "SUPPORTED":
                        st.success("Answer verified")
                    elif verification:
                        st.warning(
                            "Answer could not be verified against authorized evidence."
                        )

                    with st.expander("View audit details"):
                        st.write(
                            {
                                "role": user_role,
                                "route": result.get("route", "unknown"),
                                "verification": verification,
                                "retrieval_attempts": result.get(
                                    "retrieval_attempts",
                                    0,
                                ),
                            }
                        )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "source": source,
                    }
                )

            except Exception as exc:
                answer = "I couldn't process that request."
                st.error(answer)

                with st.expander("Technical details"):
                    st.code(str(exc))

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "source": None,
                    }
                )
