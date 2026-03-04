"""
Resume ingestion from where it left off
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.vector_store import ConstitutionVectorStore
from config import logger
import json

def resume_ingestion():
    logger.info("=" * 50)
    logger.info("🔄 Resuming Vector Store Ingestion")
    logger.info("=" * 50)
    
    # Initialize
    vector_store = ConstitutionVectorStore()
    vector_store.initialize_chromadb()
    
    # Check current status
    stats = vector_store.get_collection_stats()
    current_count = stats.get('total_documents', 0)
    
    logger.info(f"📊 Currently have {current_count} documents")
    
    # Load all chunks
    chunks_path = Path("data/processed_chunks.json")
    with open(chunks_path, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)
    
    total_chunks = len(all_chunks)
    logger.info(f"📂 Total chunks in file: {total_chunks}")
    
    if current_count >= total_chunks:
        logger.info("✅ All documents already ingested!")
        return
    
    # Ingest remaining chunks
    remaining_chunks = all_chunks[current_count:]
    logger.info(f"📥 Ingesting remaining {len(remaining_chunks)} documents...")
    
    success = vector_store.ingest_documents(remaining_chunks)
    
    if success:
        final_stats = vector_store.get_collection_stats()
        logger.info("=" * 50)
        logger.info(f"✅ Ingestion complete!")
        logger.info(f"   Total documents: {final_stats.get('total_documents', 0)}")
        logger.info("=" * 50)
    else:
        logger.error("❌ Ingestion failed")

if __name__ == "__main__":
    resume_ingestion()
