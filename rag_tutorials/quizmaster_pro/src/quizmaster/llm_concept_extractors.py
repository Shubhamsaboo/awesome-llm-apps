import logging
import json
import os
from typing import List, Dict, Optional as PyOptional

from pydantic import BaseModel, Field

# LlamaIndex and LlamaCPP imports
try:
    from llama_index.llms.llama_cpp import LlamaCPP
    from llama_index.llms.llama_cpp.llama_utils import messages_to_prompt, completion_to_prompt
    from llama_cpp.llama_grammar import LlamaGrammar
    LLAMA_INDEX_AVAILABLE_EXT = True # Extractor specific
except ImportError:
    LLAMA_INDEX_AVAILABLE_EXT = False
    LlamaCPP = None
    LlamaGrammar = None
    messages_to_prompt = None
    completion_to_prompt = None
    logging.getLogger(__name__).warning(
        "llm_concept_extractors: LlamaIndex/LlamaCPP libraries not available."
    )

# ContextGem imports
try:
    from contextgem import Document as ContextGemInternalDocument
    from contextgem import DocumentLLM
    from contextgem import StringConcept, NumericalConcept, DateConcept, Aspect # Add others if used by default_concepts_for_cg
    CONTEXTGEM_AVAILABLE_EXT = True # Extractor specific
except ImportError:
    CONTEXTGEM_AVAILABLE_EXT = False
    class DocumentLLM: pass # Placeholder
    class ContextGemInternalDocument: pass
    class StringConcept: pass
    # Define other placeholders if needed
    logging.getLogger(__name__).warning(
        "llm_concept_extractors: ContextGem library not available."
    )

from .config import QuizConfig
from .text_utils import chunk_text_by_tokens # Assuming text_utils.py is created

logger = logging.getLogger(__name__)

# --- OPTIMIZED Pydantic Schemas for Better JSON Structure ---
class ExtractedConcept(BaseModel):
    """A simplified concept schema to avoid recursion errors in grammar generation."""
    concept_type: str = Field(description="Category: Main Topic, Key Definition, Important Fact, etc.")
    content: str = Field(description="The extracted concept text.")

class ConceptsOutput(BaseModel):
    """A simplified output schema for concepts."""
    concepts: List[ExtractedConcept] = Field(description="A list of extracted concepts.")

class MainTopicItem(BaseModel): # Used by _extract_main_topics_llamacpp
    main_topic: str = Field(..., min_length=3, max_length=100, description="A concise main topic (3-100 characters)")

class MainTopicsOutput(BaseModel): # Used by _extract_main_topics_llamacpp
    main_topics: List[MainTopicItem] = Field(..., min_items=1, max_items=10, description="List of 1-10 main topics")

class LlamaCPPPreprocessedItem(BaseModel): # For LlamaCPP -> ContextGem pre-processing
    label: str = Field(..., 
                      description="Exact label type",
                      pattern="^(Main Topic|Key Definition|Important Fact|Process|Example|Concept)$")
    value: str = Field(..., min_length=10, max_length=300, description="Extracted content (10-300 characters)")

class LlamaCPPPreprocessedOutput(BaseModel): # For LlamaCPP -> ContextGem pre-processing
    extracted_data: List[LlamaCPPPreprocessedItem] = Field(..., min_items=1, max_items=15, description="List of 1-15 structured data items")


class ConceptExtractorService:
    def __init__(self, 
                 config: QuizConfig, 
                 llama_cpp_llm: PyOptional[LlamaCPP] = None, 
                 llama_grammar_concepts: PyOptional[LlamaGrammar] = None, # For ConceptsOutput schema
                 contextgem_llm: PyOptional[DocumentLLM] = None,
                 default_cg_concepts: PyOptional[List] = None): # List of ContextGem Concept objects
        self.config = config
        self.llama_cpp_llm = llama_cpp_llm
        self.llama_grammar_concepts = llama_grammar_concepts # Used by the direct LlamaCPP concept extraction
        self.contextgem_llm = contextgem_llm
        self.default_concepts_for_cg = default_cg_concepts if default_cg_concepts else []
        
        # Encoding for chunking, can be passed or initialized here too
        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.warning("ConceptExtractorService: Failed to get tiktoken encoding. Using char-based fallback for chunking.")
            self.encoding = None


    def preprocess_chunk_with_llamacpp(self, text_chunk: str, filename: str, chunk_num: int, total_chunks: int) -> PyOptional[LlamaCPPPreprocessedOutput]:
        """Uses LlamaCPP to preprocess a text chunk and extract labeled data items for ContextGem."""
        log_prefix = "LlamaCPP (PreProcessing)"
        logger.debug(f"{log_prefix}: Preprocessing chunk {chunk_num}/{total_chunks} for {filename}...")

        if not LLAMA_INDEX_AVAILABLE_EXT or not self.llama_cpp_llm:
            logger.error(f"{log_prefix}: LlamaCPP LLM not available or not initialized.")
            return None
        
        preprocessing_grammar = None
        try:
            schema_dict = LlamaCPPPreprocessedOutput.model_json_schema()
            preprocessing_grammar = LlamaGrammar.from_json_schema(json.dumps(schema_dict))
        except Exception as e:
            logger.error(f"{log_prefix}: Failed to create LlamaGrammar for LlamaCPPPreprocessedOutput: {e}", exc_info=True)
            return None

        # OPTIMIZED prompt for structured JSON output
        prompt = f"""[INST] Extract key information from this text and format as JSON using this exact structure:

{{"extracted_data": [
  {{"label": "Main Topic", "value": "specific topic here"}},
  {{"label": "Key Definition", "value": "definition content here"}},
  {{"label": "Important Fact", "value": "fact content here"}}
]}}

Label types: Main Topic, Key Definition, Important Fact, Process, Example, Concept

Text:
{text_chunk}
[/INST]"""
        
        original_grammar = self.llama_cpp_llm.generate_kwargs.get("grammar")
        original_temperature = getattr(self.llama_cpp_llm, 'temperature', None)
        
        try:
            self.llama_cpp_llm.generate_kwargs["grammar"] = preprocessing_grammar
            # Use optimized temperature for consistent JSON output
            if hasattr(self.llama_cpp_llm, 'temperature'):
                self.llama_cpp_llm.temperature = self.config.gguf_preprocessing_temperature
            
            response = self.llama_cpp_llm.complete(prompt)
            parsed_output = LlamaCPPPreprocessedOutput.parse_raw(response.text)
            logger.debug(f"{log_prefix}: Successfully preprocessed chunk {chunk_num}, extracted {len(parsed_output.extracted_data)} items.")
            return parsed_output
        except Exception as e:
            logger.error(f"{log_prefix} (chunk {chunk_num}) failed: {e}", exc_info=True)
            return None
        finally:
            # Restore original settings
            if original_grammar: 
                self.llama_cpp_llm.generate_kwargs["grammar"] = original_grammar
            elif "grammar" in self.llama_cpp_llm.generate_kwargs: 
                del self.llama_cpp_llm.generate_kwargs["grammar"]
            if original_temperature is not None and hasattr(self.llama_cpp_llm, 'temperature'):
                self.llama_cpp_llm.temperature = original_temperature
        return None


    def extract_main_topics_llamacpp(self, text_content: str, filename: str, file_format: str, chunk_processed_callback: PyOptional[callable] = None) -> PyOptional[List[Dict]]:
        """Uses LlamaCPP to extract only main topics (optimized for 'Regenerate Topics')."""
        # (Logic from DocumentProcessor._extract_main_topics_llamacpp, adapted)
        # This method uses MainTopicsOutput schema for its grammar.
        log_prefix = "LlamaCPP (MainTopics)"
        if not LLAMA_INDEX_AVAILABLE_EXT or not self.llama_cpp_llm:
            logger.error(f"{log_prefix}: LlamaCPP LLM not available for main topic extraction.")
            return None

        main_topics_grammar = None
        try:
            schema_dict = MainTopicsOutput.model_json_schema()
            main_topics_grammar = LlamaGrammar.from_json_schema(json.dumps(schema_dict))
        except Exception as e:
            logger.error(f"{log_prefix}: Failed to create LlamaGrammar for MainTopicsOutput: {e}", exc_info=True)
            return None

        LLAMACPP_CHUNK_TARGET_TOKENS = 1800 
        text_chunks = chunk_text_by_tokens(text_content, LLAMACPP_CHUNK_TARGET_TOKENS, self.encoding)
        if not text_chunks: return None
        
        all_main_topic_dicts = []
        original_grammar = self.llama_cpp_llm.generate_kwargs.get("grammar")
        original_max_new_tokens = self.llama_cpp_llm.max_new_tokens # Store original
        
        try:
            self.llama_cpp_llm.generate_kwargs["grammar"] = main_topics_grammar
            self.llama_cpp_llm.max_new_tokens = 512 # Set lower for this specific task
            logger.info(f"{log_prefix}: Temporarily set max_new_tokens to {self.llama_cpp_llm.max_new_tokens}")

            for i, chunk in enumerate(text_chunks):
                prompt = f"[INST] List primary main topics from this text:\n{chunk}\n[/INST]"
                try:
                    response = self.llama_cpp_llm.complete(prompt)
                    parsed_output = MainTopicsOutput.parse_raw(response.text)
                    for topic_item in parsed_output.main_topics:
                        all_main_topic_dicts.append({
                            "content": topic_item.main_topic, "concept_name": "Main Topic", "type": "concept",
                            "source_sentence": topic_item.main_topic[:150],
                            "metadata": {"filename": filename, "format": file_format, "extraction_method": "llamacpp_main_topics"}
                        })
                except Exception as e_chunk: logger.error(f"{log_prefix} chunk {i+1} error: {e_chunk}")
                if chunk_processed_callback:
                    try:
                        chunk_processed_callback(i + 1, len(text_chunks))
                    except Exception as cb_ex:
                        logger.error(f"Error in chunk_processed_callback for main topics: {cb_ex}")
        finally: # Restore grammar and max_new_tokens
            if original_grammar:
                self.llama_cpp_llm.generate_kwargs["grammar"] = original_grammar
            elif "grammar" in self.llama_cpp_llm.generate_kwargs:
                del self.llama_cpp_llm.generate_kwargs["grammar"]
            self.llama_cpp_llm.max_new_tokens = original_max_new_tokens # Restore
            logger.info(f"{log_prefix}: Restored max_new_tokens to {self.llama_cpp_llm.max_new_tokens}")
        
        return all_main_topic_dicts if all_main_topic_dicts else None


    def extract_concepts_llamacpp_to_contextgem(self, 
                                                 full_text_content: str, 
                                                 filename: str, 
                                                 file_format: str,
                                                 stop_signal_check: PyOptional[callable] = None,
                                                 chunk_processed_callback: PyOptional[callable] = None) -> PyOptional[List[Dict]]:
        """ULTRA-OPTIMIZED SEQUENTIAL PROCESSING: Use large chunks and aggressive optimizations, then ContextGem."""
        log_prefix = "GGUF→ContextGem (ULTRA-OPTIMIZED)"
        logger.info(f"{log_prefix}: Starting ultra-optimized sequential processing for {filename}")
        
        if not LLAMA_INDEX_AVAILABLE_EXT or not self.llama_cpp_llm:
            logger.error(f"{log_prefix}: LlamaCPP not available for preprocessing.")
            return None
        if not CONTEXTGEM_AVAILABLE_EXT or not self.contextgem_llm:
            logger.error(f"{log_prefix}: ContextGem not available for final extraction.")
            return None
        
        # Step 1: SAFE CHUNKING - Use smaller chunks to prevent context overflow
        max_safe_chunk_size = min(1500, self.config.gguf_advanced_context_window // 3)  # Use 1/3 of context window for safety
        overlap = min(150, max_safe_chunk_size // 10)  # Small overlap
        text_chunks = self._create_overlapping_chunks(full_text_content, max_safe_chunk_size, overlap)
        
        if not text_chunks:
            logger.warning(f"{log_prefix}: No text chunks generated for {filename}.")
            return None
        
        logger.info(f"{log_prefix}: Processing {len(text_chunks)} large chunks (aggressive optimization)")
        
        # Step 2: ULTRA-FAST SEQUENTIAL PROCESSING with optimized settings
        all_preprocessed_items = self._ultra_optimized_sequential_preprocess(
            text_chunks, filename, stop_signal_check, chunk_processed_callback
        )
        
        if not all_preprocessed_items:
            logger.warning(f"{log_prefix}: No preprocessed data extracted from {filename}")
            return None
        
        logger.info(f"{log_prefix}: Preprocessed {len(all_preprocessed_items)} total items, now processing with ContextGem")
        
        # Step 3: Convert preprocessed items to structured text for ContextGem
        structured_text_parts = []
        for item in all_preprocessed_items:
            structured_text_parts.append(f"{item.label}: {item.value}")
        
        structured_text = "\n".join(structured_text_parts)
        
        # Step 4: Feed structured text to ContextGem
        concepts = self.extract_concepts_contextgem(structured_text, filename, file_format)
        
        if concepts:
            # Update metadata to reflect the optimized method
            for concept in concepts:
                if concept.get("metadata"):
                    concept["metadata"]["extraction_method"] = "llamacpp_ultra_optimized_to_contextgem"
            logger.info(f"{log_prefix}: Successfully extracted {len(concepts)} final concepts for {filename}")
        else:
            logger.warning(f"{log_prefix}: ContextGem failed to extract concepts from preprocessed data")
            
        return concepts

    def _create_overlapping_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Create overlapping text chunks for better context preservation."""
        if not self.encoding:
            # Character-based fallback
            step = max(1, chunk_size - overlap)
            chunks = []
            for i in range(0, len(text), step):
                chunk = text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            return chunks
        
        # Token-based chunking with overlap
        tokens = self.encoding.encode(text)
        chunks = []
        step = max(1, chunk_size - overlap)
        
        for i in range(0, len(tokens), step):
            chunk_tokens = tokens[i:i + chunk_size]
            if chunk_tokens:
                chunk_text = self.encoding.decode(chunk_tokens)
                chunks.append(chunk_text)
        
        return chunks

    def _parallel_batch_preprocess(self, text_chunks: List[str], filename: str, n_parallel: int,
                                   stop_signal_check: PyOptional[callable] = None,
                                   chunk_processed_callback: PyOptional[callable] = None) -> List[LlamaCPPPreprocessedItem]:
        """OPTIMIZED parallel processing using LlamaIndex LlamaCPP wrapper with concurrent processing."""
        import concurrent.futures
        import threading
        
        all_items = []
        total_chunks = len(text_chunks)
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_parallel) as executor:
            # Submit all chunks for parallel processing
            future_to_chunk = {}
            
            for batch_start in range(0, total_chunks, n_parallel):
                if stop_signal_check and stop_signal_check():
                    logger.info(f"Parallel processing: Stop signal received at batch {batch_start}")
                    break
                
                batch_end = min(batch_start + n_parallel, total_chunks)
                batch_chunks = text_chunks[batch_start:batch_end]
                
                logger.debug(f"Submitting parallel batch {batch_start//n_parallel + 1}: chunks {batch_start+1}-{batch_end}")
                
                # Submit chunks for parallel processing
                futures = []
                for i, chunk in enumerate(batch_chunks):
                    chunk_num = batch_start + i + 1
                    future = executor.submit(self._process_single_chunk_parallel, chunk, filename, chunk_num, total_chunks)
                    futures.append((future, chunk_num))
                
                # Collect results as they complete
                for future, chunk_num in futures:
                    try:
                        result = future.result(timeout=60)  # 60 second timeout per chunk
                        if result:
                            all_items.extend(result)
                            logger.debug(f"Parallel chunk {chunk_num}: extracted {len(result)} items")
                    except concurrent.futures.TimeoutError:
                        logger.warning(f"Parallel chunk {chunk_num}: Processing timed out")
                    except Exception as e:
                        logger.error(f"Parallel chunk {chunk_num}: Error - {e}")
                
                # Update progress for this batch
                if chunk_processed_callback:
                    try:
                        chunk_processed_callback(batch_end, total_chunks)
                    except Exception as cb_exc:
                        logger.error(f"Error in chunk_processed_callback: {cb_exc}")
        
        return all_items

    def _process_single_chunk_parallel(self, chunk_text: str, filename: str, chunk_num: int, total_chunks: int) -> List[LlamaCPPPreprocessedItem]:
        """Process a single chunk using optimized settings for parallel execution."""
        try:
            # Create optimized prompt for preprocessing
            prompt = f"[INST] Extract key information from this text and format as JSON. For each item, provide 'label' (Main Topic, Key Definition, Important Fact, etc.) and 'value' (the actual content).\n\nText:\n{chunk_text}\n[/INST]"
            
            # Create preprocessing grammar for this thread
            preprocessing_grammar = None
            try:
                schema_dict = LlamaCPPPreprocessedOutput.model_json_schema()
                preprocessing_grammar = LlamaGrammar.from_json_schema(json.dumps(schema_dict))
            except Exception as e:
                logger.error(f"Failed to create grammar for parallel chunk {chunk_num}: {e}")
                return []
            
            # Store original settings
            original_grammar = self.llama_cpp_llm.generate_kwargs.get("grammar")
            original_temperature = getattr(self.llama_cpp_llm, 'temperature', None)
            
            try:
                # Apply optimized settings for this chunk
                self.llama_cpp_llm.generate_kwargs["grammar"] = preprocessing_grammar
                if hasattr(self.llama_cpp_llm, 'temperature'):
                    self.llama_cpp_llm.temperature = self.config.gguf_preprocessing_temperature
                
                # Process with optimized settings
                response = self.llama_cpp_llm.complete(prompt)
                parsed_output = LlamaCPPPreprocessedOutput.parse_raw(response.text)
                
                return parsed_output.extracted_data if parsed_output.extracted_data else []
                
            finally:
                # Restore original settings
                if original_grammar:
                    self.llama_cpp_llm.generate_kwargs["grammar"] = original_grammar
                elif "grammar" in self.llama_cpp_llm.generate_kwargs:
                    del self.llama_cpp_llm.generate_kwargs["grammar"]
                if original_temperature is not None and hasattr(self.llama_cpp_llm, 'temperature'):
                    self.llama_cpp_llm.temperature = original_temperature
                    
        except Exception as e:
            logger.error(f"Error processing parallel chunk {chunk_num}: {e}")
            return []

    def _ultra_optimized_sequential_preprocess(self, text_chunks: List[str], filename: str,
                                              stop_signal_check: PyOptional[callable] = None,
                                              chunk_processed_callback: PyOptional[callable] = None) -> List[LlamaCPPPreprocessedItem]:
        """ULTRA-OPTIMIZED sequential processing with aggressive settings for maximum speed."""
        all_items = []
        total_chunks = len(text_chunks)
        
        # Create grammar once and reuse for all chunks
        preprocessing_grammar = None
        try:
            schema_dict = LlamaCPPPreprocessedOutput.model_json_schema()
            preprocessing_grammar = LlamaGrammar.from_json_schema(json.dumps(schema_dict))
        except Exception as e:
            logger.error(f"Failed to create reusable grammar: {e}")
            return []
        
        # Store original settings once
        original_grammar = self.llama_cpp_llm.generate_kwargs.get("grammar")
        original_temperature = getattr(self.llama_cpp_llm, 'temperature', None)
        original_max_tokens = getattr(self.llama_cpp_llm, 'max_new_tokens', None)
        
        try:
            # Apply ultra-optimized settings for entire processing
            self.llama_cpp_llm.generate_kwargs["grammar"] = preprocessing_grammar
            if hasattr(self.llama_cpp_llm, 'temperature'):
                self.llama_cpp_llm.temperature = self.config.gguf_preprocessing_temperature
            if hasattr(self.llama_cpp_llm, 'max_new_tokens'):
                self.llama_cpp_llm.max_new_tokens = self.config.gguf_preprocessing_max_new_tokens
            
            logger.info(f"Ultra-optimized settings applied: temp={self.config.gguf_preprocessing_temperature}, max_tokens={self.config.gguf_preprocessing_max_new_tokens}")
            
            for i, chunk_text in enumerate(text_chunks):
                chunk_num = i + 1
                if stop_signal_check and stop_signal_check():
                    logger.info(f"Ultra-optimized: Stop signal received at chunk {chunk_num}/{total_chunks}")
                    break
                
                try:
                    # Ultra-optimized prompt for faster processing
                    prompt = f"Extract key info as JSON. Label types: Main Topic, Key Definition, Important Fact, Process, Example, Concept.\n\nText:\n{chunk_text}\n\nJSON:"
                    
                    # Direct processing with optimized prompt
                    response = self.llama_cpp_llm.complete(prompt)
                    
                    try:
                        parsed_output = LlamaCPPPreprocessedOutput.parse_raw(response.text)
                        if parsed_output.extracted_data:
                            all_items.extend(parsed_output.extracted_data)
                            logger.debug(f"Ultra-optimized chunk {chunk_num}: extracted {len(parsed_output.extracted_data)} items")
                    except Exception as parse_err:
                        logger.warning(f"Ultra-optimized chunk {chunk_num}: Parse failed - {parse_err}")
                        # Try to extract manually from response
                        manual_items = self._manual_extract_from_response(response.text, chunk_num)
                        if manual_items:
                            all_items.extend(manual_items)
                    
                except Exception as chunk_err:
                    logger.error(f"Ultra-optimized chunk {chunk_num}: Error - {chunk_err}")
                
                # Update progress
                if chunk_processed_callback:
                    try:
                        chunk_processed_callback(chunk_num, total_chunks)
                    except Exception as cb_exc:
                        logger.error(f"Error in chunk_processed_callback: {cb_exc}")
        
        finally:
            # Restore original settings
            if original_grammar:
                self.llama_cpp_llm.generate_kwargs["grammar"] = original_grammar
            elif "grammar" in self.llama_cpp_llm.generate_kwargs:
                del self.llama_cpp_llm.generate_kwargs["grammar"]
            if original_temperature is not None and hasattr(self.llama_cpp_llm, 'temperature'):
                self.llama_cpp_llm.temperature = original_temperature
            if original_max_tokens is not None and hasattr(self.llama_cpp_llm, 'max_new_tokens'):
                self.llama_cpp_llm.max_new_tokens = original_max_tokens
        
        return all_items

    def _manual_extract_from_response(self, response_text: str, chunk_num: int) -> List[LlamaCPPPreprocessedItem]:
        """Manually extract items from malformed JSON responses."""
        items = []
        try:
            # Try to find JSON-like patterns in the response
            import re
            
            # Look for label-value pairs
            patterns = [
                r'"label"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]+)"',
                r'"([^"]*(?:Topic|Definition|Fact|Process|Example|Concept)[^"]*)"\s*:\s*"([^"]+)"',
                r'(\w+(?:\s+\w+)*)\s*:\s*(.+?)(?=\n|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if len(match) == 2 and match[0].strip() and match[1].strip():
                        items.append(LlamaCPPPreprocessedItem(
                            label=match[0].strip(),
                            value=match[1].strip()
                        ))
                        if len(items) >= 5:  # Limit manual extraction
                            break
                
                if items:
                    break
            
            if items:
                logger.debug(f"Manual extraction chunk {chunk_num}: recovered {len(items)} items")
            
        except Exception as e:
            logger.error(f"Manual extraction chunk {chunk_num}: Failed - {e}")
        
        return items

    def _sequential_preprocess_fallback(self, text_chunks: List[str], filename: str,
                                       stop_signal_check: PyOptional[callable] = None,
                                       chunk_processed_callback: PyOptional[callable] = None) -> List[LlamaCPPPreprocessedItem]:
        """Fallback to sequential processing if parallel fails."""
        all_items = []
        total_chunks = len(text_chunks)
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_num = i + 1
            if stop_signal_check and stop_signal_check():
                logger.info(f"Sequential fallback: Stop signal received at chunk {chunk_num}/{total_chunks}")
                break
                
            preprocessed_output = self.preprocess_chunk_with_llamacpp(
                chunk_text, filename, chunk_num, total_chunks
            )
            
            if preprocessed_output and preprocessed_output.extracted_data:
                all_items.extend(preprocessed_output.extracted_data)
            
            if chunk_processed_callback:
                try:
                    chunk_processed_callback(chunk_num, total_chunks)
                except Exception as cb_exc:
                    logger.error(f"Error in chunk_processed_callback: {cb_exc}")
        
        return all_items

    def extract_concepts_contextgem(self, text_input: str, filename: str, file_format: str) -> PyOptional[List[Dict]]:
        """Core concept extraction using ContextGem library."""
        # text_input can be raw document text OR preprocessed text from LlamaCPP
        if not CONTEXTGEM_AVAILABLE_EXT or not self.contextgem_llm:
            logger.error("ContextGem LLM not available for concept extraction.")
            return None

        logger.debug(f"ContextGem: Using LLM ({self.contextgem_llm.model}) for {filename}. Input length: {len(text_input)} chars.")
        
        # ContextGem itself might do internal chunking. Pre-chunking here is for very large inputs.
        # If input is already preprocessed by LlamaCPP (chunk by chunk), it might be a string of structured items.
        # ContextGem's ability to handle this structured string effectively depends on its LLM.
        CONTEXTGEM_INPUT_MAX_TOKENS = getattr(self.contextgem_llm, 'max_input_tokens', 16000) 
        CHUNK_TARGET_TOKENS_CG = CONTEXTGEM_INPUT_MAX_TOKENS - 4000

        # Chunking here is applied to the `text_input` which might be raw or LlamaCPP preprocessed.
        text_chunks = chunk_text_by_tokens(text_input, CHUNK_TARGET_TOKENS_CG, self.encoding)
        if not text_chunks: return None
            
        all_extracted_concepts = []
        for i, chunk_text_for_cg in enumerate(text_chunks):
            cg_doc = ContextGemInternalDocument(raw_text=chunk_text_for_cg)
            cg_doc.add_concepts(self.default_concepts_for_cg) # Use concepts defined for ContextGem
            try:
                self.contextgem_llm.extract_concepts_from_document(cg_doc)
                if hasattr(cg_doc, 'concepts') and cg_doc.concepts:
                    for concept_obj in cg_doc.concepts:
                        if hasattr(concept_obj, 'name') and hasattr(concept_obj, 'extracted_items'):
                            for item in concept_obj.extracted_items:
                                item_value = getattr(item, 'value', str(item))
                                if item_value and str(item_value).strip():
                                    all_extracted_concepts.append({
                                        "content": str(item_value), "concept_name": concept_obj.name,
                                        "type": "concept", "source_sentence": str(item_value)[:150],
                                        "metadata": {"filename": filename, "format": file_format, "extraction_method": "contextgem"}
                                    })
            except Exception as e: logger.error(f"ContextGem chunk {i+1} error: {e}")
        
        return all_extracted_concepts if all_extracted_concepts else None

    # This is the old LlamaCPP direct concept extraction, kept for fallback if needed,
    # but the new flow is LlamaCPP (preprocess) -> ContextGem.
    def extract_concepts_llamacpp_direct(self,
                                         full_text_content: str,
                                         filename: str,
                                         file_format: str,
                                         stop_signal_check: PyOptional[callable] = None,
                                         chunk_processed_callback: PyOptional[callable] = None
                                         ) -> PyOptional[List[Dict]]:
        """Direct concept extraction using LlamaCPP with ConceptsOutput grammar, with internal chunking."""
        log_prefix = "LlamaCPP (DirectConceptExtraction)"
        logger.info(f"Attempting {log_prefix} for {filename}")
        
        if not LLAMA_INDEX_AVAILABLE_EXT or not self.llama_cpp_llm:
            logger.error(f"{log_prefix}: LlamaCPP LLM not available.")
            return None
        if not self.llama_grammar_concepts: # This grammar is for ConceptsOutput
             logger.error(f"{log_prefix}: LlamaGrammar for ConceptsOutput not initialized.")
             return None

        # Use configured chunk size
        chunk_target_tokens = self.config.gguf_direct_max_tokens_per_chunk
        text_chunks = chunk_text_by_tokens(full_text_content, chunk_target_tokens, self.encoding)
        
        if not text_chunks:
            logger.warning(f"{log_prefix}: No text chunks generated for {filename}.")
            return None
            
        all_formatted_concepts = []
        total_chunks = len(text_chunks)
        original_grammar = self.llama_cpp_llm.generate_kwargs.get("grammar")
        
        try:
            self.llama_cpp_llm.generate_kwargs["grammar"] = self.llama_grammar_concepts
            for i, chunk_text in enumerate(text_chunks):
                chunk_num = i + 1
                if stop_signal_check and stop_signal_check():
                    logger.info(f"{log_prefix}: Stop signal received, halting processing for {filename} at chunk {chunk_num}/{total_chunks}.")
                    break

                logger.info(f"{log_prefix}: Processing chunk {chunk_num}/{total_chunks} for {filename}...")
                prompt = f"[INST] From the text, extract concepts (type, content, source).\nText:\n{chunk_text}\n[/INST]"
                try:
                    response = self.llama_cpp_llm.complete(prompt)
                    parsed_output = ConceptsOutput.parse_raw(response.text)
                    for concept_data in parsed_output.concepts:
                        all_formatted_concepts.append({
                            "content": concept_data.content, "concept_name": concept_data.concept_type,
                            "type": "concept", "source_sentence": concept_data.source or concept_data.content[:100],
                            "metadata": {"filename": filename, "format": file_format, "extraction_method": "llamacpp_direct_chunked"}
                        })
                    logger.info(f"{log_prefix}: Successfully processed chunk {chunk_num}, extracted {len(parsed_output.concepts)} concepts.")
                except Exception as e_chunk:
                    logger.error(f"{log_prefix} chunk {chunk_num} error: {e_chunk}", exc_info=True)
                
                if chunk_processed_callback:
                    try:
                        chunk_processed_callback(chunk_num, total_chunks)
                    except Exception as cb_exc:
                        logger.error(f"{log_prefix}: Error in chunk_processed_callback: {cb_exc}", exc_info=True)
                        
        finally: # Restore grammar
            if original_grammar:
                self.llama_cpp_llm.generate_kwargs["grammar"] = original_grammar
            elif "grammar" in self.llama_cpp_llm.generate_kwargs:
                del self.llama_cpp_llm.generate_kwargs["grammar"]

        return all_formatted_concepts if all_formatted_concepts else None
