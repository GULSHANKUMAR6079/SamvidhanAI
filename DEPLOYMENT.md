# SamvidhanAI - Cloud Deployment Guide

Complete guide for deploying SamvidhanAI to production cloud environments.

---

## 🚀 Deployment Options

1. **Streamlit Community Cloud** (Recommended - Free)
2. **Google Cloud Run** (Scalable - Pay as you go)
3. **Hugging Face Spaces** (Alternative - Free tier)
4. **Railway / Render** (Alternative options)

---

## Option 1: Streamlit Community Cloud (Recommended)

**Best for**: Quick deployment, free hosting, easy updates

### Prerequisites

- GitHub account
- Streamlit Community Cloud account ([sign up](https://share.streamlit.io))
- Google Gemini API key

### Step-by-Step Deployment

#### 1. Prepare Your Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Ready for deployment"

# Push to GitHub
git remote add origin https://github.com/yourusername/samvidhanai.git
git push -u origin main
```

#### 2. Configure Secrets

Create `.streamlit/secrets.toml` (local only, don't commit):

```toml
GOOGLE_API_KEY = "your_actual_api_key_here"

# Optional configuration
GEMINI_MODEL = "gemini-1.5-pro-latest"
TEMPERATURE = "0.1"
TOP_K_RESULTS = "5"
```

**Important**: Add `.streamlit/secrets.toml` to `.gitignore`!

#### 3. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Configure:
   - **Repository**: `yourusername/samvidhanai`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click "Advanced settings" → "Secrets"
6. Paste your secrets (from `.streamlit/secrets.toml`)
7. Click "Deploy"!

#### 4. First-Time Setup on Cloud

The app will automatically:

- Install dependencies from `requirements.txt`
- Download Constitution PDF (on first run)
- Process PDF and create chunks
- Initialize ChromaDB vector database

**Note**: First deployment may take 5-10 minutes to initialize the database.

#### 5. Post-Deployment

- Your app will be available at: `https://share.streamlit.io/yourusername/samvidhanai/main/app.py`
- Updates: Push to GitHub → App auto-redeploys
- Logs: View in Streamlit Cloud dashboard

### Optimization for Streamlit Cloud

**Persistent Storage Workaround**:

Streamlit Cloud doesn't persist files between restarts. To handle this:

1. **Option A - Cloud Storage** (Recommended for production):
   - Store `chroma_db/` in Google Cloud Storage
   - Download on startup if not present

2. **Option B - Rebuild on Restart**:
   - Keep PDF processing fast
   - Accept 2-3 minute initialization on cold starts

**Example: Using Cloud Storage**

```python
# In config.py, add:
import os

def ensure_vector_db():
    """Download vector DB from cloud storage if not present"""
    if not os.path.exists('./chroma_db'):
        # Download from Google Cloud Storage
        download_from_gcs('your-bucket', 'chroma_db/', './chroma_db/')
```

---

## Option 2: Google Cloud Run

**Best for**: Production deployments, custom domains, scaling

### Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed

### Deployment Steps

#### 1. Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download and process Constitution on build
RUN python scripts/download_constitution.py && \
    python src/data_processor.py && \
    python src/vector_store.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

#### 2. Build and Deploy

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/samvidhanai

# Deploy to Cloud Run
gcloud run deploy samvidhanai \
  --image gcr.io/YOUR_PROJECT_ID/samvidhanai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_api_key \
  --memory 2Gi \
  --cpu 2
```

#### 3. Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service samvidhanai \
  --domain samvidhanai.yourdomain.com \
  --region us-central1
```

**Cost Estimate**: ~$5-20/month depending on usage (Cloud Run has generous free tier)

---

## Option 3: Hugging Face Spaces

**Best for**: ML community visibility, free GPU access (if needed)

### Deployment Steps

1. **Create Space**:
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Select "Streamlit" SDK

2. **Upload Code**:

   ```bash
   git clone https://huggingface.co/spaces/yourusername/samvidhanai
   cd samvidhanai
   
   # Copy your code
   cp -r /path/to/Constitution_project/* .
   
   # Commit and push
   git add .
   git commit -m "Initial deployment"
   git push
   ```

3. **Configure Secrets**:
   - Go to Space Settings → Repository secrets
   - Add `GOOGLE_API_KEY`

4. **Create `requirements.txt`** (Hugging Face specific):

   ```
   streamlit
   langchain
   langchain-google-genai
   chromadb
   pypdf2
   pdfplumber
   python-dotenv
   ```

---

## 🔧 Production Optimizations

### 1. Caching Strategy

```python
# In app.py
@st.cache_resource(ttl=3600)
def load_vector_store():
    """Cache vector store for 1 hour"""
    return ConstitutionVectorStore()

@st.cache_data(ttl=86400)
def load_constitution_pdf():
    """Cache PDF data for 24 hours"""
    pass
```

### 2. Environment-Specific Config

```python
# config.py
import os

IS_PRODUCTION = os.getenv('ENVIRONMENT') == 'production'

if IS_PRODUCTION:
    # Production settings
    ChunkingConfig.BATCH_SIZE = 200
    RetrievalConfig.TOP_K_RESULTS = 3
else:
    # Development settings
    RetrievalConfig.TOP_K_RESULTS = 5
```

### 3. Monitoring

```python
# Add to app.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log queries
logger.info(f"Query: {query}, User: {user_type}")
```

### 4. Rate Limiting

```python
# Add to app.py
import time

if 'last_query_time' not in st.session_state:
    st.session_state.last_query_time = 0

# Rate limit: 1 query per 2 seconds
if time.time() - st.session_state.last_query_time < 2:
    st.warning("Please wait before submitting another query")
    return

st.session_state.last_query_time = time.time()
```

---

## 🐛 Troubleshooting

### Issue: "ChromaDB not initialized"

**Solution**:

```bash
# Re-run initialization
python src/vector_store.py
```

### Issue: "Out of memory"

**Solutions**:

- Increase memory allocation (Cloud Run: `--memory 4Gi`)
- Reduce `CHUNK_SIZE` in config
- Process PDF in smaller batches

### Issue: "Gemini API quota exceeded"

**Solutions**:

- Monitor usage in Google Cloud Console
- Implement request caching
- Add rate limiting

### Issue: "Slow response times"

**Solutions**:

- Enable query result caching
- Reduce `TOP_K_RESULTS`
- Use smaller vector store (filter by Parts)

---

## 📊 Monitoring & Maintenance

### Key Metrics to Track

1. **Query Response Time**: < 5 seconds average
2. **Citation Accuracy**: > 95%
3. **User Satisfaction**: Track via feedback form
4. **API Costs**: Monitor Gemini API usage

### Monthly Maintenance

- [ ] Update Constitution PDF if amendments passed
- [ ] Review and update test queries
- [ ] Check for Gemini model updates
- [ ] Monitor error logs
- [ ] Review user feedback

---

## 🔒 Security Best Practices

1. **API Keys**:
   - Never commit to Git
   - Use environment variables only
   - Rotate keys quarterly

2. **Input Validation**:
   - Already implemented in prompts
   - Rate limiting in production

3. **Data Privacy**:
   - No user data stored (stateless)
   - Logs should not contain PII

---

## 📈 Scaling Considerations

**Current Architecture**: Handles ~100 simultaneous users

**To scale to 1000+ users**:

1. **Add Redis Caching**:
   - Cache frequent queries
   - Reduce Gemini API calls

2. **Load Balancer**:
   - Deploy multiple Cloud Run instances
   - Use Cloud Load Balancer

3. **Separate Vector DB**:
   - Host ChromaDB separately (e.g., Pinecone)
   - Better for multi-instance deployments

---

## ✅ Deployment Checklist

Before deploying:

- [ ] All dependencies in `requirements.txt`
- [ ] `.env.example` documented
- [ ] `.gitignore` includes secrets
- [ ] README updated with deployment URL
- [ ] Tests passing (`pytest tests/`)
- [ ] API keys configured in cloud secrets
- [ ] Error handling tested
- [ ] Response times acceptable
- [ ] Legal disclaimer visible

---

## 🆘 Support

For deployment issues:

- Check logs in cloud provider dashboard
- Review error messages in Streamlit logs
- Open GitHub issue with logs

---

**Your SamvidhanAI is now ready for production! 🏛️**
