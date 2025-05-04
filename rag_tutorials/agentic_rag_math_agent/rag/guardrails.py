import dspy
import os
from dotenv import load_dotenv

# Load API key
load_dotenv("config/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("🔐 Loaded OPENAI_API_KEY:", "✅ Found" if OPENAI_API_KEY else "❌ Missing")

# Configure LM
lm = dspy.LM(model="gpt-4o", api_key=OPENAI_API_KEY)
dspy.configure(lm=lm)

# ✅ Signature for Input Guard
class ClassifyMath(dspy.Signature):
    """
    Decide if a question is related to mathematics — this includes problem-solving,
    formulas, definitions (e.g., 'what is calculus'),examples to any topic, or theoretical topics.

    Return only 'Yes' or 'No' as your final verdict.
    """
    question: str = dspy.InputField()
    verdict: str = dspy.OutputField(desc="Respond with 'Yes' if the question is related to mathematics, 'No' otherwise.")



# ✅ Input Validator
class InputValidator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classifier = dspy.Predict(ClassifyMath)
        self.validate_question = dspy.ChainOfThought(
            ClassifyMath,
            examples=[
                {"question": "What is the derivative of x^2?", "verdict": "Yes"},
                {"question": "Explain the chain rule in calculus.", "verdict": "Yes"},
                {"question": "Why do I need to learn algebra?", "verdict": "Yes"},
                {"question": "What is the Pythagorean theorem?", "verdict": "Yes"},
                {"question": "How do I solve a quadratic equation?", "verdict": "Yes"},
                {"question": "What is the area of a circle?", "verdict": "Yes"},
                {"question": "How is math used in real life?", "verdict": "Yes"},
                {"question": "What is the purpose of trigonometry?", "verdict": "Yes"},
                {"question": "What is the Fibonacci sequence?", "verdict": "Yes"},
                {"question": "can you tell me about rhombus?", "verdict": "Yes"},
                {"question": "what is a circle?", "verdict": "Yes"},
                {"question": "What is the formula for the area of a circle?", "verdict": "Yes"},
                {"question": "What is the formula for the circumference of a circle?", "verdict": "Yes"},
                {"question": "What is the formula for the volume of a cone?", "verdict": "Yes"},
                {"question": "What is the formula for the area of a parallelogram?", "verdict": "Yes"},
                {"question": "What is the formula for the area of a trapezoid?", "verdict": "Yes"},
                {"question": "What is the formula for the surface area of a cube?", "verdict": "Yes"},
                {"question": "What is the area of parallelogram?", "verdict": "Yes"},
                {"question": "What is a square?", "verdict": "Yes"},
                {"question": "Explain rectangle?", "verdict": "Yes"},
                {"question": "can you tell me about pentagon?", "verdict": "Yes"},
                {"question": "What is the formula for the volume of a sphere?", "verdict": "Yes"},
                {"question": "What is the difference between a mean and median?", "verdict": "Yes"},
                {"question": "What is the formula for the area of a triangle?", "verdict": "Yes"},
                {"question": "What is the difference between a permutation and a combination?", "verdict": "Yes"},
                {"question": "What is the formula for the slope of a line?", "verdict": "Yes"},
                {"question": "What is the difference between a rational and irrational number?", "verdict": "Yes"},
                {"question": "What is the formula for the area of a rectangle?", "verdict": "Yes"},
                {"question": "What is the formula for the volume of a cylinder?", "verdict": "Yes"},
                {"question": "What is the formula for the area of a trapezoid?", "verdict": "Yes"},
                {"question": "What is the formula for the surface area of a sphere?", "verdict": "Yes"},
                {"question": "What is the formula for the surface area of a cylinder?", "verdict": "Yes"},
                {"question": "What is the integral of sin(x)?", "verdict": "Yes"},
                {"question": "What is the difference between mean and median?", "verdict": "Yes"},
                {"question": "What is the formula for the circumference of a circle?", "verdict": "Yes"},
                {"question": "What is the quadratic formula?", "verdict": "Yes"},   
                {"question": "Tell me a good movie to watch.", "verdict": "No"},
                {"question": "What is AI?", "verdict": "No"},
            ]
        )
    def forward(self, question):
        response = self.classifier(question=question)
        print("🧠 InputValidator Response:", response.verdict)
        return response.verdict.lower().strip() == "yes"

# ✅ Output Validator (no change unless needed)
class OutputValidator(dspy.Module):
    class ValidateAnswer(dspy.Signature):
        """Check if the answer is correct, step-by-step, and relevant to the question."""
        question = dspy.InputField(desc="The original math question.")
        answer = dspy.InputField(desc="The model-generated answer.")
        verdict = dspy.OutputField(desc="Answer only 'Yes' or 'No'")

    def __init__(self):
        super().__init__()
        self.validate_answer = dspy.Predict(self.ValidateAnswer)

    def forward(self, question, answer):
        response = self.validate_answer(
            question=question,
            answer=answer
        )
        print("🧠 OutputValidator Response:", response.verdict)
        return response.verdict.lower().strip() == "yes"

# Initialize validators
input_validator = InputValidator()
output_validator = OutputValidator()
