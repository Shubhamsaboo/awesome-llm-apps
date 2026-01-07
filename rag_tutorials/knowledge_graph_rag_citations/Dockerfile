FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY knowledge_graph_rag.py .

EXPOSE 8501

CMD ["streamlit", "run", "knowledge_graph_rag.py", "--server.address", "0.0.0.0"]
