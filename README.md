# SamvidhanAI 🏛️

**Production-Grade Constitutional AI Assistant**

AI-powered assistant for exploring the Constitution of India. Built with LangChain, ChromaDB, Google Gemini, and Streamlit.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

---

## 🎯 Features

- **📚 Accurate Constitutional References**: Answers backed by official Constitution text
- **🔍 Zero Hallucination**: Citation-validated responses with source documents
- **👥 User-Type Adaptation**: Tailored responses for Students, Lawyers, Citizens, and Exam Prep
- **⚡ Fast Retrieval**: ChromaDB vector database with Gemini embeddings
- **🎨 Beautiful UI**: Constitutional-themed interface with rich markdown formatting
- **☁️ Cloud-Ready**: Easy deployment to Streamlit Community Cloud

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Gemini API Key ([Get it here](https://aistudio.google.com/apikey))

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Constitution_project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 4. Download Constitution PDF
python scripts/download_constitution.py

# 5. Process the PDF
python src/data_processor.py

# 6. Initialize vector database
python src/vector_store.py

# 7. Run the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
Constitution_project/
├── app.py                      # Main Streamlit application
├── config.py                   # Centralized configuration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
│
├── data/                      # Constitutional data
│   ├── constitution_india.pdf
│   ├── processed_chunks.json
│   └── metadata_index.json
│
├── src/                       # Core application code
│   ├── data_processor.py     # PDF processing pipeline
│   ├── vector_store.py       # ChromaDB management
│   ├── rag_chain.py          # RAG orchestration
│   │
│   └── prompts/              # Multi-prompt system
│       ├── retriever_prompt.py
│       ├── answer_prompt.py
│       ├── citation_validator_prompt.py
│       └── refusal_prompt.py
│
├── scripts/                   # Utility scripts
│   └── download_constitution.py
│
├── tests/                     # Testing suite
│   ├── test_queries.json
│   └── test_rag_accuracy.py
│
└── chroma_db/                # Vector database (generated)
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RAG Chain     │
│   Orchestrator  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────┐
│ Vector │  │  Gemini  │
│  Store │  │   LLM    │
│(Chroma)│  │  1.5 Pro │
└────────┘  └──────────┘
```

**Pipeline Flow:**

1. **Query Expansion** (optional): Reformulates query for better retrieval
2. **Retrieval**: Fetches relevant Articles from ChromaDB
3. **Context Assembly**: Formats retrieved documents with metadata
4. **Answer Generation**: Gemini generates structured response
5. **Citation Validation** (optional): Verifies all claims have sources
6. **Response Formatting**: Displays in 6-section format

---

## 💡 Usage Examples

### Student Mode

```
Q: What is Article 21?

A: ✅ Direct Answer
Article 21 guarantees the Right to Life and Personal Liberty...

📜 Constitutional Basis
• Article 21 (Part III - Fundamental Rights)

🧠 Explanation in Simple Terms
This means the government cannot take away your life or freedom
without following proper legal procedures...

[Full structured response with sources]
```

### Lawyer Mode

```
Q: Analyze Article 21 scope

A: [More technical, precedent-focused response]
• Maneka Gandhi v. Union of India (1978) expanded interpretation
• Includes right to privacy, clean environment, healthcare...
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional (defaults provided)
GEMINI_MODEL=gemini-1.5-pro-latest
TEMPERATURE=0.1
TOP_K_RESULTS=5
CHUNK_SIZE=1000
```

### Streamlit Theme

Edit `.streamlit/config.toml` for custom theming.

---

## ☁️ Deployment

### Streamlit Community Cloud (Recommended)

1. **Push to GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Add secrets in Settings → Secrets:

     ```toml
     GOOGLE_API_KEY = "your_api_key"
     ```

   - Click Deploy!

3. **First-Time Setup on Cloud**
   - The vector database will be initialized on first run
   - Subsequent runs will use cached data

### Alternative: Google Cloud Run

See `DEPLOYMENT.md` for detailed instructions.

---

## 🧪 Testing

### Run Automated Tests

```bash
# Test RAG accuracy
python -m pytest tests/test_rag_accuracy.py -v

# Test specific components
python src/vector_store.py  # Test vector store
python src/rag_chain.py     # Test RAG chain
```

### Manual Testing

```bash
# Test queries from CLI
python -c "
from src.rag_chain import ConstitutionRAGChain
chain = ConstitutionRAGChain()
result = chain.query('What is Article 21?')
print(result['answer'])
"
```

---

## 📚 Data Source

- **Official PDF**: [Legislative Department, Ministry of Law & Justice, Government of India](https://legislative.gov.in/constitution-of-india/)
- **Version**: Updated to 106th Amendment Act, 2023
- **Authenticity**: Government-verified constitutional text

---

## 🛡️ Features & Safeguards

### Zero Hallucination System

- ✅ Citation-validated responses
- ✅ No fabricated Articles or case laws
- ✅ Out-of-scope query detection
- ✅ Graceful refusal with helpful suggestions

### Multi-Prompt Architecture

- **Retriever Prompt**: Query expansion for better search
- **Answer Prompt**: Structured 6-section responses
- **Citation Validator**: Verifies all factual claims
- **Refusal Prompt**: Handles out-of-scope queries

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Add more constitutional case law summaries
- Multilingual support (Hindi, regional languages)
- Voice interface
- Mobile app version
- More granular Article parsing

---

## 📄 License

This project is for educational and informational purposes.

**Important**: This is NOT legal advice. For legal matters, consult a qualified attorney.

---

## 🙏 Acknowledgments

- **Data Source**: Legislative Department, Government of India
- **AI Model**: Google Gemini-2.5-flash
- **Framework**: LangChain
- **Vector DB**: ChromaDB
- **UI**: Streamlit

---

## 📧 Contact & Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Email: [your-email]

---

**Made with ❤️ for Constitutional Awareness**

🏛️ **SamvidhanAI** - Empowering Citizens with Constitutional Knowledge
