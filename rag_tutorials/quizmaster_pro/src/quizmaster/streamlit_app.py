import streamlit as st
import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import logging # Added import

# Configure logging
logging.basicConfig(level=logging.INFO) # Basic config, can be more sophisticated
logger = logging.getLogger(__name__) # Added logger instance

# Add the src directory to sys.path to allow for absolute imports from quizmaster
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from quizmaster.document_processor import DocumentProcessor
from quizmaster.quiz_generator import QuizGenerator
from quizmaster.database_manager import DatabaseManager
from quizmaster.vector_manager import VectorManager
from quizmaster.config import QuizConfig
from quizmaster.llm_manager import MISTRAL_GGUF_MODEL_ID # Import the GGUF model ID


# Load environment variables
load_dotenv()

def main():
    st.set_page_config(
        page_title="QuizMaster Pro",
        page_icon="📚",
        layout="wide",
        menu_items={
            'about': None,
        }
    )
    
    st.title("📚 QuizMaster Pro")
    st.markdown("Transform any document into an interactive quiz using local AI")

    # Initialize shared QuizConfig in session state if not already present
    if 'shared_quiz_config' not in st.session_state:
        st.session_state.shared_quiz_config = QuizConfig()
    
    shared_config = st.session_state.shared_quiz_config

    # Initialize QuizGenerator
    if 'quiz_generator' not in st.session_state or st.session_state.quiz_generator.config is not shared_config:
        st.session_state.quiz_generator = QuizGenerator(config=shared_config)
    elif st.session_state.quiz_generator.config is not shared_config: # Ensure its config is the shared one
        st.session_state.quiz_generator.config = shared_config
        if hasattr(st.session_state.quiz_generator, 'update_llm_configuration'):
            st.session_state.quiz_generator.update_llm_configuration()


    # Initialize DocumentProcessor
    if 'document_processor' not in st.session_state or st.session_state.document_processor.config is not shared_config:
        st.session_state.document_processor = DocumentProcessor(config=shared_config)
    elif st.session_state.document_processor.config is not shared_config:
        st.session_state.document_processor.config = shared_config
        st.session_state.document_processor.update_llm_configuration() 

    # Initialize VectorManager
    if 'vector_manager' not in st.session_state or st.session_state.vector_manager.config is not shared_config:
        st.session_state.vector_manager = VectorManager(config=shared_config)
    elif st.session_state.vector_manager.config is not shared_config:
        st.session_state.vector_manager.config = shared_config
        st.session_state.vector_manager.update_llm_configuration()


    if 'processed_content' not in st.session_state:
        st.session_state.processed_content = None
    
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
    
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    
    if 'stop_processing' not in st.session_state:
        st.session_state.stop_processing = False

    if 'model_explicitly_applied' not in st.session_state:
        st.session_state.model_explicitly_applied = False
    
    def apply_model_logic(selected_model_name):
        st.session_state.model_explicitly_applied = True # Set the flag here
        st.session_state.quiz_generator.llm_manager.set_model(selected_model_name)
        if hasattr(st.session_state.document_processor, 'update_llm_configuration'):
            st.session_state.document_processor.update_llm_configuration()
        if hasattr(st.session_state.vector_manager, 'update_llm_configuration'):
            st.session_state.vector_manager.update_llm_configuration()
        if hasattr(st.session_state.quiz_generator, 'update_llm_configuration'):
             st.session_state.quiz_generator.update_llm_configuration()

        msg_col1, msg_col2 = st.columns(2) # Keep side-by-side for these messages
        with msg_col1: st.success(f"✅ AI model set to {selected_model_name} for all tasks")
        with msg_col2: st.info(f"🔄 {selected_model_name} will handle document processing and quiz generation.")
    
    with st.sidebar:
        st.page_link("streamlit_app.py", label="Quiz Setup", icon="📝")
        st.page_link("pages/01_Interactive_Quiz.py", label="Interactive Quiz", icon="🎓")
        st.page_link("pages/02_Saved_Quizzes.py", label="Saved Quizzes", icon="💾")
        st.divider()
        st.subheader("🤖 AI Model Selection")
        st.caption("This model will be used for both document processing and quiz generation. Local models are automatically pulled if needed.")

        MODEL_DESCRIPTIONS = {
            "llama3.3:8b": "⭐ Meta's Llama 3.3 (8B) - Strong general-purpose capabilities",
                "mistral:7b": "⭐ Mistral (7B) - Efficient, good for JSON generation (4.1GB)",
                "qwen2.5:7b": "⭐ Qwen 2.5 (7B) - Strong structured output, multilingual (4.4GB)",
                "deepseek-coder:6.7b": "⭐ DeepSeek Coder (6.7B) - Excellent for code-related tasks and structured output",
            "gpt-4o-mini": "⚡ OpenAI: GPT-4o Mini - Fast, cost-effective, optimized for structured output",
            "gpt-4": "⚡ OpenAI: GPT-4 - High-quality, powerful model",
            "gpt-3.5-turbo": "⚡ OpenAI: GPT-3.5 Turbo - Balanced performance and cost",
            MISTRAL_GGUF_MODEL_ID: "⚙️ Local GGUF: Mistral 7B Instruct - Grammar-enforced JSON"
        }
        
        current_model = st.session_state.quiz_generator.llm_manager.get_current_model()
        all_local_ollama_models = st.session_state.quiz_generator.llm_manager.get_local_models() 
        all_available_models = st.session_state.quiz_generator.llm_manager.get_available_models() 
        openai_model_names = st.session_state.quiz_generator.llm_manager.get_openai_models()

        gguf_models_for_display = [m for m in all_available_models if m == MISTRAL_GGUF_MODEL_ID]
        ollama_models_for_display = [
            m for m in all_available_models 
            if m not in openai_model_names and m not in gguf_models_for_display
        ]
        openai_models_for_display = [m for m in all_available_models if m in openai_model_names]

        model_options = []
        model_options.append({
            "name": "##SELECT_MODEL_PLACEHOLDER##", 
            "display": "--- Select a model first ---", 
            "description": "Please choose an AI model to proceed.", 
            "is_placeholder": True
        })
        
        model_options.append({"name": "##OLLAMA_MODELS_HEADER##", "display": "--- Ollama Local Models (Served by Ollama) ---", "description": "Locally hosted models via Ollama.", "is_header": True})
        for model in sorted(ollama_models_for_display):
            status = "📥 Auto-pull needed"
            if model in all_local_ollama_models: 
                status = "✅ Local (Ollama)"
            model_options.append({
                "name": model, "display": f"{model} - {status}",
                "description": MODEL_DESCRIPTIONS.get(model, "No description"), "is_header": False
            })
        
        model_options.append({"name": "##GGUF_MODELS_HEADER##", "display": "--- Local GGUF Models (Direct LlamaCPP) ---", "description": "Locally stored GGUF models accessed directly.", "is_header": True})
        for model in sorted(gguf_models_for_display):
            status = "❓ Check file"
            if st.session_state.quiz_generator.llm_manager.is_model_available(model): 
                status = f"✅ Local (GGUF)"
            else:
                status = f"❌ File Missing ({st.session_state.shared_quiz_config.gguf_model_path})"
            model_options.append({
                "name": model, "display": f"{model} - {status}",
                "description": MODEL_DESCRIPTIONS.get(model, "No description"), "is_header": False
            })

        model_options.append({"name": "##OPENAI_MODELS_HEADER##", "display": "--- OpenAI API Models ---", "description": "Models accessed via OpenAI API (requires API key).", "is_header": True})
        for model in sorted(openai_models_for_display):
            status = "⚡ API"
            if not os.environ.get("OPENAI_API_KEY"):
                status += " (API key missing)"
            model_options.append({
                "name": model, "display": f"{model} - {status}",
                "description": MODEL_DESCRIPTIONS.get(model, "No description"), "is_header": False
            })
        
        initial_model_index = 0 
        if current_model:
            try:
                found_idx = next(i for i, opt in enumerate(model_options) 
                                 if opt["name"] == current_model and 
                                 not opt.get("is_header") and 
                                 not opt.get("is_placeholder"))
                initial_model_index = found_idx
            except StopIteration:
                initial_model_index = 0 

        selected_option_obj = st.selectbox(
            "Select AI Model", model_options,
            format_func=lambda x: x["display"], index=initial_model_index,
            key="unified_model_select", help="This model will be used for both document processing and quiz generation"
        )

        quiz_model = None
        selected_description = ""
        if selected_option_obj.get("is_placeholder"):
            selected_description = selected_option_obj["description"]
            st.info(selected_description)
        elif selected_option_obj.get("is_header"):
            st.warning("Please select an actual model, not a category header.")
            selected_description = "Please select a valid model."
            st.caption(selected_description)
        else:
            quiz_model = selected_option_obj["name"]
            selected_description = selected_option_obj["description"]
            st.caption(selected_description)
            st.info("💡 This model handles both document processing (embedding/concept extraction) and quiz generation automatically.")

        a_model_is_selected = quiz_model is not None
        
        is_openai_model = a_model_is_selected and quiz_model in openai_model_names
        is_gguf_model = a_model_is_selected and quiz_model == MISTRAL_GGUF_MODEL_ID
        is_ollama_served_model = a_model_is_selected and not is_openai_model and not is_gguf_model



        if is_openai_model:
            if st.button("Apply AI Model", key="apply_ai_model_openai", use_container_width=True, disabled=not a_model_is_selected):
                if not os.environ.get("OPENAI_API_KEY"):
                    st.error("OpenAI API key not found in .env file")
                else:
                    with st.spinner(f"Setting up AI model {quiz_model}..."):
                        try:
                            apply_model_logic(quiz_model)
                        except Exception as e: st.error(f"Error setting AI model: {str(e)}")
        
        elif is_ollama_served_model:
            col1_btn, col2_btn = st.columns(2)
            with col1_btn:
                if st.button("Apply AI Model", key="apply_ai_model_ollama", use_container_width=True, disabled=not a_model_is_selected):
                    if not a_model_is_selected: st.stop()
                    with st.spinner(f"Setting up AI model {quiz_model}..."):
                        try:
                            if quiz_model not in all_local_ollama_models:
                                with st.status(f"📥 Downloading {quiz_model} via Ollama...", expanded=True) as status_msg:
                                    status_msg.write("Starting model download...")
                                    success = st.session_state.quiz_generator.llm_manager.pull_model(quiz_model)
                                    if success: status_msg.update(label="✅ Download completed!", state="complete", expanded=False)
                                    else:
                                        status_msg.update(label="❌ Download failed", state="error")
                                        st.error(f"Failed to download {quiz_model} via Ollama.")
                                        st.stop()
                            apply_model_logic(quiz_model)
                        except Exception as e: st.error(f"Error setting Ollama model: {str(e)}")
            with col2_btn:
                if st.button("🔗 Test Ollama Server", key="test_ollama_connection", use_container_width=True, disabled=not a_model_is_selected):
                    if not a_model_is_selected: st.stop()
                    applied_model = st.session_state.quiz_generator.llm_manager.get_current_model()
                    if quiz_model != applied_model:
                        st.error(f"Please click 'Apply AI Model' first to set '{quiz_model}' before testing.")
                    else:
                        with st.spinner("Testing Ollama connection..."):
                            if st.session_state.quiz_generator.llm_manager.test_ollama_connection():
                                st.success("✅ Ollama connection successful!")
                            else:
                                st.error("❌ Ollama connection failed. Make sure Ollama server is running and the model is available.")
        
        elif is_gguf_model:
            if st.button("Apply AI Model", key="apply_ai_model_gguf", use_container_width=True, disabled=not a_model_is_selected):
                if not a_model_is_selected: st.stop()
                with st.spinner(f"Setting up AI model {quiz_model}..."):
                    try:
                        if not st.session_state.quiz_generator.llm_manager.is_model_available(quiz_model):
                            st.error(f"GGUF model file not found: {st.session_state.shared_quiz_config.gguf_model_path}. Please download it using 'download_gguf_model.py'.")
                            st.stop()
                        apply_model_logic(quiz_model)
                    except Exception as e: st.error(f"Error setting GGUF model: {str(e)}")
        
        st.subheader("📋 Quiz Settings")
        num_questions = st.slider("Number of Questions", 1, 20, 5)
        difficulty = st.selectbox(
            "Difficulty Level", 
            ["Easy", "Medium", "Hard"],
            help="Easy: Basic facts, Medium: Understanding, Hard: Analysis"
        )
        
        # Question types dropdown removed as only Multiple Choice remains
        question_types = ["Multiple Choice"]
        
        if st.session_state.processed_content:
            st.subheader("📄 Document Info")
            metadata = st.session_state.processed_content['metadata']
            st.write(f"**File:** {st.session_state.processed_content['filename']}")
            st.write(f"**Format:** {st.session_state.processed_content['format'].upper()}")
            st.write(f"**Words:** {metadata.get('total_words',0):,}") # Safe get
            st.write(f"**Paragraphs:** {metadata.get('total_paragraphs',0)}") # Safe get
            
            if metadata.get('chapters'): # Safe get
                st.write(f"**Chapters:** {len(metadata['chapters'])}")
            if metadata.get('sections'): # Safe get
                st.write(f"**Sections:** {len(metadata['sections'])}")

    # Main content area - Section 1: Document Upload & Processing
    st.header("📤 Document Upload")
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=['pdf', 'docx', 'txt', 'html'],
        help="Supported formats: PDF, DOCX, TXT, HTML"
    )

    if uploaded_file:
        st.success(f"Document '{uploaded_file.name}' uploaded successfully!")
        
        stop_button_placeholder = st.empty()
        progress_bar_placeholder = st.empty()

        if st.button("🔄 Process Document", type="primary", disabled=st.session_state.get('is_processing', False)):
            st.session_state.is_processing = True
            st.session_state.stop_processing = False
            if 'uploaded_file_content' not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
                st.session_state.uploaded_file_content = uploaded_file.read()
                st.session_state.uploaded_file_name = uploaded_file.name
            st.rerun()

        if st.session_state.get('is_processing', False):
            with stop_button_placeholder.container():
                if st.button("⏹️ Stop Processing", key="stop_processing_button"):
                    st.session_state.stop_processing = True
                    st.warning("Stop signal sent. Processing will halt after the current chunk...")
            
            current_progress_bar = progress_bar_placeholder.progress(0)

            def update_progress_callback(chunk_index, total_chunks):
                if total_chunks > 0:
                    progress_value = (chunk_index) / total_chunks 
                    current_progress_bar.progress(progress_value)

            try:
                with st.spinner("Processing document... (this may take a while for large documents)"):
                    if 'uploaded_file_content' not in st.session_state or \
                       st.session_state.uploaded_file_name != uploaded_file.name:
                        st.error("File content not found in session. Please re-upload.")
                        st.session_state.is_processing = False
                        st.rerun()

                    logger.debug(f"DEBUG: Just before processing, shared_config.current_model is: {st.session_state.shared_quiz_config.current_model}")
                    if hasattr(st.session_state.document_processor, 'contextgem_llm') and st.session_state.document_processor.contextgem_llm:
                        logger.debug(f"DEBUG: DP's ContextGem LLM model: {st.session_state.document_processor.contextgem_llm.model}")
                    else:
                        logger.debug("DEBUG: DP's ContextGem LLM is None or not available.")

                    processed_content_result = st.session_state.document_processor.process(
                        st.session_state.uploaded_file_content, 
                        "direct_input",
                        custom_filename=st.session_state.uploaded_file_name,
                        stop_signal_check=lambda: st.session_state.get('stop_processing', False),
                        chunk_processed_callback=update_progress_callback
                    )
                    
                    if st.session_state.stop_processing:
                        st.warning("Processing was stopped by the user.")
                        st.session_state.processed_content = None
                    else:
                        current_progress_bar.progress(1.0)
                        if processed_content_result and isinstance(processed_content_result, dict):
                            try:
                                # Store the document and get the ID
                                doc_id = st.session_state.vector_manager.store_document(processed_content_result)
                                
                                # Add the ID to the processed_content_result
                                if doc_id:
                                    processed_content_result["id"] = doc_id
                                    st.success(f"✅ Document processed and stored! ID: {doc_id[:8]}...")
                                else:
                                    st.error("❌ Failed to get a document ID after storage.")
                                
                                # Now assign the augmented result to session state
                                st.session_state.processed_content = processed_content_result

                            except Exception as e:
                                st.error(f"❌ Error storing document with embeddings/metadata: {str(e)}")
                                # If storage fails, we might still want to keep the processed content (without ID)
                                # or clear it, depending on desired behavior. For now, let's keep it.
                                st.session_state.processed_content = processed_content_result
                                st.info("ℹ️ Document processed, but an error occurred during storage/metadata extraction.")
                        elif processed_content_result: # Not a dict, or some other issue
                            st.warning("Processed content is not in the expected format. Cannot store or retrieve ID.")
                            st.session_state.processed_content = processed_content_result # Store as is
                        else:
                             st.info("No content was processed to store (possibly stopped early or error).")
                             st.session_state.processed_content = None
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}", exc_info=True)
                st.error(f"❌ Error processing document: {str(e)}")
                st.info("💡 Make sure the document is not corrupted and is in a supported format.")
            finally:
                st.session_state.is_processing = False
                stop_button_placeholder.empty()
                progress_bar_placeholder.empty() 
                st.rerun()

    # Document Management Section
    st.header("🗃️ Document Management")
    try:
        stored_docs = st.session_state.vector_manager.list_documents()
        if stored_docs:
            st.subheader("Stored Documents")
            if 'selected_docs' not in st.session_state: st.session_state.selected_docs = {}
            
            for doc in stored_docs:
                doc_key = f"doc_{doc['id']}"
                col_filename, col_status = st.columns([3, 1])
                with col_filename:
                    is_selected = st.checkbox(
                        f"📄 {doc.get('filename', 'Unknown Filename')}", # Safe get
                        value=st.session_state.selected_docs.get(doc_key, False), key=doc_key
                    )
                    st.session_state.selected_docs[doc_key] = is_selected
                with col_status:
                    if 'extracted_summary' in doc and isinstance(doc['extracted_summary'], dict): # Check type
                        summary_data = doc['extracted_summary']
                        status = summary_data.get('extraction_status', 'unknown')
                        concept_count = summary_data.get('concept_count', 0)
                        main_topic_val = summary_data.get('main_topic', 'Unknown')
                        if concept_count > 0 and main_topic_val not in ['Processing...', 'Not processed yet', 'Unknown', '', 'Processing failed', 'No content available']:
                            st.success("✅ Ready")
                        elif status == 'failed' or main_topic_val in ['Processing failed', 'No content available']:
                            st.error("❌ Failed")
                        elif status == 'pending' and main_topic_val in ['Processing...', 'Not processed yet']:
                            st.warning("⏳ Processing")
                        else:
                            if concept_count > 0: st.success("✅ Ready")
                            else: st.info("🔄 Needs processing")
                    else:
                        st.info("🔄 Needs processing")

                with st.expander(f"📋 Details for {doc.get('filename', 'Unknown Filename')}", expanded=False): # Safe get
                    st.write(f"**Document ID:** {doc.get('id', 'N/A')[:12]}...") # Safe get
                    st.write(f"**Format:** {doc.get('format', 'N/A').upper()}") # Safe get
                    created_at_val = doc.get('created_at')
                    st.write(f"**Created:** {created_at_val.strftime('%Y-%m-%d %H:%M') if created_at_val else 'Unknown'}")
                    if 'extracted_summary' in doc and isinstance(doc['extracted_summary'], dict): # Check type
                        summary_data = doc['extracted_summary']
                        st.write(f"**Main Topic:** {summary_data.get('main_topic', 'Not processed yet')}")
                        st.write(f"**Document Type:** {summary_data.get('document_type', 'Unknown')}")
                        st.write(f"**Concepts Extracted:** {summary_data.get('concept_count', 0)}")
                        st.write(f"**Status:** {summary_data.get('extraction_status', 'unknown').title()}")
                    else:
                        st.write("**Status:** No extraction data available")
                st.markdown("---")

            action_col1, action_col2, action_col3 = st.columns(3)
            with action_col1:
                if st.button("Load Selected Documents", type="secondary", use_container_width=True):
                    selected_ids = [doc['id'] for doc in stored_docs if st.session_state.selected_docs.get(f"doc_{doc['id']}", False)]
                    if not selected_ids:
                        st.warning("Please select at least one document")
                    else:
                        try:
                            combined_content = ""
                            combined_metadata = {'chapters': [], 'sections': [], 'total_words': 0, 'total_paragraphs': 0}
                            combined_extracted_concepts = {} 
                            
                            for doc_id in selected_ids:
                                doc_data = st.session_state.vector_manager.get_document(doc_id)
                                if doc_data:
                                    combined_content += doc_data.get('processed_content', '') + "\n\n"
                                    doc_meta = doc_data.get('metadata', {})
                                    combined_metadata['total_words'] += doc_meta.get('total_words', 0)
                                    combined_metadata['total_paragraphs'] += doc_meta.get('total_paragraphs', 0)

                                    # Standardized concept loading logic from VectorManager's stored format
                                    if 'extracted_concepts' in doc_data and doc_data['extracted_concepts']:
                                        stored_concepts_from_db = doc_data['extracted_concepts']
                                        
                                        if isinstance(stored_concepts_from_db, dict):
                                            for concept_group_name, group_data in stored_concepts_from_db.items():
                                                if isinstance(group_data, dict) and "items" in group_data:
                                                    if concept_group_name not in combined_extracted_concepts:
                                                        combined_extracted_concepts[concept_group_name] = {"items": []}
                                                    
                                                    current_combined_items_list = combined_extracted_concepts[concept_group_name]["items"]
                                                    existing_values_in_combined_group = {item.get("value", "") for item in current_combined_items_list}
                                                    
                                                    for item_dict_from_db in group_data.get("items", []):
                                                        item_value = item_dict_from_db.get("value")
                                                        if item_value and item_value.strip() and item_value not in existing_values_in_combined_group:
                                                            current_combined_items_list.append(item_dict_from_db) 
                                                else:
                                                    logger.warning(f"Skipping unexpected structure for concept group '{concept_group_name}' in doc_id {doc_id} from DB.")
                                        # This handles the direct List[Dict] case if st.session_state.processed_content was just set by DocumentProcessor
                                        # and not yet saved/reloaded from VectorManager, or if DB somehow stores a flat list.
                                        elif isinstance(stored_concepts_from_db, list): 
                                            logger.warning(f"Found flat list in extracted_concepts for doc_id {doc_id}. Processing items.")
                                            for concept_item_dict in stored_concepts_from_db:
                                                if isinstance(concept_item_dict, dict):
                                                    actual_concept_group_name = concept_item_dict.get('concept_name', 'Uncategorized List Items')
                                                    content_value = concept_item_dict.get('content')
                                                    if content_value and content_value.strip():
                                                        if actual_concept_group_name not in combined_extracted_concepts:
                                                            combined_extracted_concepts[actual_concept_group_name] = {"items": []}
                                                        current_items_for_group = combined_extracted_concepts[actual_concept_group_name]["items"]
                                                        existing_values_in_group = {item.get("value", "") for item in current_items_for_group}
                                                        if content_value not in existing_values_in_group:
                                                            current_items_for_group.append({
                                                                "value": content_value,
                                                                "references": concept_item_dict.get("references", []), 
                                                                "justification": concept_item_dict.get("metadata", {}).get("extraction_method", "Loaded from flat list")
                                                            })
                                        else:
                                            logger.warning(f"Unexpected type for stored_concepts_from_db: {type(stored_concepts_from_db)} for doc_id {doc_id}")
                            
                            if combined_content.strip():
                                if len(selected_ids) == 1 and doc_data: # doc_data is from the loop, will be the single selected doc
                                    # If only one document was selected, use its specific data
                                    st.session_state.processed_content = {
                                        'id': doc_data.get('id'), # Crucial: Add the ID
                                        'content': doc_data.get('processed_content', ''), # Use original processed content
                                        'filename': doc_data.get('filename', 'Loaded Document'),
                                        'format': doc_data.get('format', 'unknown'),
                                        'metadata': doc_data.get('metadata', {}), # Use original metadata
                                        'extracted_concepts': doc_data.get('extracted_concepts', {}), # Use original concepts
                                        'segments': st.session_state.document_processor.intelligent_segmentation(doc_data.get('processed_content', ''))
                                    }
                                    st.success(f"Loaded document: {doc_data.get('filename', 'ID: ' + str(doc_data.get('id'))[:8])}")
                                else:
                                    # If multiple documents, use combined data (no single ID)
                                    st.session_state.processed_content = {
                                        'content': combined_content.strip(),
                                        'segments': st.session_state.document_processor.intelligent_segmentation(combined_content.strip()),
                                        'metadata': combined_metadata, # Retains combined metadata
                                        'filename': f"{len(selected_ids)} documents loaded",
                                        'format': 'combined',
                                        'extracted_concepts': combined_extracted_concepts
                                        # 'id' is intentionally omitted for multiple documents
                                    }
                                    st.success(f"Loaded and combined {len(selected_ids)} documents.")
                                st.rerun()
                            else:
                                st.warning("No content found in selected documents.")
                        except Exception as e:
                            logger.error(f"Error loading documents: {str(e)}", exc_info=True)
                            st.error(f"Error loading documents: {str(e)}")
            with action_col2:
                if st.button("Delete Selected Documents", type="secondary", use_container_width=True):
                    selected_ids_to_delete = [doc['id'] for doc in stored_docs if st.session_state.selected_docs.get(f"doc_{doc['id']}", False)]
                    if not selected_ids_to_delete:
                        st.warning("Please select documents to delete.")
                    else:
                        try:
                            deleted_count = 0
                            for doc_id_to_delete in selected_ids_to_delete:
                                if st.session_state.vector_manager.delete_document(doc_id_to_delete):
                                    deleted_count +=1
                                    doc_key_to_delete = f"doc_{doc_id_to_delete}"
                                    if doc_key_to_delete in st.session_state.selected_docs:
                                        del st.session_state.selected_docs[doc_key_to_delete]
                            
                            if deleted_count > 0:
                                st.success(f"Successfully deleted {deleted_count} document(s).")
                                # If the currently loaded content was from the deleted docs, clear it
                                if st.session_state.processed_content and \
                                   st.session_state.processed_content.get('filename', '').endswith("documents loaded"):
                                    # This is a heuristic; might need a more robust way to check if loaded content is affected
                                    st.session_state.processed_content = None
                                st.rerun()
                            else:
                                st.warning("No documents were deleted. They might have already been removed or an error occurred.")
                        except Exception as e:
                            logger.error(f"Error deleting documents: {str(e)}", exc_info=True)
                            st.error(f"Error deleting documents: {str(e)}")
            with action_col3:
                if st.button("Clear Selection", type="secondary", use_container_width=True):
                    for doc_key in list(st.session_state.selected_docs.keys()): # Iterate over a copy of keys
                         st.session_state.selected_docs[doc_key] = False
                    st.rerun()
        else:
            st.info("No documents stored yet. Upload and process a document to get started.")
    except Exception as e_list_docs:
        logger.error(f"Error listing stored documents: {str(e_list_docs)}", exc_info=True)
        st.error(f"Could not retrieve stored documents: {str(e_list_docs)}")
        st.session_state.stored_docs = [] # Ensure it's an empty list on error
    finally:
        pass

    # Section 2: Quiz Generation (if document is processed)
    if st.session_state.processed_content:
        st.header("🧠 Quiz Generation")

        # Display extracted concepts for selection
        # The expander is shown if there's processed content.
        # Buttons for regeneration/manual extraction are inside, also conditional on content.
        # Topic display is conditional on having extracted_concepts.
        with st.expander("🎯 Select Topics for Quiz", expanded=True):
            st.markdown("**Manage and select concepts for quiz generation:**")

            # Buttons for regenerating or manually extracting topics
            # These should be available if there's content, even if no topics yet.
            if st.session_state.processed_content and 'content' in st.session_state.processed_content:
                col_regen_actions1, col_regen_actions2 = st.columns(2)
                with col_regen_actions1:
                    if st.button("🔄 Regenerate Main Topics", key="regenerate_topics_button", type="secondary",
                                 help="Re-extract main topics from the document. This will replace current main topics.",
                                 use_container_width=True):
                        try:
                            with st.spinner("Regenerating main topics from document..."):
                                progress_bar_regen = st.progress(0)
                                def regen_progress_callback(current_chunk, total_chunks):
                                    if total_chunks > 0:
                                        progress_bar_regen.progress(current_chunk / total_chunks)

                                content_to_regen = st.session_state.processed_content['content']
                                filename_to_regen = st.session_state.processed_content['filename']
                                format_to_regen = st.session_state.processed_content['format']
                                
                                regenerated_main_topics = None
                                if st.session_state.shared_quiz_config.processing_engine == "llamacpp_gguf":
                                    logger.info("Regenerate Topics: Using LlamaCPP GGUF for main topic extraction.")
                                    st.session_state.document_processor.config.processing_engine = "llamacpp_gguf"
                                    st.session_state.document_processor.update_llm_configuration()
                                    
                                    # Note: _extract_main_topics_llamacpp in DocumentProcessor calls
                                    # ConceptExtractorService.extract_main_topics_llamacpp.
                                    # That service method needs to accept and use the callback.
                                    # For now, assuming it does or will be updated.
                                    regenerated_main_topics = st.session_state.document_processor._extract_main_topics_llamacpp(
                                        content_to_regen, filename_to_regen, format_to_regen,
                                        chunk_processed_callback=regen_progress_callback
                                    )
                                else: # Not GGUF engine
                                    logger.info("Regenerate Topics: GGUF not selected, using general concept extraction for main topics.")
                                    all_concepts_raw = st.session_state.document_processor.extract_concepts(
                                        content_to_regen, filename_to_regen, format_to_regen,
                                        chunk_processed_callback=regen_progress_callback
                                    )
                                    # If all_concepts_raw is populated, and we are in the non-GGUF path,
                                    # we need to populate regenerated_main_topics from it.
                                    if all_concepts_raw:
                                        regenerated_main_topics = []
                                        for item_raw in all_concepts_raw:
                                            if isinstance(item_raw, dict) and item_raw.get("concept_name") == "Main Topic" and item_raw.get("content"):
                                                regenerated_main_topics.append({"content": item_raw.get("content")})
                                            elif isinstance(item_raw, dict) and item_raw.get("content") and "concept_name" not in item_raw:
                                                regenerated_main_topics.append({"content": item_raw.get("content")})
                                
                                progress_bar_regen.progress(1.0) # Ensure it completes, now correctly placed after if/else

                                # This block processes regenerated_main_topics, which could come from either GGUF or other engines
                                if regenerated_main_topics:
                                    formatted_for_session = {"Main Topic": {"items": []}}
                                    for concept_dict in regenerated_main_topics: # concept_dict is like {"content": "value"}
                                        item_val = concept_dict.get("content")
                                        if item_val and not any(d.get("value") == item_val for d in formatted_for_session["Main Topic"]["items"]):
                                            formatted_for_session["Main Topic"]["items"].append({"value": item_val})
                                    
                                    # Merge with existing concepts, replacing "Main Topic"
                                    if 'extracted_concepts' not in st.session_state.processed_content:
                                        st.session_state.processed_content['extracted_concepts'] = {}
                                    st.session_state.processed_content['extracted_concepts']["Main Topic"] = formatted_for_session["Main Topic"]
                                    
                                    try:
                                        doc_id_for_update = st.session_state.processed_content.get("id")
                                        if not doc_id_for_update:
                                            st.error("Could not find document ID in session state. Cannot save regenerated topics.")
                                            return # Or use continue if in a loop, or handle error appropriately

                                        # Use the new VectorManager method to update only the "Main Topic"
                                        # The concepts in session state are the full set, but we only want to pass the updated "Main Topic" part.
                                        main_topic_concepts_to_update = {}
                                        if "Main Topic" in st.session_state.processed_content.get('extracted_concepts', {}):
                                            main_topic_concepts_to_update["Main Topic"] = st.session_state.processed_content['extracted_concepts']["Main Topic"]
                                        
                                        if main_topic_concepts_to_update:
                                            if st.session_state.vector_manager.update_document_concepts(doc_id_for_update, main_topic_concepts_to_update):
                                                st.info("💾 Regenerated main topics saved to database.")
                                            else:
                                                st.error("Failed to save regenerated main topics to the database via VectorManager.")
                                        else:
                                            st.warning("No 'Main Topic' concepts found to update in the session state.")
                                    except Exception as save_error:
                                        logger.error(f"Regenerated main topics extracted but couldn't save to database: {str(save_error)}", exc_info=True)
                                        st.warning(f"Regenerated main topics extracted but couldn't save to database: {str(save_error)}")
                                    
                                    st.success(f"✅ Successfully regenerated {len(formatted_for_session['Main Topic']['items'])} main topics!")
                                    st.rerun()
                                else:
                                    st.warning("No main topics could be regenerated.")
                        except Exception as e_regen:
                            logger.error(f"Error regenerating main topics: {str(e_regen)}", exc_info=True)
                            st.error(f"Error regenerating main topics: {str(e_regen)}")
                
                with col_regen_actions2:
                    if st.button("🔄 Extract All Concepts Manually", type="secondary", key="manual_extract_full",
                                 help="Attempt to extract all concepts from the document. This will merge with existing concepts.",
                                 use_container_width=True):
                        try:
                            with st.spinner("Extracting all concepts from document (manual)..."):
                                content_to_extract = st.session_state.processed_content['content']
                                filename_to_extract = st.session_state.processed_content['filename']
                                format_to_extract = st.session_state.processed_content['format']
                                
                                concepts_manual_raw = st.session_state.document_processor.extract_concepts(
                                    content_to_extract, filename_to_extract, format_to_extract
                                ) # Returns list of dicts: {"concept_name": "Group", "content": "Value"}
                                
                                if concepts_manual_raw:
                                    if 'extracted_concepts' not in st.session_state.processed_content or not st.session_state.processed_content['extracted_concepts']:
                                        st.session_state.processed_content['extracted_concepts'] = {}
                                    
                                    current_extracted_concepts = st.session_state.processed_content['extracted_concepts']
                                    newly_added_count = 0

                                    for concept_dict_manual in concepts_manual_raw:
                                        group = concept_dict_manual.get("concept_name", "Extracted Concepts")
                                        val = concept_dict_manual.get("content")
                                        if val and val.strip():
                                            if group not in current_extracted_concepts:
                                                current_extracted_concepts[group] = {"items": []}
                                            
                                            # Avoid duplicates within the same group
                                            if not any(item.get("value") == val for item in current_extracted_concepts[group]["items"]):
                                                current_extracted_concepts[group]["items"].append({"value": val, "justification": "manual_extract"})
                                                newly_added_count +=1
                                    
                                    if newly_added_count > 0:
                                        try:
                                            doc_hash_manual = hashlib.sha256(content_to_extract.encode()).hexdigest()
                                            st.session_state.vector_manager.db.update_document_concepts(doc_hash_manual, current_extracted_concepts)
                                            st.info("💾 Manually extracted concepts saved and merged into database.")
                                        except Exception as save_err_manual:
                                            st.warning(f"Manually extracted concepts but couldn't save to DB: {save_err_manual}")
                                        st.success(f"✅ Successfully extracted and merged {newly_added_count} new concepts manually!")
                                        st.rerun()
                                    else:
                                        st.info("No new unique concepts were extracted manually to add.")
                                else:
                                    st.warning("No concepts could be extracted manually.")
                        except Exception as e_manual:
                            st.error(f"Error during manual concept extraction: {str(e_manual)}")
                st.markdown("---") # Separator after action buttons

            # Display existing concepts for selection
            if 'selected_concepts' not in st.session_state: st.session_state.selected_concepts = []
            
            concept_groups_for_display = st.session_state.processed_content.get('extracted_concepts') # Safely get
            
            if concept_groups_for_display and isinstance(concept_groups_for_display, dict):
                st.markdown("**Select concepts to focus on:**")
                col1_select, col2_select = st.columns(2)
                with col1_select:
                    main_topic_key_for_button = "Main Topic"
                    concepts_for_select_all_button = []
                    if isinstance(concept_groups_for_display.get(main_topic_key_for_button), dict):
                        concepts_for_select_all_button = [
                            item.get("value") for item in concept_groups_for_display[main_topic_key_for_button].get("items", []) if item.get("value")
                        ]
                    if st.button("Select All Main Topics", key="select_all_main_topics_btn",
                                 disabled=not bool(concepts_for_select_all_button), use_container_width=True):
                        st.session_state.selected_concepts = list(set(st.session_state.selected_concepts + concepts_for_select_all_button))
                        st.rerun()
                with col2_select:
                    if st.button("Deselect All", key="deselect_all_concepts", use_container_width=True):
                        st.session_state.selected_concepts = []
                        st.rerun()
                
                st.markdown("---")
                
                display_order = ["Main Topic"] + [k for k in concept_groups_for_display.keys() if k != "Main Topic"]
                
                # Define concept groups to exclude from UI selection for quiz generation
                excluded_ui_concept_groups = ["Document Type", "Important Fact", "Key Definition", "Technical Terms", "Key People", "Key Organizations", "Locations", "Key Dates", "Key Figures"]

                for concept_group_name in display_order:
                    if concept_group_name in concept_groups_for_display and concept_group_name not in excluded_ui_concept_groups:
                        group_data = concept_groups_for_display[concept_group_name]
                        if isinstance(group_data, dict) and "items" in group_data and group_data["items"]:
                            st.markdown(f"**{concept_group_name}:**")
                            for i, item_dict in enumerate(group_data["items"]):
                                concept_value = item_dict.get("value")
                                if concept_value and concept_value.strip():
                                    is_selected_concept = concept_value in st.session_state.selected_concepts
                                    if st.checkbox(concept_value, value=is_selected_concept, key=f"concept_{concept_group_name}_{i}_{concept_value[:20]}"):
                                        if concept_value not in st.session_state.selected_concepts:
                                            st.session_state.selected_concepts.append(concept_value)
                                    else:
                                        if concept_value in st.session_state.selected_concepts:
                                            st.session_state.selected_concepts.remove(concept_value)
                            st.markdown("")
                
                if st.session_state.selected_concepts:
                    st.success(f"✅ Selected {len(st.session_state.selected_concepts)} concepts for quiz focus")
                    with st.container(): # Use a container for better layout control
                        st.markdown("**📝 Selected Concepts:**")
                        for concept_val in st.session_state.selected_concepts:
                            st.write(f"• {concept_val}")
                else:
                    st.info("💡 No specific concepts selected - quiz will cover all available topics from the document.")
            else: # No concept_groups_for_display or not a dict
                st.info("No specific concepts extracted or loaded yet. You can try regenerating main topics or manually extracting all concepts using the buttons above.")
        
        with st.expander("👀 Content Preview"):
            if st.session_state.processed_content and 'content' in st.session_state.processed_content:
                preview_content = st.session_state.processed_content['content']
                st.text_area("Document Content", preview_content, height=300, disabled=True)
            else:
                st.info("No document processed yet.")

        # Generate Quiz button
        if st.button("🚀 Generate Quiz", type="primary",
                      disabled=(not st.session_state.processed_content or
                                not st.session_state.get("model_explicitly_applied", False))):
            if not question_types:
                st.warning("Please select at least one question type.")
            else:
                quiz_params = {
                    "num_questions": num_questions,
                    "difficulty": difficulty.lower(),
                    "question_types": [qt.lower().replace(" ", "_").replace("-", "_") for qt in question_types],
                    "focus_topics": st.session_state.get('selected_concepts', []) # Renamed for clarity to match QuizGenerator
                }
                try:
                    with st.spinner("Generating quiz questions... This may take a moment."):
                        # Call generate_quiz with named arguments matching its signature
                        quiz_result_dict = st.session_state.quiz_generator.generate_quiz(
                            processed_content=st.session_state.processed_content,
                            question_types=quiz_params["question_types"],
                            num_questions=quiz_params["num_questions"],
                            difficulty=quiz_params["difficulty"],
                            focus_topics=quiz_params["focus_topics"]
                        )
                    
                    # quiz_result_dict is expected to be the dictionary returned by QuizResult.to_dict()
                    if quiz_result_dict and quiz_result_dict.get("questions"):
                        st.session_state.quiz_data = quiz_result_dict # This now contains questions, metadata (with generation_stats), etc.
                        st.session_state.quiz_data['title'] = f"Quiz on: {st.session_state.processed_content.get('filename', 'Processed Document')}"
                        st.session_state.quiz_data['config'] = quiz_params # Store the input params for reference
                        st.session_state.quiz_data['config_difficulty'] = difficulty # Add explicit difficulty field
                        # generation_info is now part of quiz_result_dict['metadata']['generation_stats']
                        # No need to assign it separately if st.session_state.quiz_data is the full result.
                        st.session_state.quiz_data['timestamp'] = datetime.now().isoformat()
                        
                        # Navigate to Interactive Quiz page
                        st.success(f"✅ Generated {len(st.session_state.quiz_data['questions'])} questions!")
                        st.info("Switching to 'Interactive Quiz' page...")
                        time.sleep(1) # Brief pause for user to see message
                        st.switch_page("pages/01_Interactive_Quiz.py")
                    else:
                        st.error("❌ Failed to generate quiz. No questions were returned.")
                        # Attempt to display generation stats if available in the result
                        if quiz_result_dict and 'metadata' in quiz_result_dict and 'generation_stats' in quiz_result_dict['metadata']:
                            with st.expander("ℹ️ Generation Info", expanded=True):
                                st.json(quiz_result_dict['metadata']['generation_stats'])
                        elif st.session_state.get('quiz_data') and 'metadata' in st.session_state.quiz_data and 'generation_stats' in st.session_state.quiz_data['metadata']:
                            # Fallback to session state if quiz_result_dict was not directly available here but was set
                            with st.expander("ℹ️ Generation Info", expanded=True):
                                st.json(st.session_state.quiz_data['metadata']['generation_stats'])
                except Exception as e:
                    logger.error(f"Error generating quiz: {str(e)}", exc_info=True)
                    st.error(f"Error generating quiz: {str(e)}")
                    st.info("💡 Try selecting fewer concepts or a less complex document if issues persist.")

if __name__ == "__main__":
    main()
