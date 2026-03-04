"""
Quick script to check available Gemini embedding models
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    print("=" * 50)
    print("Available Gemini Models")
    print("=" * 50)
    
    for model in genai.list_models():
        if 'embed' in model.name.lower():
            print(f"✓ {model.name}")
            print(f"  Supported methods: {model.supported_generation_methods}")
            print()
    
    print("=" * 50)
    print("Testing embedding with models/embedding-001:")
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content="Test"
        )
        print("✅ models/embedding-001 works!")
        print(f"   Embedding dimension: {len(result['embedding'])}")
    except Exception as e:
        print(f"❌ models/embedding-001 failed: {e}")
    
except Exception as e:
    print(f"Error: {e}")
