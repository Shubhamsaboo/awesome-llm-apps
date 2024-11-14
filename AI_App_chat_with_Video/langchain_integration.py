import torch
from transformers import pipeline
import json
import re

# Initialize the text-generation pipeline with the model
model_id = "meta-llama/Llama-3.2-1B"

pipe = pipeline("text-generation", model=model_id, torch_dtype=torch.bfloat16, device=0)


def generate_answer_and_suggested_questions(context, question):
    # Ensure entire context is sent (not truncated)
    print("Full Context:", context)  # Debugging print

    # Prompt for generating the answer
    answer_prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
    print("Answer Generation Prompt:", answer_prompt)  # Debugging print

    # Generate the answer using the model
    with torch.no_grad():
        answer_response = pipe(
            answer_prompt,
            max_new_tokens=150,
            num_return_sequences=1,
            top_k=50,
            top_p=0.9,
        )[0]["generated_text"]
        print("Raw Answer Response:", answer_response)  # Debugging print

        # Extract the answer by isolating text after "Answer:"
        if "Answer:" in answer_response:
            answer = answer_response.split("Answer:")[-1].strip()
        else:
            answer = answer_response.strip()
        print("Extracted Answer:", answer)  # Debugging print

        # Prompt for generating suggested questions, specifying array format for clarity
        suggestion_prompt = f"Context: {context}\nQuestion: {question}\nPlease provide exactly three follow-up questions in an array format, each question as a distinct item related to the topic:"
        print("Suggestion Generation Prompt:", suggestion_prompt)  # Debugging print

        # Generate the suggested questions using the model
        suggested_questions_response = pipe(
            suggestion_prompt,
            max_new_tokens=100,
            num_return_sequences=1,
            top_k=50,
            top_p=0.9,
        )[0]["generated_text"]
        print(
            "Raw Suggested Questions Response:", suggested_questions_response
        )  # Debugging print

        # Extract and clean the suggested questions
        if (
            "Please provide exactly three follow-up questions"
            in suggested_questions_response
        ):
            suggested_questions_text = suggested_questions_response.split(
                "Please provide exactly three follow-up questions"
            )[-1].strip()
        else:
            suggested_questions_text = suggested_questions_response.strip()

        # Now split the text by punctuations like '.', '?' or '\n' (for distinct questions)
        suggested_questions = re.split(
            r"[?.!]\s*", suggested_questions_text
        )  # Split by sentence-ending punctuation
        suggested_questions = [
            q.strip() for q in suggested_questions if q.strip()
        ]  # Clean up any empty strings

        # Ensure exactly 3 questions are extracted
        suggested_questions = suggested_questions[:3]

        # Remove any unwanted introductory phrase from the first question if present
        if suggested_questions and "in an array format" in suggested_questions[0]:
            suggested_questions[0] = re.sub(
                r"in an array format, each question as a distinct item related to the topic:\s*",
                "",
                suggested_questions[0],
            )

        print("Extracted Suggested Questions:", suggested_questions)  # Debugging print

    # Build the response structure
    response = {"answer": answer, "suggested_questions": suggested_questions}
    print("Final Response:", json.dumps(response, indent=2))  # Debugging print

    return response


# Example usage
if __name__ == "__main__":
    example_context = "The Llama 3.2 collection of multilingual large language models is optimized for dialogue use cases."
    example_question = "What is the main purpose?"

    response = generate_answer_and_suggested_questions(
        example_context, example_question
    )
