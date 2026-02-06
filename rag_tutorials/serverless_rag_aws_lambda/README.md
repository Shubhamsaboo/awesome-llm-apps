## ☁️ Serverless RAG API on AWS Lambda

A scalable, zero-maintenance RAG API using [RAGStack-Lambda](https://github.com/HatmanStack/RAGStack-Lambda). The entire stack scales to zero — no vector database fees, no idle compute costs. Pay only when queries are running.

### Architecture

```
Documents → Lambda (OCR/Transcription) → Step Functions → S3 Vectors + Bedrock KB
                                                                    ↓
                            Streamlit App → GraphQL API → Lambda (Query) → AI Response + Sources
```

- **Compute**: AWS Lambda + Step Functions (scale-to-zero)
- **Vector Storage**: S3 Vectors (no provisioned capacity)
- **Embeddings**: Amazon Nova multimodal (text, images, video/audio)
- **Cost**: ~$7-10/month for 1,000 documents, $0 when idle

### Features

- AI chat with source citations and conversation context
- Semantic search across documents, images, and media transcripts
- Supports 30+ file types (PDF, DOCX, images, MP4, MP3, and more)
- Video/audio results include timestamp links to the exact segment
- MCP server included for Claude Desktop, Cursor, and VS Code integration

### How to Get Started

1. **Deploy RAGStack** (choose one):

   **One-click** (no CLI required):
   - [Subscribe on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-5afdiw2zrht6o) (free)
   - [Deploy via CloudFormation](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?templateURL=https://ragstack-quicklaunch-public-631094035453.s3.us-east-1.amazonaws.com/ragstack-template.yaml&stackName=my-docs)

   **From source:**
   ```bash
   git clone https://github.com/HatmanStack/RAGStack-Lambda.git
   cd RAGStack-Lambda
   python publish.py --project-name my-docs --admin-email admin@example.com
   ```

2. **Upload documents** via the RAGStack dashboard and wait for processing to complete

3. **Get your API credentials** from Dashboard → Settings (GraphQL endpoint + API key)

4. **Run the Streamlit app**

   ```bash
   cd awesome-llm-apps/rag_tutorials/serverless_rag_aws_lambda
   pip install -r requirements.txt
   streamlit run rag_app.py
   ```

5. **Enter your endpoint and API key** in the sidebar and start querying

### Demo

A live RAGStack deployment is available for testing:

| URL | Credentials |
|-----|-------------|
| [dhrmkxyt1t9pb.cloudfront.net](https://dhrmkxyt1t9pb.cloudfront.net/) | `guest@hatstack.fun` / `Guest@123` |
