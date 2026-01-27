class Evaluator:
    def evaluate(self, task, response):
        issues = []

        if not response or len(response.strip()) < 10:
            issues.append("Response too short")

        success = len(issues) == 0

        return {
            "success": success,
            "issues": issues,
            "confidence": 0.9 if success else 0.4
        }
