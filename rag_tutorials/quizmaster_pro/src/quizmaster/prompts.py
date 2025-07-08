import random

def get_question_prompt(question_type: str, difficulty: str, context: str) -> str:
    """Constructs the prompt for generating a question with variability to prevent duplicates."""
    
    # Add variability to prevent identical questions
    instruction_variations = [
        "Create a {difficulty} difficulty {question_type} question based on the following context.",
        "Generate a {difficulty} level {question_type} question using the provided context.",
        "Develop a {difficulty} {question_type} question from the given context material.",
        "Formulate a {difficulty} difficulty {question_type} question based on this context.",
        "Design a {difficulty} level {question_type} question using the context below."
    ]
    
    understanding_variations = [
        "Ensure the question tests deep understanding, not just recall.",
        "Focus on testing comprehension and application rather than memorization.",
        "Create a question that assesses critical thinking about the material.",
        "Design the question to evaluate understanding of key concepts.",
        "Make sure the question tests analytical thinking, not just factual recall."
    ]
    
    selected_instruction = random.choice(instruction_variations).format(
        difficulty=difficulty, question_type=question_type
    )
    selected_understanding = random.choice(understanding_variations)
    
    base_prompt = f"""
You are an expert quiz question generator. {selected_instruction}
{selected_understanding}

Context:
{context}
"""
    
    if question_type == "Multiple Choice":
        mc_variations = [
            "- Provide 4 plausible options with only one correct answer.\n- Make incorrect options realistic but clearly wrong.",
            "- Create 4 believable answer choices, ensuring only one is correct.\n- Design distractors that are plausible but distinctly incorrect.",
            "- Develop 4 answer options where 3 are wrong but sound reasonable.\n- Ensure the incorrect choices test common misconceptions.",
            "- Generate 4 options with one clear correct answer.\n- Make wrong answers challenging but definitively incorrect."
        ]
        
        return base_prompt + f"""
{random.choice(mc_variations)}

CRITICAL: Your response MUST be a single, valid JSON object only. No explanatory text, no markdown, no code blocks. Just the raw JSON.

Example format:
{{"question": "What is the primary characteristic of Python?", "options": [{{"letter": "A", "text": "Compiled language"}}, {{"letter": "B", "text": "High-level interpreted language"}}, {{"letter": "C", "text": "Assembly-based language"}}, {{"letter": "D", "text": "Low-level system language"}}], "correct_answer": "B", "explanation": "Python is a high-level interpreted programming language"}}

IMPORTANT: The 'question' field must be a STRING, not an object. Do not nest the question text.

Required JSON structure (EXACT format required):
{{
  "question": "Question text as a string",
  "options": [
    {{"letter": "A", "text": "Option A"}},
    {{"letter": "B", "text": "Option B"}},
    {{"letter": "C", "text": "Option C"}},
    {{"letter": "D", "text": "Option D"}}
  ],
  "correct_answer": "A",
  "explanation": "Detailed explanation"
}}"""

# Fill-in-the-Blank question type has been removed
    return base_prompt
