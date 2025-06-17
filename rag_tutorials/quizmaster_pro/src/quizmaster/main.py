from .quiz_generator import QuizGenerator
from .config import QuizConfig

def main():
    """Main function to generate a quiz."""
    config = QuizConfig()
    quiz_generator = QuizGenerator(config)
    
    processed_content = {
        'content': 'The capital of France is Paris.',
        'extracted_concepts': [
            {
                'content': 'The capital of France is Paris.',
                'concept_name': 'Capital of France',
                'source_sentence': 'The capital of France is Paris.'
            }
        ]
    }
    
    question_types = ["Multiple Choice"]
    num_questions = 1
    difficulty = "Easy"
    
    quiz = quiz_generator.generate_quiz(
        processed_content,
        question_types,
        num_questions,
        difficulty
    )
    
    print(quiz)

if __name__ == "__main__":
    main()
