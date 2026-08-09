"""Local Retrieval-Augmented Generation (RAG) Store using ChromaDB."""
import chromadb
from chromadb.config import Settings
import random
from typing import Any
import uuid

# In-memory ChromaDB client for demonstration
client = chromadb.Client(Settings(is_persistent=False))

# We use the default embedding function (all-MiniLM-L6-v2) under the hood
try:
    collection = client.get_or_create_collection(name="geopolitics_news")
except Exception:
    collection = client.create_collection(name="geopolitics_news")

# Mock Fact Database to populate the RAG
MOCK_FACTS = [
    {"topic": "inflation", "text": "Global supply chain bottlenecks have eased, but service sector inflation remains stubbornly high across G7 nations."},
    {"topic": "inflation", "text": "Central banks indicate that rate cuts may be delayed until Q3 due to persistent core inflation data."},
    {"topic": "ukraine_war", "text": "NATO allies have pledged an additional $50 billion in military aid packages over the next year."},
    {"topic": "ukraine_war", "text": "Frontline stalemates continue as both sides heavily utilize drone warfare and electronic countermeasures."},
    {"topic": "interest_rates", "text": "The Federal Reserve's dot plot suggests fewer rate cuts than the market originally anticipated."},
    {"topic": "us_china", "text": "Bilateral trade talks resumed in Geneva, but tariffs on advanced semiconductors remain a major sticking point."},
    {"topic": "donald_trump", "text": "Recent polling aggregates show a tightening race in key battleground states amidst ongoing legal proceedings."},
]

def initialize_rag_store():
    """Populate the ChromaDB collection with mock factual data."""
    if collection.count() == 0:
        docs = []
        metas = []
        ids = []
        for i, fact in enumerate(MOCK_FACTS):
            docs.append(fact["text"])
            metas.append({"topic": fact["topic"], "source": "Reuters", "date": "2024-10-15"})
            ids.append(f"doc_{i}")
        
        collection.add(
            documents=docs,
            metadatas=metas,
            ids=ids
        )

# Initialize on import
try:
    initialize_rag_store()
except Exception:
    pass

def retrieve_context(query: str, n_results: int = 2) -> list[dict[str, Any]]:
    """Query the ChromaDB vector store for relevant contextual facts."""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        retrieved = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            for d, m in zip(docs, metas):
                retrieved.append({
                    "text": d,
                    "metadata": m
                })
        return retrieved
    except Exception as e:
        print(f"RAG Retrieval error: {e}")
        return []
