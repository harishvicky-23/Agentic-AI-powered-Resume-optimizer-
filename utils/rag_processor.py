"""
RAG Processor — FAISS + Google Embeddings
Summarises resume sections and JD requirements for better agent context.
Falls back silently to raw text on any error.
"""

from __future__ import annotations
import os

from utils.asyncio_compat import ensure_event_loop


class RAGProcessor:
    """Lightweight RAG layer using FAISS + Google Generative AI Embeddings."""

    def __init__(self):
        ensure_event_loop()
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        self._embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.environ["GOOGLE_API_KEY"],
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ── Public API ────────────────────────────────────────────────────────────────
    def summarize_resume(self, text: str) -> str:
        """Return a semantically-structured summary of the resume."""
        if not text or len(text) < 200:
            return text
        try:
            return self._retrieve(
                text,
                queries=[
                    "professional summary objective",
                    "work experience responsibilities achievements",
                    "technical skills programming languages frameworks",
                    "projects portfolio open source",
                    "education degrees certifications",
                    "awards leadership publications",
                ],
                header="# Resume — Structured Summary\n\n",
            )
        except Exception as e:
            print(f"[RAG] resume summarisation skipped: {e}")
            return text

    def summarize_job_description(self, text: str) -> str:
        """Return a structured breakdown of the JD."""
        if not text or len(text) < 200:
            return text
        try:
            return self._retrieve(
                text,
                queries=[
                    "required skills qualifications must have",
                    "preferred nice to have bonus skills",
                    "responsibilities duties day to day",
                    "years of experience seniority level",
                    "tools technologies stack",
                    "education degree requirement",
                    "company culture values team",
                ],
                header="# Job Description — Structured Summary\n\n",
            )
        except Exception as e:
            print(f"[RAG] JD summarisation skipped: {e}")
            return text

    # ── Internal ──────────────────────────────────────────────────────────────────
    def _retrieve(self, text: str, queries: list[str], header: str = "") -> str:
        from langchain_community.vectorstores import FAISS
        from langchain.docstore.document import Document

        chunks = self._splitter.split_text(text)
        if not chunks:
            return text

        docs = [Document(page_content=c) for c in chunks]
        store = FAISS.from_documents(docs, self._embeddings)

        seen: set[str] = set()
        output = header

        for query in queries:
            results = store.similarity_search(query, k=2)
            for doc in results:
                snippet = doc.page_content.strip()
                # deduplicate near-identical chunks
                key = snippet[:80]
                if key not in seen:
                    seen.add(key)
                    output += f"### {query.title()}\n{snippet}\n\n"

        return output if len(output) > len(header) + 50 else text
