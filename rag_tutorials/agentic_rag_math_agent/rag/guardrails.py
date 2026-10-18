import dspy
import os
import re
from typing import Optional
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



def parse_verdict(verdict) -> Optional[bool]:
    """Read a Yes/No verdict from the model.

    Accepts "Yes", "yes.", "**Yes**", "Yes, this is math." etc. Returns None
    when the reply is neither, so callers can log it instead of guessing.
    """
    match = re.match(r"\W*(yes|no)\b", str(verdict or ""), re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "yes"


# Few-shot examples for the input guard
MATH_CLASSIFIER_EXAMPLES = [
    ("What is the derivative of x^2?", "Yes"),
    ("Explain the chain rule in calculus.", "Yes"),
    ("Why do I need to learn algebra?", "Yes"),
    ("What is the Pythagorean theorem?", "Yes"),
    ("How do I solve a quadratic equation?", "Yes"),
    ("What is the area of a circle?", "Yes"),
    ("How is math used in real life?", "Yes"),
    ("What is the purpose of trigonometry?", "Yes"),
    ("What is the Fibonacci sequence?", "Yes"),
    ("can you tell me about rhombus?", "Yes"),
    ("what is a circle?", "Yes"),
    ("What is the formula for the area of a circle?", "Yes"),
    ("What is the formula for the circumference of a circle?", "Yes"),
    ("What is the formula for the volume of a cone?", "Yes"),
    ("What is the formula for the area of a parallelogram?", "Yes"),
    ("What is the formula for the area of a trapezoid?", "Yes"),
    ("What is the formula for the surface area of a cube?", "Yes"),
    ("What is the area of parallelogram?", "Yes"),
    ("What is a square?", "Yes"),
    ("Explain rectangle?", "Yes"),
    ("can you tell me about pentagon?", "Yes"),
    ("What is the formula for the volume of a sphere?", "Yes"),
    ("What is the formula for the area of a triangle?", "Yes"),
    ("What is the difference between a permutation and a combination?", "Yes"),
    ("What is the formula for the slope of a line?", "Yes"),
    ("What is the difference between a rational and irrational number?", "Yes"),
    ("What is the formula for the area of a rectangle?", "Yes"),
    ("What is the formula for the volume of a cylinder?", "Yes"),
    ("What is the formula for the surface area of a sphere?", "Yes"),
    ("What is the formula for the surface area of a cylinder?", "Yes"),
    ("What is the integral of sin(x)?", "Yes"),
    ("What is the difference between mean and median?", "Yes"),
    ("What is the quadratic formula?", "Yes"),
    ("Tell me a good movie to watch.", "No"),
    ("What is AI?", "No"),
]


# ✅ Input Validator
class InputValidator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classifier = dspy.Predict(ClassifyMath)
        # Attach the examples as demos so they are actually sent to the model
        self.classifier.demos = [
            dspy.Example(question=q, verdict=v).with_inputs("question")
            for q, v in MATH_CLASSIFIER_EXAMPLES
        ]

    def forward(self, question):
        response = self.classifier(question=question)
        print("🧠 InputValidator Response:", response.verdict)
        is_math = parse_verdict(response.verdict)
        if is_math is None:
            print(f"⚠️ InputValidator got an unclear verdict {response.verdict!r}; treating as not math.")
            return False
        return is_math

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
        is_valid = parse_verdict(response.verdict)
        if is_valid is None:
            print(f"⚠️ OutputValidator got an unclear verdict {response.verdict!r}; treating as failed.")
            return False
        return is_valid

# Initialize validators
input_validator = InputValidator()
output_validator = OutputValidator()
