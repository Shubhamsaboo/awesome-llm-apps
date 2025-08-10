from __future__ import annotations

import re
from typing import Tuple, List, Dict

from .prompt import LHNSPrompt
from .func_ruin import LHNSFunction, LHNSProgram
from ...base import LLM, SampleTrimmer


class LHNSSampler:
    def __init__(self, sampler: LLM, template_program: str | LHNSProgram):
        self._sampler = sampler
        self._template_program = template_program

    def get_thought_and_function(self, prompt: str) -> Tuple[str, LHNSFunction]:
        response = self._sampler.draw_sample(prompt)
        thought = self.__class__.trim_thought_from_response(response)
        code = SampleTrimmer.trim_preface_of_function(response)
        function = SampleTrimmer.sample_to_function(code, self._template_program)
        function = LHNSFunction.convert_function_to_lhnsfunction(function)
        return thought, function

    @classmethod
    def trim_thought_from_response(cls, response: str) -> str | None:
        try:
            pattern = r'\{.*?\}'  # Compared with r'\{(.*)\}'
            bracketed_texts = re.findall(pattern, response)
            return bracketed_texts[0]
        except:
            return None
