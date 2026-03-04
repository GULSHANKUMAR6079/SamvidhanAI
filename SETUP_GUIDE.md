# SamvidhanAI - Quick Setup Guide

**Get your Constitutional AI Assistant running in 5 minutes!**

---

## ⚡ Quick Start (For Testing)

### Step 1: Get Your Gemini API Key

1. Go to: <https://aistudio.google.com/apikey>
2. Click "Create API Key"
3. Copy the API key

### Step 2: Set Up Environment

```bash
# Navigate to project directory
cd d:\Constitution_project

# Copy environment template
copy .env.example .env

# Edit .env file and add your API key
notepad .env
```

In the `.env` file, replace:

```
GOOGLE_API_KEY=your_google_api_key_here
```

With your actual key:

```
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Save and close.

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Expected time**: 2-3 minutes

### Step 4: Download & Process Constitution

```bash
# Download the official Constitution PDF
python scripts\download_constitution.py

# Process the PDF (extract text, create chunks)
python src\data_processor.py
```

**Expected time**:

- Download: 30 seconds
- Processing: 1-2 minutes

### Step 5: Initialize Vector Database

```bash
# Set up ChromaDB and ingest documents
python src\vector_store.py
```

**Expected time**: 3-5 minutes (embedding generation)

**Expected output**:

```
🏛️ Constitution Vector Store Setup
📥 Ingesting 250+ documents into ChromaDB...
✅ Successfully ingested 250+ documents
✅ Vector store ready!
```

### Step 6: Run the Application

```bash
# Launch Streamlit app
streamlit run app.py
```

**Expected output**:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Your browser will automatically open to the app!

---

## 🧪 Test the System

Once the app is running, try these test queries:

1. **Basic Test**:
   - Query: "What is Article 21?"
   - Expected: Structured response about Right to Life and Personal Liberty

2. **Complex Test**:
   - Query: "Explain Fundamental Rights"
   - Expected: Overview of Part III with multiple Articles

3. **Out-of-Scope Test**:
   - Query: "Who should I vote for?"
   - Expected: Graceful refusal with suggestions

4. **User Type Test**:
   - Change user type to "Lawyer"
   - Same query should give more technical response

---

## ✅ Verification Checklist

After setup, verify:

- [ ] App loads without errors
- [ ] Chat interface is visible
- [ ] User type selector works (Student/Lawyer/Citizen/Exam)
- [ ] Query returns structured response (6 sections)
- [ ] Citations are present in response
- [ ] "View Retrieved Sources" expander shows sources
- [ ] Legal disclaimer is visible at bottom
- [ ] Out-of-scope queries are refused politely

---

## 🐛 Common Issues & Fixes

### Issue 1: "GOOGLE_API_KEY not set"

**Solution**:

```bash
# Make sure .env file exists
dir .env

# Verify API key is set correctly
type .env
```

The file should contain:

```
GOOGLE_API_KEY=AIzaSyD...
```

### Issue 2: "Constitution PDF not found"

**Solution**:

```bash
# Re-run download script
python scripts\download_constitution.py

# Verify file exists
dir data\constitution_india.pdf
```

### Issue 3: "ChromaDB not initialized"

**Solution**:

```bash
# Re-run vector store setup
python src\vector_store.py
```

### Issue 4: "Module not found"

**Solution**:

```bash
# Reinstall dependencies
pip install -r requirements.txt

# If that fails, upgrade pip first
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Issue 5: "Slow responses"

**Possible causes**:

- First query after startup (cold start)
- Gemini API rate limits
- Internet connection

**Solutions**:

- Wait 30 seconds for first query
- Check internet connection
- Verify Gemini API quota in Google Cloud Console

---

## 📊 System Requirements

**Minimum**:

- Python 3.9+
- 4 GB RAM
- 1 GB disk space
- Internet connection

**Recommended**:

- Python 3.10+
- 8 GB RAM
- 2 GB disk space
- Fast internet (for API calls)

---

## 🔄 Resetting the System

If you want to start fresh:

```bash
# Delete vector database
rmdir /s chroma_db

# Delete processed data
del data\processed_chunks.json
del data\metadata_index.json

# Re-run setup from Step 4
python src\data_processor.py
python src\vector_store.py
```

---

## 📈 Next Steps

Once basic setup works:

1. **Customize Prompts**: Edit files in `src/prompts/` to adjust tone
2. **Add More Data**: Add case law summaries to `data/` folder
3. **Deploy to Cloud**: Follow `DEPLOYMENT.md` for cloud hosting
4. **Run Tests**: Execute `pytest tests/test_rag_accuracy.py -v`

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: Look at `samvidhanai.log` file
2. **Review error message**: Often contains solution hints
3. **Restart app**: Close and rerun `streamlit run app.py`
4. **Check firewall**: Ensure ports 8501 (Streamlit) and 443 (API) are open

---

## 🎯 Expected Performance

**First Run** (with setup):

- Total setup time: ~10 minutes
- Database initialization: ~5 minutes

**Subsequent Runs**:

- App startup: <10 seconds
- First query: 5-8 seconds
- Follow-up queries: 3-5 seconds

**Database Persistence**:

- Vector database survives app restarts
- No need to re-process PDF after first setup
- Re-ingestion only needed if PDF changes

---

## ✨ Tips for Best Results

1. **Be Specific**: "What is Article 21?" > "Tell me about rights"
2. **Use Article Numbers**: System is optimized for Article-based queries
3. **Try Different User Types**: Responses adapt to your selected role
4. **Check Citations**: Expand "View Retrieved Sources" to see original text
5. **Constitutional Queries Only**: Out-of-scope queries will be refused

---

**You're all set! Enjoy exploring the Constitution with SamvidhanAI! 🏛️**
