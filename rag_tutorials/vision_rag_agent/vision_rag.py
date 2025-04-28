import requests
import os
import io
import base64
import PIL
from PIL import Image
import tqdm
import numpy as np
import streamlit as st
import cohere
from google import genai
import fitz # PyMuPDF

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide", page_title="Vision RAG with Cohere Embed-4")
st.title("Vision RAG with Cohere Embed-4 🖼️")

# --- API Key Input ---
with st.sidebar:
    st.header("🔑 API Keys")
    cohere_api_key = st.text_input("Cohere API Key", type="password", key="cohere_key")
    google_api_key = st.text_input("Google API Key (Gemini)", type="password", key="google_key")
    "[Get a Cohere API key](https://dashboard.cohere.com/api-keys)"
    "[Get a Google API key](https://aistudio.google.com/app/apikey)"

    st.markdown("---")
    if not cohere_api_key:
        st.warning("Please enter your Cohere API key to proceed.")
    if not google_api_key:
        st.warning("Please enter your Google API key to proceed.")
    st.markdown("---")


# --- Initialize API Clients ---
co = None
genai_client = None
# Initialize Session State for embeddings and paths
if 'image_paths' not in st.session_state:
    st.session_state.image_paths = []
if 'doc_embeddings' not in st.session_state:
    st.session_state.doc_embeddings = None

if cohere_api_key and google_api_key:
    try:
        co = cohere.ClientV2(api_key=cohere_api_key)
        st.sidebar.success("Cohere Client Initialized!")
    except Exception as e:
        st.sidebar.error(f"Cohere Initialization Failed: {e}")

    try:
        genai_client = genai.Client(api_key=google_api_key)
        st.sidebar.success("Gemini Client Initialized!")
    except Exception as e:
        st.sidebar.error(f"Gemini Initialization Failed: {e}")
else:
    st.info("Enter your API keys in the sidebar to start.")

# Information about the models
with st.expander("ℹ️ About the models used"):
    st.markdown("""
    ### Cohere Embed-4
    
    Cohere's Embed-4 is a state-of-the-art multimodal embedding model designed for enterprise search and retrieval. 
    It enables:
    
    - **Multimodal search**: Search text and images together seamlessly
    - **High accuracy**: State-of-the-art performance for retrieval tasks
    - **Efficient embedding**: Process complex images like charts, graphs, and infographics
    
    The model processes images without requiring complex OCR pre-processing and maintains the connection between visual elements and text.
    
    ### Google Gemini 2.5 Flash
    
    Gemini 2.5 Flash is Google's efficient multimodal model that can process text and image inputs to generate high-quality responses.
    It's designed for fast inference while maintaining high accuracy, making it ideal for real-time applications like this RAG system.
    """)

# --- Helper functions ---
# Some helper functions to resize images and to convert them to base64 format
max_pixels = 1568*1568  #Max resolution for images

# Resize too large images
def resize_image(pil_image: PIL.Image.Image) -> None:
    """Resizes the image in-place if it exceeds max_pixels."""
    org_width, org_height = pil_image.size

    # Resize image if too large
    if org_width * org_height > max_pixels:
        scale_factor = (max_pixels / (org_width * org_height)) ** 0.5
        new_width = int(org_width * scale_factor)
        new_height = int(org_height * scale_factor)
        pil_image.thumbnail((new_width, new_height))

# Convert images to a base64 string before sending it to the API
def base64_from_image(img_path: str) -> str:
    """Converts an image file to a base64 encoded string."""
    pil_image = PIL.Image.open(img_path)
    img_format = pil_image.format if pil_image.format else "PNG"

    resize_image(pil_image)

    with io.BytesIO() as img_buffer:
        pil_image.save(img_buffer, format=img_format)
        img_buffer.seek(0)
        img_data = f"data:image/{img_format.lower()};base64,"+base64.b64encode(img_buffer.read()).decode("utf-8")

    return img_data

# Convert PIL image to base64 string
def pil_to_base64(pil_image: PIL.Image.Image) -> str:
    """Converts a PIL image to a base64 encoded string."""
    if pil_image.format is None:
        img_format = "PNG"
    else:
        img_format = pil_image.format
    
    resize_image(pil_image)

    with io.BytesIO() as img_buffer:
        pil_image.save(img_buffer, format=img_format)
        img_buffer.seek(0)
        img_data = f"data:image/{img_format.lower()};base64,"+base64.b64encode(img_buffer.read()).decode("utf-8")

    return img_data

# Compute embedding for an image
@st.cache_data(ttl=3600, show_spinner=False)
def compute_image_embedding(base64_img: str, _cohere_client) -> np.ndarray | None:
    """Computes an embedding for an image using Cohere's Embed-4 model."""
    try:
        api_response = _cohere_client.embed(
            model="embed-v4.0",
            input_type="search_document",
            embedding_types=["float"],
            images=[base64_img],
        )
        
        if api_response.embeddings and api_response.embeddings.float:
            return np.asarray(api_response.embeddings.float[0])
        else:
            st.warning("Could not get embedding. API response might be empty.")
            return None
    except Exception as e:
        st.error(f"Error computing embedding: {e}")
        return None

# Process a PDF file: extract pages as images and embed them
# Note: Caching PDF processing might be complex due to potential large file sizes and streams
# We will process it directly for now, but show progress.
def process_pdf_file(pdf_file, cohere_client, base_output_folder="pdf_pages") -> tuple[list[str], list[np.ndarray] | None]:
    """Extracts pages from a PDF as images, embeds them, and saves them.

    Args:
        pdf_file: UploadedFile object from Streamlit.
        cohere_client: Initialized Cohere client.
        base_output_folder: Directory to save page images.

    Returns:
        A tuple containing: 
          - list of paths to the saved page images.
          - list of numpy array embeddings for each page, or None if embedding fails.
    """
    page_image_paths = []
    page_embeddings = []
    pdf_filename = pdf_file.name
    output_folder = os.path.join(base_output_folder, os.path.splitext(pdf_filename)[0])
    os.makedirs(output_folder, exist_ok=True)

    try:
        # Open PDF from stream
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        st.write(f"Processing PDF: {pdf_filename} ({len(doc)} pages)")
        pdf_progress = st.progress(0.0)

        for i, page in enumerate(doc.pages()):
            page_num = i + 1
            page_img_path = os.path.join(output_folder, f"page_{page_num}.png")
            page_image_paths.append(page_img_path)

            # Render page to pixmap (image)
            pix = page.get_pixmap(dpi=150) # Adjust DPI as needed for quality/performance
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Save the page image temporarily
            pil_image.save(page_img_path, "PNG")
            
            # Convert PIL image to base64
            base64_img = pil_to_base64(pil_image)
            
            # Compute embedding for the page image
            emb = compute_image_embedding(base64_img, _cohere_client=cohere_client)
            if emb is not None:
                page_embeddings.append(emb)
            else:
                st.warning(f"Could not embed page {page_num} from {pdf_filename}. Skipping.")
                # Add a placeholder to keep lists aligned, will be filtered later
                page_embeddings.append(None)

            # Update progress
            pdf_progress.progress((i + 1) / len(doc))

        doc.close()
        pdf_progress.empty() # Remove progress bar after completion
        
        # Filter out pages where embedding failed
        valid_paths = [path for i, path in enumerate(page_image_paths) if page_embeddings[i] is not None]
        valid_embeddings = [emb for emb in page_embeddings if emb is not None]
        
        if not valid_embeddings:
             st.error(f"Failed to generate any embeddings for {pdf_filename}.")
             return [], None

        return valid_paths, valid_embeddings

    except Exception as e:
        st.error(f"Error processing PDF {pdf_filename}: {e}")
        return [], None

# Download and embed sample images
@st.cache_data(ttl=3600, show_spinner=False)
def download_and_embed_sample_images(_cohere_client) -> tuple[list[str], np.ndarray | None]:
    """Downloads sample images and computes their embeddings using Cohere's Embed-4 model."""
    # Several images from https://www.appeconomyinsights.com/
    images = {
        "tesla.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbef936e6-3efa-43b3-88d7-7ec620cdb33b_2744x1539.png",
        "netflix.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F23bd84c9-5b62-4526-b467-3088e27e4193_2744x1539.png",
        "nike.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fa5cd33ba-ae1a-42a8-a254-d85e690d9870_2741x1541.png",
        "google.png": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F395dd3b9-b38e-4d1f-91bc-d37b642ee920_2741x1541.png",
        "accenture.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F08b2227c-7dc8-49f7-b3c5-13cab5443ba6_2741x1541.png",
        "tecent.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F0ec8448c-c4d1-4aab-a8e9-2ddebe0c95fd_2741x1541.png"
    }

    # Prepare folders
    img_folder = "img"
    os.makedirs(img_folder, exist_ok=True)

    img_paths = []
    doc_embeddings = []
    
    # Wrap TQDM with st.spinner for better UI integration
    with st.spinner("Downloading and embedding sample images..."):
        pbar = tqdm.tqdm(images.items(), desc="Processing sample images")
        for name, url in pbar:
            img_path = os.path.join(img_folder, name)
            # Don't re-append if already processed (useful if function called multiple times)
            if img_path not in img_paths:
                img_paths.append(img_path)

                # Download the image
                if not os.path.exists(img_path):
                    try:
                        response = requests.get(url)
                        response.raise_for_status()
                        with open(img_path, "wb") as fOut:
                            fOut.write(response.content)
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to download {name}: {e}")
                        # Optionally remove the path if download failed
                        img_paths.pop()
                        continue # Skip if download fails

            # Get embedding for the image if it exists and we haven't computed one yet
            # Find index corresponding to this path
            current_index = -1
            try:
                current_index = img_paths.index(img_path)
            except ValueError:
                continue # Should not happen if append logic is correct

            # Check if embedding already exists for this index
            if current_index >= len(doc_embeddings):
                 try:
                     # Ensure file exists before trying to embed
                     if os.path.exists(img_path):
                         base64_img = base64_from_image(img_path)
                         emb = compute_image_embedding(base64_img, _cohere_client=_cohere_client)
                         if emb is not None:
                             # Placeholder to ensure list length matches paths before vstack
                             while len(doc_embeddings) < current_index:
                                 doc_embeddings.append(None) # Append placeholder if needed
                             doc_embeddings.append(emb)
                     else:
                         # If file doesn't exist (maybe failed download), add placeholder
                         while len(doc_embeddings) < current_index:
                                 doc_embeddings.append(None)
                         doc_embeddings.append(None)
                 except Exception as e:
                     st.error(f"Failed to embed {name}: {e}")
                     # Add placeholder on error
                     while len(doc_embeddings) < current_index:
                             doc_embeddings.append(None)
                     doc_embeddings.append(None)
    
    # Filter out None embeddings and corresponding paths before stacking
    filtered_paths = [path for i, path in enumerate(img_paths) if i < len(doc_embeddings) and doc_embeddings[i] is not None]
    filtered_embeddings = [emb for emb in doc_embeddings if emb is not None]

    if filtered_embeddings:
        doc_embeddings_array = np.vstack(filtered_embeddings)
        return filtered_paths, doc_embeddings_array
        
    return [], None

# Search function
def search(question: str, co_client: cohere.Client, embeddings: np.ndarray, image_paths: list[str], max_img_size: int = 800) -> str | None:
    """Finds the most relevant image path for a given question."""
    if not co_client or embeddings is None or embeddings.size == 0 or not image_paths:
        st.warning("Search prerequisites not met (client, embeddings, or paths missing/empty).")
        return None
    if embeddings.shape[0] != len(image_paths):
         st.error(f"Mismatch between embeddings count ({embeddings.shape[0]}) and image paths count ({len(image_paths)}). Cannot perform search.")
         return None

    try:
        # Compute the embedding for the query
        api_response = co_client.embed(
            model="embed-v4.0",
            input_type="search_query",
            embedding_types=["float"],
            texts=[question],
        )

        if not api_response.embeddings or not api_response.embeddings.float:
            st.error("Failed to get query embedding.")
            return None

        query_emb = np.asarray(api_response.embeddings.float[0])

        # Ensure query embedding has the correct shape for dot product
        if query_emb.shape[0] != embeddings.shape[1]:
            st.error(f"Query embedding dimension ({query_emb.shape[0]}) does not match document embedding dimension ({embeddings.shape[1]}).")
            return None

        # Compute cosine similarities
        cos_sim_scores = np.dot(query_emb, embeddings.T)

        # Get the most relevant image
        top_idx = np.argmax(cos_sim_scores)
        hit_img_path = image_paths[top_idx]
        print(f"Question: {question}") # Keep for debugging
        print(f"Most relevant image: {hit_img_path}") # Keep for debugging

        return hit_img_path
    except Exception as e:
        st.error(f"Error during search: {e}")
        return None

# Answer function
def answer(question: str, img_path: str, gemini_client) -> str:
    """Answers the question based on the provided image using Gemini."""
    if not gemini_client or not img_path or not os.path.exists(img_path):
        missing = []
        if not gemini_client: missing.append("Gemini client")
        if not img_path: missing.append("Image path")
        elif not os.path.exists(img_path): missing.append(f"Image file at {img_path}")
        return f"Answering prerequisites not met ({', '.join(missing)} missing or invalid)."
    try:
        img = PIL.Image.open(img_path)
        prompt = [f"""Answer the question based on the following image. Be as elaborate as possible giving extra relevant information.
Don't use markdown formatting in the response.
Please provide enough context for your answer.

Question: {question}""", img]

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=prompt
        )

        llm_answer = response.text
        print("LLM Answer:", llm_answer) # Keep for debugging
        return llm_answer
    except Exception as e:
        st.error(f"Error during answer generation: {e}")
        return f"Failed to generate answer: {e}"

# --- Main UI Setup ---
st.subheader("📊 Load Sample Images")
if cohere_api_key and co:
    # If button clicked, load sample images into session state
    if st.button("Load Sample Images", key="load_sample_button"):
        sample_img_paths, sample_doc_embeddings = download_and_embed_sample_images(_cohere_client=co)
        if sample_img_paths and sample_doc_embeddings is not None:
            # Append sample images to session state (avoid duplicates if clicked again)
            current_paths = set(st.session_state.image_paths)
            new_paths = [p for p in sample_img_paths if p not in current_paths]
            
            if new_paths:
                new_indices = [i for i, p in enumerate(sample_img_paths) if p in new_paths]
                st.session_state.image_paths.extend(new_paths)
                new_embeddings_to_add = sample_doc_embeddings[[idx for idx, p in enumerate(sample_img_paths) if p in new_paths]]
                
                if st.session_state.doc_embeddings is None or st.session_state.doc_embeddings.size == 0:
                    st.session_state.doc_embeddings = new_embeddings_to_add
                else:
                    st.session_state.doc_embeddings = np.vstack((st.session_state.doc_embeddings, new_embeddings_to_add))
                st.success(f"Loaded {len(new_paths)} sample images.")
            else:
                 st.info("Sample images already loaded.")
        else:
             st.error("Failed to load sample images. Check console for errors.")
else:
     st.warning("Enter API keys to enable loading sample images.")

st.markdown("--- ")
# --- File Uploader (Main UI) ---
st.subheader("📤 Upload Your Images")
st.info("Or, upload your own images or PDFs. The RAG process will search across all loaded content.")

# File uploader
uploaded_files = st.file_uploader("Upload images (PNG, JPG, JPEG) or PDFs", 
                                type=["png", "jpg", "jpeg", "pdf"], 
                                accept_multiple_files=True, key="image_uploader",
                                label_visibility="collapsed")

# Process uploaded images
if uploaded_files and co:
    st.write(f"Processing {len(uploaded_files)} uploaded images...")
    progress_bar = st.progress(0)
    
    # Create a temporary directory for uploaded images
    upload_folder = "uploaded_img"
    os.makedirs(upload_folder, exist_ok=True)
    
    newly_uploaded_paths = []
    newly_uploaded_embeddings = []

    for i, uploaded_file in enumerate(uploaded_files):
        # Check if already processed this session (simple name check)
        img_path = os.path.join(upload_folder, uploaded_file.name)
        if img_path not in st.session_state.image_paths:
            try:
                # Check file type
                file_type = uploaded_file.type
                if file_type == "application/pdf":
                    # Process PDF - returns list of paths and list of embeddings
                    pdf_page_paths, pdf_page_embeddings = process_pdf_file(uploaded_file, cohere_client=co)
                    if pdf_page_paths and pdf_page_embeddings:
                         # Add only paths/embeddings not already in session state
                         current_paths_set = set(st.session_state.image_paths)
                         unique_new_paths = [p for p in pdf_page_paths if p not in current_paths_set]
                         if unique_new_paths:
                             indices_to_add = [i for i, p in enumerate(pdf_page_paths) if p in unique_new_paths]
                             newly_uploaded_paths.extend(unique_new_paths)
                             newly_uploaded_embeddings.extend([pdf_page_embeddings[idx] for idx in indices_to_add])
                elif file_type in ["image/png", "image/jpeg"]:
                    # Process regular image
                    # Save the uploaded file
                    with open(img_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Get embedding
                    base64_img = base64_from_image(img_path)
                    emb = compute_image_embedding(base64_img, _cohere_client=co)
                    
                    if emb is not None:
                        newly_uploaded_paths.append(img_path)
                        newly_uploaded_embeddings.append(emb)
                else:
                     st.warning(f"Unsupported file type skipped: {uploaded_file.name} ({file_type})")

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
        # Update progress regardless of processing status for user feedback
        progress_bar.progress((i + 1) / len(uploaded_files))

    # Add newly processed files to session state
    if newly_uploaded_paths:
        st.session_state.image_paths.extend(newly_uploaded_paths)
        if newly_uploaded_embeddings:
            new_embeddings_array = np.vstack(newly_uploaded_embeddings)
            if st.session_state.doc_embeddings is None or st.session_state.doc_embeddings.size == 0:
                st.session_state.doc_embeddings = new_embeddings_array
            else:
                st.session_state.doc_embeddings = np.vstack((st.session_state.doc_embeddings, new_embeddings_array))
            st.success(f"Successfully processed and added {len(newly_uploaded_paths)} new images.")
        else:
             st.warning("Failed to generate embeddings for newly uploaded images.")
    elif uploaded_files: # If files were selected but none were new
         st.info("Selected images already seem to be processed.")

# --- Vision RAG Section (Main UI) ---
st.markdown("---")
st.subheader("❓ Ask a Question")

if not st.session_state.image_paths:
    st.warning("Please load sample images or upload your own images first.")
else:
    st.info(f"Ready to answer questions about {len(st.session_state.image_paths)} images.")

    # Display thumbnails of all loaded images (optional)
    with st.expander("View Loaded Images", expanded=False):
        if st.session_state.image_paths:
            num_images_to_show = len(st.session_state.image_paths)
            cols = st.columns(5) # Show 5 thumbnails per row
            for i in range(num_images_to_show):
                with cols[i % 5]:
                    # Add try-except for missing files during display
                    try:
                         # Display PDF pages differently? For now, just show the image
                         st.image(st.session_state.image_paths[i], width=100, caption=os.path.basename(st.session_state.image_paths[i]))
                    except FileNotFoundError:
                        st.error(f"Missing: {os.path.basename(st.session_state.image_paths[i])}")
        else:
            st.write("No images loaded yet.")

question = st.text_input("Ask a question about the loaded images:", 
                          key="main_question_input",
                          placeholder="E.g., What is Nike's net profit?",
                          disabled=not st.session_state.image_paths)

run_button = st.button("Run Vision RAG", key="main_run_button", 
                      disabled=not (cohere_api_key and google_api_key and question and st.session_state.image_paths and st.session_state.doc_embeddings is not None and st.session_state.doc_embeddings.size > 0))

# Output Area
st.markdown("### Results")
retrieved_image_placeholder = st.empty()
answer_placeholder = st.empty()

# Run search and answer logic
if run_button:
    if co and genai_client and st.session_state.doc_embeddings is not None and len(st.session_state.doc_embeddings) > 0:
         with st.spinner("Finding relevant image..."):
            # Ensure embeddings and paths match before search
             if len(st.session_state.image_paths) != st.session_state.doc_embeddings.shape[0]:
                 st.error("Error: Mismatch between number of images and embeddings. Cannot proceed.")
             else:
                top_image_path = search(question, co, st.session_state.doc_embeddings, st.session_state.image_paths)

                if top_image_path:
                    caption = f"Retrieved content for: '{question}' (Source: {os.path.basename(top_image_path)})"
                    # Add source PDF name if it's a page image
                    if top_image_path.startswith("pdf_pages/"):
                         parts = top_image_path.split(os.sep)
                         if len(parts) >= 3:
                             pdf_name = parts[1]
                             page_name = parts[-1]
                             caption = f"Retrieved content for: '{question}' (Source: {pdf_name}.pdf, {page_name.replace('.png','')})"

                    retrieved_image_placeholder.image(top_image_path, caption=caption, use_container_width=True)

                    with st.spinner("Generating answer..."):
                        final_answer = answer(question, top_image_path, genai_client)
                        answer_placeholder.markdown(f"**Answer:**\n{final_answer}")
                else:
                    retrieved_image_placeholder.warning("Could not find a relevant image for your question.")
                    answer_placeholder.text("") # Clear answer placeholder
    else:
        # This case should ideally be prevented by the disabled state of the button
        st.error("Cannot run RAG. Check API clients and ensure images are loaded with embeddings.")

# Footer
st.markdown("---")
st.caption("Vision RAG with Cohere Embed-4 | Built with Streamlit, Cohere Embed-4, and Google Gemini 2.5 Flash")