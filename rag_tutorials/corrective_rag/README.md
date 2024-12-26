# Corrective RAG Demo

This project demonstrates Corrective RAG (Retrieval Augmented Generation), an advanced approach to RAG that incorporates self-reflection / self-grading on retrieved documents - document relevance checking, query transformation, and web search fallback mechanisms to improve the quality of responses by far. Complete explanation of CRAG down below.

## Demo


## Features

- **Smart Document Retrieval**: Uses Qdrant vector store for efficient document retrieval
- **Document Relevance Grading**: Employs Claude 3.5 sonnet to assess document relevance
- **Query Transformation**: Improves search results by optimizing queries when needed
- **Web Search Fallback**: Uses Tavily API for web search when local documents aren't sufficient
- **Multi-Model Approach**: Combines OpenAI embeddings and Claude 3.5 sonnet for different tasks
- **Interactive UI**: Built with Streamlit for easy document upload and querying

## How to Run?

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd rag_tutorials/corrective_rag
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up API Keys**:
   You'll need to obtain the following API keys:
   - OpenAI API key (for embeddings)
   - Anthropic API key (for Claude 3.5 sonnet as llm)
   - Tavily API key (for web search)
   - Qdrant API key and URL

4. **Run the Application**:
   ```bash
   streamlit run corrective_rag.py
   ```

5. **Use the Application**:
   - Upload documents or provide URLs
   - Enter your questions in the query box
   - View the step-by-step Corrective RAG process
   - Get comprehensive answers

## Technologies Used

- **LangChain**: For RAG orchestration and chains
- **LangGraph**: For workflow management
- **Qdrant**: Vector database for document storage
- **Claude 3.5 sonnet**: Main language model for analysis and generation
- **OpenAI**: For document embeddings
- **Tavily**: For web search capabilities
- **Streamlit**: For the user interface

## CRAG Step by Step Explanation

1. Initial Retrieval

A user query is presented to the system.    
The system uses an existing retriever model to gather relevant documents from a knowledge base. This retriever could be any existing model.    
2. Evaluation of Retrieved Documents

A lightweight retrieval evaluator is used to assess the relevance of each retrieved document to the user query.    
The evaluator assigns a confidence score to each document, indicating how confident it is in the relevance of the document to the query.
    
3. Action Trigger

Based on the confidence scores, the system categorizes the retrieved documents and decides on the necessary action for each document.    

Correct: If the confidence score of a retrieved document is above a certain threshold, the document is marked as "Correct".    
Incorrect: If the confidence score of a retrieved document is below a certain threshold, the document is marked as "Incorrect".    
Ambiguous: If the confidence score falls between the thresholds for "Correct" and "Incorrect", the document is marked as "Ambiguous".    

4. Handling of Retrieved Documents

Correct Documents: These documents undergo a knowledge refinement process.    

Decomposition: The document is segmented into smaller knowledge strips, typically consisting of a few sentences each.    
Filtering: The retrieval evaluator is used again to assess the relevance of each knowledge strip. Irrelevant strips are discarded.    
Recomposition: The remaining relevant knowledge strips are recombined to form a refined representation of the essential knowledge from the document.    
Incorrect Documents: These documents are discarded, and the system resorts to web searches for additional information.    

Query Rewriting: The user query is rewritten into a form suitable for web searches, typically focusing on keywords.    
Web Search: The system uses a web search API to find web pages related to the rewritten query. Authoritative sources like Wikipedia are preferred.    
Knowledge Selection: The content of the web pages is transcribed, and the knowledge refinement process (decomposition, filtering, and recomposition) is applied to extract the most relevant information.    
Ambiguous Documents: The system combines the refined knowledge from the "Correct" documents and the external knowledge from the web searches to provide a comprehensive set of information for the generator.    

5. Generation of Response

The refined knowledge from the retrieved documents and/or web searches is presented to a generative language model.    
The language model generates a response to the user query based on this knowledge

