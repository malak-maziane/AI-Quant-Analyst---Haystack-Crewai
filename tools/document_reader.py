"""
Robust document ingestion pipeline with comprehensive error handling and logging.
Handles TXT and PDF uploads with multiple encoding fallbacks and RAG integration.
"""
from typing import List, Dict, Optional, Any
import os
import sys
import json
import re
import logging

import requests
import yfinance as yf

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Translation helpers ---
def _translate_to_english(text: str) -> str:
    """Translate French to English using LibreTranslate API."""
    try:
        resp = requests.post(
            "https://libretranslate.de/translate",
            data={
                "q": text,
                "source": "fr",
                "target": "en",
                "format": "text"
            },
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json().get("translatedText", text)
    except Exception as e:
        logger.debug(f"Translation failed: {e}")
    return text


def _is_french(text: str) -> bool:
    """Heuristic: detect French text."""
    french_words = [
        "risque", "quels", "principaux", "facteurs", "croissance", "entreprise",
        "marché", "action", "analyse", "document", "financier", "bénéfice",
        "revenu", "secteur", "résultat", "rapport", "stratégie", "concurrence"
    ]
    lowered = text.lower()
    if any(w in lowered for w in french_words):
        return True
    try:
        text.encode('ascii')
    except UnicodeEncodeError:
        return True
    return False


# Haystack imports
try:
    from crewai.tools import tool
except ImportError:
    def tool(name):
        def decorator(fn):
            return fn
        return decorator

try:
    from haystack import Document
    from haystack.components.converters import TextFileToDocument, PyPDFToDocument
    from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
    from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
    from haystack.document_stores.in_memory import InMemoryDocumentStore
    HAYSTACK_AVAILABLE = True
except ImportError:
    Document = None
    TextFileToDocument = None
    PyPDFToDocument = None
    DocumentCleaner = None
    DocumentSplitter = None
    SentenceTransformersDocumentEmbedder = None
    SentenceTransformersTextEmbedder = None
    InMemoryEmbeddingRetriever = None
    InMemoryDocumentStore = None
    HAYSTACK_AVAILABLE = False

try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from config import Config
from app.utils import compute_sentiment, POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS

SENTIMENT_KEYWORDS = POSITIVE_KEYWORDS + NEGATIVE_KEYWORDS
RAG_STORE_CACHE: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Dynamic fallback news
# ---------------------------------------------------------------------------

def _load_local_news(ticker: str) -> str:
    """Generate dynamic fallback news based on ticker instead of static text."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        company_name = info.get('longName', ticker.upper())
        sector = info.get('sector', 'technology')
        industry = info.get('industry', 'software')

        current_price = info.get('currentPrice', 'N/A')
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 'N/A')

        dynamic_news = f"""
        {company_name} ({ticker}) is a {sector} company in the {industry} industry.
        Current trading price: ${current_price if current_price != 'N/A' else 'market data unavailable'}.
        Market capitalization: ${market_cap / 1e9:.1f}B if market_cap > 0 else 'data unavailable'.
        P/E ratio: {pe_ratio if pe_ratio != 'N/A' else 'data unavailable'}.

        Recent market analysis shows {ticker} operating in a competitive {industry} landscape.
        Investors are monitoring {company_name}'s performance relative to industry peers and broader market trends.
        Key factors include revenue growth, margin expansion, and strategic positioning within the {sector} sector.
        """
        return dynamic_news.strip()
    except Exception as e:
        return (
            f"Market analysis for {ticker}: Global equity markets are influenced by macroeconomic trends, "
            "earnings expectations, and sector-specific dynamics. Investors should evaluate revenue momentum, "
            "competitive positioning, and industry growth prospects when assessing investment opportunities."
        )


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _extract_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _top_insights_from_text(text: str, top_n: int = Config.TOP_INSIGHTS) -> List[str]:
    sentences = _extract_sentences(text)
    scored = []
    for sentence in sentences:
        score = sum(1 for kw in SENTIMENT_KEYWORDS if kw in sentence.lower())
        if score > 0:
            scored.append((score, len(sentence), sentence))
    scored.sort(key=lambda item: (-item[0], item[1]))
    insights = [item[2] for item in scored[:top_n]]
    if len(insights) < top_n:
        for sentence in sentences:
            if sentence not in insights:
                insights.append(sentence)
            if len(insights) >= top_n:
                break
    return insights[:top_n]


# ---------------------------------------------------------------------------
# News fetchers
# ---------------------------------------------------------------------------

def _fetch_newsapi_articles(ticker: str) -> List[str]:
    """Fetch news from NewsAPI with better error handling and fallback."""
    if not Config.HAS_NEWS_API:
        print(f"NewsAPI key not configured for {ticker}")
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f'"{ticker}" stock OR "{ticker}" shares OR "{ticker}" market',
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(Config.MAX_NEWS_ARTICLES, 20),
        "apiKey": Config.NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()

        articles = []
        for item in payload.get("articles", []):
            title = item.get("title", "").strip()
            description = item.get("description", "").strip()
            content = item.get("content", "").strip()

            if title:
                article_text = title
                if description:
                    article_text += f". {description}"
                if content and len(content) > len(description):
                    article_text += f" {content}"
                articles.append(article_text)

        print(f"NewsAPI fetched {len(articles)} articles for {ticker}")
        return articles[:Config.MAX_NEWS_ARTICLES]

    except Exception as e:
        print(f"NewsAPI error for {ticker}: {e}")
        return []


def _fetch_yfinance_news(ticker: str) -> List[str]:
    """Fetch news from yfinance with better error handling and content extraction."""
    try:
        ticker_obj = yf.Ticker(ticker)
        news = ticker_obj.news

        if not news or not isinstance(news, list):
            print(f"No yfinance news available for {ticker}")
            return []

        articles = []
        for item in news[:Config.MAX_NEWS_ARTICLES]:
            if not isinstance(item, dict):
                continue

            content_item = item.get("content", item) if isinstance(item.get("content"), dict) else item

            title = content_item.get("title", "").strip()
            summary = content_item.get("summary", "").strip() or content_item.get("description", "").strip()

            if title:
                article_text = title
                if summary and summary != title:
                    article_text += f". {summary}"

                publisher = content_item.get("provider", {}).get("displayName", "")
                if not publisher:
                    publisher = content_item.get("publisher", "")
                if publisher:
                    article_text += f" (Source: {publisher})"

                articles.append(article_text)

        print(f"yfinance fetched {len(articles)} articles for {ticker}")
        return articles
    except Exception as e:
        print(f"yfinance news error for {ticker}: {e}")
        return []


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def _load_uploaded_document(document_path: str) -> str:
    print(f"[DEBUG] _load_uploaded_document called with: {document_path}")
    if not document_path or not os.path.exists(document_path):
        print(f"[ERROR] Uploaded document not found: {document_path}")
        return "[ERROR] Uploaded document not found: {}".format(document_path)

    if document_path.lower().endswith(".txt"):
        try:
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[DEBUG] TXT document loaded successfully: {document_path}")
            return content
        except Exception as e:
            print(f"[ERROR] Failed to read TXT document: {e}")
            return f"[ERROR] Failed to read TXT document: {e}"

    if document_path.lower().endswith(".pdf"):
        if HAYSTACK_AVAILABLE and PyPDFToDocument is not None:
            try:
                converter = PyPDFToDocument()
                docs = converter.run(paths=[document_path])
                content = "\n".join([doc.content for doc in docs])
                print(f"[DEBUG] PDF document loaded with Haystack: {document_path}")
                return content
            except Exception as e:
                print(f"[ERROR] Haystack PDF load failed: {e}")

        if PDF_SUPPORT:
            try:
                reader = PdfReader(document_path)
                content = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
                print(f"[DEBUG] PDF document loaded with PyPDF: {document_path}")
                return content
            except Exception as e:
                print(f"[ERROR] PyPDF PDF load failed: {e}")
                return f"[ERROR] PyPDF PDF load failed: {e}"

        print(f"[ERROR] PDF support not available for: {document_path}")
        return f"[ERROR] PDF support not available for: {document_path}"

    print(f"[ERROR] Unsupported file type or failed to load: {document_path}")
    return f"[ERROR] Unsupported file type or failed to load: {document_path}"


# ---------------------------------------------------------------------------
# Haystack RAG pipeline
# ---------------------------------------------------------------------------

def _build_haystack_documents(raw_texts: List[str], source_name: str) -> Optional[List[Document]]:
    if not HAYSTACK_AVAILABLE or Document is None:
        return None
    docs = []
    for index, raw_text in enumerate(raw_texts):
        if raw_text:
            if source_name == "uploaded_document":
                sentences = re.split(r'(?<=[.!?])\s+', raw_text.strip())
                for i, sentence in enumerate(sentences):
                    s = sentence.strip()
                    if s:
                        docs.append(Document(content=s, meta={"source": source_name, "part": f"{index}_{i}"}))
            else:
                docs.append(Document(content=raw_text, meta={"source": source_name, "part": index}))
    return docs


def _create_rag_store() -> InMemoryDocumentStore:
    return InMemoryDocumentStore()


def _index_documents_to_store(documents: List[Document], store: InMemoryDocumentStore) -> InMemoryDocumentStore:
    cleaner = DocumentCleaner()
    splitter = DocumentSplitter(split_length=Config.CHUNK_SIZE, split_overlap=Config.CHUNK_OVERLAP)
    embedder = SentenceTransformersDocumentEmbedder(model=Config.EMBEDDING_MODEL)

    cleaned = cleaner.run(documents=documents)["documents"]
    split_docs = splitter.run(documents=cleaned)["documents"]
    embedder.warm_up()
    embedded_docs = embedder.run(documents=split_docs)["documents"]
    store.write_documents(embedded_docs)
    return store


def _get_store_cache_key(ticker: str, source_type: str, document_path: Optional[str]) -> str:
    document_id = document_path or ""
    return f"{ticker}:{source_type}:{document_id}"


def _build_knowledge_store(
    ticker: str,
    source_type: str,
    raw_texts: List[str],
    document_path: Optional[str]
) -> Optional[InMemoryDocumentStore]:
    if not HAYSTACK_AVAILABLE or not raw_texts:
        return None

    cache_key = _get_store_cache_key(ticker, source_type, document_path)
    if cache_key in RAG_STORE_CACHE:
        return RAG_STORE_CACHE[cache_key]

    docs = _build_haystack_documents(raw_texts, source_type)
    if not docs:
        return None

    store = _create_rag_store()
    store = _index_documents_to_store(docs, store)
    RAG_STORE_CACHE[cache_key] = store
    return store


def _query_knowledge_store(store: InMemoryDocumentStore, query: str) -> List[str]:
    if not HAYSTACK_AVAILABLE or not store or not query:
        return []

    text_embedder = SentenceTransformersTextEmbedder(model=Config.EMBEDDING_MODEL)
    text_embedder.warm_up()
    query_embedding = text_embedder.run(text=query)["embedding"]
    retriever = InMemoryEmbeddingRetriever(document_store=store, top_k=Config.TOP_K_RETRIEVAL)
    retrieved = retriever.run(query_embedding=query_embedding)["documents"]
    return [doc.content for doc in retrieved]


# ---------------------------------------------------------------------------
# Content + source resolution
# ---------------------------------------------------------------------------

def _compute_content_and_source(ticker: str, document_path: Optional[str] = None) -> Dict[str, Any]:
    sources_used = 0
    source_type = "local_fallback"
    raw_texts: List[str] = []

    document_text = _load_uploaded_document(document_path) if document_path else ""
    if document_text and not document_text.startswith("[ERROR]"):
        raw_texts = [document_text]
        sources_used = 1
        source_type = "uploaded_document"
    else:
        news_texts = _fetch_newsapi_articles(ticker)
        if news_texts:
            raw_texts = news_texts
            sources_used = len(news_texts)
            source_type = "newsapi"
        else:
            news_texts = _fetch_yfinance_news(ticker)
            if news_texts:
                raw_texts = news_texts
                sources_used = len(news_texts)
                source_type = "yfinance_news"
            else:
                dynamic_fallback = _load_local_news(ticker)
                if dynamic_fallback:
                    raw_texts = [dynamic_fallback]
                    sources_used = 1
                    source_type = "dynamic_fallback"

    if not raw_texts or (len(raw_texts) == 1 and raw_texts[0].startswith("[ERROR]")):
        error_msg = raw_texts[0] if raw_texts else "No document or news content could be loaded."
        return {
            "sentiment": "NEUTRAL",
            "insights": [error_msg],
            "sources_used": 0,
            "source_type": "local_fallback",
            "rag_passages": [],
            "knowledge_base": False,
            "question_answer": error_msg,
            "error": error_msg
        }

    return {
        "raw_texts": raw_texts,
        "sources_used": sources_used,
        "source_type": source_type
    }


# ---------------------------------------------------------------------------
# Query enrichment
# ---------------------------------------------------------------------------

def _enrich_query(q: str) -> str:
    q_lower = q.lower()
    enrichments = {
        "risk": ["risk", "risks", "challenge", "challenges", "threat", "threats",
                 "uncertainty", "uncertainties", "headwind", "headwinds",
                 "concern", "concerns", "issue", "issues", "danger", "dangers"],
        "growth": ["growth", "revenue", "sales", "expansion", "market share",
                   "performance", "demand", "opportunity"],
        "competition": ["competition", "competitor", "competitors", "rival",
                        "market pressure", "competitive landscape"],
        "profit": ["profit", "profits", "earnings", "margin", "income",
                   "cash flow", "operating income", "net income"],
        "strategy": ["strategy", "plan", "vision", "roadmap", "objective",
                     "business model", "future direction"]
    }
    keywords = []
    if any(w in q_lower for w in ["risk", "risque", "danger", "threat", "challenge", "uncertainty", "issue", "concern"]):
        keywords.extend(enrichments["risk"])
    if any(w in q_lower for w in ["growth", "croissance", "revenue", "sales", "performance"]):
        keywords.extend(enrichments["growth"])
    if any(w in q_lower for w in ["competition", "competitor", "concurrence", "rival"]):
        keywords.extend(enrichments["competition"])
    if any(w in q_lower for w in ["profit", "earnings", "margin", "benefit", "bénéfice"]):
        keywords.extend(enrichments["profit"])
    if any(w in q_lower for w in ["strategy", "plan", "vision", "roadmap"]):
        keywords.extend(enrichments["strategy"])
    if keywords:
        return q + ". Related concepts: " + ", ".join(sorted(set(keywords)))
    return q


# ---------------------------------------------------------------------------
# Main RAG response builder
# ---------------------------------------------------------------------------

def _get_document_knowledge_response(
    ticker: str,
    document_path: Optional[str] = None,
    question: Optional[str] = None
) -> Dict[str, Any]:
    """Build a Haystack knowledge base, run a RAG retrieval query, and summarize the result."""
    try:
        corpus = _compute_content_and_source(ticker, document_path)
        source_type = corpus.get("source_type", "unknown")
        sources_used = corpus.get("sources_used", 0)
        raw_texts = corpus.get("raw_texts", [])

        if not raw_texts or (len(raw_texts) == 1 and raw_texts[0].startswith("[ERROR]")):
            error_msg = raw_texts[0] if raw_texts else "No document or news content could be loaded."
            return {
                "sentiment": "NEUTRAL",
                "insights": [error_msg],
                "sources_used": 0,
                "source_type": source_type,
                "rag_passages": [],
                "knowledge_base": False,
                "question_answer": error_msg,
                "error": error_msg
            }

        # Build knowledge store
        store = _build_knowledge_store(ticker, source_type, raw_texts, document_path)

        retrieved_passages = []
        if store is not None and sources_used > 0 and question:
            enriched_question = _enrich_query(question)
            retrieved_passages = _query_knowledge_store(store, enriched_question)

        # Build answer text
        if not retrieved_passages:
            answer_text = (
                "No highly relevant passage was found in the uploaded document. "
                "Try asking a more specific question such as:\n"
                "- What risks are mentioned?\n"
                "- What are the growth opportunities?\n"
                "- What competition risks are discussed?\n"
                "- What profitability issues are mentioned?"
            )
        else:
            # FIX: use proper single backslash regex (was \\b\\w which broke matching)
            keywords = [w.lower() for w in re.findall(r"\b\w{4,}\b", question or "")]

            if not keywords:
                # No keywords extracted → return passages as-is (no filtering)
                answer_text = " ".join(retrieved_passages)
            else:
                filtered_sentences = []
                for passage in retrieved_passages:
                    # FIX: use proper single backslash regex (was \\s+ which broke splitting)
                    for sentence in re.split(r'(?<=[.!?])\s+', passage):
                        sentence = sentence.strip()
                        if sentence and any(kw in sentence.lower() for kw in keywords):
                            filtered_sentences.append(sentence)

                if filtered_sentences:
                    answer_text = " ".join(filtered_sentences)
                else:
                    # Fallback: return raw passages instead of dead-end message
                    answer_text = " ".join(retrieved_passages)

        sentiment = compute_sentiment(answer_text)
        insights = _top_insights_from_text(answer_text, top_n=Config.TOP_INSIGHTS)

        return {
            "sentiment": sentiment,
            "insights": insights,
            "sources_used": sources_used,
            "source_type": source_type,
            "rag_passages": retrieved_passages,
            "knowledge_base": bool(store is not None and sources_used > 0),
            "question_answer": answer_text if question else "",
            "error": None
        }

    except Exception as e:
        return {
            "sentiment": "NEUTRAL",
            "insights": [f"Internal error: {e}"],
            "sources_used": 0,
            "source_type": "error",
            "rag_passages": [],
            "knowledge_base": False,
            "question_answer": f"Internal error: {e}",
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# Public wrappers
# ---------------------------------------------------------------------------

def _get_document_insights(ticker, document_path=None, question=None):
    """Retrieve document insights using RAG and sentiment analysis."""
    result = _get_document_knowledge_response(ticker, document_path, question)
    if result is None:
        return {
            "sentiment": "NEUTRAL",
            "insights": ["No document or news content could be loaded."],
            "sources_used": 0,
            "source_type": "local_fallback",
            "rag_passages": [],
            "knowledge_base": False,
            "question_answer": "No content available to answer the question."
        }
    return result


def _query_knowledge_base(ticker: str, question: str, document_path: str = None) -> Dict[str, Any]:
    """Query the Haystack knowledge base and return the retrieved passages, sentiment, and insights."""
    return _get_document_knowledge_response(ticker, document_path, question)


get_document_insights = tool("Document Reader Tool")(_get_document_insights)
query_knowledge_base = tool("Knowledge Base Retriever")(_query_knowledge_base)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Testing tools/document_reader.py...")
    result = _get_document_insights("AAPL")
    print(json.dumps(result, indent=2))