from __future__ import annotations

import copy
from typing import List, Dict

from ...base import *
from .func_ruin import LHNSFunction, LHNSFunctionRuin

class LHNSPrompt:
    @classmethod
    def create_instruct_prompt(cls, prompt: str) -> List[Dict]:
        content = [
            {'role': 'system', 'message': cls.get_system_prompt()},
            {'role': 'user', 'message': prompt}
        ]
        return content

    @classmethod
    def get_system_prompt(cls) -> str:
        return ''

    @classmethod
    def get_prompt_i1(cls, task_prompt: str, template_function: LHNSFunction):
        # template
        temp_func = copy.deepcopy(template_function)
        temp_func.body = ''
        # create prompt content
        prompt_content = f'''{task_prompt}
1. First, describe your new algorithm and main steps in one sentence. The description must be inside within boxed {{}}. 
2. Next, implement the following Python function:
{str(temp_func)}
Import statements should be placed outside the function. Do not give additional explanations.'''
        return prompt_content

    @classmethod
    def get_prompt_merge(cls, task_prompt: str, indi: LHNSFunction, prev_indi: LHNSFunction, template_function: LHNSFunction):
        assert hasattr(indi, 'algorithm')
        
        indi = LHNSFunctionRuin.merge_features(indi, prev_indi.features)
        # template
        temp_func = copy.deepcopy(template_function)
        temp_func.body = ''
        # create prompt content for all individuals
        indivs_prompt = ''
        indi.docstring = ''
        indivs_prompt += f'No. A algorithm and the corresponding code are:\n{indi.algorithm}\n{str(indi)}'
        indivs_prompt += f'No. B algorithm is:\n{indi.algorithm}'
        # create prmpt content
        prompt_content = f'''{task_prompt}
I have algorithm A with its code, which inserts key lines from algorithm B's code, inserted just before the 'return' statement:
{indivs_prompt}
Please review the given code, integrating two algorithm descriptions provided to rearrange it to get a better result.
1. First, describe your new algorithm and main steps in one sentence. The description must be inside within boxed {{}}.
2. Next, implement the following Python function:
{str(temp_func)}
Import statements should be placed outside the function. Do not give additional explanations.'''
        return prompt_content

    @classmethod
    def get_prompt_rr(cls, task_prompt: str, indi: LHNSFunction, cooling_rate: float, template_function: LHNSFunction):
        assert hasattr(indi, 'algorithm')
        indi, number_of_delete = LHNSFunctionRuin.delete_function_snips(indi, cooling_rate)
        # template
        temp_func = copy.deepcopy(template_function)
        temp_func.body = ''

        # create prmpt content
        prompt_content = f'''{task_prompt}
I have one algorithm with its code as follows. Algorithm description:
{indi.algorithm}
Code:
{str(indi)}
{number_of_delete} lines have been removed from the provided code. 
Please review the code, revise and explore more lines to improve the algorithm.
1. First, describe your new algorithm and main steps in one sentence. The description must be inside within boxed {{}}.
2. Next, implement the following Python function:
{str(temp_func)}
Import statements should be placed outside the function. Do not give additional explanations.'''
        return prompt_content

    @classmethod
    def get_prompt_m(cls, task_prompt: str, indi: LHNSFunction, template_function: LHNSFunction):
        assert hasattr(indi, 'algorithm')
        # template
        temp_func = copy.deepcopy(template_function)
        temp_func.body = ''
        # create prmpt content
        prompt_content = f'''{task_prompt}
I have one algorithm with its code as follows. Algorithm description:
{indi.algorithm}
Code:
{str(indi)}
Please modify the provided algorithm to improve its performance, where you can determine the degree of modification needed.
1. First, describe your new algorithm and main steps in one sentence. The description must be inside within boxed {{}}.
2. Next, implement the following Python function:
{str(temp_func)}
Import statements should be placed outside the function. Do not give additional explanations.'''
        return prompt_content
