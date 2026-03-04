"""
PDF Download Script for Constitution of India
Downloads the official Constitution PDF from Government of India sources.
"""

import os
import sys
import requests
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import DataConfig, logger


def download_constitution_pdf():
    """
    Downloads the Constitution of India PDF from official government source.
    """
    pdf_url = DataConfig.CONSTITUTION_PDF_URL
    output_path = DataConfig.CONSTITUTION_PDF_PATH
    
    logger.info(f"📥 Downloading Constitution PDF from: {pdf_url}")
    
    try:
        # Make request with timeout
        response = requests.get(pdf_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Get file size
        total_size = int(response.headers.get('content-length', 0))
        logger.info(f"📊 File size: {total_size / (1024*1024):.2f} MB")
        
        # Download with progress
        downloaded = 0
        chunk_size = 8192
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress indicator
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        logger.info(f"✅ Constitution PDF downloaded successfully to: {output_path}")
        
        # Validate file
        if output_path.exists() and output_path.stat().st_size > 1024:
            logger.info(f"✅ File validated: {output_path.stat().st_size / (1024*1024):.2f} MB")
            return True
        else:
            logger.error("❌ Downloaded file is invalid or too small")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        logger.info("Trying alternative sources...")
        
        # Try multiple alternative sources
        alternative_urls = [
            "https://drive.google.com/file/d/0B6CteV1FAWVGSFN6NWhCalJhdm8/view?resourcekey=0-TH-x9nrRXLR-ZzNhX6rs4Q",
            "https://cdnbbsr.s3waas.gov.in/s380537a945c7aaa788ccfcdf1b99b5d8f/uploads/2023/05/2023050112.pdf",
            "https://www.mea.gov.in/Images/pdf1/S3.pdf"
        ]
        
        for alt_url in alternative_urls:
            logger.info(f"Attempting download from: {alt_url}")
            
            try:
                response = requests.get(alt_url, timeout=60, stream=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'pdf' not in content_type.lower() and 'application' not in content_type.lower():
                    logger.warning(f"Not a PDF file (content-type: {content_type}), trying next...")
                    continue
                
                # Download
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Validate size
                file_size = output_path.stat().st_size
                if file_size > 1024 * 1024:  # Must be > 1 MB
                    logger.info(f"Downloaded from alternative source ({file_size / (1024*1024):.2f} MB)")
                    return True
                else:
                    logger.warning(f"Downloaded file too small ({file_size} bytes), trying next...")
                    
            except Exception as alt_error:
                logger.warning(f"Failed: {alt_error}, trying next source...")
                continue
        
        # All sources failed
        logger.error(
            "Manual Download Required:\n"
            "All automatic download sources failed.\n"
            "Please download Constitution PDF manually from:\n"
            "- https://legislative.gov.in/constitution-of-india/\n"
            f"Save it to: {output_path}"
        )
        return False


def verify_pdf_structure(pdf_path):
    """
    Verify the downloaded PDF can be opened and has content.
    """
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            
            logger.info(f"📄 PDF has {num_pages} pages")
            
            # Try to extract text from first page
            first_page_text = pdf_reader.pages[0].extract_text()
            
            if "CONSTITUTION" in first_page_text.upper():
                logger.info("✅ PDF structure validated - contains Constitution text")
                return True
            else:
                logger.warning("⚠️ PDF may not contain Constitution text")
                return False
                
    except Exception as e:
        logger.error(f"❌ PDF validation failed: {e}")
        return False


def main():
    """Main execution"""
    logger.info("=" * 50)
    logger.info("🏛️ Constitution of India - PDF Downloader")
    logger.info("=" * 50)
    
    # Check if already downloaded
    if DataConfig.CONSTITUTION_PDF_PATH.exists():
        logger.info(f"📄 Constitution PDF already exists at: {DataConfig.CONSTITUTION_PDF_PATH}")
        
        user_input = input("Do you want to re-download? (y/n): ").strip().lower()
        if user_input != 'y':
            logger.info("Skipping download.")
            return
        else:
            logger.info("Re-downloading...")
    
    # Download
    success = download_constitution_pdf()
    
    if success:
        # Verify
        logger.info("🔍 Verifying PDF structure...")
        verify_pdf_structure(DataConfig.CONSTITUTION_PDF_PATH)
        
        logger.info("=" * 50)
        logger.info("✅ Constitution PDF ready for processing!")
        logger.info("=" * 50)
    else:
        logger.error("❌ Download failed. Please download manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()
