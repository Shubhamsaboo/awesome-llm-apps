from __future__ import annotations

import re
from typing import Tuple, List, Dict

from .prompt import MAPrompt
from ...base import LLM, SampleTrimmer, Function, Program


class MASampler:
    def __init__(self, llm: LLM, template_program: str | Program):
        self.llm = llm
        self._template_program = template_program

    def get_thought_and_function(self, task_description: str, prompt: str) -> Tuple[str, Function]:
        response = self.llm.draw_sample(prompt)
        thought = self.__class__.trim_thought_from_response(response)
        code = SampleTrimmer.trim_preface_of_function(response)
        function = SampleTrimmer.sample_to_function(code, self._template_program)
        if thought is None or function is None:
            return thought, function
        prompt2 = self.get_prompt_refine(task_description, thought, str(function))
        describe = self.llm.draw_sample(prompt2)
        return describe, function

    def get_prompt_refine(self, task_prompt: str, idea: str, code: str):
        prompt_content = task_prompt + "\n" + "Following is the Design Idea of a heuristic algorithm for the problem and the code for implementing the heuristic algorithm.\n"
        prompt_content += "\nDesign Idea:\n" + idea
        prompt_content += "\n\nCode:\n" + code
        prompt_content += "\n\nThe content of the Design Idea idea cannot fully represent what the algorithm has done informative. So, now you should re-describe the algorithm using less than 3 sentences.\n"
        prompt_content += "Hint: You should reference the given Design Idea and highlight the most critical design ideas of the code. You can analyse the code to describe which variables are given higher priorities and which variables are given lower priorities, the parameters and the structure of the code."
        return prompt_content

    @classmethod
    def trim_thought_from_response(cls, response: str) -> str | None:
        try:
            pattern = r'\{(.*?)\}'  # Compared with r'\{(.*)\}'
            bracketed_texts = re.findall(pattern, response)
            return bracketed_texts[0]
        except:
            return None
