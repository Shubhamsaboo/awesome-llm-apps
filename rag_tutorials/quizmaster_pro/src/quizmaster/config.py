from dataclasses import dataclass, field

@dataclass
class QuizConfig:
    """Configuration for quiz generation."""
    ollama_base_url: str = "http://localhost:11434"
    max_retries: int = 3
    retry_delay: float = 1.0
    pull_timeout: int = 1800
    default_temperature: float = 0.7
    # Model-specific temperatures for better structured output
    structured_output_temperature: float = 0.2  # Lower temperature for JSON generation
    openai_structured_temperature: float = 0.1  # Even lower for OpenAI models
    cache_size: int = 100
    current_model: str = "gpt-4o-mini" # Default model for the application if nothing else is chosen
    openai_models: list = field(default_factory=lambda: ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"])
    processing_engine: str = "contextgem" # 'contextgem' or 'llamacpp_gguf'
    gguf_model_path: str = "./mistral-7b-instruct-v0.1.Q8_0.gguf" # Default path for local GGUF model
    use_gpu_if_available: bool = True # For LlamaCPP n_gpu_layers
    gguf_direct_max_tokens_per_chunk: int = 800 # Max tokens per chunk for direct GGUF concept extraction
    # Optimized settings for GGUF preprocessing -> ContextGem flow
    gguf_preprocessing_chunk_size: int = 2000 # Larger chunks for preprocessing (2x more efficient)
    gguf_preprocessing_max_new_tokens: int = 768 # Optimized for preprocessing output
    gguf_preprocessing_temperature: float = 0.1 # Lower temperature for consistent JSON output
    gguf_preprocessing_context_window: int = 4096 # Larger context for better understanding
    
    # ADVANCED PERFORMANCE OPTIMIZATIONS (Based on llama-cpp-python best practices)
    gguf_advanced_batch_size: int = 1024 # Large batch for better throughput (vs default 512)
    gguf_advanced_parallel_sequences: int = 4 # Process multiple chunks in parallel
    gguf_enable_kv_cache_offload: bool = True # Offload KV cache to GPU for speed
    gguf_enable_mlock: bool = True # Lock memory to prevent swapping
    gguf_advanced_context_window: int = 8192 # Larger context for fewer chunks
    gguf_chunk_overlap: int = 100 # Overlap tokens between chunks for better context
    gguf_enable_speculative_decoding: bool = True # Use speculative decoding for speed
    gguf_numa_optimization: bool = False # Disable NUMA for consistent performance
    
    # QUIZ GENERATION PERFORMANCE OPTIMIZATIONS
    enable_performance_tracking: bool = True # Track success rates and response times
    max_generation_attempts: int = 3 # Reduced from default 6 for faster generation
    early_stop_on_consecutive_failures: int = 2 # Stop early if too many failures in a row
    enable_debug_logging: bool = False # Enable detailed logging for troubleshooting
