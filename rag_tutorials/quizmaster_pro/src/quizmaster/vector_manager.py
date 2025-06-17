import os
import json
import re
import hashlib
from typing import Dict, List, Optional as PyOptional, Union
import logging
from pathlib import Path
import requests

from .config import QuizConfig
from .database_manager import DatabaseManager

# Pydantic Schemas for LlamaCPP output
from pydantic import BaseModel, Field

# LlamaIndex and LlamaCPP imports
try:
    from llama_index.llms.llama_cpp import LlamaCPP
    from llama_index.llms.llama_cpp.llama_utils import messages_to_prompt, completion_to_prompt
    from llama_cpp.llama_grammar import LlamaGrammar
    LLAMA_INDEX_AVAILABLE_VM = True
except ImportError:
    LLAMA_INDEX_AVAILABLE_VM = False
    LlamaCPP = None 
    LlamaGrammar = None
    messages_to_prompt = None
    completion_to_prompt = None
    logging.getLogger(__name__).warning(
        "VectorManager: LlamaIndex/LlamaCPP libraries not available. "
        "LlamaCPP functionality for VectorManager will be disabled."
    )

# ContextGem imports
try:
    from contextgem import (
        Document as ContextGemInternalDocument, # Alias to avoid conflict with any other Document
        DocumentLLM,
        Aspect,
        StringConcept,
        JsonObjectConcept, # Keep if used by self.simple_pipeline
        DateConcept,
        NumericalConcept,
        BooleanConcept,
        DocumentPipeline
    )
    CONTEXTGEM_AVAILABLE = True
    logging.getLogger(__name__).info("ContextGem library loaded successfully for VectorManager.")
except ImportError as e:
    CONTEXTGEM_AVAILABLE = False
    # Define placeholders if ContextGem is not available to avoid NameErrors on class attributes
    class DocumentLLM: pass 
    class DocumentPipeline: pass
    class Aspect: pass
    class StringConcept: pass
    class JsonObjectConcept: pass
    class DateConcept: pass
    class NumericalConcept: pass
    class BooleanConcept: pass
    logging.getLogger(__name__).error(f"VectorManager: ContextGem not available: {e}. ContextGem features disabled.")


logger = logging.getLogger(__name__)

# --- Pydantic Schemas for VectorManager's LlamaCPP Output ---
class VMTopic(BaseModel):
    topic: str = Field(..., description="A key topic extracted from the document.")
    # relevance: PyOptional[str] = Field(None, description="Optional relevance score, e.g., High, Medium, Low")

class VMSummaryAndTopics(BaseModel):
    document_summary: str = Field(..., description="A concise summary of the document.")
    key_topics: List[VMTopic] = Field(..., description="A list of key topics.")

class VectorManager:
    """Manages storage, retrieval, and ContextGem/LlamaCPP-based metadata extraction for documents."""
    
    def __init__(self, config: PyOptional[QuizConfig] = None):
        self.db = DatabaseManager()
        self.config = config if config else QuizConfig()
        
        self.contextgem_llm: PyOptional[DocumentLLM] = None # For ContextGem operations
        self.contextgem_pipeline: PyOptional[DocumentPipeline] = None # Defined by _setup_extraction_pipeline

        self.llama_cpp_llm_vm: PyOptional[LlamaCPP] = None # For LlamaCPP operations
        self.llama_grammar_vm: PyOptional[LlamaGrammar] = None
        self.llama_cpp_model_path = self.config.gguf_model_path # Set from global config

        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.warning("VectorManager: Failed to get tiktoken cl100k_base encoding. Using gpt-3.5-turbo as fallback.")
            try:
                self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            except Exception:
                logger.error("VectorManager: Failed to get any tiktoken encoding. Token counting will be char-based.")
                self.encoding = None
        
        self._create_enhanced_documents_table()
        if CONTEXTGEM_AVAILABLE:
            self._setup_extraction_pipeline() # Defines self.contextgem_pipeline
        
        self.update_llm_configuration() # Initial call to set up LLMs based on config

    def update_llm_configuration(self):
        """Re-initializes LLM instances based on current config's processing_engine."""
        if not self.config:
            logger.warning("VectorManager: No config set; LLM configuration update skipped.")
            return

        logger.info(f"VectorManager: Updating LLM configurations for engine: {self.config.processing_engine}.")
        self.llama_cpp_model_path = self.config.gguf_model_path # Ensure path is current

        if self.config.processing_engine == "llamacpp_gguf":
            logger.info("VectorManager: Engine is LlamaCPP GGUF.")
            self.contextgem_llm = None # Clear ContextGem LLM for generative tasks
            logger.info("VectorManager: ContextGem LLM (self.contextgem_llm) cleared for generative tasks.")
            if LLAMA_INDEX_AVAILABLE_VM:
                logger.info("VectorManager: Initializing LlamaCPP pipeline for its own tasks.")
                self.llama_cpp_llm_vm = None 
                self.llama_grammar_vm = None
                self._init_llamacpp_pipeline_for_vm()
            else:
                logger.error("VectorManager: LlamaCPP GGUF engine selected, but LlamaIndex/LlamaCPP libraries not available.")
        
        elif self.config.processing_engine == "contextgem":
            logger.info("VectorManager: Engine is ContextGem.")
            if CONTEXTGEM_AVAILABLE:
                self._initialize_contextgem() # This sets self.contextgem_llm
            else:
                logger.warning("VectorManager: ContextGem engine selected, but ContextGem library not available.")
                self.contextgem_llm = None
            self.llama_cpp_llm_vm = None # Clear LlamaCPP if switching to ContextGem
            self.llama_grammar_vm = None
            logger.info("VectorManager: LlamaCPP pipeline (for VM) cleared as ContextGem is the engine.")
        else:
            logger.warning(f"VectorManager: Unknown processing engine '{self.config.processing_engine}'. No LLM configured.")
            self.contextgem_llm = None
            self.llama_cpp_llm_vm = None
            self.llama_grammar_vm = None

    def _initialize_contextgem(self):
        """Initializes ContextGem DocumentLLM instance for 'contextgem' engine."""
        if not CONTEXTGEM_AVAILABLE:
            self.contextgem_llm = None
            logger.warning("VectorManager: ContextGem library not available, cannot initialize ContextGem LLM.")
            return

        self.contextgem_llm = None 
        current_global_model = self.config.current_model
        logger.info(f"VectorManager: Initializing ContextGem LLM. Globally selected model: '{current_global_model}'.")

        try:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            ollama_base_url = self.config.ollama_base_url

            if current_global_model in self.config.openai_models:
                if openai_api_key:
                    cg_model_name = f"openai/{current_global_model.replace('openai/', '')}"
                    self.contextgem_llm = DocumentLLM(model=cg_model_name, api_key=openai_api_key)
                    logger.info(f"VectorManager: ContextGem using globally selected OpenAI model '{cg_model_name}'.")
                    return
                else:
                    logger.warning(f"VectorManager: Globally selected OpenAI model '{current_global_model}' but OPENAI_API_KEY missing.")
            
            is_ollama_candidate = current_global_model not in self.config.openai_models and "gguf" not in current_global_model.lower()
            if is_ollama_candidate:
                try:
                    requests.get(f"{ollama_base_url}/api/tags", timeout=2).raise_for_status()
                    # A more robust check would involve LLMManager.get_local_models() to see if current_global_model is truly available
                    logger.info(f"VectorManager: Attempting to use globally selected Ollama model '{current_global_model}' for ContextGem.")
                    self.contextgem_llm = DocumentLLM(model=f"ollama/{current_global_model}", api_base=ollama_base_url)
                    logger.info(f"VectorManager: ContextGem using globally selected Ollama model '{current_global_model}'.")
                    return
                except Exception as e:
                    logger.warning(f"VectorManager: Failed to use globally selected Ollama model '{current_global_model}' for ContextGem: {e}. Trying preferred.")

            # Fallback to preferred Ollama models
            try:
                response = requests.get(f"{ollama_base_url}/api/tags", timeout=2)
                if response.status_code == 200:
                    available_ollama_models = [m['name'] for m in response.json().get('models', [])]
                    preferred_ollama = ["mistral:7b", "qwen2.5:7b", "llama3.3:8b"]
                    for model in preferred_ollama:
                        if model in available_ollama_models:
                            self.contextgem_llm = DocumentLLM(model=f"ollama/{model}", api_base=ollama_base_url)
                            logger.info(f"VectorManager: ContextGem using preferred Ollama model '{model}'.")
                            return
                    if available_ollama_models: # Pick first available if no preferred found
                        self.contextgem_llm = DocumentLLM(model=f"ollama/{available_ollama_models[0]}", api_base=ollama_base_url)
                        logger.info(f"VectorManager: ContextGem using first available Ollama model '{available_ollama_models[0]}'.")
                        return
            except Exception as e:
                logger.info(f"VectorManager: Ollama not available or error selecting default model for ContextGem: {e}")

            if openai_api_key and not self.contextgem_llm: # Final fallback to OpenAI default
                self.contextgem_llm = DocumentLLM(model="openai/gpt-4o-mini", api_key=openai_api_key)
                logger.info("VectorManager: ContextGem using fallback OpenAI model 'gpt-4o-mini'.")
                return
            
            logger.warning("VectorManager: ContextGem LLM could not be initialized with any suitable model.")
        except Exception as e:
            logger.error(f"VectorManager: General failure during ContextGem LLM initialization: {e}", exc_info=True)
            self.contextgem_llm = None
            
    def _init_llamacpp_pipeline_for_vm(self) -> bool:
        """Initializes the LlamaCPP model and grammar for VectorManager's tasks."""
        if not LLAMA_INDEX_AVAILABLE_VM:
            logger.error("VectorManager: LlamaIndex/LlamaCPP libraries not available.")
            return False
        if self.llama_cpp_llm_vm and self.llama_grammar_vm and \
           hasattr(self.llama_cpp_llm_vm, 'model_path') and self.llama_cpp_llm_vm.model_path == self.config.gguf_model_path:
            logger.debug("VectorManager: LlamaCPP pipeline for VM already initialized with the correct model path.")
            return True
        
        try:
            logger.info("VectorManager: Initializing LlamaCPP pipeline for VM tasks...")
            json_schema_dict_vm = VMSummaryAndTopics.model_json_schema()
            json_schema_str_vm = json.dumps(json_schema_dict_vm)
            self.llama_grammar_vm = LlamaGrammar.from_json_schema(json_schema_str_vm)
            
            current_gguf_path = self.config.gguf_model_path 
            if not os.path.exists(current_gguf_path):
                logger.error(f"VectorManager: LlamaCPP model not found at {current_gguf_path}.")
                self.llama_grammar_vm = None 
                self.llama_cpp_llm_vm = None
                return False

            self.llama_cpp_llm_vm = LlamaCPP(
                model_path=current_gguf_path,
                temperature=0.2,
                max_new_tokens=1024,
                context_window=self.config.gguf_advanced_context_window,  # Use proper context window
                generate_kwargs={},  # Don't set grammar by default
                model_kwargs={
                    "n_gpu_layers": -1 if self.config.use_gpu_if_available else 0,
                    "n_batch": self.config.gguf_advanced_batch_size,
                    "offload_kqv": self.config.gguf_enable_kv_cache_offload,
                    "use_mlock": self.config.gguf_enable_mlock,
                    "numa": self.config.gguf_numa_optimization,
                },
                messages_to_prompt=messages_to_prompt,
                completion_to_prompt=completion_to_prompt,
                verbose=False,  # Reduce verbosity for performance
            )
            logger.info(f"VectorManager: LlamaCPP model for VM initialized: {current_gguf_path}")
            return True
        except Exception as e:
            logger.error(f"VectorManager: Failed to initialize LlamaCPP model for VM: {e}", exc_info=True)
            self.llama_cpp_llm_vm = None
            self.llama_grammar_vm = None
            return False

    def _create_enhanced_documents_table(self):
        # (Content of _create_enhanced_documents_table from previous version)
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents_enhanced (
                        id TEXT PRIMARY KEY, filename TEXT, format TEXT,
                        raw_content TEXT, processed_content TEXT,
                        extracted_concepts JSONB, extracted_aspects JSONB, metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ) ''')
                # Indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_enhanced_filename ON documents_enhanced(filename)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_enhanced_format ON documents_enhanced(format)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_enhanced_concepts ON documents_enhanced USING GIN (extracted_concepts)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_enhanced_aspects ON documents_enhanced USING GIN (extracted_aspects)')
            conn.commit()

    def _setup_extraction_pipeline(self):
        """Setup ContextGem extraction pipeline for document processing."""
        if not CONTEXTGEM_AVAILABLE: return
        # (Content of _setup_extraction_pipeline from previous version)
        self.default_concepts = [
            StringConcept(name="Main Topic", description="Primary topic or subject of the document", singular_occurrence=True, add_references=False),
            StringConcept(name="Document Type", description="Type or category of the document", singular_occurrence=True, add_references=False),
            StringConcept(name="Key Arguments", description="Main arguments or theses presented", singular_occurrence=False, add_references=False),
            StringConcept(name="Conclusions", description="Main conclusions or outcomes reported", singular_occurrence=False, add_references=False),
            StringConcept(name="Technical Terms", description="Specific technical terms or jargon used", singular_occurrence=False, add_references=False),
            StringConcept(name="Key People", description="Important individuals mentioned", singular_occurrence=False, add_references=False),
            StringConcept(name="Key Organizations", description="Important organizations or entities mentioned", singular_occurrence=False, add_references=False),
            StringConcept(name="Locations", description="Geographical places mentioned", singular_occurrence=False, add_references=False),
            DateConcept(name="Key Dates", description="Significant dates or time periods mentioned", singular_occurrence=False, add_references=False),
            NumericalConcept(name="Key Figures", description="Important numbers or statistics presented", singular_occurrence=False, add_references=False)
        ]
        self.contextgem_pipeline = DocumentPipeline()
        key_info_concepts = [
            StringConcept(name="Key Topics", description="Main topics covered", add_references=False, singular_occurrence=False),
            StringConcept(name="Summary Points", description="Brief summary points", add_references=False, singular_occurrence=False)
        ]
        for concept in self.default_concepts:
            if concept.name in ["Key Arguments", "Conclusions", "Technical Terms"]:
                key_info_concepts.append(StringConcept(name=concept.name, description=concept.description, add_references=False, singular_occurrence=False))

        self.contextgem_pipeline.aspects = [
            Aspect(name="Key Information", description="Core informational content", concepts=key_info_concepts),
            Aspect(name="Contextual Elements", description="People, places, organizations", concepts=[
                StringConcept(name="Mentioned People", description="Individuals discussed"),
                StringConcept(name="Mentioned Organizations", description="Entities discussed"),
                StringConcept(name="Mentioned Locations", description="Places discussed")
            ]),
            Aspect(name="Document Purpose", description="Intended purpose and audience", concepts=[
                StringConcept(name="Stated Purpose", description="Explicit or implicit purpose"),
                StringConcept(name="Target Audience", description="Intended audience")
            ])
        ]
        
    def _count_tokens_for_chunking(self, text: str) -> int:
        """Helper for token counting, prioritizing self.encoding."""
        if self.encoding and text:
            try: return len(self.encoding.encode(text))
            except: pass # Fallback if encoding fails for some reason
        return len(text) // 3 # Rough char-based fallback

    def _chunk_text_for_llamacpp(self, text: str) -> List[str]:
        """Chunks text for LlamaCPP, aiming for ~1500 tokens per chunk."""
        LLAMACPP_CHUNK_TARGET_TOKENS = 1500
        if not text: return []
        
        # Simple split by paragraphs first, then join paragraphs into larger chunks
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk_paras = []
        current_token_estimate = 0
        for para in paragraphs:
            para_token_estimate = self._count_tokens_for_chunking(para)
            if current_token_estimate + para_token_estimate > LLAMACPP_CHUNK_TARGET_TOKENS and current_chunk_paras:
                chunks.append("\n\n".join(current_chunk_paras))
                current_chunk_paras = []
                current_token_estimate = 0
            current_chunk_paras.append(para)
            current_token_estimate += para_token_estimate
        if current_chunk_paras: chunks.append("\n\n".join(current_chunk_paras))
        
        return chunks if chunks else [text] # Ensure at least one chunk if text is not empty

    def _extract_summary_and_topics_llamacpp(self, text_content: str, filename: str) -> Dict:
        """Uses LlamaCPP to extract summary and key topics."""
        if not self.llama_cpp_llm_vm or not self.llama_grammar_vm:
            if not self._init_llamacpp_pipeline_for_vm():
                logger.error(f"VectorManager: LlamaCPP pipeline for VM not initialized. Cannot extract summary/topics for {filename}.")
                return {"summary": "Extraction failed: LlamaCPP pipeline not available.", "topics": []}

        text_chunks = self._chunk_text_for_llamacpp(text_content)
        if not text_chunks:
            logger.warning(f"VectorManager: No text chunks to process with LlamaCPP for {filename}.")
            return {"summary": "No content to process.", "topics": []}

        aggregated_summary_parts = []
        aggregated_topics = []
        processed_chunk_count = 0

        for i, chunk in enumerate(text_chunks):
            logger.info(f"VectorManager: Processing LlamaCPP chunk {i+1}/{len(text_chunks)} for summary/topics of {filename}...")
            prompt = f"[INST] From the following text, provide a concise summary and list 3-5 main, high-level key topics that represent the core themes of the document. Avoid overly specific details or individual facts as topics.\nText:\n{chunk}\n[/INST]"
            try:
                self.llama_cpp_llm_vm.generate_kwargs["grammar"] = self.llama_grammar_vm
                response = self.llama_cpp_llm_vm.complete(prompt)
                parsed_output = VMSummaryAndTopics.parse_raw(response.text)
                
                if parsed_output.document_summary:
                    aggregated_summary_parts.append(parsed_output.document_summary)
                if parsed_output.key_topics:
                    aggregated_topics.extend(parsed_output.key_topics)
                processed_chunk_count +=1
            except Exception as e:
                logger.error(f"VectorManager: Error processing LlamaCPP chunk {i+1} for {filename}: {e}", exc_info=True)
        
        final_summary = " ".join(aggregated_summary_parts) if aggregated_summary_parts else "Summary could not be generated."
        # Deduplicate topics (simple deduplication by topic string)
        unique_topics = []
        seen_topic_strings = set()
        for vm_topic in aggregated_topics:
            if vm_topic.topic not in seen_topic_strings:
                unique_topics.append({"topic": vm_topic.topic}) # Store as simple dict
                seen_topic_strings.add(vm_topic.topic)

        logger.info(f"VectorManager: LlamaCPP extracted summary and {len(unique_topics)} unique topics from {processed_chunk_count} chunks for {filename}.")
        return {"summary": final_summary, "topics": unique_topics}

    def store_document(self, processed_doc: Dict) -> str:
        """Store document with metadata extraction in PostgreSQL."""
        content = processed_doc.get("content", "")
        filename = processed_doc.get("filename", "Unknown Filename")
        file_format = processed_doc.get("format", "unknown")
        doc_id = processed_doc.get("raw_content_hash") # Use pre-calculated hash

        if not doc_id: # Fallback if hash not provided
            doc_id = hashlib.sha256(content.encode('utf-8', 'replace')).hexdigest()

        logger.info(f"VectorManager: Storing document {filename} (ID: {doc_id[:8]}...). Engine: {self.config.processing_engine}")

        # Initial DB insert with minimal data (concepts/aspects will be updated later)
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO documents_enhanced 
                           (id, filename, format, raw_content, processed_content, metadata, extracted_concepts, extracted_aspects, updated_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                           ON CONFLICT (id) DO UPDATE SET
                           filename = EXCLUDED.filename, format = EXCLUDED.format, raw_content = EXCLUDED.raw_content,
                           processed_content = EXCLUDED.processed_content, metadata = EXCLUDED.metadata, 
                           updated_at = CURRENT_TIMESTAMP""",
                        (doc_id, filename, file_format, processed_doc.get("original_content", content), content, 
                         json.dumps(processed_doc.get("metadata", {})), json.dumps({}), json.dumps({}))
                    )
                conn.commit()
            logger.info(f"VectorManager: Initial database store for {filename} (ID: {doc_id[:8]}) successful.")
        except Exception as e:
            logger.error(f"VectorManager: Failed initial database store for {filename} (ID: {doc_id[:8]}): {e}", exc_info=True)
            raise ConnectionError(f"Failed to store document: {e}")

        # --- Metadata Extraction (Summary, Topics/Aspects) ---
        extracted_concepts_json = {}
        extracted_aspects_json = {} # For ContextGem aspects or LlamaCPP summary

        # Standardized format for extracted_concepts_json: {"Concept Name": {"items": [{"value": "...", "justification": "..."}]}}
        
        # 1. Process concepts from DocumentProcessor (if any)
        if "concepts" in processed_doc and processed_doc["concepts"]:
            logger.info(f"VectorManager: Processing {len(processed_doc['concepts'])} concepts from DocumentProcessor for {filename}.")
            for concept_item_dict in processed_doc["concepts"]: # These are List[Dict]
                actual_concept_name = concept_item_dict.get('concept_name', 'Uncategorized DP Concepts')
                content_value = concept_item_dict.get('content')
                if content_value and content_value.strip():
                    if actual_concept_name not in extracted_concepts_json:
                        extracted_concepts_json[actual_concept_name] = {"items": []}
                    
                    current_items = extracted_concepts_json[actual_concept_name]["items"]
                    # Avoid duplicates based on 'value'
                    if not any(item.get("value") == content_value for item in current_items):
                        current_items.append({
                            "value": content_value,
                            "references": concept_item_dict.get("references", []), # Preserve if available
                            "justification": concept_item_dict.get("metadata", {}).get("extraction_method", "doc_processor")
                        })

        # 2. Perform additional extraction based on engine (for VectorManager's own summary/topics)
        if self.config.processing_engine == "llamacpp_gguf":
            if LLAMA_INDEX_AVAILABLE_VM:
                logger.info(f"VectorManager: Using LlamaCPP GGUF for additional summary/topic extraction for {filename}.")
                llamacpp_output = self._extract_summary_and_topics_llamacpp(content, filename) # Returns {"summary": ..., "topics": [{"topic": ...}]}
                if llamacpp_output:
                    if llamacpp_output.get("summary"):
                        extracted_aspects_json["OverallSummary_LlamaCPP"] = {"summary_text": llamacpp_output.get("summary")}
                    
                    llamacpp_topics = llamacpp_output.get("topics", [])
                    if llamacpp_topics:
                        group_name = "Key Topics (GGUF)"
                        if group_name not in extracted_concepts_json:
                            extracted_concepts_json[group_name] = {"items": []}
                        current_items = extracted_concepts_json[group_name]["items"]
                        existing_values = {item.get("value") for item in current_items}
                        for topic_item in llamacpp_topics: # topic_item is {"topic": "..."}
                            topic_value = topic_item.get("topic")
                            if topic_value and topic_value.strip() and topic_value not in existing_values:
                                current_items.append({"value": topic_value, "justification": "vm_llamacpp_topic"})
            else:
                logger.error("VectorManager: LlamaCPP GGUF engine selected, but LlamaIndex/LlamaCPP libraries not available. Skipping VM LlamaCPP extraction.")
        
        elif self.config.processing_engine == "contextgem":
            if CONTEXTGEM_AVAILABLE and self.contextgem_llm and self.contextgem_pipeline:
                logger.info(f"VectorManager: Using ContextGem pipeline for aspect/concept extraction for {filename}.")
                try:
                    cg_doc_internal = ContextGemInternalDocument(raw_text=content)
                    # The pipeline aspects are added to the document, and then concepts are extracted.
                    # The `extract_concepts_from_document` method modifies cg_doc_internal in place.
                    if self.contextgem_pipeline and hasattr(self.contextgem_pipeline, 'aspects'):
                        cg_doc_internal.add_aspects(self.contextgem_pipeline.aspects) # Add aspects defined in the pipeline
                    
                    # This call modifies cg_doc_internal by extracting concepts based on its defined aspects and any globally added concepts.
                    self.contextgem_llm.extract_concepts_from_document(cg_doc_internal)
                    
                    # Process aspects from ContextGem (which are now populated in cg_doc_internal)
                    if hasattr(cg_doc_internal, 'aspects') and cg_doc_internal.aspects:
                        for aspect_obj in cg_doc_internal.aspects:
                            aspect_items_for_json = []
                            if hasattr(aspect_obj, 'concepts') and aspect_obj.concepts:
                                for concept_obj_in_aspect in aspect_obj.concepts:
                                    if hasattr(concept_obj_in_aspect, 'extracted_items') and concept_obj_in_aspect.extracted_items:
                                        for item in concept_obj_in_aspect.extracted_items:
                                            item_value = getattr(item, 'value', str(item))
                                            if item_value and str(item_value).strip():
                                                aspect_items_for_json.append({"value": str(item_value), "source_concept": concept_obj_in_aspect.name})
                            if aspect_items_for_json:
                                extracted_aspects_json[aspect_obj.name] = {"items": aspect_items_for_json}

                    # Process concepts from ContextGem (these are usually what's defined in self.default_concepts)
                    if hasattr(cg_doc_internal, 'concepts') and cg_doc_internal.concepts:
                         for concept_obj in cg_doc_internal.concepts: # These are the top-level concepts added via cg_doc.add_concepts()
                            concept_group_name = concept_obj.name or "Uncategorized CG"
                            if hasattr(concept_obj, 'extracted_items') and concept_obj.extracted_items:
                                if concept_group_name not in extracted_concepts_json:
                                    extracted_concepts_json[concept_group_name] = {"items": []}
                                current_items = extracted_concepts_json[concept_group_name]["items"]
                                existing_values = {item.get("value") for item in current_items}
                                for item in concept_obj.extracted_items:
                                    item_value = getattr(item, 'value', str(item))
                                    if item_value and str(item_value).strip() and item_value not in existing_values:
                                        current_items.append({"value": str(item_value), "justification": "vm_contextgem"})
                except Exception as e:
                    logger.error(f"VectorManager: ContextGem pipeline extraction failed for {filename}: {e}", exc_info=True)
            else:
                logger.warning(f"VectorManager: ContextGem not available or LLM/pipeline not set up. Skipping ContextGem pipeline extraction for {filename}.")

        # Update DB with extracted metadata
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """UPDATE documents_enhanced SET 
                           extracted_concepts = %s, extracted_aspects = %s, updated_at = CURRENT_TIMESTAMP
                           WHERE id = %s""",
                        (json.dumps(extracted_concepts_json), json.dumps(extracted_aspects_json), doc_id)
                    )
                conn.commit()
            logger.info(f"VectorManager: Successfully updated {filename} (ID: {doc_id[:8]}) with extracted metadata.")
        except Exception as e:
            logger.error(f"VectorManager: Failed to update {filename} (ID: {doc_id[:8]}) with extracted metadata: {e}", exc_info=True)
            
        return doc_id

    # ... (rest of the methods: list_documents, get_document, delete_document, etc. remain largely unchanged)
    # Need to ensure they correctly query and present data from `extracted_concepts` and `extracted_aspects`
    
    def list_documents(self) -> List[Dict]:
        """List all stored documents with metadata and extraction summaries"""
        # (Content of list_documents from previous version, adapted for new JSON structure)
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, filename, format, metadata, extracted_concepts, extracted_aspects, created_at FROM documents_enhanced ORDER BY created_at DESC")
                docs = []
                for row in cursor.fetchall():
                    doc_dict = dict(zip([desc[0] for desc in cursor.description], row))
                    # Create a simple summary for display
                    summary_display = {}
                    if doc_dict.get('extracted_aspects'):
                        try:
                            aspects = doc_dict['extracted_aspects'] # Already JSONB from DB
                            if "OverallSummary_LlamaCPP" in aspects and aspects["OverallSummary_LlamaCPP"].get("summary_text"):
                                summary_display['main_topic'] = aspects["OverallSummary_LlamaCPP"]["summary_text"][:100] + "..." # Show part of summary
                            elif "Key Information" in aspects and aspects["Key Information"].get("items"):
                                summary_display['main_topic'] = aspects["Key Information"]["items"][0]['value'][:100] + "..."
                        except Exception: pass # Ignore parsing errors for summary display
                    
                    if doc_dict.get('extracted_concepts'):
                        try:
                            concepts = doc_dict['extracted_concepts']
                            gguf_topics_key = "Key Topics (GGUF)"
                            
                            if gguf_topics_key in concepts and isinstance(concepts[gguf_topics_key], dict) and concepts[gguf_topics_key].get("items"):
                                items = concepts[gguf_topics_key]["items"]
                                summary_display['concept_count'] = len(items)
                                if not summary_display.get('main_topic') and items:
                                    # Ensure 'value' exists and is not None before trying to access it
                                    first_item_value = items[0].get('value')
                                    if first_item_value:
                                        summary_display['main_topic'] = str(first_item_value) # Ensure it's a string
                            else:
                                # Fallback: Iterate over other concepts to find a main topic and count
                                all_concept_items_count = 0
                                found_main_topic_fallback = False
                                # Define concept groups to exclude from being considered as the 'main_topic'
                                excluded_concept_groups_for_main_topic = ["Document Type", "Key Arguments", "Conclusions", "Technical Terms", "Key People", "Key Organizations", "Locations", "Key Dates", "Key Figures"]
                                
                                for concept_group_name, concept_group_data in concepts.items():
                                    if isinstance(concept_group_data, dict) and "items" in concept_group_data:
                                        current_items = concept_group_data["items"]
                                        if isinstance(current_items, list):
                                            all_concept_items_count += len(current_items)
                                            # Check if this concept group should be considered for the main_topic
                                            if not summary_display.get('main_topic') and \
                                               not found_main_topic_fallback and \
                                               current_items and \
                                               concept_group_name not in excluded_concept_groups_for_main_topic:
                                                
                                                first_item_value_fallback = current_items[0].get('value')
                                                if first_item_value_fallback:
                                                    summary_display['main_topic'] = str(first_item_value_fallback)
                                                    found_main_topic_fallback = True
                                
                                if all_concept_items_count > 0:
                                    summary_display['concept_count'] = all_concept_items_count
                        except Exception: pass # Closes the try block from line 549
                    
                    doc_dict['extracted_summary'] = summary_display
                    docs.append(doc_dict)
                return docs # Closes the for loop from line 535
            # Closes 'with conn.cursor()' from line 532
        # Closes 'with self.db._get_connection()' from line 531
    # End of list_documents method

    def update_document_concepts(self, doc_id: str, concepts_to_update: Dict) -> bool:
        """
        Updates specific concepts for an existing document.
        Fetches the document, merges the new concepts with existing ones, and saves back.
        """
        logger.info(f"VectorManager: Attempting to update concepts for document ID {doc_id[:8]}...")
        existing_doc_data = self.get_document(doc_id)
        if not existing_doc_data:
            logger.error(f"VectorManager: Document with ID {doc_id[:8]} not found. Cannot update concepts.")
            return False

        current_concepts = existing_doc_data.get('extracted_concepts', {})
        if not isinstance(current_concepts, dict): # Should be a dict from JSONB
            logger.warning(f"VectorManager: Existing concepts for doc ID {doc_id[:8]} is not a dict. Re-initializing.")
            current_concepts = {}
        
        # Merge new concepts into current concepts
        # This will overwrite existing keys in current_concepts with those from concepts_to_update
        for key, value in concepts_to_update.items():
            current_concepts[key] = value
            logger.info(f"VectorManager: Updating concept group '{key}' for doc ID {doc_id[:8]}.")

        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """UPDATE documents_enhanced SET
                           extracted_concepts = %s, updated_at = CURRENT_TIMESTAMP
                           WHERE id = %s""",
                        (json.dumps(current_concepts), doc_id)
                    )
                conn.commit()
            logger.info(f"VectorManager: Successfully updated concepts for document ID {doc_id[:8]}.")
            return True
        except Exception as e:
            logger.error(f"VectorManager: Failed to update concepts for document ID {doc_id[:8]}: {e}", exc_info=True)
            return False
                                

    def get_document(self, doc_id: str) -> PyOptional[Dict]:
        # (Content of get_document from previous version)
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM documents_enhanced WHERE id = %s", (doc_id,))
                row = cursor.fetchone()
                if row:
                    return dict(zip([desc[0] for desc in cursor.description], row))
                return None

    def delete_document(self, doc_id: str) -> bool:
        # (Content of delete_document from previous version)
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM documents_enhanced WHERE id = %s", (doc_id,))
                return cursor.rowcount > 0
            conn.commit() # Ensure commit is outside cursor block if not autocommit
        return False # Should not reach here if successful

    # Placeholder for other methods like concept_search, aspect_search, get_retriever, get_stats
    # These would need to be adapted to the new JSON structures in extracted_concepts/aspects
    def concept_search(self, query: str, concept_type: str = None, k: int = 5) -> List[Dict]:
        logger.warning("Concept search not fully adapted to new JSON structures yet.")
        return []

    def aspect_search(self, aspect_name: str, query: str = None, k: int = 5) -> List[Dict]:
        logger.warning("Aspect search not fully adapted to new JSON structures yet.")
        return []
        
    def get_retriever(self):
        logger.warning("Retriever functionality not fully adapted yet.")
        if not LLAMA_INDEX_AVAILABLE_VM: return None # Or some default retriever
        # This would need significant rework if embeddings are not from ContextGem
        from llama_index.core.schema import Document as LlamaIndexDocument
        from llama_index.core.vector_stores import SimpleVectorStore
        from llama_index.core import StorageContext, VectorStoreIndex
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding # Example

        # This is a placeholder and needs proper embedding model integration
        # If ContextGem was handling embeddings, and self.llm is None, this will fail.
        # If GGUF is selected, a separate embedding model needs to be used.
        try:
            # Example: using a HuggingFace embedding model if GGUF is selected
            # This should be configurable.
            embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load embedding model for retriever: {e}")
            return None

        all_docs_data = self.list_documents()
        llama_idx_docs = [LlamaIndexDocument(text=doc.get('processed_content',''), metadata={'doc_id': doc.get('id'), 'filename': doc.get('filename')}) for doc in all_docs_data if doc.get('processed_content')]
        
        if not llama_idx_docs: return None

        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(llama_idx_docs, storage_context=storage_context, embed_model=embed_model)
        return index.as_retriever(similarity_top_k=k)

    def get_stats(self) -> Dict:
        # (Content of get_stats from previous version)
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM documents_enhanced")
                total_docs = cursor.fetchone()[0]
                # More stats can be added here
                return {"total_documents": total_docs}
        return {"total_documents": 0}
