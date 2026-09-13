import os

import streamlit as st

from agent.graph import app as auditagent_app
from ingest.pipeline import (
    ingest_uploaded_files,
)


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

    .source-card {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        background: rgba(128, 128, 128, 0.08);
        margin-bottom: 0.5rem;
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
        "Demo role selector. In a production deployment, "
        "this role should come from authenticated identity "
        "or SSO claims rather than user input."
    )

    st.divider()

    st.markdown(
        """
        ### Knowledge sources

        **Company documents**
        PDF · DOCX · TXT

        **Structured data**
        SQL database

        **External knowledge**
        Web search
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
# Tabs
# ============================================================

chat_tab, knowledge_tab = st.tabs(
    [
        "Chat",
        "Knowledge Base",
    ]
)


# ============================================================
# CHAT
# ============================================================

with chat_tab:

    st.subheader(
        "Ask your organization anything"
    )

    # --------------------------------------------------------
    # Existing conversation
    # --------------------------------------------------------

    for message in (
        st.session_state.messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            if (
                message["role"]
                == "assistant"
            ):

                sources = message.get(
                    "sources",
                    [],
                )

                if sources:

                    st.markdown(
                        "**Sources**"
                    )

                    for source in sources:

                        st.markdown(
                            f"- `{source}`"
                        )

                verification = (
                    message.get(
                        "verification"
                    )
                )

                if verification:

                    if (
                        verification
                        == "SUPPORTED"
                    ):

                        st.caption(
                            "✓ Answer verified "
                            "against available evidence."
                        )

                    else:

                        st.caption(
                            "⚠ Answer could not "
                            "be verified."
                        )


    # --------------------------------------------------------
    # Question
    # --------------------------------------------------------

    question = st.chat_input(
        "Ask a question about your organization's knowledge..."
    )


    if question:

        # ----------------------------------------------------
        # User message
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message(
            "user"
        ):

            st.markdown(
                question
            )


        # ----------------------------------------------------
        # Agent execution
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Searching authorized knowledge..."
            ):

                try:

                    result = (
                        auditagent_app.invoke(
                            {
                                "question": (
                                    question.strip()
                                ),
                                "user_role": (
                                    user_role
                                ),
                                "retrieval_attempts": 0,
                            }
                        )
                    )

                except Exception as exc:

                    answer = (
                        "I couldn't process "
                        "that request."
                    )

                    st.error(
                        answer
                    )

                    with st.expander(
                        "Technical details"
                    ):

                        st.code(
                            str(exc)
                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": [],
                            "verification": None,
                        }
                    )

                    st.stop()


            answer = result.get(
                "answer",
                "No answer was generated.",
            )

            verification = result.get(
                "verification"
            )

            route = result.get(
                "route",
                "unknown",
            )


            # ------------------------------------------------
            # Display answer
            # ------------------------------------------------

            st.markdown(
                answer
            )


            # ------------------------------------------------
            # Collect sources
            # ------------------------------------------------

            sources = []

            documents = result.get(
                "documents",
                [],
            )

            for item in documents:

                document = getattr(
                    item,
                    "document",
                    item,
                )

                source = getattr(
                    document,
                    "source",
                    None,
                )

                if (
                    source
                    and source not in sources
                ):

                    sources.append(
                        source
                    )


            web_results = result.get(
                "web_results",
                [],
            )

            for item in web_results:

                url = getattr(
                    item,
                    "url",
                    None,
                )

                if (
                    url
                    and url not in sources
                ):

                    sources.append(
                        url
                    )


            # ------------------------------------------------
            # Sources
            # ------------------------------------------------

            if sources:

                st.markdown(
                    "**Sources**"
                )

                for source in sources:

                    st.markdown(
                        f"- `{source}`"
                    )


            # ------------------------------------------------
            # Verification
            # ------------------------------------------------

            if (
                verification
                == "SUPPORTED"
            ):

                st.success(
                    "Answer verified"
                )

            else:

                st.warning(
                    "AuditAgent could not "
                    "verify the answer from "
                    "authorized evidence."
                )


            # ------------------------------------------------
            # Technical transparency
            # ------------------------------------------------

            with st.expander(
                "View audit details"
            ):

                st.write(
                    {
                        "role": user_role,
                        "route": route,
                        "verification": verification,
                        "retrieval_attempts": (
                            result.get(
                                "retrieval_attempts",
                                0,
                            )
                        ),
                    }
                )


            # ------------------------------------------------
            # Save assistant message
            # ------------------------------------------------

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "verification": verification,
                }
            )


# ============================================================
# KNOWLEDGE BASE
# ============================================================

with knowledge_tab:

    st.subheader(
        "Company Knowledge Base"
    )

    st.write(
        """
        Upload enterprise documents once. AuditAgent will extract
        the text, chunk it, generate embeddings, apply access
        permissions, and index the content in Qdrant.
        """
    )

    st.info(
        "This section is for administrators or data owners. "
        "End users normally only ask questions."
    )


    # --------------------------------------------------------
    # Admin authentication
    # --------------------------------------------------------

    configured_password = os.getenv(
        "ADMIN_PASSWORD"
    )

    if not configured_password:

        st.warning(
            "ADMIN_PASSWORD is not configured. "
            "Set it in your .env file before using "
            "document ingestion."
        )

    else:

        admin_password = st.text_input(
            "Admin password",
            type="password",
        )

        if (
            admin_password
            != configured_password
        ):

            st.caption(
                "Enter the administrator password "
                "to manage the knowledge base."
            )

        else:

            st.success(
                "Administrator access enabled."
            )

            st.divider()

            # ------------------------------------------------
            # Upload
            # ------------------------------------------------

            uploaded_files = (
                st.file_uploader(
                    "Upload enterprise documents",
                    type=[
                        "pdf",
                        "docx",
                        "txt",
                        "md",
                    ],
                    accept_multiple_files=True,
                )
            )

            allowed_roles = st.multiselect(
                "Who can access these documents?",
                ROLES,
                default=[
                    "employee",
                    "hr",
                    "finance",
                    "admin",
                ],
            )

            if st.button(
                "Index documents",
                type="primary",
                use_container_width=True,
            ):

                if not uploaded_files:

                    st.warning(
                        "Select at least one document."
                    )

                elif not allowed_roles:

                    st.warning(
                        "Select at least one "
                        "authorized role."
                    )

                else:

                    with st.spinner(
                        "Extracting, chunking and indexing..."
                    ):

                        results = (
                            ingest_uploaded_files(
                                uploaded_files,
                                allowed_roles,
                            )
                        )

                    st.subheader(
                        "Ingestion results"
                    )

                    for filename, status in (
                        results.items()
                    ):

                        if status.startswith(
                            "Indexed successfully"
                        ):

                            st.success(
                                f"{filename}: {status}"
                            )

                        else:

                            st.error(
                                f"{filename}: {status}"
                            )


    st.divider()

    st.markdown(
        """
        ### How this works

        **1. Upload**

        Administrator uploads company documents.

        **2. Process**

        AuditAgent extracts and chunks the content.

        **3. Secure**

        Each chunk receives an allowed-role ACL.

        **4. Index**

        Embeddings are stored in Qdrant.

        **5. Query**

        Users ask natural-language questions.

        **6. Retrieve**

        Only authorized evidence reaches the agent.

        **7. Verify**

        Unsupported answers are rejected.
        """
    )