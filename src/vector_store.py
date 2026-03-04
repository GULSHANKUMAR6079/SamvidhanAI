"""
Vector Store Management with ChromaDB
Handles document ingestion, embedding, and retrieval.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import (
    VectorDBConfig, 
    RetrievalConfig, 
    ModelConfig,
    DataConfig,
    GOOGLE_API_KEY,
    logger
)

try:
    import chromadb
    from chromadb.config import Settings
    from langchain_community.vectorstores import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_core.documents import Document
except ImportError as e:
    logger.error(f"Required libraries not installed: {e}")
    logger.error("Run: pip install chromadb langchain langchain-google-genai langchain-core")
    sys.exit(1)


class ConstitutionVectorStore:
    """
    Manages ChromaDB vector store for Constitution documents.
    """
    
    def __init__(self):
        self.collection_name = VectorDBConfig.COLLECTION_NAME
        self.persist_directory = VectorDBConfig.PERSIST_DIRECTORY
        self.embeddings = None
        self.vectorstore = None
        
        logger.info(f"🗄️ Initializing Vector Store: {self.collection_name}")
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize Gemini embeddings."""
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=ModelConfig.EMBEDDING_MODEL,
                google_api_key=GOOGLE_API_KEY
            )
            logger.info(f"✅ Embeddings initialized: {ModelConfig.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise
    
    def initialize_chromadb(self) -> bool:
        """
        Initialize ChromaDB with persistence.
        """
        try:
            logger.info(f"📦 Initializing ChromaDB at: {self.persist_directory}")
            
            # Create persistent client
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info("✅ ChromaDB initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            return False
    
    def load_processed_chunks(self) -> List[Dict[str, Any]]:
        """
        Load processed chunks from JSON file.
        """
        chunks_path = DataConfig.PROCESSED_CHUNKS_PATH
        
        if not chunks_path.exists():
            logger.error(f"❌ Processed chunks not found: {chunks_path}")
            logger.info("💡 Run: python src/data_processor.py")
            return []
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        logger.info(f"📂 Loaded {len(chunks)} chunks from: {chunks_path}")
        return chunks
    
    def ingest_documents(self, chunks: Optional[List[Dict]] = None) -> bool:
        """
        Ingest documents into ChromaDB with metadata.
        Includes rate limit handling for Gemini API.
        
        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'.
                   If None, loads from processed_chunks.json
        """
        import time
        
        if chunks is None:
            chunks = self.load_processed_chunks()
        
        if not chunks:
            logger.error("❌ No chunks to ingest")
            return False
        
        logger.info(f"📥 Ingesting {len(chunks)} documents into ChromaDB...")
        
        try:
            # Convert to LangChain Document format
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk['text'],
                    metadata=chunk['metadata']
                )
                documents.append(doc)
            
            # Batch processing for large datasets
            batch_size = 100
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"   Processing batch {batch_num}/{total_batches}...")
                
                # Retry logic for rate limits
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        # Add to vectorstore
                        self.vectorstore.add_documents(batch)
                        logger.info(f"   ✅ Batch {batch_num}/{total_batches} completed")
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        error_msg = str(e)
                        
                        # Check if it's a rate limit error
                        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                            wait_time = 60  # Wait 60 seconds for rate limit
                            
                            # Try to extract suggested wait time from error
                            if "retry in" in error_msg.lower():
                                import re
                                match = re.search(r'retry in (\d+\.?\d*)', error_msg.lower())
                                if match:
                                    wait_time = int(float(match.group(1))) + 5  # Add 5 sec buffer
                            
                            if retry < max_retries - 1:
                                logger.warning(f"   ⏳ Rate limit hit. Waiting {wait_time} seconds before retry {retry + 1}/{max_retries}...")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"   ❌ Rate limit persists after {max_retries} retries")
                                raise
                        else:
                            # Not a rate limit error, raise immediately
                            raise
                
                # Add delay between batches to avoid hitting rate limits
                # Free tier: 100 requests/minute, so ~1 batch/60 seconds
                if batch_num < total_batches:
                    delay = 65  # 65 seconds between batches for safety
                    logger.info(f"   ⏳ Waiting {delay}s before next batch (API rate limit: 100/min)...")
                    time.sleep(delay)
            
            # Persist
            logger.info("💾 Persisting to disk...")
            # Note: Chroma auto-persists with persist_directory
            
            logger.info(f"✅ Successfully ingested {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Document ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def hybrid_search(
        self, 
        query: str, 
        k: int = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """
        Hybrid search: semantic similarity + metadata filtering.
        
        Args:
            query: Search query
            k: Number of results (default from config)
            filter_metadata: Metadata filters, e.g. {"part_number": "III"}
        
        Returns:
            List of relevant Documents with metadata
        """
        if k is None:
            k = RetrievalConfig.TOP_K_RESULTS
        
        logger.info(f"🔍 Searching for: '{query}' (top-{k})")
        
        try:
            if filter_metadata:
                logger.info(f"   Applying filters: {filter_metadata}")
                results = self.vectorstore.similarity_search(
                    query, 
                    k=k,
                    filter=filter_metadata
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)
            
            logger.info(f"   Found {len(results)} results")
            
            # Log first result for debugging
            if results:
                first_result = results[0]
                logger.info(f"   Top result metadata: {first_result.metadata}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = None
    ) -> List[tuple]:
        """
        Search with similarity scores.
        
        Returns:
            List of (Document, score) tuples
        """
        if k is None:
            k = RetrievalConfig.TOP_K_RESULTS
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # Filter by threshold
            threshold = RetrievalConfig.SIMILARITY_THRESHOLD
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= threshold
            ]
            
            logger.info(
                f"🔍 Found {len(results)} results, "
                f"{len(filtered_results)} above threshold ({threshold})"
            )
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ Search with score failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        """
        try:
            # Access underlying ChromaDB collection
            collection = self.vectorstore._collection
            count = collection.count()
            
            stats = {
                "collection_name": self.collection_name,
                "total_documents": count,
                "persist_directory": self.persist_directory
            }
            
            logger.info(f"📊 Collection stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
    
    def delete_collection(self):
        """
        Delete the collection (for re-indexing).
        """
        logger.warning(f"⚠️ Deleting collection: {self.collection_name}")
        try:
            self.vectorstore.delete_collection()
            logger.info("✅ Collection deleted")
        except Exception as e:
            logger.error(f"❌ Deletion failed: {e}")


def main():
    """
    Main execution: Initialize and ingest documents.
    """
    logger.info("=" * 50)
    logger.info("🏛️ Constitution Vector Store Setup")
    logger.info("=" * 50)
    
    # Initialize
    vector_store = ConstitutionVectorStore()
    
    # Initialize ChromaDB
    if not vector_store.initialize_chromadb():
        logger.error("❌ Failed to initialize ChromaDB")
        sys.exit(1)
    
    # Check if already populated
    stats = vector_store.get_collection_stats()
    if stats.get('total_documents', 0) > 0:
        logger.info(f"✅ Collection already has {stats['total_documents']} documents")
        
        user_input = input("\nDo you want to re-ingest? This will clear existing data. (y/n): ").strip().lower()
        if user_input == 'y':
            vector_store.delete_collection()
            vector_store.initialize_chromadb()
        else:
            logger.info("Skipping ingestion.")
            return
    
    # Ingest documents
    success = vector_store.ingest_documents()
    
    if success:
        # Show stats
        final_stats = vector_store.get_collection_stats()
        logger.info("=" * 50)
        logger.info(f"✅ Vector store ready!")
        logger.info(f"   Total documents: {final_stats.get('total_documents', 0)}")
        logger.info("=" * 50)
        
        # Test search
        logger.info("\n🧪 Testing search...")
        results = vector_store.hybrid_search("What is Article 21?", k=3)
        
        if results:
            logger.info(f"✅ Search test passed! Found {len(results)} results")
            logger.info(f"   First result: {results[0].metadata}")
        else:
            logger.warning("⚠️ Search test returned no results")
    else:
        logger.error("❌ Ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
