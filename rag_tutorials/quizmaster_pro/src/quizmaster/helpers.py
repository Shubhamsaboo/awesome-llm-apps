import json
import re
import logging
from typing import Dict, List, Optional, Any
from jsonschema import validate, ValidationError
from difflib import SequenceMatcher
import tiktoken

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_json_response(response_text: str, schema: Dict) -> Optional[Dict]:
    """Parse and validate JSON response from LLM with improved robustness."""
    if not response_text:
        logger.warning("Empty response from LLM")
        return None
        
    logger.info(f"Parsing JSON from response (first 100 chars): {response_text[:100]}...")
        
    json_data = None
    
    # Method 1: Direct JSON parsing
    try:
        json_data = json.loads(response_text)
        logger.info("Successfully parsed JSON directly")
    except Exception as e:
        logger.info(f"Direct JSON parsing failed: {str(e)}")

    # Method 2: Extract from markdown code block
    if not json_data:
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"`(.*?)`"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                json_str_from_markdown = match.group(1).strip()
                try:
                    json_data = json.loads(json_str_from_markdown)
                    logger.info(f"Successfully parsed JSON from pattern: {pattern}")
                    break
                except Exception as e:
                    logger.info(f"Pattern {pattern} JSON parsing failed: {str(e)}")
    
    # Method 3: Brace matching for JSON objects
    if not json_data:
        start_index = response_text.find('{')
        if start_index != -1:
            brace_count = 0
            end_index = -1
            for i in range(start_index, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_index = i
                        break
            if end_index != -1:
                json_str = response_text[start_index:end_index+1]
                try:
                    json_data = json.loads(json_str)
                    logger.info("Successfully parsed JSON using brace matching")
                except Exception as e:
                    logger.info(f"Brace matching JSON parsing failed: {str(e)}")
    # Method 4: Common JSON formatting fixes
    if not json_data:
        fixed_text = response_text
        
        # Fix common issues
        fixes = [
            (r"'([^']*)':", r'"\1":'),  # Single quotes to double quotes for keys
            (r":\s*'([^']*)'", r': "\1"'),  # Single quotes to double quotes for values
            (r',\s*}', '}'),  # Remove trailing commas in objects
            (r',\s*]', ']'),  # Remove trailing commas in arrays
            (r'([{,]\s*)(\w+):', r'\1"\2":'),  # Add quotes around unquoted keys
            (r':\s*True\b', ': true'),  # Python True to JSON true
            (r':\s*False\b', ': false'),  # Python False to JSON false
            (r':\s*None\b', ': null'),  # Python None to JSON null
        ]
        
        for pattern, replacement in fixes:
            fixed_text = re.sub(pattern, replacement, fixed_text)
        
        # Try to extract JSON after fixes
        json_patterns = [
            r'({[\s\S]*?})',  # Any object
            r'(\[[\s\S]*?\])'  # Any array
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, fixed_text, re.DOTALL)
            if match:
                json_str = match.group(1)
                try:
                    json_data = json.loads(json_str)
                    logger.info("Successfully parsed JSON after applying fixes")
                    break
                except Exception as e:
                    logger.info(f"JSON parsing after fixes failed: {str(e)}")
                    continue
                
    if json_data:
        try:
            validate(instance=json_data, schema=schema)
            logger.info("JSON validation successful")
            return json_data
        except ValidationError as e:
            logger.warning(f"JSON validation failed: {str(e)}")
            
            if isinstance(json_data, dict):
                if 'options' in json_data and isinstance(json_data['options'], list):
                    for i, opt in enumerate(json_data['options']):
                        if isinstance(opt, str):
                            letter = chr(65 + i)
                            json_data['options'][i] = {"letter": letter, "text": opt}
                    
                    try:
                        validate(instance=json_data, schema=schema)
                        logger.info("JSON validation successful after fixes")
                        return json_data
                    except ValidationError:
                        pass
            
    logger.warning("All JSON parsing methods failed")
    return None

def is_question_unique(new_question: Dict, existing_questions: List[Dict], similarity_threshold: float = 0.85) -> bool:
    """
    Check if a new question is unique compared to existing questions using text similarity.
    """
    if not existing_questions:
        logger.info("No existing questions, new question is unique")
        return True

    new_text = new_question.get('text', '') or new_question.get('question', '') or new_question.get('statement', '')
    if not new_text:
        logger.warning("New question has no text content")
        return False

    # Normalize text for comparison
    new_text_normalized = new_text.lower().strip()
    
    logger.info(f"Checking uniqueness for question: '{new_text[:50]}...' against {len(existing_questions)} existing questions")

    for i, existing in enumerate(existing_questions):
        existing_text = existing.get('text', '') or existing.get('question', '') or existing.get('statement', '')
        if not existing_text:
            continue

        existing_text_normalized = existing_text.lower().strip()
        similarity = SequenceMatcher(None, new_text_normalized, existing_text_normalized).ratio()
        
        logger.debug(f"Similarity check {i+1}: {similarity:.3f} vs threshold {similarity_threshold}")
        
        if similarity > similarity_threshold:
            logger.info(f"Question rejected due to similarity {similarity:.2f} > {similarity_threshold}")
            logger.info(f"New: {new_text[:50]}...")
            logger.info(f"Existing: {existing_text[:50]}...")
            return False

    # Also check for very short questions (likely incomplete)
    if len(new_text.strip()) < 10:
        logger.warning("Question rejected: too short")
        return False

    logger.info("Question is unique")
    return True

def truncate_content(content: str, max_tokens: int = 3000) -> str:
    """Truncate content to fit within token limit."""
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens = encoding.encode(content)
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[:max_tokens]
            return encoding.decode(truncated_tokens)
    except Exception as e:
        logger.warning(f"Token encoding failed, using character truncation: {str(e)}")
        estimated_chars = max_tokens * 4
        if len(content) > estimated_chars:
            return content[:estimated_chars] + "..."
    return content

def distribute_questions(question_types: List[str], total_questions: int) -> Dict[str, int]:
    """Distribute total questions across selected question types."""
    distribution = {}
    if not question_types:
        return distribution
        
    base_count = total_questions // len(question_types)
    remainder = total_questions % len(question_types)
    
    for q_type in question_types:
        distribution[q_type] = base_count
        
    for i in range(remainder):
        distribution[question_types[i]] += 1
        
    actual_total = sum(distribution.values())
    if actual_total < total_questions:
        distribution[question_types[0]] += (total_questions - actual_total)
        
    return distribution
