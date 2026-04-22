#!/usr/bin/env python3
"""
End-to-End Test Scenario for RAG System
Tests the complete RAG pipeline: ingest → retrieve → generate
"""
import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.rag_pipeline import get_rag_pipeline
from app.utils.document_processor import DocumentProcessor
from app.utils.embedding import get_embedding_manager
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestScenario:
    """End-to-end test scenario for RAG system."""

    def __init__(self):
        """Initialize test scenario."""
        self.qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_admin_key,
            https=False,
            timeout=30,
        )
        self.embedding_manager = get_embedding_manager()
        self.processor = DocumentProcessor()
        self.rag_pipeline = get_rag_pipeline()
        self.test_results = []

    def setup_test_collection(self):
        """Create test collection with sample data."""
        logger.info("=" * 80)
        logger.info("STEP 1: Setup Test Collection")
        logger.info("=" * 80)
        
        try:
            # Check collection
            collections = self.qdrant_client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if settings.qdrant_collection_name not in existing:
                logger.info(f"Creating collection: {settings.qdrant_collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=settings.qdrant_collection_name,
                    vectors_config=VectorParams(
                        size=settings.qdrant_vector_size,
                        distance=Distance.COSINE,
                    ),
                )
            
            logger.info(f"✓ Collection ready: {settings.qdrant_collection_name}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to setup collection: {str(e)}")
            return False

    def ingest_test_documents(self):
        """Ingest test documents."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Ingest Sample Documents")
        logger.info("=" * 80)
        
        # Sample documents for testing
        test_docs = {
            "machine_learning": {
                "title": "Machine Learning Basics",
                "content": """
Machine Learning is a subset of Artificial Intelligence that enables systems to learn and improve 
from experience without being explicitly programmed.

Key Concepts:
1. Supervised Learning: Learning from labeled data
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Reinforcement Learning: Learning through rewards and penalties

Common Algorithms:
- Decision Trees: Used for classification and regression
- Random Forests: Ensemble method combining multiple trees
- Support Vector Machines: Powerful for binary classification
- Neural Networks: Inspired by biological neurons

Applications:
- Image Recognition: Identifying objects in images
- Natural Language Processing: Understanding human language
- Recommendation Systems: Personalizing user experiences
- Anomaly Detection: Finding unusual patterns
"""
            },
            "vector_databases": {
                "title": "Vector Databases Guide",
                "content": """
Vector databases are specialized data stores optimized for storing and querying high-dimensional 
vectors, particularly embeddings from machine learning models.

Why Vector Databases?
- Enable semantic search across large document collections
- Support similarity-based queries (nearest neighbor search)
- Handle high-dimensional data efficiently
- Provide real-time retrieval of relevant information

Qdrant Features:
- Fast vector search using HNSW algorithm
- Support for various distance metrics (Cosine, Euclidean, Dot)
- Built-in payload filtering
- Snapshot backup and recovery
- REST and gRPC APIs

Use Cases:
- Semantic search: Find documents by meaning, not just keywords
- Recommendation systems: Find similar users or products
- Image search: Find visually similar images
- RAG systems: Retrieve relevant documents for LLM context
"""
            },
            "rag_systems": {
                "title": "Retrieval-Augmented Generation (RAG)",
                "content": """
RAG (Retrieval-Augmented Generation) is a technique that combines document retrieval with 
generative AI to provide more accurate and contextual responses.

How RAG Works:
1. User Query: User asks a question
2. Embedding: Convert query to vector representation
3. Retrieval: Search vector database for similar documents
4. Context Building: Create context from retrieved documents
5. Generation: Feed context to LLM for answer generation
6. Response: Return generated answer with source references

Benefits:
- Reduces hallucination: LLM responses are grounded in real documents
- Up-to-date information: Easily add new documents without retraining
- Transparent sources: Know which documents influenced the answer
- Cost-effective: Smaller models can work with proper context

RAG Pipeline Components:
- Embedding Model: Converts text to vectors (e.g., Mistral Embed, nomic-embed-text)
- Vector Database: Stores and retrieves embeddings (e.g., Qdrant)
- Retriever: Finds relevant documents based on query
- LLM: Generates answers using retrieved context
- Chunker: Splits documents into manageable pieces
"""
            },
            "azure_fundamentals": {
                "title": "Azure Cloud Fundamentals",
                "content": """
Microsoft Azure is a cloud computing platform offering infrastructure and services for 
building and deploying applications.

Core Azure Services:
1. Compute Services:
   - Virtual Machines: On-demand computing resources
   - App Service: Host web apps and APIs
   - Azure Container Instances: Run containers without managing VMs

2. Storage Services:
   - Blob Storage: Unstructured data storage
   - File Storage: Cloud file shares
   - Table Storage: NoSQL data store

3. Database Services:
   - SQL Database: Managed relational database
   - Cosmos DB: Globally distributed database
   - Azure Cache: In-memory data store

AI & Machine Learning Services:
- Azure OpenAI Service: Access to GPT models
- Azure Cognitive Services: Pre-built AI services
- Machine Learning: Build custom ML models
- Bot Service: Create intelligent bots

Benefits:
- Global infrastructure with multiple regions
- Integrated security and compliance
- Hybrid cloud capabilities
- Enterprise-grade SLA guarantees
"""
            }
        }
        
        total_chunks = 0
        for doc_id, doc_info in test_docs.items():
            try:
                content = doc_info["content"]
                title = doc_info["title"]
                
                # Split into chunks
                chunks = self.processor.split_text(
                    content,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                )
                
                logger.info(f"Processing: {title} ({len(chunks)} chunks)")
                
                # Embed chunks
                embeddings = self.embedding_manager.embed_documents(chunks)
                
                # Create Qdrant points
                points = []
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    point_id = abs(hash(f"{doc_id}-{i}")) % (2**31)
                    points.append(PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk,
                            "source": title,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                        }
                    ))
                
                # Upsert to Qdrant
                self.qdrant_client.upsert(
                    collection_name=settings.qdrant_collection_name,
                    points=points,
                )
                
                total_chunks += len(chunks)
                logger.info(f"✓ Ingested '{title}' - {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"✗ Failed to ingest {doc_id}: {str(e)}")
        
        logger.info(f"\n✓ Total chunks ingested: {total_chunks}")
        return total_chunks > 0

    def test_queries(self):
        """Test the RAG pipeline with various queries."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Test RAG Queries")
        logger.info("=" * 80)
        
        test_queries = [
            "What is machine learning?",
            "How does Qdrant store vectors?",
            "Explain how RAG systems work",
            "What are the benefits of Azure?",
            "What is a vector database used for?",
        ]
        
        results = []
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n📝 Query {i}: {query}")
            logger.info("-" * 80)
            
            try:
                start_time = time.time()
                response = self.rag_pipeline.query(
                    user_query=query,
                    top_k=3,
                    include_sources=True,
                )
                elapsed = time.time() - start_time
                
                logger.info(f"⏱️  Time: {elapsed:.2f}s")
                logger.info(f"📊 Tokens: {response['tokens_used']}")
                logger.info(f"📚 Sources: {len(response['sources'])}")
                logger.info(f"\n💬 Answer: {response['answer'][:300]}...")
                
                logger.info(f"\n📖 Sources:")
                for j, source in enumerate(response['sources'], 1):
                    logger.info(f"   {j}. [{source['source']}] Score: {source['score']:.3f}")
                
                results.append({
                    "query": query,
                    "success": True,
                    "time_ms": elapsed * 1000,
                    "tokens_used": response['tokens_used'],
                    "sources_count": len(response['sources']),
                })
                
            except Exception as e:
                logger.error(f"✗ Query failed: {str(e)}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                })
        
        self.test_results.extend(results)
        return results

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        successful = sum(1 for r in self.test_results if r.get("success", False))
        total = len(self.test_results)
        
        logger.info(f"\nQueries Tested: {successful}/{total} successful")
        
        if total > 0:
            avg_time = sum(r.get("time_ms", 0) for r in self.test_results if r.get("success")) / max(successful, 1)
            total_tokens = sum(r.get("tokens_used", 0) for r in self.test_results if r.get("success"))
            
            logger.info(f"Average Query Time: {avg_time:.1f}ms")
            logger.info(f"Total Tokens Used: {total_tokens}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ RAG System Test Complete!")
        logger.info("=" * 80)
        
        return {
            "total_tests": total,
            "successful": successful,
            "configuration": {
                "llm_provider": settings.llm_provider,
                "embedding_provider": settings.embedding_provider,
            }
        }


def main():
    """Run the end-to-end test scenario."""
    logger.info("\n" + "🚀 " * 20)
    logger.info("RAG SYSTEM END-TO-END TEST")
    logger.info("🚀 " * 20)
    
    scenario = TestScenario()
    
    # Step 1: Setup
    if not scenario.setup_test_collection():
        return
    
    # Step 2: Ingest
    if not scenario.ingest_test_documents():
        logger.error("Failed to ingest test documents")
        return
    
    # Step 3: Test
    scenario.test_queries()
    
    # Summary
    summary = scenario.print_summary()
    
    # Save results
    results_file = Path(__file__).parent / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(scenario.test_results, f, indent=2)
    logger.info(f"\n📄 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
