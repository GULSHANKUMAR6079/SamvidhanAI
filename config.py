"""
Configuration Management for SamvidhanAI
Loads environment variables and provides centralized access to all settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# PROJECT PATHS
# ============================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SRC_DIR = PROJECT_ROOT / "src"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# ============================================
# API KEYS
# ============================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate API key
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here":
    raise ValueError(
        "❌ GOOGLE_API_KEY not set! Please:\n"
        "1. Copy .env.example to .env\n"
        "2. Get your API key from https://aistudio.google.com/apikey\n"
        "3. Add it to .env file"
    )

# ============================================
# MODEL CONFIGURATION
# ============================================
class ModelConfig:
    """Gemini Model Settings"""
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_OUTPUT_TOKENS = 4096
    TOP_P = 1
    TOP_K = 40

# ============================================
# VECTOR DATABASE CONFIGURATION
# ============================================
class VectorDBConfig:
    """ChromaDB Settings"""
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "constitution_india")
    PERSIST_DIRECTORY = str(CHROMA_DIR)
    EMBEDDING_FUNCTION = ModelConfig.EMBEDDING_MODEL

# ============================================
# RETRIEVAL CONFIGURATION
# ============================================
class RetrievalConfig:
    """RAG Retrieval Settings"""
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))
    MAX_CONTEXT_LENGTH = 8000  # tokens

# ============================================
# CHUNKING CONFIGURATION
# ============================================
class ChunkingConfig:
    """Document Chunking Settings"""
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
    SEPARATOR = "\n\n"
    
# ============================================
# DATA SOURCE CONFIGURATION
# ============================================
class DataConfig:
    """Constitution Data Sources"""
    # Official Government PDF - Direct download link
    CONSTITUTION_PDF_URL = os.getenv(
        "CONSTITUTION_PDF_URL",
        "https://cdnbbsr.s3waas.gov.in/s380537a945c7aaa788ccfcdf1b99b5d8f/uploads/2023/05/2023050195.pdf"
    )
    # Backup URL if primary fails
    CONSTITUTION_PDF_URL_BACKUP = "https://legislative.gov.in/sites/default/files/COI.pdf"
    CONSTITUTION_PDF_PATH = DATA_DIR / "constitution_india.pdf"
    PROCESSED_CHUNKS_PATH = DATA_DIR / "processed_chunks.json"
    METADATA_INDEX_PATH = DATA_DIR / "metadata_index.json"

# ============================================
# STREAMLIT UI CONFIGURATION
# ============================================
class UIConfig:
    """Streamlit UI Settings"""
    PAGE_TITLE = "🏛️ SamvidhanAI - Constitution of India Assistant"
    PAGE_ICON = "🏛️"
    LAYOUT = "wide"
    
    # Constitutional Color Scheme
    COLORS = {
        "saffron": "#FF9933",
        "white": "#FFFFFF",
        "green": "#138808",
        "navy_blue": "#000080",
        "ashoka_blue": "#6495ED"
    }
    
    # User Types
    USER_TYPES = ["Student", "Lawyer", "Citizen", "Competitive Exam"]
    
    # Legal Disclaimer
    DISCLAIMER = (
        "⚠️ **Legal Disclaimer**: This is an informational constitutional "
        "explanation tool, not a substitute for professional legal advice. "
        "For legal matters, please consult a qualified attorney."
    )

# ============================================
# PROMPT TEMPLATES
# ============================================
class PromptConfig:
    """Prompt Template Settings"""
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30

# ============================================
# LOGGING CONFIGURATION
# ============================================
import logging

def setup_logging(level=logging.INFO):
    """Configure logging for the application"""
    # Fix Windows console encoding for emojis
    import sys
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Force UTF-8 encoding for Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass  # Fallback if reconfigure not available
    
    # File handler
    file_handler = logging.FileHandler(
        PROJECT_ROOT / 'samvidhanai.log',
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Configure root logger
    logger = logging.getLogger('SamvidhanAI')
    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# ============================================
# CONFIGURATION VALIDATION
# ============================================
def validate_config():
    """Validate all configuration settings"""
    errors = []
    
    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY is missing")
    
    if not DATA_DIR.exists():
        errors.append(f"Data directory not found: {DATA_DIR}")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
    
    logger.info("✅ Configuration validated successfully")

# Validate on import
try:
    validate_config()
except ValueError as e:
    logger.warning(f"Configuration validation failed: {e}")
