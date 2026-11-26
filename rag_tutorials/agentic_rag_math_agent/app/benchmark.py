# Add the project root to the Python path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import pandas as pd
import time
from datetime import datetime
from rag.query_router import answer_math_question
from data.load_gsm8k_data import load_jeebench_dataset

def is_answer_correct(expected, response: str) -> bool:
    """Check that the gold answer appears as a standalone token in the response.

    A plain substring test counts gold "C" as correct for any reply containing
    the letter c, and gold "12" as correct inside "112" or "0.12".
    """
    pattern = rf"(?<![A-Za-z0-9.]){re.escape(str(expected).strip())}(?![A-Za-z0-9]|\.\d)"
    return re.search(pattern, response) is not None


def benchmark_math_agent(limit: int = 10):
    # ✅ Always filter math-only questions
    df = load_jeebench_dataset()
    df = df.head(limit)  # Limit the number of questions for benchmarking

    total = len(df)
    correct = 0
    results = []

    for idx, row in df.iterrows():
        question = row["question"]
        expected = row["gold"]
        start = time.time()

        try:
            response = answer_math_question(question)
            is_correct = is_answer_correct(expected, response)
            if is_correct:
                correct += 1

            results.append({
                "Question": question,
                "Expected": expected,
                "Predicted": response,
                "Correct": is_correct,
                "TimeTakenSec": round(time.time() - start, 2)
            })

        except Exception as e:
            results.append({
                "Question": question,
                "Expected": expected,
                "Predicted": f"Error: {e}",
                "Correct": False,
                "TimeTakenSec": None
            })

    df_result = pd.DataFrame(results)
    accuracy = correct / total * 100
    return df_result, accuracy
