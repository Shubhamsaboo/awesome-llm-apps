# Deployment & Setup Guide

## System Requirements

### Minimum
- **OS:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 4GB minimum, 8GB+ recommended
- **Storage:** 10GB free (for Ollama models)
- **GPU:** Optional (recommended for faster generation)
- **Python:** 3.10 or higher

### Recommended
- **RAM:** 16GB+
- **GPU:** CUDA-compatible (NVIDIA) or Metal (Apple Silicon)
- **Python:** 3.11 or 3.12

---

## Installation Steps

### 1. Install Ollama

Ollama runs local LLMs. Download from: https://ollama.ai

**After Installation:**
```bash
# Start Ollama server (runs in background)
ollama serve

# In another terminal, pull a model
ollama pull mistral    # ~4GB, good balance of speed/quality
# OR
ollama pull neural-chat  # ~5GB, optimized for chat
# OR
ollama pull llama2     # ~7GB, more powerful

# Test it works
ollama list
# Should show: mistral (7.3GB)
```

**Keep Ollama running** - it listens on `http://localhost:11434`

### 2. Clone & Setup Python Environment

```bash
# Navigate to the project
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/ai_code_refactor_agent_memory

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import streamlit; import ollama; print('✓ Setup complete')"
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env if needed (defaults usually work)
# OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=mistral
```

---

## Running the Agent

### Option A: Streamlit UI (Recommended for Users)

```bash
# Make sure Ollama is running in another terminal
# (ollama serve)

# Start Streamlit
streamlit run streamlit_app.py

# Opens browser at http://localhost:8501
```

**First run:**
- Takes 30-60s for first refactoring (model warming up)
- Subsequent runs: 20-30s
- Close Streamlit: Ctrl+C in terminal

### Option B: Command Line Demo

```bash
# Run agent directly
python refactor_agent.py

# Shows sample refactoring with session summary
```

### Option C: Python API

```python
from refactor_agent import CodeRefactorAgent

agent = CodeRefactorAgent(model="mistral")

code = """
def calculate(items):
    result = 0
    for item in items:
        result += item['price'] * item['qty']
    return result
"""

outcome = agent.refactor_code(
    code=code,
    task="Convert to object-oriented design",
    refactoring_type="procedural_to_oop",
)

print(f"Status: {outcome.status}")
print(f"Output:\n{outcome.code_output}")
print(f"Insight: {outcome.key_insight}")
```

---

## Troubleshooting

### Issue: "Only one usage of each socket address" (Port Already Bound)

**Problem:** Ollama fails with: `bind: Only one usage of each socket address (protocol/network address/port) is normally permitted`

**Solutions:**
1. **Quick fix - Use a different port:**
   ```bash
   # Windows PowerShell
   $env:OLLAMA_HOST="127.0.0.1:11435"
   ollama serve
   
   # Linux/Mac
   export OLLAMA_HOST="127.0.0.1:11435"
   ollama serve
   ```
   Then update `.env` to use `OLLAMA_HOST=http://localhost:11435`

2. **Kill existing Ollama processes:**
   ```bash
   # Windows
   taskkill /F /IM ollama.exe
   
   # Linux/Mac
   pkill ollama
   
   # Wait 2 seconds then try again
   ```

3. **Check what's using the port:**
   ```bash
   # Windows
   netstat -ano | findstr :11434
   
   # Linux/Mac
   lsof -i :11434
   ```

### Issue: "Connection refused" to Ollama

**Problem:** Agent can't reach Ollama at `http://localhost:11434`

**Solutions:**
1. Check Ollama is running:
   ```bash
   ollama serve
   # Should show: "Listening on 127.0.0.1:11434"
   ```

2. Check OLLAMA_HOST in .env matches
   ```bash
   cat .env | grep OLLAMA_HOST
   # Should be: OLLAMA_HOST=http://localhost:11434
   ```

3. Try direct test:
   ```bash
   curl http://localhost:11434/api/tags
   # Should return JSON list of models
   ```

### Issue: "Model not found" error

**Problem:** Selected model isn't installed

**Solution:**
```bash
# List available models
ollama list

# Pull missing model
ollama pull mistral

# Verify it's there
ollama list
```

### Issue: Out of memory error

**Problem:** Your machine doesn't have enough RAM

**Solutions:**
- Use a smaller model: `ollama pull neural-chat` (lighter than mistral)
- Close other applications
- Add swap space (Linux): `fallocate -l 4G /swapfile`
- Use GPU: See "GPU Acceleration" below

### Issue: Streamlit keeps rerunning code

**Problem:** Streamlit reruns entire script on input change

**Solution:** Already handled by `@st.cache_resource` in refactor_agent
- First run is slow, subsequent runs use cached agent
- Click "View Learned Constraints" to see memory growth

### Issue: "ModuleNotFoundError: No module named 'ollama'"

**Problem:** Dependencies not installed

**Solution:**
```bash
# Verify you're in venv
which python
# Should show: /path/to/venv/bin/python

# Reinstall
pip install -r requirements.txt --force-reinstall
```

---

## GPU Acceleration

### NVIDIA GPU (CUDA)

```bash
# Check if Ollama detects GPU
ollama list
# If not using GPU, reinstall with CUDA support

# On Windows, restart Ollama after installing CUDA
# Check utilization
nvidia-smi  # Should show ollama process using GPU

# In streamlit_app.py, disable CPU fallback:
agent = CodeRefactorAgent(
    model="mistral",
    ollama_host="http://localhost:11434",  # Ollama handles GPU auto-detection
)
```

### Apple Silicon (Metal)

```bash
# Ollama auto-detects Metal on macOS
# No additional setup needed
# Can use `top -o MEM` to verify GPU usage

# If not using Metal, check Ollama settings:
# Settings → Model Acceleration → Metal
```

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy agent code
COPY refactor_agent.py .
COPY memory_schema.py .
COPY streamlit_app.py .

# Expose Streamlit port
EXPOSE 8501

# Expect Ollama running on host network
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
```

**Run with Docker:**
```bash
# Build image
docker build -t refactor-agent .

# Run container (connect to host's Ollama)
docker run -p 8501:8501 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  refactor-agent
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: refactor-agent
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: agent
        image: refactor-agent:latest
        ports:
        - containerPort: 8501
        env:
        - name: OLLAMA_HOST
          value: http://ollama-service:11434
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
```

### Cloud Deployment Options

#### Option 1: AWS EC2 + Ollama
```bash
# Launch Ubuntu 22.04 instance (t3.large or larger)
# SSH in, then:

curl https://ollama.ai/install.sh | sh
ollama pull mistral

# Install agent
git clone <repo>
cd ai_code_refactor_agent_memory
pip install -r requirements.txt

# Run (keep terminal open or use screen)
screen
streamlit run streamlit_app.py --server.address=0.0.0.0
```

#### Option 2: Replicate (Hosted Inference)
```python
# Use Replicate's hosted Ollama models
# Modify refactor_agent.py to use Replicate API

import replicate

response = replicate.run(
    "mistral:latest",  # Hosted mistral
    input={"prompt": prompt}
)
```

---

## Performance Tuning

### Increase Speed

**1. Use faster model:**
```bash
ollama pull neural-chat  # Faster than mistral
# Update .env: OLLAMA_MODEL=neural-chat
```

**2. Reduce token limit:**
```python
# In refactor_agent.py
response = self._call_ollama(prompt, max_tokens=1000)  # was 2000
```

**3. Parallelize searches:**
```python
# Use ThreadPoolExecutor to query memory in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(memory.search, query)
        for query in queries
    ]
```

### Reduce Memory Usage

**1. Use smaller model:**
```bash
ollama pull orca-mini  # 3GB, lighter
```

**2. Limit constraint history:**
```python
# Keep only last 100 constraints
if len(agent.discovered_constraints) > 100:
    agent.discovered_constraints = agent.discovered_constraints[-100:]
```

**3. Disable extended tracking:**
```python
# Don't store full code snippets if memory is tight
outcome.code_input = outcome.code_input[:200]  # Truncate
outcome.code_output = outcome.code_output[:200]
```

---

## Monitoring & Logging

### Enable Debug Logging

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Then run
streamlit run streamlit_app.py
# Check terminal for detailed logs
```

### Capture Metrics

```python
import time
import logging

logger = logging.getLogger(__name__)

start = time.time()
outcome = agent.refactor_code(...)
duration = time.time() - start

logger.info(f"Refactor took {duration:.2f}s")
logger.info(f"Memory items: {len(agent.discovered_constraints)}")
logger.info(f"Success rate: {agent.get_session_summary()['success_rate']}")
```

### Monitor Resource Usage

```bash
# Terminal 1: Run agent
streamlit run streamlit_app.py

# Terminal 2: Monitor resources
# On macOS/Linux:
top -p $(pgrep -f streamlit)

# On Windows (PowerShell):
Get-Process python | Get-WmiObject -ComputerName . -Class Win32_Process | Format-Table ProcessId, WorkingSetSize
```

---

## Backup & Recovery

### Save Agent State

```python
import json
import pickle

agent = CodeRefactorAgent()
# ... run refactorings ...

# Backup memory
backup = {
    "outcomes": [o.dict() for o in agent.session_outcomes],
    "constraints": [c.dict() for c in agent.discovered_constraints],
    "adaptations": [a.dict() for a in agent.adaptations],
}

with open("agent_backup.json", "w") as f:
    json.dump(backup, f)
```

### Restore State

```python
import json
from memory_schema import ExecutionOutcome, ConstraintDiscovered

with open("agent_backup.json", "r") as f:
    backup = json.load(f)

agent = CodeRefactorAgent()
agent.session_outcomes = [ExecutionOutcome(**o) for o in backup["outcomes"]]
agent.discovered_constraints = [ConstraintDiscovered(**c) for c in backup["constraints"]]
# ... etc
```

---

## Maintenance

### Regular Tasks

- **Weekly:** Check Ollama model updates: `ollama pull mistral`
- **Monthly:** Clean up old memory backups
- **Quarterly:** Review constraint effectiveness, remove unused ones
- **Annually:** Update dependencies: `pip install -U -r requirements.txt`

### Version Pinning

Keep `requirements.txt` pinned to specific versions:
```
streamlit==1.39.0  # NOT streamlit>=1.39.0
mem0ai==0.1.29     # Specific version for compatibility
```

This ensures reproducible deployments across machines.

---

## Support & Debugging

### Get Help

1. Check logs: `streamlit run streamlit_app.py` shows errors in terminal
2. Test Ollama directly: `ollama run mistral "Hello"`
3. Test memory models: `python tests/test_memory_schema.py`
4. Review architecture: See `docs/architecture.md`

### Report Issues

Include:
- OS and Python version
- Ollama model and version
- Error messages (full traceback)
- Steps to reproduce
- System specs (RAM, GPU, etc)

---

**Last Updated:** 2026-09-06  
**Tested On:** Windows 11, macOS 13.5, Ubuntu 22.04  
**Ollama Version:** 0.1.31+  
**Python Version:** 3.10-3.12
