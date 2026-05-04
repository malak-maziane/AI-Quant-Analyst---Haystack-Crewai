from crewai.tools import tool
import os
from pathlib import Path

try:
    from haystack import Pipeline
    from haystack.document_stores.in_memory import InMemoryDocumentStore
    from haystack.components.converters import PyPDFToDocument
    from haystack.components.preprocessors import DocumentSplitter
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
    from haystack.components.writers import DocumentWriter
    from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
    from haystack.components.builders import PromptBuilder
    from haystack.components.generators import OpenAIGenerator
except ImportError:
    pass

# Global Document Store - using Chroma for persistence
try:
    from haystack.document_stores import ChromaDocumentStore
    document_store = ChromaDocumentStore(
        collection_name="financial_docs",
        persist_dir="./chroma_db"
    )
except ImportError:
    # Fallback to InMemory if Chroma not available
    document_store = InMemoryDocumentStore()

# Global embedder instance for performance
EMBEDDER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
text_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL)

def index_pdf_to_store(file_path: str):
    """
    Reads a PDF, extracts text, chunks it, embeds it, and stores it in the vector DB.
    """
    if not os.path.exists(file_path):
        print(f"Error: PDF file not found at {file_path}")
        return False

    print(f"Indexing PDF {file_path} into Haystack Vector Database...")

    indexing_pipeline = Pipeline()

    # 1. Convert PDF to Document
    indexing_pipeline.add_component("converter", PyPDFToDocument())

    # 2. Split Document into smaller chunks with overlap
    indexing_pipeline.add_component("splitter", DocumentSplitter(split_by="word", split_length=200, split_overlap=50))

    # 3. Embed the chunks
    indexing_pipeline.add_component("embedder", SentenceTransformersDocumentEmbedder(model=EMBEDDER_MODEL))

    # 4. Write to Document Store
    indexing_pipeline.add_component("writer", DocumentWriter(document_store=document_store))

    # Connect the components
    indexing_pipeline.connect("converter", "splitter")
    indexing_pipeline.connect("splitter", "embedder")
    indexing_pipeline.connect("embedder", "writer")

    # Run the pipeline
    indexing_pipeline.run({"converter": {"sources": [Path(file_path)]}})
    print(f"Indexing complete! {document_store.count_documents()} chunks added.")
    return True

def index_pdf_to_store(file_path: str):
    """
    Reads a PDF, extracts text, chunks it, embeds it, and stores it in the vector DB.
    """
    if not os.path.exists(file_path):
        print(f"Error: PDF file not found at {file_path}")
        return False

    print(f"Indexing PDF {file_path} into Haystack Vector Database...")

    indexing_pipeline = Pipeline()
    
    # 1. Convert PDF to Document
    indexing_pipeline.add_component("converter", PyPDFToDocument())
    
    # 2. Split Document into smaller chunks
    indexing_pipeline.add_component("splitter", DocumentSplitter(split_by="word", split_length=200, split_overlap=20))
    
    # 3. Embed the chunks
    indexing_pipeline.add_component("embedder", SentenceTransformersDocumentEmbedder(model=EMBEDDER_MODEL))
    
    # 4. Write to Document Store
    indexing_pipeline.add_component("writer", DocumentWriter(document_store=document_store))
    
    # Connect the components
    indexing_pipeline.connect("converter", "splitter")
    indexing_pipeline.connect("splitter", "embedder")
    indexing_pipeline.connect("embedder", "writer")
    
    # Run the pipeline
    indexing_pipeline.run({"converter": {"sources": [Path(file_path)]}})
    print(f"Indexing complete! {document_store.count_documents()} chunks added.")
    return True


@tool("Financial Knowledge Base RAG Query Tool")
def query_financial_knowledge_base(query: str) -> str:
    """
    Queries the indexed financial documents using semantic search (RAG) to find insights.
    Provide a clear, detailed question as the query, for example: 'What was the revenue growth?' or 'What are the risks mentioned?'
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if document_store.count_documents() == 0:
        return "No explicit data found in documents regarding: " + query

    try:
        query_pipeline = Pipeline()

        # Use global embedder instance
        query_pipeline.add_component("text_embedder", text_embedder)

        # 2. Retrieve relevant chunks from DB
        if hasattr(document_store, 'collection_name'):  # Chroma
            from haystack.components.retrievers import ChromaEmbeddingRetriever
            query_pipeline.add_component("retriever", ChromaEmbeddingRetriever(document_store=document_store, top_k=5))
        else:  # InMemory
            query_pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=document_store, top_k=5))

        # 3. Create prompt with strict fallback control
        template = """
        You are a financial RAG agent. You must answer based ONLY on the Context below.
        Context:
        {% for document in documents %}
            - {{ document.content }}
        {% empty %}
            NO CONTEXT FOUND.
        {% endfor %}

        Question: {{ question }}
        Answer: If NO CONTEXT FOUND, simply reply "No explicit data found in documents regarding: {{ question }}." Do NOT invent metrics.
        """
        query_pipeline.add_component("prompt_builder", PromptBuilder(template=template))

        # 4. Generate answer
        query_pipeline.add_component("llm", OpenAIGenerator())

        # Connect pipelines
        query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        query_pipeline.connect("retriever", "prompt_builder.documents")
        query_pipeline.connect("prompt_builder", "llm")

        # Run
        result = query_pipeline.run({
            "text_embedder": {"text": query},
            "prompt_builder": {"question": query}
        })

        return result["llm"]["replies"][0]

    except Exception as e:
        return f"Error during RAG Query: {str(e)}"
        query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        query_pipeline.connect("retriever", "prompt_builder.documents")
        query_pipeline.connect("prompt_builder", "llm")
        
        # Run
        result = query_pipeline.run({
            "text_embedder": {"text": query},
            "prompt_builder": {"question": query}
        })
        
        return result["llm"]["replies"][0]
        
    except Exception as e:
        return f"Error during RAG Query: {str(e)}"
