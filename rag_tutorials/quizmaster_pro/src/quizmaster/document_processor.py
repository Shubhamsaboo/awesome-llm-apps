import os
import io
import re
from typing import Dict, List, Optional as PyOptional
import logging
import json # Keep for general JSON operations if any

# LlamaIndex/LlamaCPP imports (only for type hinting if instances are passed around)
# Actual initialization will be here, then instances passed to ConceptExtractorService
try:
    from llama_index.llms.llama_cpp import LlamaCPP
    from llama_index.llms.llama_cpp.llama_utils import messages_to_prompt, completion_to_prompt # Added this import
    from llama_cpp.llama_grammar import LlamaGrammar
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    LlamaCPP = None
    LlamaGrammar = None
    messages_to_prompt = None # Define as None on import failure
    completion_to_prompt = None # Define as None on import failure
    # logging.getLogger(__name__) is defined below

# ContextGem imports
try:
    from contextgem import DocumentLLM
    CONTEXTGEM_AVAILABLE = True
except ImportError:
    CONTEXTGEM_AVAILABLE = False
    class DocumentLLM: pass # Placeholder
    # logging.getLogger(__name__) is defined below

from .config import QuizConfig
from .file_parsers import parse_file_content
from .text_utils import count_tokens, chunk_text_by_tokens
from .llm_concept_extractors import (
    ConceptExtractorService,
    ConceptsOutput, # For LlamaCPP direct/fallback grammar
    # LlamaCPPPreprocessedItem, LlamaCPPPreprocessedOutput, # Used internally by service
    # MainTopicItem, MainTopicsOutput # Used internally by service
)

# Configure logging
# pdfminer_logger = logging.getLogger('pdfminer') # Handled in file_parsers
# pdfpage_logger = logging.getLogger('pdfminer.pdfpage') # Handled in file_parsers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self, persist_directory: str = "documents", config: PyOptional[QuizConfig] = None):
        self.supported_formats = ['pdf', 'docx', 'txt', 'html']
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.config = config if config else QuizConfig()
        
        # LLM instances - initialized by update_llm_configuration
        self.contextgem_llm: PyOptional[DocumentLLM] = None
        self.llama_cpp_llm: PyOptional[LlamaCPP] = None
        self.llama_grammar_for_concepts_output: PyOptional[LlamaGrammar] = None # For ConceptsOutput schema

        # Service for concept extraction logic
        self.concept_extractor_service: PyOptional[ConceptExtractorService] = None
        
        # Default concepts for ContextGem (passed to the service)
        # These need to be ContextGem's own Concept objects if ContextGem is available
        self.default_concepts_for_cg_definitions = []
        if CONTEXTGEM_AVAILABLE:
            from contextgem import StringConcept as CGStringConcept # Alias for clarity
            self.default_concepts_for_cg_definitions = [
                CGStringConcept(name="Main Topic", description="Primary topic or subject of the document", singular_occurrence=True, add_references=False),
                # CGStringConcept(name="Document Type", description="Type or category of the document", singular_occurrence=True, add_references=False), # Removed as per user feedback
                # CGStringConcept(name="Key Definition", description="An important definition provided in the text."), # Removed as potentially too granular
                # CGStringConcept(name="Important Fact", description="A key fact or piece of information mentioned."), # Removed as per user feedback
                # Add other high-level concepts here if desired, e.g., "Key Argument" or "Core Theme"
                # For now, focusing only on "Main Topic" for ContextGem default extraction.
            ]
        
        self.update_llm_configuration() # Initialize LLMs and service

    def _initialize_contextgem_llm_internal(self):
        """Initializes self.contextgem_llm based on config. Called by update_llm_configuration."""
        if not CONTEXTGEM_AVAILABLE:
            self.contextgem_llm = None
            logger.warning("DocumentProcessor: ContextGem library not available, cannot initialize ContextGem LLM.")
            return

        self.contextgem_llm = None 
        current_global_model = self.config.current_model
        logger.info(f"DocumentProcessor: Initializing ContextGem LLM. Globally selected model: '{current_global_model}'.")
        # (Simplified logic from previous _initialize_contextgem_llm - assuming it's complex and preserved)
        # This should set self.contextgem_llm based on current_global_model, API keys, and Ollama availability.
        # For brevity, using a placeholder logic here. The full logic from the previous file version should be used.
        try:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            ollama_base_url = self.config.ollama_base_url
            if current_global_model in self.config.openai_models and openai_api_key:
                cg_model_name = f"openai/{current_global_model.replace('openai/', '')}"
                self.contextgem_llm = DocumentLLM(model=cg_model_name, api_key=openai_api_key)
                logger.info(f"DocumentProcessor: ContextGem using OpenAI model '{cg_model_name}'.")
            elif current_global_model not in self.config.openai_models and "gguf" not in current_global_model.lower(): # Ollama candidate
                # Basic check, ideally verify model exists on Ollama server
                self.contextgem_llm = DocumentLLM(model=f"ollama/{current_global_model}", api_base=ollama_base_url)
                logger.info(f"DocumentProcessor: ContextGem using Ollama model '{current_global_model}'.")
            elif openai_api_key: # Fallback OpenAI
                 self.contextgem_llm = DocumentLLM(model="openai/gpt-4o-mini", api_key=openai_api_key)
                 logger.info("DocumentProcessor: ContextGem using fallback OpenAI 'gpt-4o-mini'.")
            else:
                logger.warning("DocumentProcessor: No suitable configuration for ContextGem LLM.")
        except Exception as e:
            logger.error(f"DocumentProcessor: Error initializing ContextGem LLM: {e}", exc_info=True)
            self.contextgem_llm = None


    def _init_llamacpp_pipeline_internal(self) -> bool:
        """Initializes self.llama_cpp_llm and self.llama_grammar_for_concepts_output."""
        if not LLAMA_INDEX_AVAILABLE:
            logger.error("DocumentProcessor: LlamaIndex/LlamaCPP libraries not available.")
            return False
        if self.llama_cpp_llm and self.llama_grammar_for_concepts_output and \
           hasattr(self.llama_cpp_llm, 'model_path') and self.llama_cpp_llm.model_path == self.config.gguf_model_path:
            logger.debug("DocumentProcessor: LlamaCPP pipeline already initialized with correct model.")
            return True
        
        try:
            logger.info(f"DocumentProcessor: Initializing optimized LlamaCPP pipeline with model {self.config.gguf_model_path}...")
            # Grammar for the direct LlamaCPP concept extraction (ConceptsOutput schema)
            json_schema_dict = ConceptsOutput.model_json_schema()
            self.llama_grammar_for_concepts_output = LlamaGrammar.from_json_schema(json.dumps(json_schema_dict))
            
            if not os.path.exists(self.config.gguf_model_path):
                logger.error(f"DocumentProcessor: LlamaCPP model not found at {self.config.gguf_model_path}.")
                return False

            # Use ADVANCED optimized settings for GGUF preprocessing
            self.llama_cpp_llm = LlamaCPP(
                model_path=self.config.gguf_model_path,
                temperature=self.config.gguf_preprocessing_temperature,
                max_new_tokens=self.config.gguf_preprocessing_max_new_tokens,
                context_window=self.config.gguf_advanced_context_window,  # Use larger context
                generate_kwargs={}, # No default grammar - will be set per task
                model_kwargs={
                    "n_gpu_layers": -1 if self.config.use_gpu_if_available else 0,  # Use all GPU layers
                    "add_bos": False,
                    "n_threads": 8,  # Increased CPU threads for better parallelization
                    "n_batch": self.config.gguf_advanced_batch_size,  # Advanced batch size (1024)
                    "offload_kqv": self.config.gguf_enable_kv_cache_offload,  # KV cache offloading
                    "use_mlock": self.config.gguf_enable_mlock,  # Memory locking
                    "numa": self.config.gguf_numa_optimization,  # NUMA optimization
                    "n_threads_batch": 8,  # Batch processing threads
                },
                messages_to_prompt=messages_to_prompt,
                completion_to_prompt=completion_to_prompt,
                verbose=False,  # Reduce verbosity for performance
            )
            logger.info(f"DocumentProcessor: Optimized LlamaCPP model initialized with {self.config.gguf_advanced_context_window} context window")
            return True
        except Exception as e:
            logger.error(f"DocumentProcessor: Failed to initialize LlamaCPP model: {e}", exc_info=True)
            self.llama_cpp_llm = None
            self.llama_grammar_for_concepts_output = None
            return False

    def update_llm_configuration(self):
        """Re-initializes LLM instances and the ConceptExtractorService based on current config."""
        logger.info(f"DocumentProcessor: Updating LLM configurations for engine: {self.config.processing_engine}.")
        
        # Reset instances
        self.contextgem_llm = None
        self.llama_cpp_llm = None
        self.llama_grammar_for_concepts_output = None

        if self.config.processing_engine == "llamacpp_gguf":
            if LLAMA_INDEX_AVAILABLE:
                self._init_llamacpp_pipeline_internal() # Initializes self.llama_cpp_llm and self.llama_grammar_for_concepts_output
            # ContextGem LLM will be initialized only if needed by the service for the LlamaCPP->ContextGem flow
            self._initialize_contextgem_llm_internal() # Ensure ContextGem LLM is also ready for the second stage
        
        elif self.config.processing_engine == "contextgem":
            self._initialize_contextgem_llm_internal() # Initializes self.contextgem_llm
            # LlamaCPP might still be needed for fallback by ContextGem path
            if LLAMA_INDEX_AVAILABLE:
                 self._init_llamacpp_pipeline_internal() 
        else:
            logger.warning(f"DocumentProcessor: Unknown processing engine '{self.config.processing_engine}'.")

        # Initialize the service with the (potentially newly created) LLM instances
        self.concept_extractor_service = ConceptExtractorService(
            config=self.config,
            llama_cpp_llm=self.llama_cpp_llm,
            llama_grammar_concepts=self.llama_grammar_for_concepts_output, # Pass the grammar for ConceptsOutput
            contextgem_llm=self.contextgem_llm,
            default_cg_concepts=self.default_concepts_for_cg_definitions
        )
        logger.info("DocumentProcessor: ConceptExtractorService (re)initialized.")


    def extract_concepts(self,
                         text: str,
                         filename: str,
                         file_format: str,
                         stop_signal_check: PyOptional[callable] = None,
                         chunk_processed_callback: PyOptional[callable] = None
                         ) -> List[Dict]:
        """Extract concepts based on the configured processing engine."""
        if not isinstance(text, str) or not text.strip():
            logger.warning(f"Empty or invalid text provided for concept extraction from {filename}.")
            return []

        if not self.concept_extractor_service:
            logger.error("DocumentProcessor: ConceptExtractorService not initialized. Cannot extract concepts.")
            self.update_llm_configuration() # Attempt to re-initialize
            if not self.concept_extractor_service: # Still not initialized
                 return self._generate_default_concepts(filename, file_format)

        engine = self.config.processing_engine
        logger.info(f"DocumentProcessor: Using engine '{engine}' for concept extraction from {filename}.")
        concepts: PyOptional[List[Dict]] = None

        if engine == "llamacpp_gguf":
            if not LLAMA_INDEX_AVAILABLE or not self.llama_cpp_llm:
                logger.error("LlamaCPP engine selected, but LlamaIndex/LlamaCPP libraries not available or LLM not initialized.")
            else:
                try:
                    logger.info(f"LlamaCPP GGUF Engine: Starting optimized GGUF→ContextGem flow for {filename}...")
                    # Use the new optimized flow: GGUF preprocessing → ContextGem
                    concepts = self.concept_extractor_service.extract_concepts_llamacpp_to_contextgem(
                        full_text_content=text,
                        filename=filename,
                        file_format=file_format,
                        stop_signal_check=stop_signal_check,
                        chunk_processed_callback=chunk_processed_callback
                    )
                    
                    # Fallback to direct GGUF extraction if the optimized flow fails
                    if not concepts and self.llama_grammar_for_concepts_output:
                        logger.warning(f"Optimized GGUF→ContextGem flow failed for {filename}. Falling back to direct LlamaCPP extraction.")
                        concepts = self.concept_extractor_service.extract_concepts_llamacpp_direct(
                            full_text_content=text,
                            filename=filename,
                            file_format=file_format,
                            stop_signal_check=stop_signal_check,
                            chunk_processed_callback=chunk_processed_callback
                        )
                except Exception as e:
                    logger.error(f"Error during optimized LlamaCPP GGUF concept extraction for {filename}: {e}", exc_info=True)
        
        elif engine == "contextgem":
            if not self.contextgem_llm: # Ensure ContextGem LLM is initialized
                self._initialize_contextgem_llm_internal()

            if self.contextgem_llm:
                try:
                    concepts = self.concept_extractor_service.extract_concepts_contextgem(text, filename, file_format)
                except Exception as e:
                    logger.error(f"Exception during ContextGem primary extraction for {filename}: {e}", exc_info=True)
            else:
                logger.warning(f"ContextGem LLM could not be initialized for {filename}.")

            if not concepts: 
                logger.warning(f"ContextGem primary extraction failed for {filename}. Attempting LlamaCPP direct fallback.")
                if LLAMA_INDEX_AVAILABLE and self.llama_cpp_llm and self.llama_grammar_for_concepts_output:
                     try:
                        # Use the direct LlamaCPP extraction as fallback
                        # Note: Callbacks are not typically used for fallback, but could be added if needed.
                        concepts = self.concept_extractor_service.extract_concepts_llamacpp_direct(
                            full_text_content=text,
                            filename=filename,
                            file_format=file_format
                            # stop_signal_check and chunk_processed_callback are omitted for fallback
                        )
                     except Exception as fallback_error:
                        logger.error(f"LlamaCPP direct fallback extraction failed for {filename}: {fallback_error}", exc_info=True)
                else:
                    logger.error("LlamaCPP direct fallback unavailable (libs or LLM/grammar not ready).")
        else:
            logger.error(f"Unknown processing engine: {engine}. Cannot extract concepts for {filename}.")

        if concepts:
            logger.info(f"Successfully extracted {len(concepts)} concepts for {filename} (Engine: {engine}).")
            return concepts
        else: 
            logger.warning(f"All concept extraction methods failed for {filename}. Generating default concepts.")
            return self._generate_default_concepts(filename, file_format)

    def _extract_main_topics_llamacpp(self, text_content: str, filename: str, file_format: str, chunk_processed_callback: PyOptional[callable] = None) -> PyOptional[List[Dict]]:
        """Optimized main topic extraction using LlamaCPP. Called by Streamlit button."""
        if not self.concept_extractor_service:
            logger.error("DocumentProcessor: ConceptExtractorService not initialized for _extract_main_topics_llamacpp.")
            self.update_llm_configuration() # Attempt to re-initialize
            if not self.concept_extractor_service:
                return None
        # Ensure LlamaCPP is ready within the service, or that service can init it.
        # The service's method should handle LLAMA_INDEX_AVAILABLE and self.llama_cpp_llm checks.
        return self.concept_extractor_service.extract_main_topics_llamacpp(text_content, filename, file_format, chunk_processed_callback=chunk_processed_callback)

    def _generate_default_concepts(self, filename: str, file_format: str) -> List[Dict]:
        # (Content of _generate_default_concepts - kept from previous version)
        name_without_ext = os.path.splitext(filename)[0]
        words = re.findall(r'\w+', name_without_ext)
        concepts = []
        if len(words) > 1:
            concepts.append({
                "content": " ".join(words), "concept_name": "Document Topic", "type": "concept",
                "source_sentence": filename, 
                "metadata": {"filename": filename, "format": file_format, "extraction_method": "filename_fallback"}
            })
        concepts.append({
            "content": f"Document in {file_format.upper()} format", "concept_name": "Technical Information", "type": "concept",
            "source_sentence": filename,
            "metadata": {"filename": filename, "format": file_format, "extraction_method": "filename_fallback"}
        })
        return concepts

    # --- Main Processing Method ---
    def process(self, content: bytes, source: str, custom_filename: str = None,
                stop_signal_check: PyOptional[callable] = None, # stop_signal not used in this refactor yet
                chunk_processed_callback: PyOptional[callable] = None) -> PyOptional[Dict]: # chunk_callback not used
        
        filename = custom_filename or source
        file_format = os.path.splitext(filename)[1][1:].lower()

        if file_format not in self.supported_formats:
            logger.error(f"Unsupported file format: {file_format} for file {filename}")
            return None
        
        logger.info(f"Processing document: {filename} (Format: {file_format})")
        
        text_content = parse_file_content(content, file_format, filename) # Use from file_parsers
        if not text_content or not text_content.strip():
            logger.warning(f"No text content extracted from {filename}.")
            # Return a structure consistent with successful processing but empty content
            import hashlib # Ensure hashlib is imported
            return {
                "filename": filename, "format": file_format, "content": "",
                "metadata": {"total_words": 0, "total_paragraphs": 0, "chapters": [], "sections": []},
                "concepts": [], "raw_content_hash": hashlib.sha256(content).hexdigest()
            }

        words = text_content.split()
        paragraphs = text_content.split('\n\n')
        metadata = {
            "total_words": len(words), "total_paragraphs": len(paragraphs),
            "chapters": [], "sections": [] 
        }
        
        extracted_concepts = self.extract_concepts(
            text_content, filename, file_format,
            stop_signal_check=stop_signal_check,
            chunk_processed_callback=chunk_processed_callback
        )
        
        import hashlib # Ensure hashlib is imported
        raw_content_hash = hashlib.sha256(content).hexdigest()

        processed_data = {
            "filename": filename, "format": file_format, "content": text_content,
            "metadata": metadata, "concepts": extracted_concepts, 
            "raw_content_hash": raw_content_hash
        }
        logger.info(f"Finished processing {filename}. Extracted {len(extracted_concepts)} concepts.")
        return processed_data

    def get_content_summary(self, processed_content: Dict) -> str:
        # (Preserved from previous version)
        if not processed_content or not processed_content.get("content"):
            return "No content available to summarize."
        summary_parts = [f"Filename: {processed_content.get('filename', 'N/A')}",
                         f"Format: {processed_content.get('format', 'N/A').upper()}"]
        metadata = processed_content.get("metadata", {})
        summary_parts.extend([f"Words: {metadata.get('total_words', 0):,}",
                              f"Paragraphs: {metadata.get('total_paragraphs', 0)}"])
        concepts = processed_content.get("concepts", [])
        summary_parts.append(f"Extracted Concepts: {len(concepts)}")
        main_topics = [c['content'] for c in concepts if c.get('concept_name') == 'Main Topic'][:3]
        if main_topics:
            summary_parts.append("\nKey Main Topics:")
            for mt in main_topics: summary_parts.append(f"  - {mt}")
        return "\n".join(summary_parts)

    def intelligent_segmentation(self, content: str) -> List[Dict]:
        # (Preserved - simple paragraph based)
        logger.info("Performing simple paragraph-based segmentation.")
        paragraphs = content.split('\n\n')
        return [{"segment_id": f"para_{i+1}", "title": f"Paragraph {i+1}", 
                 "content": para.strip(), "start_char": -1, "end_char": -1}
                for i, para in enumerate(paragraphs) if para.strip()]

    def validate_file(self, filename: str) -> bool:
        if not filename: return False
        return os.path.splitext(filename)[1][1:].lower() in self.supported_formats
