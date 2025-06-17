from typing import Dict, List

class QuizResult:
    def __init__(self, questions: List[Dict], metadata: Dict, model_used: str, content_length: int, fallback_used: bool):
        self.questions = questions
        self.metadata = metadata
        self.model_used = model_used
        self.content_length = content_length
        self.fallback_used = fallback_used

    def to_dict(self) -> Dict:
        return {
            'questions': self.questions,
            'metadata': self.metadata,
            'model_used': self.model_used,
            'content_length': self.content_length,
            'fallback_used': self.fallback_used
        }
