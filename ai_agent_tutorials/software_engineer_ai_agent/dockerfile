FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run as non-root user for additional security
RUN useradd -m appuser
USER appuser

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501"]