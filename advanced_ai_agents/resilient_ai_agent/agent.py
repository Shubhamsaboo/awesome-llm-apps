from planner import Planner
from memory import AgentMemory
from evaluator import Evaluator
from tools import LLMTool
from config import MAX_RETRIES

class ResilientAgent:
    def __init__(self):
        self.planner = Planner()
        self.memory = AgentMemory()
        self.evaluator = Evaluator()
        self.llm = LLMTool()

    def run(self, task):
        plan = self.planner.create_plan(task)
        print("Plan:", plan)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"Attempt {attempt}")
                response = self.llm.run(task)
                evaluation = self.evaluator.evaluate(task, response)

                if evaluation["success"]:
                    self.memory.add_interaction(task, response)
                    return {
                        "response": response,
                        "evaluation": evaluation
                    }

                print("Evaluation failed:", evaluation["issues"])

            except Exception as e:
                print("Execution error:", e)

        return {
            "response": None,
            "evaluation": {
                "success": False,
                "issues": ["Max retries exceeded"]
            }
        }


if __name__ == "__main__":
    agent = ResilientAgent()
    task = input("Enter a task: ")
    result = agent.run(task)
    print("\nFinal Result:\n", result)
