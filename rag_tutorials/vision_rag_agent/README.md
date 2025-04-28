# Vision RAG with Cohere Embed-4 🖼️

A powerful visual Retrieval-Augmented Generation (RAG) system that utilizes Cohere's state-of-the-art Embed-4 model for multimodal embedding and Google's efficient Gemini 2.5 Flash model for answering questions about images.

## Features

- **Multimodal Search**: Leverages Cohere Embed-4 to find the most semantically relevant image for a given text question.
- **Visual Question Answering**: Employs Google Gemini 2.5 Flash to analyze the content of the retrieved image and generate accurate, context-aware answers.
- **Flexible Image Sources**: 
    - Use pre-loaded sample financial charts and infographics.
    - Upload your own custom images (PNG, JPG, JPEG).
- **No OCR Required**: Directly processes complex images like charts, graphs, and infographics without needing separate text extraction steps.
- **Interactive UI**: Built with Streamlit for easy interaction, including image loading, question input, and result display.
- **Session Management**: Remembers loaded/uploaded images within a session.

## Requirements

- Python 3.8+
- Cohere API key
- Google Gemini API key

## How to Run

Follow these steps to set up and run the application:

1.  **Clone and Navigate to Directory** :
    ```bash
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd awesome-llm-apps/rag_tutorials/vision_rag_agent
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your API keys**:
    - Get a Cohere API key from: [https://dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)
    - Get a Google API key from: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

4.  **Run the Streamlit app**:
    ```bash
    streamlit run vision_rag.py
    ```

5.  **Access the Web Interface**:
    - Streamlit will provide a local URL (usually `http://localhost:8501`) in your terminal.
    - Open this URL in your web browser.

## How It Works

The application follows a two-stage RAG process:

1.  **Retrieval**: 
    - When you load sample images or upload your own, each image is converted to a base64 string.
    - Cohere's `embed-v4.0` model (with `input_type="search_document"`) is used to generate a dense vector embedding for each image.
    - When you ask a question, the text query is embedded using the same `embed-v4.0` model (with `input_type="search_query"`).
    - Cosine similarity is calculated between the question embedding and all image embeddings.
    - The image with the highest similarity score is retrieved as the most relevant context.

2.  **Generation**:
    - The original text question and the retrieved image are passed as input to the Google `gemini-2.5-flash-preview-04-17` model.
    - Gemini analyzes the image content in the context of the question and generates a textual answer.

## Usage

1.  Enter your Cohere and Google API keys in the sidebar.
2.  Load images:
    - Click **"Load Sample Images"** to download and process the built-in examples.
    - *OR/AND* Use the **"Upload Your Images"** section to upload your own image files.
3.  Once images are loaded and processed (embeddings generated), the **"Ask a Question"** section will be enabled.
4.  Optionally, expand **"View Loaded Images"** to see thumbnails of all images currently in the session.
5.  Type your question about the loaded images into the text input field.
6.  Click **"Run Vision RAG"**.
7.  View the results:
    - The **Retrieved Image** deemed most relevant to your question.
    - The **Generated Answer** from Gemini based on the image and question.

## Use Cases

- Analyze financial charts and extract key figures or trends.
- Answer specific questions about diagrams, flowcharts, or infographics.
- Extract information from tables or text within screenshots without explicit OCR.
- Build and query visual knowledge bases using natural language.
- Understand the content of various complex visual documents.

## Note

- Image processing (embedding) can take time, especially for many or large images. Sample images are cached after the first load.
- Ensure your API keys have the necessary permissions and quotas for the Cohere and Gemini models used.
- The quality of the answer depends on both the relevance of the retrieved image and the capability of the Gemini model to interpret the image based on the question.
