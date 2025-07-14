from typing import Dict, Optional

class QuestionFormatter:
    def _extract_field(self, parsed_question: Dict, field_name: str, fallback_fields: list = None):
        """Extract field from potentially nested JSON structure."""
        # Try direct access first
        if field_name in parsed_question:
            value = parsed_question[field_name]
            # If it's a dict with a 'text' field, extract the text
            if isinstance(value, dict) and 'text' in value:
                return value['text']
            return value
        
        # Try nested access (e.g., question.text)
        if isinstance(parsed_question.get('question'), dict):
            nested_q = parsed_question['question']
            if field_name in nested_q:
                value = nested_q[field_name]
                # If it's a dict with a 'text' field, extract the text
                if isinstance(value, dict) and 'text' in value:
                    return value['text']
                return value
            # Also try 'text' field within nested question
            if field_name == 'question' and 'text' in nested_q:
                return nested_q['text']
        
        # Try fallback fields at top level
        if fallback_fields:
            for fallback in fallback_fields:
                if fallback in parsed_question:
                    value = parsed_question[fallback]
                    # If it's a dict with a 'text' field, extract the text
                    if isinstance(value, dict) and 'text' in value:
                        return value['text']
                    return value
                    
                # Try fallback fields in nested question
                if isinstance(parsed_question.get('question'), dict) and fallback in parsed_question['question']:
                    value = parsed_question['question'][fallback]
                    # If it's a dict with a 'text' field, extract the text
                    if isinstance(value, dict) and 'text' in value:
                        return value['text']
                    return value
        
        return None
    
    def _normalize_options(self, options):
        """Normalize options to the expected format: [{'letter': 'A', 'text': 'option text'}]"""
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"FORMATTER DEBUG: Normalizing options: {options}")
        
        if not options:
            return None
            
        normalized = []
        
        # Handle nested options (dict with 'options' key)
        if isinstance(options, dict):
            # Check for different possible keys that might contain options
            for key in ['options', 'choices', 'answers', 'alternatives']:
                if key in options:
                    options = options[key]
                    logger.info(f"FORMATTER DEBUG: Found options in '{key}' key: {options}")
                    break
        
        # If options is still a dict, convert to list based on values
        if isinstance(options, dict):
            # Check if dict keys are A, B, C, D or 1, 2, 3, 4
            if all(k in 'ABCD' for k in options.keys()):
                # Transform {A: text, B: text} to [{letter: A, text: text}, ...]
                ordered_options = []
                for letter in 'ABCD':
                    if letter in options:
                        ordered_options.append({'letter': letter, 'text': options[letter]})
                options = ordered_options
                logger.info(f"FORMATTER DEBUG: Converted letter-keyed dict options: {options}")
            # Check if dict keys are numeric
            elif all(k.isdigit() for k in options.keys() if isinstance(k, str)):
                # Sort by numeric key
                options = [options[str(k)] if str(k) in options else options[k] 
                          for k in sorted([int(k) if isinstance(k, str) else k for k in options.keys()])]
                logger.info(f"FORMATTER DEBUG: Converted numeric-keyed dict options: {options}")
            else:
                # Generic dict to list conversion
                options = list(options.values())
                logger.info(f"FORMATTER DEBUG: Converted dict options to list: {options}")
        
        # Process each option
        for i, option in enumerate(options):
            letter = chr(65 + i)  # A, B, C, D, ...
            opt_letter, opt_text, opt_id = None, None, None
            is_correct = False
            
            # Option is a string
            if isinstance(option, str):
                # Try to split out letter if present (e.g., 'A) Text', 'B. Text', 'A. Text', etc.)
                m = re.match(r"^([A-Da-d][).\-:]?)\s*(.*)$", option.strip())
                if m:
                    opt_letter = m.group(1)[0].upper()
                    opt_text = m.group(2).strip()
                else:
                    opt_text = option.strip()
                    
            # Option is a dict
            elif isinstance(option, dict):
                # Extract is_correct flag if present
                is_correct = option.get('is_correct', False)
                if isinstance(is_correct, str):
                    is_correct = is_correct.lower() == 'true'
                    
                # Extract ID
                for id_key in ['id', 'option_id', 'optionId', 'value']:
                    if id_key in option:
                        opt_id = str(option[id_key])
                        break
                
                # Extract text
                for text_key in ['text', 'content', 'label', 'answer', 'body']:
                    if text_key in option and option[text_key]:
                        opt_text = option[text_key]
                        break
                
                # Handle 'option' key with various formats
                if 'option' in option:
                    val = option['option']
                    if isinstance(val, str):
                        m = re.match(r"^([A-Da-d][).\-:]?)\s*(.*)$", val.strip())
                        if m:
                            opt_letter = m.group(1)[0].upper()
                            if not opt_text:
                                opt_text = m.group(2).strip()
                        elif len(val.strip()) == 1 and val.strip().upper() in 'ABCD':
                            opt_letter = val.strip().upper()
                        elif not opt_text:
                            opt_text = val.strip()
                
                # Try 'answer_text', 'option_text', etc.
                if not opt_text:
                    for key in option:
                        if ('text' in key.lower() or 'content' in key.lower() or 'answer' in key.lower()) and isinstance(option[key], str):
                            opt_text = option[key]
                            break
                            
                # If only 'option' and no 'text', treat 'option' as text
                if not opt_text and 'option' in option:
                    opt_text = str(option['option'])
                
                # Handle 'correct_option' or 'correct_answer' flag
                for correct_key in ['correct', 'correct_option', 'correct_answer']:
                    if correct_key in option:
                        is_correct = option[correct_key]
                        if isinstance(is_correct, str):
                            is_correct = is_correct.lower() == 'true'
                        break
                        
                # Extract letter from option structure
                for letter_key in ['letter', 'id', 'identifier']:
                    if letter_key in option and isinstance(option[letter_key], str) and len(option[letter_key]) == 1:
                        if option[letter_key].upper() in 'ABCD':
                            opt_letter = option[letter_key].upper()
                            break
                
                # Fallback: use stringified dict if no text found
                if not opt_text:
                    opt_text = str(option)
            else:
                # Fallback: string conversion for non-string, non-dict options
                opt_text = str(option)
            
            # Construct normalized option
            norm_option = {'letter': opt_letter or letter, 'text': opt_text}
            
            # Add optional fields if present
            if opt_id:
                norm_option['id'] = opt_id
            if is_correct:
                norm_option['is_correct'] = is_correct
                
            normalized.append(norm_option)
            
        logger.info(f"FORMATTER DEBUG: Normalized options output: {normalized}")
        return normalized

    def _normalize_correct_answer(self, correct_answer, options):
        """Normalize correct answer to letter format (A, B, C, D)"""
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"FORMATTER DEBUG: Normalizing correct answer: {correct_answer}")
        
        if not options:
            logger.warning(f"FORMATTER DEBUG: No options provided for answer normalization")
            return None
        
        # Build mapping dictionaries for answer lookups
        id_map = {}
        text_map = {}
        letter_map = {}
        index_map = {}
        lower_text_map = {}
        
        # Populate maps for all options
        for i, opt in enumerate(options):
            # Store letter to letter mapping
            letter_map[opt['letter']] = opt['letter']
            
            # Store ID to letter mapping (with various key formats)
            if 'id' in opt:
                id_map[str(opt['id'])] = opt['letter']
            
            # Store lowercase text to letter mapping
            text = opt['text'].strip()
            text_map[text] = opt['letter']
            lower_text_map[text.lower()] = opt['letter']
            
            # Store index to letter mapping
            index_map[i] = opt['letter']
            index_map[str(i)] = opt['letter']
            index_map[str(i+1)] = opt['letter']  # 1-indexed
            
        logger.info(f"FORMATTER DEBUG: Built mappings: id_map={id_map}, letter_map={letter_map}, text_map length={len(text_map)}")
        
        # Return None if no correct answer and no is_correct flags on options
        if correct_answer is None:
            # Check for is_correct flags on options as a fallback
            for opt in options:
                if opt.get('is_correct'):
                    logger.info(f"FORMATTER DEBUG: Found is_correct flag, returning letter {opt['letter']}")
                    return opt['letter']
            logger.warning(f"FORMATTER DEBUG: No correct answer provided and no is_correct flags")
            return None
            
        # Case 1: Answer is already a letter (A, B, C, D)
        if isinstance(correct_answer, str) and len(correct_answer.strip()) == 1:
            letter = correct_answer.strip().upper()
            if letter in letter_map:
                logger.info(f"FORMATTER DEBUG: Direct letter match: {letter}")
                return letter
        
        # Case 2: Answer is a string with format like "A) Text", "B. Text"
        if isinstance(correct_answer, str):
            m = re.match(r"^([A-Da-d][).\-:]?)\s*(.*)$", correct_answer.strip())
            if m and m.group(1)[0].upper() in letter_map:
                letter = m.group(1)[0].upper()
                logger.info(f"FORMATTER DEBUG: Letter extracted from pattern: {letter}")
                return letter
        
        # Case 3: Answer is an ID that matches an option ID
        if isinstance(correct_answer, (str, int)) and str(correct_answer) in id_map:
            letter = id_map[str(correct_answer)]
            logger.info(f"FORMATTER DEBUG: ID match: {correct_answer} -> {letter}")
            return letter
            
        # Case 4: Answer is an index (0, 1, 2, 3) or string index ('0', '1', '2', '3')
        if (isinstance(correct_answer, (int, str)) and 
            (str(correct_answer) in index_map)):
            letter = index_map[str(correct_answer)]
            logger.info(f"FORMATTER DEBUG: Index match: {correct_answer} -> {letter}")
            return letter
        
        # Case 5: Answer is a string that matches option text
        if isinstance(correct_answer, str):
            # Try exact match
            text = correct_answer.strip()
            if text in text_map:
                letter = text_map[text]
                logger.info(f"FORMATTER DEBUG: Text exact match: {text} -> {letter}")
                return letter
                
            # Try lowercase match
            lower_text = text.lower()
            if lower_text in lower_text_map:
                letter = lower_text_map[lower_text]
                logger.info(f"FORMATTER DEBUG: Text lowercase match: {lower_text} -> {letter}")
                return letter
                
            # Try matching ignoring trailing punctuation
            text_no_punct = text.rstrip('.!?')
            lower_text_no_punct = text_no_punct.lower()
            for orig_text, letter in text_map.items():
                if text_no_punct == orig_text.rstrip('.!?'):
                    logger.info(f"FORMATTER DEBUG: Text match without punctuation: {text_no_punct} -> {letter}")
                    return letter
            for orig_text, letter in lower_text_map.items():
                if lower_text_no_punct == orig_text.rstrip('.!?').lower():
                    logger.info(f"FORMATTER DEBUG: Text lowercase match without punctuation: {lower_text_no_punct} -> {letter}")
                    return letter
                    
            # Try substring match as last resort for text matching
            for opt_text, letter in sorted(text_map.items(), key=lambda x: len(x[0]), reverse=True):
                if opt_text in text or text in opt_text:
                    logger.info(f"FORMATTER DEBUG: Text substring match: option '{opt_text}' matches answer '{text}' -> {letter}")
                    return letter
        
        # Case 6: Answer is a dict with letter, id, or text
        if isinstance(correct_answer, dict):
            # Check for letter key
            if 'letter' in correct_answer and correct_answer['letter'].upper() in letter_map:
                letter = correct_answer['letter'].upper()
                logger.info(f"FORMATTER DEBUG: Dict with letter: {letter}")
                return letter
                
            # Check for id key
            for id_key in ['id', 'option_id', 'answer_id', 'correct_id', 'correctId', 'correct_answer_id']:
                if id_key in correct_answer and str(correct_answer[id_key]) in id_map:
                    letter = id_map[str(correct_answer[id_key])]
                    logger.info(f"FORMATTER DEBUG: Dict with {id_key}: {correct_answer[id_key]} -> {letter}")
                    return letter
            
            # Check for text key
            for text_key in ['text', 'option', 'answer', 'correct_option', 'correct_answer', 'value']:
                if text_key in correct_answer and isinstance(correct_answer[text_key], str):
                    text = correct_answer[text_key].strip()
                    if text in text_map:
                        letter = text_map[text]
                        logger.info(f"FORMATTER DEBUG: Dict with {text_key} exact match: {text} -> {letter}")
                        return letter
                    
                    # Try lowercase
                    lower_text = text.lower()
                    if lower_text in lower_text_map:
                        letter = lower_text_map[lower_text]
                        logger.info(f"FORMATTER DEBUG: Dict with {text_key} lowercase match: {lower_text} -> {letter}")
                        return letter
                        
            # Check for 'correct' field
            if 'correct' in correct_answer:
                correct_value = correct_answer['correct']
                # If it's a boolean, find option with is_correct
                if isinstance(correct_value, bool) and correct_value:
                    for opt in options:
                        if opt.get('is_correct'):
                            logger.info(f"FORMATTER DEBUG: Dict with correct=True, found option with is_correct -> {opt['letter']}")
                            return opt['letter']
                # If it's a value, try to match it
                elif str(correct_value) in id_map:
                    letter = id_map[str(correct_value)]
                    logger.info(f"FORMATTER DEBUG: Dict with correct value as ID: {correct_value} -> {letter}")
                    return letter
                elif isinstance(correct_value, str) and correct_value in letter_map:
                    logger.info(f"FORMATTER DEBUG: Dict with correct value as letter: {correct_value}")
                    return correct_value.upper()
        
        # Case 7: Check options for is_correct flag
        for opt in options:
            # Check for is_correct flag (boolean or string "true")
            is_correct = opt.get('is_correct')
            if is_correct:
                if isinstance(is_correct, str) and is_correct.lower() == 'true':
                    is_correct = True
                if is_correct:
                    logger.info(f"FORMATTER DEBUG: Found option with is_correct flag -> {opt['letter']}")
                    return opt['letter']
                    
        # Final fallback: default to first option if no match found
        if options:
            logger.warning(f"FORMATTER DEBUG: No match found for answer {correct_answer}, defaulting to first option {options[0]['letter']}")
            return options[0]['letter']
            
        logger.error(f"FORMATTER DEBUG: Unable to determine answer and no options available")
        return 'A'  # Absolute last resort
    
    def format_question(self, question_type: str, parsed_question: Dict) -> Optional[Dict]:
        """Formats the parsed question into the internal representation."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Normalize question_type to lowercase for case-insensitive comparison
        question_type_lower = question_type.lower() if isinstance(question_type, str) else ""
        
        # Handle multiple choice questions (with various type names)
        if any(qt in question_type_lower for qt in ["multiple choice", "multiple_choice", "multiplechoice", "mcq"]):
            # Enhanced debug logging
            logger.info(f"FORMATTER DEBUG: Starting format_question with data: {parsed_question}")
            
            # Try to extract question text with various fallback fields
            question_text = self._extract_field(parsed_question, 'question', 
                                              ['text', 'prompt', 'question_text', 'stem'])
            
            # Try to extract options with various fallback fields
            options = self._extract_field(parsed_question, 'options', 
                                        ['choices', 'answers', 'alternatives', 'option_list'])
            
            # Try to extract correct answer with various fallback fields
            correct_answer = self._extract_field(parsed_question, 'correct_answer', 
                                              ['answer', 'correct_option', 'correct_answer_id', 
                                               'correct', 'correct_index', 'correct_option_index',
                                               'correctAnswer', 'correctOption'])
            
            # Try to extract explanation with various fallback fields
            explanation = self._extract_field(parsed_question, 'explanation', 
                                           ['rationale', 'reason', 'justification', 'feedback'])
            
            logger.info(f"FORMATTER DEBUG: question_text = {question_text}")
            logger.info(f"FORMATTER DEBUG: options = {options}")
            logger.info(f"FORMATTER DEBUG: correct_answer = {correct_answer}")
            
            # If we don't have key fields, abort
            if not question_text or not options:
                logger.warning(f"FORMATTER DEBUG: Missing key fields: question_text={bool(question_text)}, options={bool(options)}")
                return None
                
            # Normalize options to consistent format
            normalized_options = self._normalize_options(options)
            if len(normalized_options) < 2:  # Need at least 2 options for multiple choice
                logger.warning(f"FORMATTER DEBUG: Not enough options after normalization: {len(normalized_options)}")
                return None
                
            # Try to determine the correct answer
            correct_letter = self._normalize_correct_answer(correct_answer, normalized_options)
            if not correct_letter:
                logger.warning(f"FORMATTER DEBUG: Unable to determine correct answer")
                return None
                
            # Build the final result
            result = {
                'type': 'Multiple Choice',
                'text': question_text,
                'options': normalized_options,
                'answer': correct_letter,
                'explanation': explanation or ''
            }
            
            logger.info(f"FORMATTER DEBUG: Returning successful result: {result}")
            return result
        # Fill-in-the-Blank question type has been removed
        return None
