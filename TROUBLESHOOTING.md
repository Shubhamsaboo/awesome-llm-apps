# 🔧 Troubleshooting Guide

This guide helps you resolve common issues when working with Awesome LLM Apps.

## 📋 Table of Contents

- [Installation Issues](#installation-issues)
- [Import Errors](#import-errors)
- [API Key Issues](#api-key-issues)
- [Agent Initialization Errors](#agent-initialization-errors)
- [Vector Database Issues](#vector-database-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)

## 🔨 Installation Issues

### Issue: `pip install` fails

**Symptoms:**
```bash
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**

1. **Update pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Use Python 3.8+:**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

3. **Install in virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

### Issue: Conflicting dependencies

**Symptoms:**
```bash
ERROR: pip's dependency resolver does not currently take into account all the packages...
```

**Solutions:**

1. **Create fresh virtual environment:**
   ```bash
   deactivate  # if in a venv
   rm -rf venv  # or rmdir /s venv on Windows
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Install specific versions:**
   ```bash
   pip install agno==0.1.0  # Use specific version
   ```

## 📦 Import Errors

### Issue: `ModuleNotFoundError: No module named 'agno.knowledge.pdf'`

**Symptoms:**
```python
ModuleNotFoundError: No module named 'agno.knowledge.pdf'
```

**Solution:**

Update your imports to use the correct module paths:

```python
# ❌ OLD (Incorrect)
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader

# ✅ NEW (Correct)
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.document.reader.pdf_reader import PDFReader
```

**Files to check:**
- All files in `advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team/`
- Any custom agents you've created

### Issue: `ImportError: cannot import name 'X' from 'agno'`

**Solutions:**

1. **Update agno package:**
   ```bash
   pip install --upgrade agno
   ```

2. **Check agno version:**
   ```bash
   pip show agno
   ```

3. **Reinstall agno:**
   ```bash
   pip uninstall agno
   pip install agno
   ```

## 🔑 API Key Issues

### Issue: API key not recognized

**Symptoms:**
```
AuthenticationError: Invalid API key
```

**Solutions:**

1. **Check .env file:**
   ```bash
   # Create .env file in project root
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

2. **Verify key format:**
   - OpenAI keys start with `sk-`
   - Anthropic keys start with `sk-ant-`
   - No spaces or quotes around the key

3. **Load environment variables:**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   api_key = os.getenv("OPENAI_API_KEY")
   
   if not api_key:
       raise ValueError("OPENAI_API_KEY not found in environment")
   ```

### Issue: Rate limit exceeded

**Symptoms:**
```
RateLimitError: Rate limit exceeded
```

**Solutions:**

1. **Implement retry logic:**
   ```python
   import time
   from tenacity import retry, wait_exponential, stop_after_attempt
   
   @retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(3))
   def call_api():
       return agent.run(query)
   ```

2. **Use lower tier model:**
   ```python
   # Instead of gpt-4o
   model = OpenAIChat(id="gpt-4o-mini")
   ```

3. **Add delays between requests:**
   ```python
   import time
   
   for query in queries:
       response = agent.run(query)
       time.sleep(1)  # Wait 1 second between requests
   ```

## 🤖 Agent Initialization Errors

### Issue: `TypeError: Agent.__init__() got an unexpected keyword argument 'team'`

**Symptoms:**
```python
TypeError: Agent.__init__() got an unexpected keyword argument 'team'
```

**Solution:**

Update agent initialization to use `agents` instead of `team`:

```python
# ❌ OLD (Incorrect)
agent_team = Agent(
    name="Team Lead",
    team=[agent1, agent2, agent3]
)

# ✅ NEW (Correct)
agent_team = Agent(
    name="Team Lead",
    agents=[agent1, agent2, agent3]
)
```

**Files to check:**
- `advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team/finance_agent_team.py`
- `advanced_ai_agents/single_agent_apps/ai_journalist_agent/journalist_agent.py`
- `advanced_ai_agents/single_agent_apps/ai_movie_production_agent/movie_production_agent.py`

### Issue: Agent not responding

**Symptoms:**
- Agent hangs indefinitely
- No response after long wait

**Solutions:**

1. **Check model availability:**
   ```python
   try:
       response = agent.run(query, timeout=30)
   except TimeoutError:
       st.error("Request timed out. Please try again.")
   ```

2. **Verify API connectivity:**
   ```python
   import requests
   
   try:
       response = requests.get("https://api.openai.com/v1/models", timeout=5)
       response.raise_for_status()
   except requests.exceptions.RequestException as e:
       st.error(f"Cannot connect to API: {e}")
   ```

3. **Enable debug mode:**
   ```python
   agent = Agent(
       name="Debug Agent",
       model=OpenAIChat(id="gpt-4o"),
       debug_mode=True  # Enable debug logging
   )
   ```

## 🗄️ Vector Database Issues

### Issue: Qdrant connection failed

**Symptoms:**
```
ConnectionError: Failed to connect to Qdrant
```

**Solutions:**

1. **Check Qdrant is running:**
   ```bash
   # For local Qdrant
   docker ps | grep qdrant
   
   # Start Qdrant if not running
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Verify connection settings:**
   ```python
   vector_db = Qdrant(
       collection="my_collection",
       url="http://localhost:6333",  # Check URL
       api_key=None  # For local instance
   )
   ```

3. **Test connection:**
   ```python
   try:
       from qdrant_client import QdrantClient
       client = QdrantClient(url="http://localhost:6333")
       collections = client.get_collections()
       print(f"Connected! Collections: {collections}")
   except Exception as e:
       print(f"Connection failed: {e}")
   ```

### Issue: Collection not found

**Symptoms:**
```
CollectionNotFound: Collection 'xyz' does not exist
```

**Solutions:**

1. **Create collection first:**
   ```python
   knowledge_base = PDFUrlKnowledgeBase(
       vector_db=vector_db,
       num_documents=3
   )
   # This will create the collection automatically
   ```

2. **Check collection name:**
   ```python
   # Ensure consistent naming
   COLLECTION_NAME = "legal_documents"
   
   vector_db = Qdrant(
       collection=COLLECTION_NAME,
       url=qdrant_url,
       api_key=qdrant_api_key
   )
   ```

### Issue: Document loading fails

**Symptoms:**
```
Error loading documents: No documents extracted from PDF
```

**Solutions:**

1. **Verify PDF is valid:**
   ```python
   from agno.document.reader.pdf_reader import PDFReader
   
   reader = PDFReader()
   try:
       documents = reader.read("path/to/file.pdf")
       if not documents:
           print("No content extracted from PDF")
       else:
           print(f"Extracted {len(documents)} documents")
   except Exception as e:
       print(f"Failed to read PDF: {e}")
   ```

2. **Check file permissions:**
   ```bash
   # On Unix-like systems
   ls -l path/to/file.pdf
   chmod 644 path/to/file.pdf  # If needed
   ```

3. **Try different PDF:**
   - Ensure PDF is not password-protected
   - Ensure PDF contains extractable text (not just images)
   - Try with a simple text PDF first

## ⚡ Performance Issues

### Issue: Slow response times

**Solutions:**

1. **Use faster models:**
   ```python
   # Instead of gpt-4o
   model = OpenAIChat(id="gpt-4o-mini")  # Faster and cheaper
   ```

2. **Reduce context size:**
   ```python
   knowledge_base = PDFUrlKnowledgeBase(
       vector_db=vector_db,
       num_documents=2  # Reduce from 3 to 2
   )
   ```

3. **Enable caching:**
   ```python
   import streamlit as st
   
   @st.cache_resource
   def get_agent():
       return Agent(...)
   ```

4. **Optimize vector search:**
   ```python
   vector_db = Qdrant(
       collection="my_collection",
       url=qdrant_url,
       api_key=qdrant_api_key,
       # Add search optimization
       search_params={"hnsw_ef": 128}  # Adjust based on needs
   )
   ```

### Issue: High memory usage

**Solutions:**

1. **Process documents in chunks:**
   ```python
   chunk_size = 1000  # Smaller chunks
   overlap = 100      # Less overlap
   ```

2. **Clear cache periodically:**
   ```python
   import streamlit as st
   
   if st.button("Clear Cache"):
       st.cache_resource.clear()
       st.success("Cache cleared!")
   ```

3. **Limit concurrent operations:**
   ```python
   # Process one document at a time
   for doc in documents:
       process_document(doc)
       # Don't load all at once
   ```

## 🚨 Common Error Messages

### Error: `agno.storage exception`

**Cause:** Storage initialization issues

**Solution:**

```python
from agno.storage.agent.sqlite import SqliteAgentStorage

try:
    storage = SqliteAgentStorage(
        table_name="agent_storage",
        db_file="agents.db"
    )
except Exception as e:
    print(f"Storage initialization failed: {e}")
    # Use in-memory storage as fallback
    storage = None
```

### Error: `Failed to retrieve google sheets link`

**Cause:** Missing or incorrect Google Sheets API configuration

**Solution:**

1. **Set up Google Sheets API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google Sheets API
   - Create credentials (Service Account)
   - Download JSON key file

2. **Configure in code:**
   ```python
   import gspread
   from oauth2client.service_account import ServiceAccountCredentials
   
   scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
   
   creds = ServiceAccountCredentials.from_json_keyfile_name(
       'path/to/credentials.json',
       scope
   )
   client = gspread.authorize(creds)
   ```

### Error: `Streamlit app not loading`

**Solutions:**

1. **Check port availability:**
   ```bash
   # Try different port
   streamlit run app.py --server.port 8502
   ```

2. **Clear Streamlit cache:**
   ```bash
   # Delete cache directory
   rm -rf ~/.streamlit/cache
   ```

3. **Check for syntax errors:**
   ```bash
   python -m py_compile app.py
   ```

## 🔍 Debugging Tips

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Use Streamlit Debug Mode

```python
import streamlit as st

# Show session state
st.write("Session State:", st.session_state)

# Show exception details
try:
    risky_operation()
except Exception as e:
    st.exception(e)  # Shows full traceback
```

### Test Components Individually

```python
# Test vector DB connection
def test_vector_db():
    try:
        vector_db = init_qdrant()
        st.success("✅ Vector DB connected")
    except Exception as e:
        st.error(f"❌ Vector DB failed: {e}")

# Test agent initialization
def test_agent():
    try:
        agent = create_agent()
        st.success("✅ Agent initialized")
    except Exception as e:
        st.error(f"❌ Agent failed: {e}")

# Run tests
if st.button("Run Tests"):
    test_vector_db()
    test_agent()
```

## 📞 Getting Additional Help

If you're still experiencing issues:

1. **Check GitHub Issues:** [Search existing issues](https://github.com/Shubhamsaboo/awesome-llm-apps/issues)
2. **Create New Issue:** Include:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version, package versions)
   - Code snippet (minimal reproducible example)
3. **Join Community:** Discord/Slack (if available)

## 📚 Additional Resources

- [Agno Documentation](https://docs.agno.com)
- [Streamlit Documentation](https://docs.streamlit.io)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

---

**Still stuck?** Don't hesitate to ask for help! The community is here to support you. 🤝
