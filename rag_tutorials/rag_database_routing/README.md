# RAG Agent with Database Routing

This project showcases the RAG with database routing capabilities - which is a very efficient way to retrieve information from a large set of documents. The application allows users to:

1. Upload documents to three different databases:
   - Product Information
   - Customer Support & FAQ
   - Financial Information

2. Query information using natural language, with automatic routing to the most relevant database.

## Features

- **Document Upload**: Users can upload multiple PDF documents related to a particular company. These documents are processed and stored in one of the three databases: Product Information, Customer Support & FAQ, or Financial Information.
  
- **Natural Language Querying**: Users can ask questions in natural language. The system automatically routes the query to the most relevant database using a phidata agent as the router.

- **RAG Orchestration**: Utilizes Langchain for orchestrating the retrieval augmented generation process, ensuring that the most relevant information is retrieved and presented to the user.

- **Fallback Mechanism**: If no relevant documents are found in the databases, a LangGraph agent with a DuckDuckGo search tool is used to perform web research and provide an answer.

- **User Interface**: Built with Streamlit, providing an intuitive and interactive user experience.

## How to Run?

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd rag_tutorials/rag_database_routing
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   streamlit run rag_database_routing.py
   ```

4. **Configure API Key**: Obtain an OpenAI API key and set it in the application. This is required for initializing the language models used in the application.

5. **Upload Documents**: Use the document upload section to add PDF documents to the desired database.

6. **Ask Questions**: Enter your questions in the query section. The application will route your question to the appropriate database and provide an answer.

## Technologies Used

- **Langchain**: For RAG orchestration, ensuring efficient retrieval and generation of information.
- **Phidata Agent**: Used as the router agent to determine the most relevant database for a given query.
- **LangGraph Agent**: Acts as a fallback mechanism, utilizing DuckDuckGo for web research when necessary.
- **Streamlit**: Provides a user-friendly interface for document upload and querying.
- **ChromaDB**: Used for managing the databases, storing and retrieving document embeddings efficiently.

This application is designed to streamline the process of retrieving information from large sets of documents, making it easier for users to find the answers they need quickly and efficiently.
