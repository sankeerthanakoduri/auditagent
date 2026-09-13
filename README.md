---
title: AuditAgent
emoji: 🔐
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# AuditAgent

AuditAgent is an agentic, access-controlled RAG system designed for secure and auditable enterprise question answering.

## Features

- Retrieval-time access control
- Hybrid dense + BM25 retrieval
- BGE reranking
- PDF/DOCX/TXT/Markdown document ingestion
- SQL and web routing
- LangGraph agent orchestration
- Retrieval critique and reformulation
- Answer verification and abstention
- Audit logging
- Deterministic evaluation
- Automated CI testing

## Architecture

Streamlit UI → LangGraph Agent → Router → Retrieval / SQL / Web → ACL → Reranking → Critic → Synthesizer → Verifier

## Technology

- Python 3.11
- LangGraph
- LangChain
- Groq
- Qdrant
- FastEmbed
- BM25
- SQLite
- Streamlit

## Deployment

This application runs as a Docker-based Hugging Face Space on port 7860.

Environment variables and secrets are configured through the Space Settings page.

## Security

This demo uses synthetic/sample data. Production deployments should integrate authentication and authorization with an enterprise identity provider rather than relying on a client-side role selector.
