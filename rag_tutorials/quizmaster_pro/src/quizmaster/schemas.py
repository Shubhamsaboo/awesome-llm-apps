MCQ_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "letter": {"type": "string", "pattern": "^[A-D]$"},
                    "text": {"type": "string"}
                },
                "required": ["letter", "text"]
            },
            "minItems": 4,
            "maxItems": 4
        },
        "correct_answer": {"type": "string", "pattern": "^[A-D]$"},
        "explanation": {"type": "string"}
    },
    "required": ["question", "options", "correct_answer", "explanation"]
}




