import json
from datetime import datetime

class AgentMemory:
    def __init__(self):
        self.short_term = []
        self.long_term_file = "long_term_memory.json"

    def add_interaction(self, user_input, agent_output):
        record = {
            "time": datetime.utcnow().isoformat(),
            "input": user_input,
            "output": agent_output
        }
        self.short_term.append(record)
        self._persist(record)

    def _persist(self, record):
        try:
            data = []
            try:
                with open(self.long_term_file, "r") as f:
                    data = json.load(f)
            except FileNotFoundError:
                pass

            data.append(record)
            with open(self.long_term_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Memory persistence failed:", e)
