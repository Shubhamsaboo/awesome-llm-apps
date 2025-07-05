import random
import logging
from typing import Dict, List, Optional

from .helpers import is_question_unique, distribute_questions, parse_json_response
from .context_manager import ContextManager
from .quiz_result import QuizResult
from .config import QuizConfig
from .schemas import MCQ_SCHEMA
from .prompts import get_question_prompt # Import the function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .llm_manager import LLMManager
from .question_formatter import QuestionFormatter

class QuizGenerator:
    def __init__(self, config: Optional[QuizConfig] = None):
        self.config = config or QuizConfig()
        self.llm_manager = LLMManager(self.config)
        self.question_formatter = QuestionFormatter()
        self.current_model = self.config.current_model
        self.openai_models = self.config.openai_models
        self.MCQ_SCHEMA = MCQ_SCHEMA


        
    def generate_quiz(self, processed_content: Dict, question_types: List[str],
                      num_questions: int, difficulty: str, focus_topics: Optional[List[str]] = None) -> Dict:
        """Generate quiz questions using ContextGem extracted data."""

        original_content = processed_content.get('content', '') # Renamed to avoid conflict
        extracted_concepts = processed_content.get('extracted_concepts', [])

        logger.info(f"Starting quiz generation for {num_questions} questions of type {question_types} and difficulty {difficulty}. Focus topics: {focus_topics}")
        logger.info(f"Processed content available: {bool(original_content)}")
        logger.info(f"Extracted concepts count: {len(extracted_concepts)}")

        if not original_content:
            logger.error("No content found in processed_content.")
            return {
                'questions': [],
                'metadata': processed_content.get('metadata', {}),
                'model_used': self.current_model,
                'content_length': 0,
                'generation_stats': {
                    'requested': num_questions,
                    'generated': 0,
                    'failed': num_questions,
                    'success_rate': 0
                }
            }

        context_data = []
        
        context_data.append({
            'content': self.llm_manager._truncate_content(original_content, 2000),
            'type': 'full_document',
            'source': 'document',
            'used': False
        })
        
        for concept in extracted_concepts:
            try:
                if isinstance(concept, dict):
                    concept_content = concept.get('content', '') # Renamed to avoid conflict
                    concept_name = concept.get('concept_name', 'General')
                    source = concept.get('source_sentence', '')
                elif isinstance(concept, str):
                    concept_content = concept
                    concept_name = 'Extracted Concept'
                    source = ''
                else:
                    logger.warning(f"Skipping unknown concept format: {type(concept)}")
                    continue
                
                if concept_content and concept_content.strip():
                    context_data.append({
                        'content': concept_content,
                        'type': concept_name,
                        'source': source,
                        'used': False
                    })
            except Exception as e:
                logger.warning(f"Error processing concept: {str(e)}")
                continue

        questions = []
        generated_count = 0
        failed_count = 0
        
        # Create single context manager instance to track used contexts
        context_manager = ContextManager(context_data)
        
        question_pool = []
        for question_type, count in distribute_questions(question_types, num_questions).items():
            for _ in range(count):
                question_pool.append(question_type)
        
        random.shuffle(question_pool)

        logger.info(f"Initial question pool distribution: {distribute_questions(question_types, num_questions)}")
        logger.info(f"Question pool size: {len(question_pool)}")

        attempts = 0
        # OPTIMIZATION: Reduce max attempts for better speed
        max_attempts = num_questions * 3  # Reduced from 6 to 3
        
        # Add success tracking for adaptive retry
        consecutive_failures = 0
        max_consecutive_failures = 2
        
        logger.info(f"Starting question generation loop. Target: {num_questions}, Max attempts: {max_attempts}")
        
        while len(questions) < num_questions and attempts < max_attempts:
            question_type = question_pool[attempts % len(question_pool)]
            logger.info(f"Attempt {attempts + 1}/{max_attempts}: Generating {question_type} question.")
            
            try:
                selected_context = context_manager.select_relevant_context(question_type, focus_topics)
                
                question = self._generate_question_with_context(
                    selected_context, question_type, difficulty
                )

                if question:
                    logger.info(f"Successfully generated a question (type: {question.get('type', 'N/A')}). Question text: '{question.get('text', 'N/A')[:100]}...'")
                    logger.info(f"Checking uniqueness against {len(questions)} existing questions")
                    if is_question_unique(question, questions):
                        questions.append(question)
                        generated_count += 1
                        consecutive_failures = 0  # Reset failure counter
                        logger.info(f"Question added successfully. Total generated: {generated_count}/{num_questions}")
                    else:
                        failed_count += 1
                        consecutive_failures += 1
                        logger.warning(f"Duplicate/similar question skipped: {question.get('text', 'N/A')[:50]}...")
                else:
                    failed_count += 1
                    consecutive_failures += 1
                    logger.warning(f"Failed to generate {question_type} question (attempt {attempts + 1})")
                
                # OPTIMIZATION: Break early if too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(f"Breaking due to {consecutive_failures} consecutive failures")
                    break
                    
            except Exception as e:
                failed_count += 1
                consecutive_failures += 1
                logger.error(f"Error generating question (attempt {attempts + 1}): {str(e)}", exc_info=True)
                
            attempts += 1
            
        logger.info(f"Question generation loop finished. Generated: {len(questions)}, Failed: {failed_count}, Attempts: {attempts}")
        
        if len(questions) < num_questions:
            remaining = num_questions - len(questions)
            logger.warning(f"Generating {remaining} additional questions with relaxed constraints")
            
            # Use simpler approach for remaining questions
            for _ in range(min(remaining, 3)):  # Limit additional attempts to 3
                try:
                    context_manager = ContextManager(context_data)
                    # Use any available context for remaining questions
                    selected_context = context_manager.select_relevant_context(random.choice(question_types), focus_topics=None)
                    
                    q_type = random.choice(question_types)
                    question = self._generate_question_with_context(
                        selected_context, q_type, difficulty
                    )
                    
                    if question and is_question_unique(question, questions, similarity_threshold=0.75):  # More lenient similarity
                        questions.append(question)
                        generated_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error generating additional question: {str(e)}", exc_info=True)
        
        logger.info(f"Final question count: {len(questions)}")
        
        return QuizResult(
            questions=questions,
            metadata={
                **processed_content.get('metadata', {}),
                'generation_stats': {
                    'requested': num_questions,
                    'generated': generated_count,
                    'failed': failed_count,
                    'success_rate': generated_count / num_questions if num_questions > 0 else 0
                }
            },
            model_used=self.current_model,
            content_length=len(original_content), # Use the original content length
            fallback_used=False
        ).to_dict()

    def _generate_question_with_context(self, context: str, question_type: str, difficulty: str) -> Optional[Dict]:
        """Generate a single question based on context with enhanced error handling."""
        if not context or not context.strip():
            logger.warning("Context is empty or None, cannot generate question.")
            return None

        prompt = get_question_prompt(question_type, difficulty, context)
        
        logger.info(f"Prompt for LLM (snippet): {prompt[:500]}...")
        
        # Use model-specific parameters for better JSON generation
        current_model = self.llm_manager.get_current_model()
        if current_model in self.config.openai_models:
            # For OpenAI models, use more tokens and lower temperature with slight randomization
            max_tokens = 1000
            base_temp = self.config.openai_structured_temperature
            # Add small random variation to prevent identical outputs
            temperature = base_temp + random.uniform(-0.05, 0.05)
            temperature = max(0.0, min(1.0, temperature))  # Clamp to valid range
        else:
            # For other models, use standard settings with randomization
            max_tokens = 800
            base_temp = self.config.structured_output_temperature
            temperature = base_temp + random.uniform(-0.1, 0.1)
            temperature = max(0.0, min(1.0, temperature))  # Clamp to valid range
        
        # Enhanced error handling with quick validation
        response = self.llm_manager.make_llm_request(prompt, max_tokens=max_tokens, temperature=temperature)
        logger.info(f"Raw LLM response length: {len(response) if response else 0}")
        
        if not response:
            logger.warning("LLM request returned None.")
            return None
        
        # Quick pre-validation to catch obvious issues
        if len(response.strip()) < 50:
            logger.warning("Response too short, likely incomplete.")
            return None
            
        if response.count('{') != response.count('}'):
            logger.warning("Unmatched braces in response, JSON likely malformed.")
            return None
        
        schema = self.get_schema_for_question_type(question_type)
        parsed_question = parse_json_response(response, schema)

        if not parsed_question:
            logger.warning("JSON parsing or validation failed.")
            # Log the raw response for debugging (truncated)
            logger.debug(f"Failed response: {response[:200]}...")
            return None

        logger.info(f"Parsed question data: {parsed_question}")
        
        # DEBUG: Check the question formatter being used
        logger.info(f"Using question formatter: {self.question_formatter.__class__.__name__}")
        
        if hasattr(self.question_formatter, 'format_question'):
            logger.info("Formatter has format_question method")
        else:
            logger.error("!!! CRITICAL ERROR: Formatter missing format_question method !!!")
            
        # Call the format_question method with more error handling
        try:
            # Use the standard formatter
            if not hasattr(self.question_formatter, 'format_question'):
                logger.error("CRITICAL ERROR: question_formatter has no format_question method!")
                return None
            
            logger.info(f"Calling standard formatter.format_question with type={question_type}")
            formatted_question = self.question_formatter.format_question(question_type, parsed_question)
            
            if not formatted_question:
                logger.warning(f"Question formatting failed for {question_type}. Parsed data: {parsed_question}")
                
                # Only Multiple Choice questions remain
                logger.debug("Question details:")
                if "question" in parsed_question:
                    logger.debug(f"  - question field is present: {type(parsed_question['question'])}")
                    logger.debug(f"  - question content: {parsed_question['question'][:50]}...")
                
                return None
            else:
                logger.info(f"Successfully formatted question: {formatted_question}")
                return formatted_question
        except Exception as e:
            logger.error(f"Exception during question formatting: {str(e)}", exc_info=True)
            return None
            
        logger.info(f"Successfully formatted question: {formatted_question.get('text', 'No text')[:50]}...")
        return formatted_question

    def get_schema_for_question_type(self, question_type: str) -> Dict:
        """Returns the JSON schema for a given question type."""
        schemas = {
            "Multiple Choice": self.MCQ_SCHEMA,
        }
        return schemas.get(question_type, {})
