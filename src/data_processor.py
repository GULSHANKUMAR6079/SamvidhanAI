"""
Data Processor for Constitution of India
Extracts text from PDF, parses structure, and creates chunks with metadata.
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import DataConfig, ChunkingConfig, logger

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    logger.error("Required libraries not installed. Run: pip install PyPDF2 pdfplumber")
    sys.exit(1)


class ConstitutionProcessor:
    """
    Processes Constitution PDF and extracts structured data.
    """
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.raw_text = ""
        self.articles = []
        self.parts = {}
        self.schedules = {}
        
    def extract_text_from_pdf(self) -> str:
        """
        Extract text from PDF using pdfplumber (better formatting preservation).
        """
        logger.info(f"📖 Extracting text from: {self.pdf_path}")
        
        full_text = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"📄 Processing {total_pages} pages...")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                    
                    if page_num % 20 == 0:
                        logger.info(f"   Processed {page_num}/{total_pages} pages...")
                
                self.raw_text = "\n\n".join(full_text)
                logger.info(f"✅ Extracted {len(self.raw_text)} characters")
                
                return self.raw_text
                
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            logger.info("Trying fallback method (PyPDF2)...")
            
            # Fallback to PyPDF2
            try:
                with open(self.pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            full_text.append(text)
                
                self.raw_text = "\n\n".join(full_text)
                logger.info(f"✅ Extracted {len(self.raw_text)} characters (fallback)")
                return self.raw_text
                
            except Exception as e2:
                logger.error(f"❌ Both extraction methods failed: {e2}")
                raise
    
    def parse_constitutional_structure(self) -> Dict[str, Any]:
        """
        Parse Constitution structure: Parts, Articles, Schedules.
        """
        logger.info("🔍 Parsing constitutional structure...")
        
        # Regex patterns for structure
        part_pattern = r'PART\s+([IVX]+)\s*[-–—]\s*(.+?)(?=\n|$)'
        article_pattern = r'(\d+[A-Z]?)\.\s*(.+?)(?=\n\d+[A-Z]?\.|$)'
        schedule_pattern = r'(THE\s+)?([A-Z]+)\s+SCHEDULE'
        
        # Extract Parts
        parts = re.findall(part_pattern, self.raw_text, re.MULTILINE | re.IGNORECASE)
        for part_num, part_title in parts:
            self.parts[part_num] = part_title.strip()
        
        logger.info(f"   Found {len(self.parts)} Parts")
        
        # Extract Articles (simplified - full implementation would be more complex)
        # This is a basic extraction; real implementation needs context-aware parsing
        articles_rough = re.findall(article_pattern, self.raw_text[:100000], re.DOTALL)
        logger.info(f"   Found ~{len(articles_rough)} article-like patterns")
        
        # Extract Schedules
        schedules = re.findall(schedule_pattern, self.raw_text, re.IGNORECASE)
        logger.info(f"   Found {len(schedules)} Schedules")
        
        return {
            "parts": self.parts,
            "articles_count": len(articles_rough),
            "schedules_count": len(schedules)
        }
    
    def create_chunks_with_metadata(self) -> List[Dict[str, Any]]:
        """
        Create document chunks with rich metadata.
        
        Strategy: Split by major sections (Parts/Articles) rather than arbitrary chunks.
        Each chunk gets metadata: article_number, part, title, type.
        """
        logger.info("✂️ Creating chunks with metadata...")
        
        chunks = []
        
        # For MVP, we'll create smart chunks based on sections
        # Pattern: Split on "PART" and "Article" headings
        
        # Split into major sections
        sections = re.split(r'\n(?=PART\s+[IVX]+)', self.raw_text)
        
        current_part = "Preamble"
        current_part_num = "0"
        
        for section_idx, section in enumerate(sections):
            if not section.strip():
                continue
            
            # Check if this is a PART heading
            part_match = re.match(r'PART\s+([IVX]+)\s*[-–—]\s*(.+)', section, re.IGNORECASE)
            if part_match:
                current_part_num = part_match.group(1)
                current_part = f"Part {current_part_num} - {part_match.group(2).strip()}"
            
            # Split section into article-sized chunks
            # Use a sliding window approach
            words = section.split()
            chunk_size_words = ChunkingConfig.CHUNK_SIZE // 5  # Approximate words
            overlap_words = ChunkingConfig.CHUNK_OVERLAP // 5
            
            for i in range(0, len(words), chunk_size_words - overlap_words):
                chunk_words = words[i:i + chunk_size_words]
                chunk_text = " ".join(chunk_words)
                
                if len(chunk_text.strip()) < 100:  # Skip tiny chunks
                    continue
                
                # Try to extract article number from chunk
                article_match = re.search(r'\b(\d+[A-Z]?)\.\s+', chunk_text)
                article_num = article_match.group(1) if article_match else "Unknown"
                
                # Extract title (first sentence or heading)
                title_match = re.search(r'^\s*(.{10,100}?)[.:\n]', chunk_text)
                title = title_match.group(1).strip() if title_match else chunk_text[:50]
                
                # Determine type
                if "SCHEDULE" in chunk_text.upper()[:100]:
                    doc_type = "schedule"
                elif "PART" in chunk_text.upper()[:50]:
                    doc_type = "part_heading"
                else:
                    doc_type = "article"
                
                chunk_metadata = {
                    "text": chunk_text.strip(),
                    "metadata": {
                        "article_number": article_num,
                        "part": current_part,
                        "part_number": current_part_num,
                        "title": title,
                        "type": doc_type,
                        "chunk_index": len(chunks),
                        "source": "Constitution of India"
                    }
                }
                
                chunks.append(chunk_metadata)
        
        logger.info(f"✅ Created {len(chunks)} chunks with metadata")
        
        # Show sample
        if chunks:
            logger.info(f"   Sample chunk metadata: {chunks[0]['metadata']}")
        
        return chunks
    
    def validate_extraction(self, chunks: List[Dict]) -> bool:
        """
        Validate that extraction is reasonable.
        """
        logger.info("🔍 Validating extraction quality...")
        
        checks = {
            "total_chunks": len(chunks) > 50,  # Should have many chunks
            "has_parts": len(self.parts) >= 10,  # Constitution has many parts
            "text_length": len(self.raw_text) > 100000,  # Substantial text
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {check}: {passed}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            logger.info("✅ Validation passed!")
        else:
            logger.warning("⚠️ Some validation checks failed")
        
        return all_passed
    
    def save_processed_data(self, chunks: List[Dict]):
        """
        Save processed chunks and metadata to disk.
        """
        logger.info("💾 Saving processed data...")
        
        # Save chunks
        chunks_path = DataConfig.PROCESSED_CHUNKS_PATH
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"   Saved {len(chunks)} chunks to: {chunks_path}")
        
        # Save metadata index
        metadata_index = {
            "parts": self.parts,
            "total_chunks": len(chunks),
            "processing_date": str(Path(__file__).stat().st_mtime)
        }
        
        metadata_path = DataConfig.METADATA_INDEX_PATH
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_index, f, indent=2)
        
        logger.info(f"   Saved metadata index to: {metadata_path}")
    
    def process(self):
        """
        Full processing pipeline.
        """
        logger.info("=" * 50)
        logger.info("🏛️ Constitution Processing Pipeline")
        logger.info("=" * 50)
        
        # Step 1: Extract text
        self.extract_text_from_pdf()
        
        # Step 2: Parse structure
        structure = self.parse_constitutional_structure()
        logger.info(f"📊 Structure: {structure}")
        
        # Step 3: Create chunks
        chunks = self.create_chunks_with_metadata()
        
        # Step 4: Validate
        self.validate_extraction(chunks)
        
        # Step 5: Save
        self.save_processed_data(chunks)
        
        logger.info("=" * 50)
        logger.info("✅ Processing complete!")
        logger.info("=" * 50)
        
        return chunks


def main():
    """Main execution"""
    pdf_path = DataConfig.CONSTITUTION_PDF_PATH
    
    if not pdf_path.exists():
        logger.error(f"❌ Constitution PDF not found at: {pdf_path}")
        logger.info("💡 Run: python scripts/download_constitution.py")
        sys.exit(1)
    
    processor = ConstitutionProcessor(pdf_path)
    chunks = processor.process()
    
    logger.info(f"📦 Total chunks created: {len(chunks)}")


if __name__ == "__main__":
    main()
