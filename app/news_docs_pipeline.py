import os
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Haystack 2.x imports
try:
    from haystack import Pipeline, Document
    from haystack.document_stores.in_memory import InMemoryDocumentStore
    from haystack.components.converters import PyPDFToDocument, TextFileToDocument
    from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
    from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
    from haystack.components.builders import PromptBuilder
    from haystack.components.generators import OpenAIGenerator, HuggingFaceLocalGenerator
    from haystack.components.writers import DocumentWriter
    from haystack.utils import Secret
    HAYSTACK_AVAILABLE = True
except ImportError as e:
    HAYSTACK_AVAILABLE = False
    Pipeline = None
    InMemoryDocumentStore = None
    PyPDFToDocument = None
    TextFileToDocument = None
    DocumentCleaner = None
    DocumentSplitter = None
    InMemoryBM25Retriever = None
    PromptBuilder = None
    OpenAIGenerator = None
    HuggingFaceLocalGenerator = None
    DocumentWriter = None
    Document = None
    Secret = None

import logging
logger = logging.getLogger("news_docs_pipeline")

GENERATOR_TYPE = os.getenv("GENERATOR_TYPE", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_generator():
    if GENERATOR_TYPE == "openai" and OPENAI_API_KEY and OpenAIGenerator:
        return OpenAIGenerator(api_key=Secret.from_token(OPENAI_API_KEY))
    elif GENERATOR_TYPE == "hf" and HuggingFaceLocalGenerator:
        return HuggingFaceLocalGenerator()
    return None


def _convert_document(document_path: str) -> List:
    """
    Convert a PDF or TXT file to Haystack Documents.
    Uses sources=[Path(...)] — correct Haystack 2.x API.
    Falls back to plain text read if converter fails.
    """
    path = Path(document_path)

    # --- Haystack converters (Haystack 2.x: sources= not paths=) ---
    if document_path.lower().endswith(".pdf") and PyPDFToDocument:
        try:
            converter = PyPDFToDocument()
            result = converter.run(sources=[path])
            docs = result.get("documents", [])
            if docs:
                logger.debug(f"PDF converted via Haystack: {document_path}")
                return docs
        except Exception as e:
            logger.warning(f"Haystack PyPDFToDocument failed: {e} — trying pypdf fallback")

        # pypdf fallback
        try:
            from pypdf import PdfReader
            reader = PdfReader(document_path)
            text = "\n".join(
                page.extract_text() for page in reader.pages if page.extract_text()
            )
            if text and Document:
                return [Document(content=text)]
        except Exception as e:
            logger.error(f"pypdf fallback failed: {e}")
            raise RuntimeError(f"Cannot read PDF: {e}")

    else:  # TXT
        if TextFileToDocument:
            try:
                converter = TextFileToDocument()
                result = converter.run(sources=[path])
                docs = result.get("documents", [])
                if docs:
                    logger.debug(f"TXT converted via Haystack: {document_path}")
                    return docs
            except Exception as e:
                logger.warning(f"Haystack TextFileToDocument failed: {e} — trying plain read")

        # Plain read fallback
        try:
            with open(document_path, "r", encoding="utf-8") as f:
                text = f.read()
            if Document:
                return [Document(content=text)]
        except Exception as e:
            raise RuntimeError(f"Cannot read TXT file: {e}")

    raise RuntimeError(f"Unsupported file type: {document_path}")


def _extractive_summary(chunks: List[str], max_sections: int = 3) -> Dict[str, Any]:
    """Simple extractive fallback when no LLM is available."""
    sections = []
    for i, chunk in enumerate(chunks[:max_sections]):
        sections.append({
            "title": f"Section {i + 1}",
            "insights": [chunk.strip()[:200]]
        })
    return {
        "doc_type": "Unknown",
        "summary": "Extractive summary (model unavailable)",
        "sections": sections,
        "sentiment": "NEUTRAL",
        "key_entities": [],
        "raw_text_preview": " ".join(chunks)[:300]
    }


def _clean_and_split(docs: List, split_length: int = 150, split_overlap: int = 20) -> List:
    """Clean and split Haystack documents."""
    cleaner = DocumentCleaner()
    splitter = DocumentSplitter(split_length=split_length, split_overlap=split_overlap)
    cleaned = cleaner.run(documents=docs)["documents"]
    return splitter.run(documents=cleaned)["documents"]


# ---------------------------------------------------------------------------
# Document Q&A Pipeline
# ---------------------------------------------------------------------------

class DocumentQAPipeline:
    def __init__(self, document_path: str):
        self.document_path = document_path
        self.store = None
        self.chunks = []
        self.error = None
        self._index_document()

    def _index_document(self):
        if not HAYSTACK_AVAILABLE:
            self.error = "Haystack not installed."
            return
        if not self.document_path or not os.path.exists(self.document_path):
            self.error = "No document uploaded."
            return
        try:
            docs = _convert_document(self.document_path)
            split_docs = _clean_and_split(docs)
            self.chunks = [d.content for d in split_docs]
            logger.debug("Chunks after split: %s", self.chunks[:3])

            self.store = InMemoryDocumentStore()
            writer = DocumentWriter(document_store=self.store)
            writer.run(documents=split_docs)

        except Exception as e:
            self.error = f"Indexing error: {e}"
            logger.error(traceback.format_exc())

    def answer(self, question: str) -> Dict[str, Any]:
        if self.error:
            return {"error": self.error}
        if not question:
            return {"error": "No question provided."}
        try:
            retriever = InMemoryBM25Retriever(document_store=self.store, top_k=3)
            generator = _get_generator()

            if not generator:
                passages = self.chunks[:3]
                return {
                    "answer": "Model unavailable. Extractive summary:",
                    "sources": passages,
                    "confidence": "LOW",
                    "error": "Generator unavailable"
                }

            prompt = (
                "You are a financial document QA agent. Answer ONLY using the provided Context. "
                "If the answer is not found, say 'Not found in document.'\n"
                "Context:\n{% for doc in documents %}- {{ doc.content }}\n{% endfor %}\n"
                "Question: {{ question }}\n"
                "Answer (cite passage location if possible):"
            )

            pipe = Pipeline()
            pipe.add_component("retriever", retriever)
            pipe.add_component("prompt_builder", PromptBuilder(template=prompt))
            pipe.add_component("llm", generator)
            pipe.connect("retriever", "prompt_builder.documents")
            pipe.connect("prompt_builder", "llm")

            result = pipe.run({"retriever": {"query": question}, "prompt_builder": {"question": question}})
            answer = result["llm"]["replies"][0]
            sources = [d.content for d in result["retriever"]["documents"]]
            scores = [d.score for d in result["retriever"]["documents"] if hasattr(d, "score")]
            conf = "HIGH" if scores and scores[0] > 2 else "MEDIUM" if scores else "LOW"

            return {"answer": answer, "sources": sources, "confidence": conf}

        except Exception as e:
            logger.error(traceback.format_exc())
            return {"error": f"QA error: {e}"}


# ---------------------------------------------------------------------------
# Document Analysis Pipeline
# ---------------------------------------------------------------------------

class DocumentAnalysisPipeline:
    def __init__(self):
        self.error = None

    def analyze(self, document_path: str) -> Dict[str, Any]:
        if not HAYSTACK_AVAILABLE:
            return {"error": "Haystack not installed."}

        if not document_path or not os.path.exists(document_path):
            return {"error": "No document uploaded."}

        try:
            # Convert + split
            docs = _convert_document(document_path)
            split_docs = _clean_and_split(docs)
            chunks = [d.content for d in split_docs if d.content]

            if not chunks:
                return {"error": "No readable content found in document."}

            full_text = " ".join(chunks)
            text_lower = full_text.lower()

            # Sentiment detection
            positive_words = [
                "growth", "profit", "increase", "strong", "improvement",
                "opportunity", "positive", "success", "gain", "expansion"
            ]

            negative_words = [
                "risk", "loss", "decline", "debt", "competition",
                "weakness", "negative", "lawsuit", "uncertainty", "threat"
            ]

            positive_score = sum(text_lower.count(word) for word in positive_words)
            negative_score = sum(text_lower.count(word) for word in negative_words)

            if positive_score > negative_score:
                sentiment = "POSITIVE"
            elif negative_score > positive_score:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"

            # Detect document type
            if any(word in text_lower for word in [
                "revenue", "net income", "earnings", "balance sheet"
            ]):
                doc_type = "Financial Report"
            elif any(word in text_lower for word in [
                "breaking news", "announced", "according to"
            ]):
                doc_type = "News Article"
            elif any(word in text_lower for word in [
                "conference call", "operator", "question-and-answer"
            ]):
                doc_type = "Earnings Call"
            else:
                doc_type = "General Document"

            # Build sections
            sections = []

            for i, chunk in enumerate(chunks[:3]):
                short_chunk = chunk.strip().replace("\n", " ")

                sections.append({
                    "title": f"Section {i + 1}",
                    "insights": [
                        short_chunk[:300]
                    ]
                })

            # Extract important entities
            keywords = []
            important_terms = [
                "Apple", "Microsoft", "Google", "Amazon", "Tesla",
                "revenue", "profit", "growth", "risk", "competition",
                "market", "AI", "cloud", "debt", "inflation"
            ]

            for term in important_terms:
                if term.lower() in text_lower:
                    keywords.append(term)

            return {
                "doc_type": doc_type,
                "summary": full_text[:500] + "..." if len(full_text) > 500 else full_text,
                "sections": sections,
                "sentiment": sentiment,
                "key_entities": keywords[:10],
                "raw_text_preview": full_text[:300]
            }

        except Exception as e:
            logger.error(traceback.format_exc())
            return {"error": f"Analysis error: {e}"}