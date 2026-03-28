from google import genai
from google.genai import types
import json
import asyncio
import copy
import re
from typing import Dict, List, Optional, Callable


class SkillOptimizer:
    def __init__(self, api_key: str, model: str = "gemini-3-flash-preview"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    async def analyze_skill(self, skill_files: Dict[str, str]) -> dict:
        """Read all skill files, generate 3-5 test scenarios + 3-6 binary eval criteria.
        
        Returns:
            {"scenarios": [{"id": 1, "input": "...", "description": "..."}],
             "evals": [{"id": 1, "name": "...", "question": "...", "pass_condition": "...", "fail_condition": "..."}]}
        """
        skill_md = skill_files.get("SKILL.md", "")
        references = {k: v for k, v in skill_files.items() if k != "SKILL.md"}
        
        context = f"# Skill Content\n\n{skill_md}\n\n"
        if references:
            context += "# Reference Files\n\n"
            for filename, content in references.items():
                context += f"## {filename}\n\n{content}\n\n"
        
        prompt = f"""Analyze this agent skill and generate test scenarios and evaluation criteria.

{context}

Generate:
1. 3-5 diverse test scenarios that exercise different aspects of the skill
2. 3-6 binary evaluation criteria (yes/no questions) to measure quality

For each scenario, provide:
- id (number)
- description (what this scenario tests)
- input (the actual test input to send to the skill)

For each evaluation criterion, provide:
- id (number)
- name (short label)
- question (a yes/no question to evaluate the output)
- pass_condition (what makes it pass)
- fail_condition (what makes it fail)

Return valid JSON with this structure:
{{
  "scenarios": [
    {{"id": 1, "description": "...", "input": "..."}}
  ],
  "evals": [
    {{"id": 1, "name": "...", "question": "...", "pass_condition": "...", "fail_condition": "..."}}
  ]
}}"""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return result
    
    async def execute_skill(self, skill_md: str, test_input: str) -> str:
        """Run the skill as a system prompt with the test input as user message.
        
        Returns:
            The output from executing the skill.
        """
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"System instructions:\n\n{skill_md}\n\n---\n\nUser request:\n\n{test_input}")]
                )
            ]
        )
        
        return response.text
    
    async def score_output(self, output: str, test_input: str, evals: List[dict]) -> List[dict]:
        """Score one output against all evals.
        
        Returns:
            [{"eval_id": 1, "passed": true/false, "reason": "..."}]
        """
        eval_questions = "\n".join([
            f"{i+1}. {ev['question']}\n   Pass: {ev['pass_condition']}\n   Fail: {ev['fail_condition']}"
            for i, ev in enumerate(evals)
        ])
        
        prompt = f"""Evaluate this output against the criteria below.

# Test Input
{test_input}

# Output
{output}

# Evaluation Criteria
{eval_questions}

For each criterion, determine if it passes (yes) or fails (no), and explain why.

Return valid JSON array:
[
  {{"eval_id": 1, "passed": true, "reason": "..."}},
  {{"eval_id": 2, "passed": false, "reason": "..."}}
]"""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
    
    async def analyze_failures(self, experiment_results: list, evals: list, changelog: list) -> str:
        """Analyze which evals fail most and why.
        
        Returns:
            Text analysis of failure patterns.
        """
        results_summary = json.dumps(experiment_results, indent=2)
        evals_summary = json.dumps(evals, indent=2)
        changelog_summary = json.dumps(changelog, indent=2)
        
        prompt = f"""Analyze these experiment results to identify failure patterns.

# Evaluation Criteria
{evals_summary}

# Recent Experiment Results
{results_summary}

# Previous Changes (if any)
{changelog_summary}

Analyze:
1. Which evaluation criteria fail most frequently?
2. What patterns do you see in the failures?
3. What specific aspect of the skill needs improvement?

Provide a concise analysis focusing on the root cause."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt
        )
        
        return response.text
    
    async def mutate_skill(self, current_skill_md: str, failure_analysis: str, changelog: list) -> dict:
        """Propose ONE targeted change.
        
        Returns:
            {"description": "what changed", "reasoning": "why", "new_skill_md": "..."}
        """
        changelog_summary = "\n".join([
            f"- {entry['description']} ({entry['status']})"
            for entry in changelog[-5:] if changelog
        ]) if changelog else "No previous changes"
        
        prompt = f"""You are improving an agent skill prompt. Based on the failure analysis, propose ONE specific change.

# Current Skill Prompt
{current_skill_md}

# Failure Analysis
{failure_analysis}

# Recent Changes
{changelog_summary}

Propose ONE targeted change to address the failures. Changes can include:
- Adding specific rules or constraints
- Clarifying existing instructions
- Adding examples
- Restructuring sections
- Adding checklists or formats

Be surgical: change only what's needed. Avoid changes that were already tried and failed.

Return valid JSON:
{{
  "description": "Brief description of the change",
  "reasoning": "Why this addresses the failures",
  "new_skill_md": "The complete modified SKILL.md content"
}}"""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
    
    async def run_experiment(self, skill_md: str, scenarios: list, evals: list, runs_per_scenario: int = 2) -> dict:
        """Run skill across all scenarios, score all outputs.
        
        Returns:
            {"score": 14, "max_score": 20, "pass_rate": 70.0, "per_eval": [...], "per_scenario": [...]}
        """
        all_results = []
        per_scenario_results = []
        
        for scenario in scenarios:
            scenario_results = []
            
            for run_idx in range(runs_per_scenario):
                output = await self.execute_skill(skill_md, scenario["input"])
                scores = await self.score_output(output, scenario["input"], evals)
                
                scenario_results.append({
                    "scenario_id": scenario["id"],
                    "run": run_idx + 1,
                    "output": output,
                    "scores": scores
                })
                all_results.extend(scores)
            
            passed = sum(1 for r in scenario_results for s in r["scores"] if s["passed"])
            total = len(scenario_results) * len(evals)
            
            per_scenario_results.append({
                "scenario_id": scenario["id"],
                "description": scenario["description"],
                "passed": passed,
                "total": total,
                "pass_rate": round((passed / total * 100), 1) if total > 0 else 0
            })
        
        per_eval_results = []
        for eval_item in evals:
            eval_scores = [r for r in all_results if r["eval_id"] == eval_item["id"]]
            passed = sum(1 for s in eval_scores if s["passed"])
            total = len(eval_scores)
            
            per_eval_results.append({
                "eval_id": eval_item["id"],
                "name": eval_item["name"],
                "passed": passed,
                "total": total,
                "pass_rate": round((passed / total * 100), 1) if total > 0 else 0
            })
        
        total_passed = sum(1 for r in all_results if r["passed"])
        total_checks = len(all_results)
        
        return {
            "score": total_passed,
            "max_score": total_checks,
            "pass_rate": round((total_passed / total_checks * 100), 1) if total_checks > 0 else 0,
            "per_eval": per_eval_results,
            "per_scenario": per_scenario_results,
            "raw_results": all_results
        }
    
    async def optimize(
        self,
        skill_files: dict,
        scenarios: list,
        evals: list,
        max_rounds: int = 20,
        callback: Optional[Callable] = None
    ):
        """Main optimization loop.
        
        1. Run baseline experiment (experiment 0)
        2. Loop:
           a. Analyze failures
           b. Mutate skill (one change)
           c. Run experiment
           d. If score improved: keep. Else: revert.
           e. Log to changelog
           f. Call callback with progress event
           g. Stop if 95%+ for 3 consecutive or max_rounds hit
        3. Return final results
        """
        skill_md = skill_files.get("SKILL.md", "")
        current_skill_md = skill_md
        original_skill_md = skill_md
        
        changelog = []
        experiments = []
        consecutive_95_plus = 0
        
        if callback:
            await callback({"type": "status", "data": {"message": "Running baseline experiment..."}})
        
        baseline = await self.run_experiment(current_skill_md, scenarios, evals)
        baseline_result = {
            "experiment_id": 0,
            "description": "Baseline",
            "status": "baseline",
            "score": baseline["score"],
            "max_score": baseline["max_score"],
            "pass_rate": baseline["pass_rate"],
            "per_eval": baseline["per_eval"],
            "per_scenario": baseline["per_scenario"]
        }
        experiments.append(baseline_result)
        
        if callback:
            await callback({"type": "baseline", "data": baseline_result})
        
        best_score = baseline["score"]
        best_skill_md = current_skill_md
        
        if baseline["pass_rate"] >= 95:
            consecutive_95_plus = 1
        
        for round_idx in range(max_rounds):
            if consecutive_95_plus >= 3:
                break
            
            recent_experiments = experiments[-3:] if len(experiments) >= 3 else experiments
            failure_analysis = await self.analyze_failures(recent_experiments, evals, changelog)
            
            if callback:
                await callback({
                    "type": "experiment_start",
                    "data": {
                        "experiment_id": round_idx + 1,
                        "analyzing": True
                    }
                })
            
            mutation = await self.mutate_skill(current_skill_md, failure_analysis, changelog)
            
            if callback:
                await callback({
                    "type": "experiment_start",
                    "data": {
                        "experiment_id": round_idx + 1,
                        "description": mutation["description"]
                    }
                })
            
            new_skill_md = mutation["new_skill_md"]
            
            result = await self.run_experiment(new_skill_md, scenarios, evals)
            
            if result["score"] > best_score:
                status = "keep"
                current_skill_md = new_skill_md
                best_score = result["score"]
                best_skill_md = new_skill_md
                
                if result["pass_rate"] >= 95:
                    consecutive_95_plus += 1
                else:
                    consecutive_95_plus = 0
            else:
                status = "discard"
                if result["pass_rate"] >= 95:
                    consecutive_95_plus += 1
                else:
                    consecutive_95_plus = 0
            
            experiment_result = {
                "experiment_id": round_idx + 1,
                "description": mutation["description"],
                "reasoning": mutation["reasoning"],
                "status": status,
                "score": result["score"],
                "max_score": result["max_score"],
                "pass_rate": result["pass_rate"],
                "per_eval": result["per_eval"],
                "per_scenario": result["per_scenario"]
            }
            
            experiments.append(experiment_result)
            changelog.append({
                "experiment_id": round_idx + 1,
                "description": mutation["description"],
                "reasoning": mutation["reasoning"],
                "status": status,
                "score_before": best_score if status == "discard" else experiments[-2]["score"],
                "score_after": result["score"]
            })
            
            if callback:
                await callback({"type": "experiment_result", "data": experiment_result})
        
        kept_count = sum(1 for e in experiments if e.get("status") == "keep")
        discarded_count = sum(1 for e in experiments if e.get("status") == "discard")
        
        final_result = {
            "baseline_score": baseline["pass_rate"],
            "final_score": experiments[-1]["pass_rate"],
            "experiments_run": len(experiments) - 1,
            "kept": kept_count,
            "discarded": discarded_count,
            "changelog": changelog,
            "experiments": experiments,
            "improved_skill_md": best_skill_md,
            "original_skill_md": original_skill_md
        }
        
        if callback:
            await callback({"type": "complete", "data": final_result})
        
        return final_result
